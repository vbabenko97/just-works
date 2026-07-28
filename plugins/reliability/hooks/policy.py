#!/usr/bin/env python3
"""The policy layer: what a repository may add, and how its manifest is validated.

Three states, and the third is the one that matters:

  ABSENT   no `.claude/reliability-policy.json`. Universal rules only. An ordinary
           repository is usable: `npm run build` and `bash deploy.sh` are not
           refused, because nothing in that repository claims to have reviewed
           anything.
  VALID    a manifest that parses, carries a bundled and supported version, and
           declares only known keys with well-formed values. Universal rules plus
           everything the manifest asks for.
  INVALID  a manifest that exists but cannot be trusted: malformed JSON, an
           unsupported version, unknown keys, a non-regular file, or a symlink
           resolving outside the repository. Mutation is denied with a
           configuration error. It is never downgraded to ABSENT — a repository
           that declared policy and got it wrong must not silently run with less
           enforcement than it asked for, because the failure would be invisible
           exactly when it matters.

Reads survive an invalid manifest deliberately: a repository whose policy is broken
has to remain inspectable, or it cannot be diagnosed or fixed.

Policy is monotonic. There is no key that permits anything. `allowed-scripts.json`
excepts exactly one denial that lives in this file — unknown local scripts — and
the engine never reaches this layer for a decision the universal layer already
refused.
"""
from __future__ import annotations

import hashlib
import json
import os
import pathlib
import re
import stat

from rules import (
    ENV_VALUE_FLAGS, SHELLS, flag_cluster, head_and_args, looks_like_script,
    tokens,
)

ABSENT, VALID, INVALID = "absent", "valid", "invalid"

MANIFEST_REL = ".claude/reliability-policy.json"

# Bundled with this plugin version. A manifest asking for anything else is invalid,
# not "close enough": the repository is describing rules this build cannot enforce.
SUPPORTED_POLICY_VERSIONS = (1,)

ALLOWED_KEYS = {
    "policy_version", "contract_version", "description", "allowlist", "contract",
    "protected", "maintenance", "require_subagent_receipts",
}
ALLOWED_MAINTENANCE_KEYS = {"issuer", "ledger"}

RUNNER_RULES: dict[str, set[str] | None] = {
    "make": None, "rake": None, "just": None, "task": None, "tox": None,
    "nox": None, "invoke": None, "gradle": None, "mvn": None, "npx": None,
    "pnpx": None, "bunx": None, "gulp": None, "grunt": None,
    "npm": {"run", "run-script", "start", "test", "exec", "explore"},
    "pnpm": {"run", "exec", "start", "test"},
    "yarn": {"run", "start", "test", "exec", "dlx", "node"},
    "uv": {"run", "tool"},
    "poetry": {"run"},
    "pipenv": {"run"},
    "hatch": {"run"},
    "cargo": {"run"},
}

OPAQUE_GIT_SUBCOMMANDS = {"apply", "am"}
INSTALLERS = {"pip", "pip3", "npm", "pnpm", "yarn", "brew", "gem", "cargo"}
INSTALL_SUBCOMMANDS = {"install", "i", "ci", "add", "reinstall"}
PAYLOAD_FLAGS = {"-r", "--requirement", "-e", "--editable", "-c", "--constraint",
                 "-i", "--input", "--file"}
LOCAL_ARCHIVES = (".whl", ".tar.gz", ".tgz", ".zip", ".patch", ".diff", ".gem")
INTERPRETERS = {"python", "python2", "python3", "node", "nodejs", "ruby", "perl",
                "php", "deno", "bun", "Rscript", "osascript", "tsx", "ts-node"}

INLINE_SIDE_EFFECT = re.compile(
    r"(open\s*\([^)]*['\"][wax]|write_text|writelines|write_bytes|makedirs|"
    r"\bmkdir\b|copyfile|copytree|copy2|copymode|writeFileSync|appendFileSync|"
    r"mkdirSync|renameSync|os\.system|subprocess|popen|pty\.spawn|"
    r"\bexec\s*\(|\beval\s*\(|shutil\.|Path\([^)]*\)\.touch)")


class Policy:
    def __init__(self, state: str, reason: str = "", data: dict | None = None,
                 allowlist: dict[str, str] | None = None,
                 protected: tuple[str, ...] = (), require_receipts: bool = False,
                 contract_version: str = "", path: str = ""):
        self.state = state
        self.reason = reason
        self.data = data or {}
        self.allowlist = allowlist or {}
        self.protected = protected
        self.require_receipts = require_receipts
        self.contract_version = contract_version
        self.path = path

    @property
    def active(self) -> bool:
        return self.state == VALID


def safe_regular_file(path: str, root: str) -> tuple[str | None, str]:
    """Resolve `path` and require that it is a regular file inside `root`.

    A symlink is permitted only when its canonical target is still inside the
    repository: a link pointing at /etc or at another checkout would let content
    from outside the reviewed tree act as policy. Directories, FIFOs and devices
    are rejected because reading them is not a bounded operation.
    """
    try:
        lst = os.lstat(path)
    except OSError as exc:
        return None, f"cannot be read ({exc.strerror})"
    resolved = os.path.realpath(path)
    root_real = os.path.realpath(root)
    try:
        rel = os.path.relpath(resolved, root_real)
    except ValueError:
        return None, "resolves onto a different filesystem root"
    if rel == ".." or rel.startswith(".." + os.sep):
        return None, (f"is a symlink resolving outside the repository root "
                      f"({resolved})" if stat.S_ISLNK(lst.st_mode)
                      else f"resolves outside the repository root ({resolved})")
    try:
        st = os.stat(resolved)
    except OSError as exc:
        return None, f"target cannot be read ({exc.strerror})"
    if not stat.S_ISREG(st.st_mode):
        return None, "is not a regular file"
    return resolved, ""


def _rel_inside(value: str) -> bool:
    """A manifest path must be repository-relative and must not climb out."""
    if not isinstance(value, str) or not value:
        return False
    if os.path.isabs(value) or value.startswith("~"):
        return False
    parts = pathlib.PurePosixPath(value).parts
    return ".." not in parts


def load(project: str) -> Policy:
    """Resolve the policy state for a project. Never raises."""
    manifest = os.path.join(project, MANIFEST_REL)
    if not os.path.lexists(manifest):
        return Policy(ABSENT, "no policy manifest", path=manifest)

    def invalid(why: str) -> Policy:
        return Policy(INVALID, f"{MANIFEST_REL} {why}", path=manifest)

    resolved, problem = safe_regular_file(manifest, project)
    if resolved is None:
        return invalid(problem)
    try:
        data = json.loads(pathlib.Path(resolved).read_text())
    except Exception as exc:
        return invalid(f"is not readable JSON ({exc})")
    if not isinstance(data, dict):
        return invalid("does not contain a JSON object")

    unknown = sorted(set(data) - ALLOWED_KEYS)
    if unknown:
        return invalid(f"declares unknown keys: {', '.join(unknown)}")

    version = data.get("policy_version")
    if not isinstance(version, int) or isinstance(version, bool):
        return invalid("has no integer policy_version")
    if version not in SUPPORTED_POLICY_VERSIONS:
        return invalid(f"asks for policy_version {version}; this plugin bundles "
                       f"{', '.join(str(v) for v in SUPPORTED_POLICY_VERSIONS)}")

    receipts = data.get("require_subagent_receipts", False)
    if not isinstance(receipts, bool):
        return invalid("require_subagent_receipts is not a boolean")

    contract_version = data.get("contract_version", "")
    if not isinstance(contract_version, str):
        return invalid("contract_version is not a string")

    protected = data.get("protected", [])
    if not isinstance(protected, list) or \
            not all(_rel_inside(p) for p in protected):
        return invalid("protected must be a list of repository-relative paths "
                       "that do not climb outside the repository")

    maintenance = data.get("maintenance", {})
    if not isinstance(maintenance, dict):
        return invalid("maintenance must be an object")
    unknown_m = sorted(set(maintenance) - ALLOWED_MAINTENANCE_KEYS)
    if unknown_m:
        return invalid(f"maintenance declares unknown keys: {', '.join(unknown_m)}")
    if not all(_rel_inside(v) for v in maintenance.values()):
        return invalid("maintenance paths must be repository-relative")

    allowlist: dict[str, str] = {}
    declared = data.get("allowlist")
    if declared is not None:
        if not _rel_inside(declared):
            return invalid("allowlist must be a repository-relative path")
        allow_path = os.path.join(project, declared)
        if not os.path.lexists(allow_path):
            return invalid(f"declares an allowlist that does not exist: {declared}")
        allow_resolved, problem = safe_regular_file(allow_path, project)
        if allow_resolved is None:
            return invalid(f"allowlist {declared} {problem}")
        try:
            raw = json.loads(pathlib.Path(allow_resolved).read_text())
            scripts = raw.get("scripts")
            if not isinstance(scripts, dict):
                raise ValueError("no scripts object")
            allowlist = {str(k): str(v) for k, v in scripts.items()}
        except Exception as exc:
            return invalid(f"allowlist {declared} is not readable JSON ({exc})")

    contract = data.get("contract")
    if contract is not None and not _rel_inside(contract):
        return invalid("contract must be a repository-relative path")

    return Policy(VALID, "policy manifest is valid", data=data, allowlist=allowlist,
                  protected=tuple(protected), require_receipts=receipts,
                  contract_version=contract_version, path=manifest)


# --------------------------------------------------------------------------- #
# the policy layer's own rules
# --------------------------------------------------------------------------- #

def sha256_file(path: str) -> str | None:
    try:
        h = hashlib.sha256()
        with open(path, "rb") as fh:
            for chunk in iter(lambda: fh.read(65536), b""):
                h.update(chunk)
        return h.hexdigest()
    except Exception:
        return None


def script_verdict(raw: str, cwd: str, project: str,
                   pol: Policy) -> tuple[str, str] | None:
    """Classify execution of a local script against the policy allowlist.

    This is the single denial `allowed-scripts.json` may except. It cannot reach
    anything in the universal layer, because the engine has already returned by the
    time this runs."""
    if "$" in raw or "`" in raw:
        return ("deny", f"script path is variable-derived, so it cannot be checked "
                        f"against the allowlist: {raw}")
    candidate = os.path.expanduser(raw)
    if not os.path.isabs(candidate):
        candidate = os.path.join(cwd, candidate)
    abs_path = os.path.realpath(candidate)
    try:
        rel = os.path.relpath(abs_path, os.path.realpath(project)).replace(os.sep, "/")
    except ValueError:
        rel = ".."
    if rel == ".." or rel.startswith("../"):
        return ("deny", f"execution of a script outside the project: {raw}")

    pinned = pol.allowlist.get(rel)
    if pinned is None:
        return ("deny", f"execution of an unreviewed script: {rel}. It is not "
                        f"pinned in {pol.data.get('allowlist', 'the allowlist')}")
    actual = sha256_file(abs_path)
    if actual is None:
        return ("deny", f"allowlisted script cannot be read: {rel}")
    if actual != pinned:
        return ("deny", f"allowlisted script has changed since review: {rel}; "
                        f"pinned {pinned[:12]}, on disk {actual[:12]}")
    return ("allow", f"reviewed script, hash matches pin: {rel}")


def looks_local(arg: str) -> bool:
    if arg in (".", ".."):
        return True
    if arg.startswith(("./", "../", "/", "~")):
        return True
    return arg.endswith(LOCAL_ARCHIVES)


def payload_targets(args: list[str]) -> list[str]:
    found = []
    for i, t in enumerate(args):
        if t in PAYLOAD_FLAGS and i + 1 < len(args):
            found.append(args[i + 1])
        elif t.startswith("--") and "=" in t and t.split("=", 1)[0] in PAYLOAD_FLAGS:
            found.append(t.split("=", 1)[1])
        elif not t.startswith("-") and looks_local(t):
            found.append(t)
    return found


def protected_paths(pol: Policy) -> tuple[str, ...]:
    """Paths the manifest asks to protect, on top of the universal set."""
    extra = list(pol.protected)
    for key in ("allowlist", "contract"):
        value = pol.data.get(key)
        if isinstance(value, str):
            extra.append(value)
    ledger = (pol.data.get("maintenance") or {}).get("ledger")
    if isinstance(ledger, str):
        extra.append(ledger)
    issuer = (pol.data.get("maintenance") or {}).get("issuer")
    if isinstance(issuer, str):
        extra.append(issuer)
    return tuple(dict.fromkeys(extra))


def classify_segment(segment: str, cwd: str, project: str, pol: Policy,
                     recurse) -> tuple[str, str] | None:
    """Policy-layer verdict for one segment, or None to fall through."""
    toks = tokens(segment)
    if not toks:
        return None
    head, args = head_and_args(toks)
    if not head:
        return None
    base = os.path.basename(head)

    if base in ("source",) or head == ".":
        target = next((a for a in args if not a.startswith("-")), None)
        if target:
            return script_verdict(target, cwd, project, pol)
        return ("deny", "source with no readable target")

    if base in RUNNER_RULES:
        allowed_subs = RUNNER_RULES[base]
        sub = next((a for a in args if not a.startswith("-")), None)
        if allowed_subs is None or (sub in allowed_subs):
            return ("deny", f"package or build script indirection: "
                            f"`{base}{' ' + sub if sub else ''}` runs recipes this "
                            "gate cannot see")

    def reviewed_payloads(label: str, candidates: list[str]):
        if not candidates:
            return ("deny", f"{label} with no inspectable payload file")
        for candidate in candidates:
            verdict = script_verdict(candidate, cwd, project, pol)
            if verdict and verdict[0] != "allow":
                return ("deny", f"{label} carries an unreviewed payload: {verdict[1]}")
        return ("allow", f"{label} of a reviewed, hash-pinned payload")

    if base == "git":
        sub = next((a for a in args if not a.startswith("-")), None)
        if sub in OPAQUE_GIT_SUBCOMMANDS:
            return reviewed_payloads(f"`git {sub}`",
                                     payload_targets([a for a in args if a != sub]))
        return None

    if base == "patch":
        return reviewed_payloads("`patch`", payload_targets(args))

    if base in INSTALLERS:
        sub = next((a for a in args if not a.startswith("-")), None)
        if sub in INSTALL_SUBCOMMANDS:
            local = payload_targets([a for a in args if a != sub])
            if local:
                return reviewed_payloads(f"`{base} {sub}` from a local path", local)
        return None

    if base in SHELLS:
        if any(flag_cluster(t, "n") for t in args):
            return ("allow", f"{base} -n parses without executing")
        for i, t in enumerate(args):
            if flag_cluster(t, "c"):
                inner = args[i + 1] if i + 1 < len(args) else ""
                if not inner:
                    return ("deny", f"{base} -c with no readable program")
                return recurse(inner)
        target = next((a for a in args if not a.startswith("-")), None)
        if target:
            return script_verdict(target, cwd, project, pol)
        return None

    if base in INTERPRETERS:
        for i, t in enumerate(args):
            if t in ("-c", "-e"):
                inner = " ".join(args[i + 1:])
                if INLINE_SIDE_EFFECT.search(inner):
                    return ("deny", f"inline {base} program with filesystem or "
                                    "process side effects")
                return ("allow", f"inline {base} program with no side effects detected")
            if t == "-m":
                module = args[i + 1] if i + 1 < len(args) else ""
                # `python3 -m pip install ./local` carries a payload the command
                # string does not show. The universal layer defers installer modules
                # here rather than allowing them, so this branch has to judge it.
                if module in ("pip",):
                    rest = args[i + 2:]
                    if "install" in rest:
                        local = payload_targets([a for a in rest if a != "install"])
                        if local:
                            return reviewed_payloads("`pip install` via -m from a "
                                                     "local path", local)
                return ("allow", f"{base} -m module invocation")
        skip = {"run", "-u", "-X", "-W", "-O", "-B", "-q", "--"}
        target = next((a for a in args if not a.startswith("-") and a not in skip),
                      None)
        if target:
            return script_verdict(target, cwd, project, pol)
        return None

    if looks_like_script(head) or ("/" in head and head.endswith(
            tuple(x for x in (".sh", ".py", ".js", ".rb", ".pl")))):
        return script_verdict(head, cwd, project, pol)
    return None

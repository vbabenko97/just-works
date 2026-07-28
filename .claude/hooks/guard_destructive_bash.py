#!/usr/bin/env python3
"""PreToolUse gate for Bash. Fail-closed classification, not blast-radius estimation.

This hook makes no attempt to predict how many files an arbitrary shell command
will touch: that is undecidable in general, and a wrong estimate is worse than no
estimate. It classifies instead.

  allow  the command matches a known-safe read-only shape, a bounded single
         mutation, or a reviewed script pinned in .claude/allowed-scripts.json
  deny   the command matches a recognised destructive shape, mutates in a way
         this classifier cannot bound (loops, globs, xargs, find -delete,
         command substitution feeding a mutation), executes an unreviewed local
         script, or would modify the reliability harness itself

Two routes are gated, because closing only the first leaves the guard decorative:

  direct   rm -rf, git push --force, DROP TABLE, inline interpreter deletion
  indirect Write cleanup.sh, then `bash cleanup.sh`. The guard used to see only
           the interpreter and allow it. Now every execution of a local script,
           `-c` inline program, `source`, `eval`, or package-script runner is
           classified, and local scripts run only when their path AND content
           hash appear in the allowlist. Unknown, untracked and modified scripts
           are denied, and the reason says which.

The historical case this exists for:
    for s in $STALE; do rm -rf "$dest/$s"; done
46 directories, authorised by a one-file comparison. Unbounded target set, so denied.

Protocol: reads a PreToolUse payload on stdin, writes a decision to stdout.
"""
from __future__ import annotations

import hashlib
import json
import os
import pathlib
import re
import shlex
import subprocess
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from reliability_paths import (  # noqa: E402
    CONTRACT_VERSION, mentions_protected, project_dir,
)

# Recognised destructive shapes. Denied outright.
DESTRUCTIVE = [
    (r"\brm\s+(-[a-zA-Z]*\s+)*-[a-zA-Z]*[rR][a-zA-Z]*\b", "recursive rm"),
    (r"\brm\b(?=[^|;&]*\*)", "rm with a glob"),
    (r"\bfind\b[^|;&]*-delete\b", "find -delete"),
    (r"\bfind\b[^|;&]*-exec\s+rm\b", "find -exec rm"),
    (r"\bxargs\b[^|;&]*\brm\b", "xargs rm"),
    (r"\bgit\s+push\b[^|;&]*(--force\b|-f\b)", "git force push"),
    (r"\bgit\s+reset\b[^|;&]*--hard\b", "git reset --hard"),
    (r"\bgit\s+clean\b[^|;&]*-[a-zA-Z]*[dfx]", "git clean"),
    (r"\bgit\s+(checkout|restore)\s+\.", "git discard all working changes"),
    (r"\b(DROP|TRUNCATE)\s+(TABLE|DATABASE|SCHEMA)\b", "destructive SQL"),
    (r"\bDELETE\s+FROM\b(?![^|;&]*\bWHERE\b)", "unbounded SQL DELETE"),
    (r"\bUPDATE\b[^|;&]*\bSET\b(?![^|;&]*\bWHERE\b)", "unbounded SQL UPDATE"),
    (r"\bdd\s+[^|;&]*\bof=", "dd to a device or file"),
    (r"\bmkfs(\.|\s)", "mkfs"),
    (r"\bchmod\s+(-[a-zA-Z]*\s+)*-[a-zA-Z]*R\b", "recursive chmod"),
    (r"\bchown\s+(-[a-zA-Z]*\s+)*-[a-zA-Z]*R\b", "recursive chown"),
    (r">\s*/dev/(sd|disk|nvme)", "write to a block device"),
    (r"\bshred\b", "shred"),
    (r":\(\)\s*\{.*\};:", "fork bomb"),
    (r"^\s*(sudo|doas|su)\b", "privilege escalation"),
    (r"[;&|]\s*(sudo|doas)\b", "privilege escalation"),
    # Interpreter-level deletion: the shell verbs are absent, so the mutator
    # patterns below never see it. Matches inline programs only, so running a
    # reviewed script such as bulk_mutate.py stays allowed.
    # `;` is deliberately allowed inside the match: an inline program contains
    # statement separators, so excluding `;` here missed `-c "import shutil;
    # shutil.rmtree(...)"`. Pipes still terminate the match.
    (r"\b(python3?|node|ruby|perl)\b[^|&]*\s-(c|e)\b[^|&]*"
     r"(rmtree|os\.remove|os\.unlink|os\.rmdir|\bunlink\(|fs\.rm|rmSync|"
     r"FileUtils\.rm|shutil\.move|os\.rename)", "inline interpreter deletion"),
    # Decoded or fetched text piped into a shell cannot be classified at all.
    (r"\|\s*(sh|bash|zsh|dash)\b", "piping text into a shell"),
    (r"\bbase64\b[^|;&]*-[dD]\b", "base64 decode"),
    (r"\bcurl\b[^|;&]*\|\s*\w*sh\b", "curl piped to shell"),
]

# Mutating verbs. Safe only when the target set is explicit and bounded.
MUTATORS = [
    r"\brm\b", r"\bmv\b", r"\bcp\b", r"\bmkdir\b", r"\btouch\b", r"\btee\b",
    r"\bsed\b[^|;&]*-i", r"\bperl\b[^|;&]*-[a-zA-Z]*i", r"\btruncate\b",
    r"\bgit\s+(commit|add|rm|mv|apply|checkout|restore|reset|stash|merge|rebase|push|pull|fetch)\b",
    r"\brsync\b", r"\binstall\b", r"\bln\b", r"\bchmod\b", r"\bchown\b",
    r"\bnpm\s+(install|i|ci|publish)\b", r"\bpip\s+install\b", r"\bbrew\s+(install|uninstall)\b",
    # Only redirects whose destination is variable- or glob-derived. A redirect to
    # a literal path names exactly one target, so `cmd > /tmp/out.txt 2>&1` is
    # bounded; treating every `>` as a mutator denied ordinary work whenever any
    # variable appeared elsewhere in the same compound command.
    r">>?\s*(\$|[^\s|&;]*[*?])",
    r"\bdefaults\s+write\b", r"\bcrontab\b", r"\blaunchctl\b",
]

# Shapes that make a target set unbounded for this classifier.
UNBOUNDED = [
    (r"\bfor\b[^;]*\bin\b", "shell loop"),
    (r"\bwhile\b[^;]*\b(read|do)\b", "shell loop"),
    (r"\$\(", "command substitution"),
    (r"`[^`]+`", "backtick substitution"),
    (r"\bxargs\b", "xargs"),
    (r"\bfind\b", "find"),
    (r"[*?]", "glob"),
    (r"\{[^}]*\.\.[^}]*\}", "brace range expansion"),
    (r"\$[A-Za-z_][A-Za-z0-9_]*", "variable-derived target"),
    (r"\bparallel\b", "gnu parallel"),
]

# Command heads that would rewrite a protected file, matched against the head of
# each segment rather than anywhere in the command string. Whole-string matching
# was wrong twice: a read-only Python one-liner was refused because a loop
# variable named `ln` matched the pattern for the `ln` command, and a diagnostic
# whose *data* contained the word `patch` was refused the same way.
# `git add` and `git commit` are deliberately absent: recording an existing file
# in version control does not change it, and the harness has to be committable.
PROTECTED_MUTATOR_HEADS = {
    "rm", "mv", "cp", "tee", "ln", "truncate", "chmod", "chown", "rsync",
    "patch", "dd", "install", "ditto", "shred", "unlink",
}
PROTECTED_GIT_SUBCOMMANDS = {"checkout", "restore", "reset", "stash", "clean",
                             "apply", "am", "rm", "mv"}

# Routes that carry their payload outside the command string, so this gate cannot
# see what they would change. `git apply /tmp/fix.diff` names no protected path
# yet can rewrite the guard itself. Permitted only when the payload file is
# hash-pinned in the allowlist, which is the same standard applied to scripts.
OPAQUE_GIT_SUBCOMMANDS = {"apply", "am"}
INSTALLERS = {"pip", "pip3", "npm", "pnpm", "yarn", "brew", "gem", "cargo"}
INSTALL_SUBCOMMANDS = {"install", "i", "ci", "add", "reinstall"}
PAYLOAD_FLAGS = {"-r", "--requirement", "-e", "--editable", "-c", "--constraint",
                 "-i", "--input", "--file"}
LOCAL_ARCHIVES = (".whl", ".tar.gz", ".tgz", ".zip", ".patch", ".diff", ".gem")
# Flags that consume the following token, so the head is not the token after them.
ENV_VALUE_FLAGS = {"-u", "--unset", "-C", "--chdir", "-S", "--split-string", "-n"}

SHELLS = {"sh", "bash", "zsh", "dash", "ksh", "ash"}
INTERPRETERS = {"python", "python2", "python3", "node", "nodejs", "ruby", "perl",
                "php", "deno", "bun", "Rscript", "osascript", "tsx", "ts-node"}
SCRIPT_EXTS = (".sh", ".bash", ".zsh", ".py", ".rb", ".pl", ".js", ".mjs", ".cjs",
               ".ts", ".php", ".lua", ".command", ".osascript")

# Runners that execute unreviewed local recipes or package scripts. `None` means
# every invocation; a set means only those subcommands. Dependency installation
# (`npm install`, `uv sync`, `pip install`) is deliberately not here — denying it
# would break ordinary work, and it is listed as a known gap instead.
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

# Tokens that precede the real command and must be skipped to find the head.
PREFIXES = {"env", "command", "exec", "nohup", "time", "nice", "stdbuf",
            "caffeinate", "builtin"}

# Filesystem or process side effects inside an inline `-c` / `-e` program.
INLINE_SIDE_EFFECT = re.compile(
    r"(open\s*\([^)]*['\"][wax]|write_text|writelines|write_bytes|makedirs|"
    r"\bmkdir\b|copyfile|copytree|copy2|copymode|writeFileSync|appendFileSync|"
    r"mkdirSync|renameSync|os\.system|subprocess|popen|pty\.spawn|"
    r"\bexec\s*\(|\beval\s*\(|shutil\.|Path\([^)]*\)\.touch)")

# Read-only commands. Allowed even when other heuristics would be noisy.
READ_ONLY_HEAD = re.compile(
    r"^\s*(ls|cat|head|tail|wc|stat|file|find|grep|rg|egrep|fgrep|awk|sed|sort|uniq|cut|tr|"
    r"diff|cmp|shasum|md5|md5sum|sha256sum|od|xxd|strings|du|df|pwd|which|whence|type|echo|printf|"
    r"basename|dirname|realpath|readlink|env|date|uname|python3?|node|jq|yq|tree|"
    r"comm|join|paste|column|less|more|man|help|true|false|test|\[)\b"
)

WRAPPER_HINT = (
    "This gate classifies commands; it does not estimate how many files yours "
    "would touch.\n"
    "For bulk filesystem mutation use the controlled wrapper, which enumerates "
    "exact targets and binds them to a plan:\n"
    "  python3 scripts/verify/bulk_mutate.py plan --operation delete "
    "--root <approved-root> --max <n> --plan plan.json <target> ...\n"
    "  python3 scripts/verify/bulk_mutate.py apply --plan plan.json --dry-run\n"
    "  python3 scripts/verify/bulk_mutate.py apply --plan plan.json\n"
    "Before deleting anything justified by a comparison, establish it with:\n"
    "  python3 scripts/verify/verify_tree_equivalence.py <a> <b>"
)


# --------------------------------------------------------------------------- #
# command structure
# --------------------------------------------------------------------------- #

def split_segments(cmd: str) -> list[str]:
    """Split a compound command on shell separators, ignoring separators inside
    quotes. Each segment is classified independently, so `chmod +x x && ./x`
    cannot hide its second half behind a benign first half."""
    segments: list[str] = []
    buf: list[str] = []
    quote: str | None = None
    i = 0
    while i < len(cmd):
        ch = cmd[i]
        if quote:
            buf.append(ch)
            if ch == quote and (i == 0 or cmd[i - 1] != "\\"):
                quote = None
            i += 1
            continue
        if ch in "'\"":
            quote = ch
            buf.append(ch)
            i += 1
            continue
        if cmd[i:i + 2] in ("&&", "||"):
            segments.append("".join(buf))
            buf = []
            i += 2
            continue
        if ch in ";\n|&":
            segments.append("".join(buf))
            buf = []
            i += 1
            continue
        buf.append(ch)
        i += 1
    segments.append("".join(buf))
    return [s.strip() for s in segments if s.strip()]


def tokens(segment: str) -> list[str]:
    try:
        return shlex.split(segment, posix=True)
    except ValueError:
        return segment.split()


def head_and_args(toks: list[str]) -> tuple[str, list[str]]:
    """Skip env assignments and wrappers (`env -i`, `time`, `exec`) to find the
    command actually being run.

    Flags belonging to a wrapper are skipped for as long as a wrapper has been
    seen, not merely when the previous token was one: `env -i -u FOO bash x.sh`
    used to leave the head as `FOO`. Flags that consume a value skip two tokens,
    so `env -u VAR cmd` does not mistake `VAR` for the command."""
    i = 0
    saw_prefix = False
    while i < len(toks):
        t = toks[i]
        if re.match(r"^[A-Za-z_][A-Za-z0-9_]*=", t):
            i += 1
            continue
        if t in PREFIXES:
            saw_prefix = True
            i += 1
            continue
        if saw_prefix and t.startswith("-"):
            i += 2 if t in ENV_VALUE_FLAGS else 1
            continue
        break
    return (toks[i], toks[i + 1:]) if i < len(toks) else ("", [])


# --------------------------------------------------------------------------- #
# script allowlist
# --------------------------------------------------------------------------- #

def load_allowlist(project: str) -> tuple[dict[str, str], str]:
    """Path -> sha256 for scripts reviewed and pinned by the repository owner.
    A missing or unreadable allowlist means nothing is allowlisted, so every
    local script execution is denied rather than silently permitted."""
    path = os.environ.get("RELIABILITY_ALLOWLIST") or \
        os.path.join(project, ".claude", "allowed-scripts.json")
    try:
        with open(path) as fh:
            data = json.load(fh)
        scripts = data.get("scripts") or {}
        return ({k: str(v) for k, v in scripts.items()}, path)
    except Exception:
        return ({}, path)


def sha256_file(path: str) -> str | None:
    try:
        h = hashlib.sha256()
        with open(path, "rb") as fh:
            for chunk in iter(lambda: fh.read(65536), b""):
                h.update(chunk)
        return h.hexdigest()
    except Exception:
        return None


def git_state(project: str, rel: str) -> str:
    """Label a denied script as untracked, modified or clean. Only called on the
    deny path, so it costs nothing during ordinary commands.

    Trackedness is established with `git ls-files --error-unmatch`, not with empty
    `git status` output: an unmatched pathspec makes `git status` print nothing and
    exit 0, so reading silence as "tracked and unmodified" invents a fact about a
    file that may not exist at all."""
    abs_path = os.path.join(project, rel)
    if not os.path.exists(abs_path):
        return "no such file"
    try:
        tracked = subprocess.run(["git", "ls-files", "--error-unmatch", "--", rel],
                                 cwd=project, capture_output=True, text=True, timeout=5)
        if tracked.returncode != 0:
            return "untracked"
        out = subprocess.run(["git", "status", "--porcelain", "--", rel],
                             cwd=project, capture_output=True, text=True, timeout=5)
        if out.returncode != 0:
            return "git state unavailable"
        return "tracked and unmodified" if not out.stdout.strip() \
            else "modified relative to git"
    except Exception:
        return "git state unavailable"


def script_verdict(raw: str, cwd: str, project: str) -> tuple[str, str] | None:
    """Classify execution of a script path. Returns (decision, reason), or None
    when the path is not a project-local script this gate needs to judge."""
    if "$" in raw or "`" in raw:
        # The gate sees the unexpanded command string. A variable-derived script
        # path cannot be hashed, so it cannot be checked against the allowlist.
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
    outside = rel == ".." or rel.startswith("../")

    if outside:
        return ("deny", f"execution of a script outside the project: {raw}. "
                        "Only reviewed scripts inside the repository may run")

    allowlist, allowlist_path = load_allowlist(project)
    pinned = allowlist.get(rel)
    if pinned is None:
        return ("deny", f"execution of an unreviewed script: {rel} "
                        f"({git_state(project, rel)}). It is not listed in "
                        f"{os.path.relpath(allowlist_path, project)}")

    actual = sha256_file(abs_path)
    if actual is None:
        return ("deny", f"allowlisted script cannot be read: {rel}")
    if actual != pinned:
        return ("deny", f"allowlisted script has changed since review: {rel} "
                        f"({git_state(project, rel)}); pinned {pinned[:12]}, "
                        f"on disk {actual[:12]}")
    return ("allow", f"reviewed script, hash matches pin: {rel}")


def looks_like_script(token: str) -> bool:
    return token.endswith(SCRIPT_EXTS) or token.startswith(("./", "../", "~/"))


def flag_cluster(token: str, letter: str) -> bool:
    return bool(re.match(rf"^-[a-zA-Z]*{letter}[a-zA-Z]*$", token))


# --------------------------------------------------------------------------- #
# classification
# --------------------------------------------------------------------------- #

def classify_segment(segment: str, cwd: str, project: str,
                     depth: int) -> tuple[str, str] | None:
    """Return (decision, reason) when this segment is decided by the indirection
    rules, or None to fall through to the mutator analysis."""
    toks = tokens(segment)
    if not toks:
        return None
    head, args = head_and_args(toks)
    if not head:
        return None
    base = os.path.basename(head)

    if base in ("eval",):
        return ("deny", "eval executes text this gate cannot classify")

    if base in ("source",) or head == ".":
        target = next((a for a in args if not a.startswith("-")), None)
        if target:
            return script_verdict(target, cwd, project)
        return ("deny", "source with no readable target")

    rule_key = base if base in RUNNER_RULES else None
    if rule_key:
        allowed_subs = RUNNER_RULES[rule_key]
        sub = next((a for a in args if not a.startswith("-")), None)
        if allowed_subs is None or (sub in allowed_subs):
            return ("deny", f"package or build script indirection: "
                            f"`{base}{' ' + sub if sub else ''}` runs recipes this "
                            "gate cannot see")

    def reviewed_payloads(label: str, candidates: list[str]):
        """Opaque payloads are held to the same standard as scripts: the file must
        be hash-pinned in the allowlist, or the command is refused."""
        if not candidates:
            return ("deny", f"{label} with no inspectable payload file")
        for candidate in candidates:
            verdict = script_verdict(candidate, cwd, project)
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
                if depth >= 2:
                    return ("deny", "nested -c programs beyond the inspection depth")
                d, r, _ = decide(inner, cwd=cwd, depth=depth + 1)
                if d != "allow":
                    return (d, f"inside `{base} -c`: {r}")
                return ("allow", f"inside `{base} -c`: {r}")
        target = next((a for a in args if not a.startswith("-")), None)
        if target:
            return script_verdict(target, cwd, project)
        return None

    if base in INTERPRETERS:
        for i, t in enumerate(args):
            if t in ("-c", "-e") or (base.startswith("python") and t == "-c"):
                inner = " ".join(args[i + 1:])
                if INLINE_SIDE_EFFECT.search(inner):
                    return ("deny", f"inline {base} program with filesystem or "
                                    "process side effects")
                return ("allow", f"inline {base} program with no side effects detected")
            if t == "-m":
                module = args[i + 1] if i + 1 < len(args) else ""
                if module in ("pip",):
                    rest = args[i + 2:]
                    if "install" in rest:
                        local = payload_targets([a for a in rest if a != "install"])
                        if local:
                            return reviewed_payloads("`pip install` via -m from a "
                                                     "local path", local)
                return ("allow", f"{base} -m module invocation")
        skip = {"run", "-u", "-X", "-W", "-O", "-B", "-q", "--"}
        target = next((a for a in args if not a.startswith("-") and a not in skip), None)
        if target:
            return script_verdict(target, cwd, project)
        return None

    # Direct execution: ./cleanup.sh, /abs/path/tool.py, tools/gen.sh
    if looks_like_script(head) or ("/" in head and head.endswith(SCRIPT_EXTS)):
        return script_verdict(head, cwd, project)
    if "/" in head:
        candidate = os.path.realpath(os.path.join(cwd, os.path.expanduser(head)))
        try:
            rel = os.path.relpath(candidate, os.path.realpath(project))
        except ValueError:
            rel = ".."
        if not (rel == ".." or rel.startswith("../")):
            return script_verdict(head, cwd, project)
    return None


def looks_local(arg: str) -> bool:
    """A path-like installer argument, as opposed to a registry name. `@scope/pkg`
    and `requests` are registry specs; `.`, `./pkg`, `/abs`, `x.whl` are local."""
    if arg in (".", ".."):
        return True
    if arg.startswith(("./", "../", "/", "~")):
        return True
    return arg.endswith(LOCAL_ARCHIVES)


def payload_targets(args: list[str]) -> list[str]:
    """Path-like arguments that carry content this gate cannot inspect."""
    found = []
    for i, t in enumerate(args):
        if t in PAYLOAD_FLAGS and i + 1 < len(args):
            found.append(args[i + 1])
        elif t.startswith("--") and "=" in t and t.split("=", 1)[0] in PAYLOAD_FLAGS:
            found.append(t.split("=", 1)[1])
        elif not t.startswith("-") and looks_local(t):
            found.append(t)
    return found


def protected_hit(segment: str, project: str) -> tuple[str, str] | None:
    """Detect a Bash route to rewriting the harness, judged per segment.

    Only the segment's own command head counts. Naming a protected file is not a
    refusal on its own, so `cat`, `grep`, `git add` and `git diff` on the guard
    stay allowed while `cp`, `sed -i`, `git checkout` and redirects into it do not."""
    entry = mentions_protected(segment)
    if not entry:
        return None
    toks = tokens(segment)
    if not toks:
        return None
    head, args = head_and_args(toks)
    base = os.path.basename(head)

    if base in PROTECTED_MUTATOR_HEADS:
        return (entry, f"`{base}` would rewrite it")
    if base in ("sed", "perl") and any(t.startswith("-i") or flag_cluster(t, "i")
                                      for t in args):
        return (entry, f"`{base} -i` would rewrite it")
    if base == "git":
        sub = next((a for a in args if not a.startswith("-")), None)
        if sub in PROTECTED_GIT_SUBCOMMANDS:
            return (entry, f"`git {sub}` would rewrite it")
    needle = entry.rstrip("/")
    if re.search(r">>?\s*['\"]?[^\s'\";|&]*" + re.escape(needle), segment):
        return (entry, "a redirect writes to it")
    return None


def decide(command: str, cwd: str | None = None,
           project: str | None = None, depth: int = 0) -> tuple[str, str, list[str]]:
    """Return (decision, reason, notes). decision in {allow, deny}."""
    notes: list[str] = []
    cmd = command.strip()
    cwd = cwd or os.getcwd()
    project = project or project_dir()

    for pattern, label in DESTRUCTIVE:
        if re.search(pattern, cmd, re.IGNORECASE):
            return ("deny", f"recognised destructive operation: {label}", notes)

    segments = split_segments(cmd)

    for segment in segments:
        hit = protected_hit(segment, project)
        if hit:
            entry, why = hit
            return ("deny",
                    f"would modify reliability infrastructure ({entry}; {why}). "
                    "That file constrains what agents may do, so agents do not "
                    "rewrite it — hand the diff to the repository owner, or have "
                    "them issue a narrow maintenance authorization",
                    notes)

    fell_through = False
    for segment in segments:
        verdict = classify_segment(segment, cwd, project, depth)
        if verdict is None:
            fell_through = True
            continue
        decision, reason = verdict
        if decision != "allow":
            return (decision, reason, notes)
        notes.append(reason)
    if not fell_through and notes:
        return ("allow", "; ".join(notes), notes)

    mutates = [m for m in MUTATORS if re.search(m, cmd)]
    if not mutates:
        if READ_ONLY_HEAD.match(cmd):
            notes.append("matched read-only command head")
        return ("allow", "no mutating operation detected", notes)

    unbounded = [label for pattern, label in UNBOUNDED if re.search(pattern, cmd)]
    if unbounded:
        return ("deny",
                "mutation with a target set this gate cannot bound: "
                + ", ".join(sorted(set(unbounded))),
                notes)

    notes.append(f"bounded mutation: {', '.join(sorted(set(mutates)))}")
    return ("allow", "single explicit mutation target", notes)


# --------------------------------------------------------------------------- #
# hook protocol
# --------------------------------------------------------------------------- #

def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except Exception:
        # Fail closed: an unreadable payload must not become an allow.
        print(json.dumps({
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "ask",
                "permissionDecisionReason":
                    "guard_destructive_bash.py could not parse the hook payload; "
                    "asking rather than allowing.",
            }}))
        return 0

    tool = payload.get("tool_name") or payload.get("tool") or ""
    tool_input = payload.get("tool_input") or {}
    command = tool_input.get("command") or ""

    if tool != "Bash" or not command:
        print(json.dumps({"hookSpecificOutput": {
            "hookEventName": "PreToolUse", "permissionDecision": "allow",
            "permissionDecisionReason": "not a Bash command"}}))
        return 0

    decision, reason, notes = decide(command, cwd=payload.get("cwd") or os.getcwd())

    if decision == "allow":
        print(json.dumps({"hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "allow",
            "permissionDecisionReason": f"[{CONTRACT_VERSION}] {reason}",
            "notes": notes}}))
        return 0

    print(json.dumps({"hookSpecificOutput": {
        "hookEventName": "PreToolUse",
        "permissionDecision": "deny",
        "permissionDecisionReason": (
            f"[{CONTRACT_VERSION}] Blocked: {reason}.\n" + WRAPPER_HINT
        )}}))
    return 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""Installed-cache concerns only: is something installed, does it match the
checkout, is the installed copy itself internally sound (fails closed under
sabotage of a copy of it, denies live probes correctly).

Two modes:

* default (source/pre-install mode): checkout correctness is enforced; an
  absent or stale installed cache is reported as a deployment-state line, not
  a functional failure. Internal-soundness checks (sabotage, live probes)
  still run as real check()s against whatever *is* installed, and are skipped
  only when nothing is installed at all.
* ``--require-current``: deployment mode. The installed plugin is required to
  exist and to match the checkout tree byte-for-byte. Absent or stale exits
  nonzero. Use this after commit, push, `claude plugin marketplace update
  just-works`, `claude plugin update reliability@just-works`, and restart.

Split out of test_manifest_commands.py. Before a revision has been pushed and
installed, "installed != checkout" is the expected, correct state in default
mode, not a functional bug — but it must never be silently permanent: that is
exactly what --require-current is for.
"""
from __future__ import annotations

import json
import os
import pathlib
import shutil
import subprocess
import sys
import tempfile
import time

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from _fixture import VALID_MANIFEST, Checks, build  # noqa: E402

CHECKOUT = pathlib.Path(__file__).resolve().parents[1]
CACHE_ROOT = pathlib.Path.home() / ".claude" / "plugins" / "cache"
INSTALLED_RECORD = pathlib.Path.home() / ".claude" / "plugins" / \
    "installed_plugins.json"

EXCLUDE_DIRS = {".in_use", "__pycache__", ".git"}
EXCLUDE_FILES = {".DS_Store"}

SABOTAGE = {
    "gate.py syntax error": ("write", "hooks/gate.py", "def broken(:\n    pass\n"),
    "gate.py missing": ("unlink", "hooks/gate.py", None),
    "gate.py import failure": ("write", "hooks/gate.py",
                               "import definitely_not_a_real_module_xyz\n"),
    "gate.py exits 1": ("write", "hooks/gate.py", "import sys\nsys.exit(1)\n"),
    "gate.py exits 127": ("write", "hooks/gate.py", "import sys\nsys.exit(127)\n"),
    "gate.py prints junk and exits 0": ("write", "hooks/gate.py",
                                        'print("not a decision")\n'),
    "gate.py hangs past every deadline": ("write", "hooks/gate.py",
                                          "import time\ntime.sleep(45)\n"),
    "run_gate.sh missing": ("unlink", "hooks/run_gate.sh", None),
    "run_gate.sh unparseable": ("write", "hooks/run_gate.sh",
                                "this ( is not ( valid bash\n"),
}


def installed_entry() -> dict | None:
    try:
        record = json.loads(INSTALLED_RECORD.read_text())
        entries = record["plugins"]["reliability@just-works"]
        return entries[0]
    except Exception:
        return None


def installed_root(entry: dict | None) -> pathlib.Path | None:
    if entry is None:
        return None
    try:
        path = pathlib.Path(entry["installPath"])
    except Exception:
        return None
    return path if path.is_dir() else None


def checkout_git_info() -> tuple[str | None, bool | None]:
    """(HEAD sha or None, dirty-under-plugins/reliability or None)."""
    try:
        rev = subprocess.run(["git", "rev-parse", "HEAD"], cwd=CHECKOUT,
                             capture_output=True, text=True, timeout=10)
        head = rev.stdout.strip() if rev.returncode == 0 else None
    except Exception:
        head = None
    try:
        status = subprocess.run(["git", "status", "--porcelain", "--", "."],
                                cwd=CHECKOUT, capture_output=True, text=True,
                                timeout=10)
        dirty = bool(status.stdout.strip()) if status.returncode == 0 else None
    except Exception:
        dirty = None
    return head, dirty


def checkout_label() -> str:
    head, dirty = checkout_git_info()
    if head is None:
        return "unknown (git rev-parse HEAD failed)"
    if dirty is None:
        return f"{head} (dirty state unknown — git status failed)"
    if dirty:
        return f"{head} (dirty: uncommitted changes under plugins/reliability)"
    return f"{head} (clean)"


def snapshot(root: pathlib.Path) -> dict[str, bytes]:
    out = {}
    for path in root.rglob("*"):
        if path.is_dir():
            continue
        rel = path.relative_to(root)
        if any(part in EXCLUDE_DIRS for part in rel.parts):
            continue
        if path.name in EXCLUDE_FILES:
            continue
        try:
            out[str(rel)] = path.read_bytes()
        except OSError:
            pass
    return out


def tree_diff(installed: pathlib.Path, checkout: pathlib.Path) -> tuple[bool, str]:
    a, b = snapshot(installed), snapshot(checkout)
    only_installed = sorted(set(a) - set(b))
    only_checkout = sorted(set(b) - set(a))
    differing = sorted(p for p in (set(a) & set(b)) if a[p] != b[p])
    if not only_installed and not only_checkout and not differing:
        return True, "installed tree matches checkout tree byte-for-byte"
    parts = []
    if only_installed:
        parts.append(f"{len(only_installed)} file(s) only in installed "
                     f"(e.g. {only_installed[0]})")
    if only_checkout:
        parts.append(f"{len(only_checkout)} file(s) only in checkout "
                     f"(e.g. {only_checkout[0]})")
    if differing:
        parts.append(f"{len(differing)} file(s) differ in content "
                     f"(e.g. {differing[0]})")
    return False, "; ".join(parts)


def commands(root: pathlib.Path) -> list[tuple[str, str]]:
    hooks = json.loads((root / "hooks" / "hooks.json").read_text())
    found = []
    for entry in hooks["hooks"].get("PreToolUse", []):
        for hook in entry["hooks"]:
            found.append((entry.get("matcher", "?"), hook["command"]))
    return found


def run(command: str, root: pathlib.Path, payload: dict, project: pathlib.Path,
       data: pathlib.Path, deadline: str = "4") -> tuple[int, float, str, str]:
    env = os.environ.copy()
    env["CLAUDE_PLUGIN_ROOT"] = str(root)
    env["CLAUDE_PROJECT_DIR"] = str(project)
    env["RELIABILITY_DATA_DIR"] = str(data)
    env["RELIABILITY_GATE_DEADLINE"] = deadline
    env["RELIABILITY_GUARD_TIMEOUT"] = "3"
    env["RELIABILITY_TRACE_FILE"] = str(data / "trace.jsonl")
    started = time.time()
    proc = subprocess.run(["bash", "-c", command], input=json.dumps(payload),
                          capture_output=True, text=True, timeout=180, env=env)
    return (proc.returncode, time.time() - started, proc.stdout, proc.stderr[:300])


def payload_for(matcher: str, project: pathlib.Path) -> dict:
    base = {"session_id": "s-accept", "cwd": str(project)}
    if matcher == "Bash":
        return {**base, "tool_name": "Bash", "tool_input": {"command": "ls -la"}}
    return {**base, "tool_name": "Read", "tool_input": {"file_path": "README.md"}}


def main() -> int:
    require_current = "--require-current" in sys.argv[1:]
    entry = installed_entry()
    root = installed_root(entry)
    check = Checks()

    label = checkout_label()

    if root is None:
        print("installed path: <none>")
        print("installed revision: <none>")
        print(f"checkout revision: {label}")
        print("deployment state: NOT_INSTALLED — reliability@just-works has no "
              "recorded, existing install path in installed_plugins.json.")
        if require_current:
            check(False, "reliability@just-works is installed "
                         "(--require-current requires a real installation)",
                  "NOT_INSTALLED")
            return check.finish()
        print("This is expected before a first install and is not a functional "
              "failure in default mode; nothing else in this file runs. Run "
              "with --require-current after install to enforce this.")
        return 0

    installed_sha = entry.get("gitCommitSha") or entry.get("version") or "unknown"
    tree_match, tree_detail = tree_diff(root, CHECKOUT)
    state = "CURRENT" if tree_match else "STALE"

    print(f"installed path: {root}")
    print(f"installed revision: {installed_sha}")
    print(f"checkout revision: {label}")
    print(f"deployment state: {state} — {tree_detail}")
    if state == "STALE" and not require_current:
        print("STALE is expected and NOT a functional failure before you've "
              "pushed and run `claude plugin update`. If you've already shipped "
              "and this still says STALE, push, `claude plugin marketplace "
              "update just-works`, `claude plugin update reliability@just-works`, "
              "restart, and rerun with --require-current.")

    if require_current:
        check(state == "CURRENT", "installed plugin matches checkout "
                                  "(--require-current)", f"{state}: {tree_detail}")

    work = pathlib.Path(tempfile.mkdtemp(prefix="jw-cache-parity-"))
    try:
        data = work / "data"
        data.mkdir()
        project = build(work, "policed", manifest=VALID_MANIFEST)

        check(str(root).startswith(str(CACHE_ROOT)),
              "the installed plugin runs from the versioned cache", str(root))

        configured = commands(root)
        check(len(configured) >= 2, f"hooks.json declares PreToolUse commands "
                                    f"({len(configured)})")

        # Controls against the real cache directory, unmodified.
        for matcher, command in configured:
            code, _, out, err = run(command, root, payload_for(matcher, project),
                                    project, data)
            ok = code == 0 and '"permissionDecision"' in out
            check(ok, f"control, installed cache [{matcher}] -> exit 0",
                  f"exit {code}: out={out[:100]!r} err={err!r}")

        # Sabotage a copy, never the install.
        replica = work / "replica"
        shutil.copytree(root, replica)
        for label_, (action, rel, body) in SABOTAGE.items():
            for matcher, command in configured:
                shutil.rmtree(replica)
                shutil.copytree(root, replica)
                victim = replica / rel
                if action == "write":
                    victim.write_text(body)
                else:
                    victim.unlink()
                code, elapsed, out, err = run(command, replica,
                                              payload_for(matcher, project), project,
                                              data)
                ok = code == 2
                if ok and "hangs" in label_:
                    ok = elapsed < 25
                check(ok, f"{label_} [{matcher}] -> exit 2",
                      f"exit {code} in {elapsed:.1f}s: out={out[:80]!r} err={err!r}")

        # Guard-specific sabotage: each configured command has its own guard.
        for guard, matcher_wanted in (("guard_bash.py", "Bash"),
                                      ("guard_common.py", "*")):
            shutil.rmtree(replica)
            shutil.copytree(root, replica)
            (replica / "hooks" / guard).write_text("def broken(:\n    pass\n")
            command = next(c for m, c in configured if m == matcher_wanted)
            code, _, out, err = run(command, replica,
                                    payload_for(matcher_wanted, project), project,
                                    data)
            check(code == 2, f"{guard} syntax error [{matcher_wanted}] -> exit 2",
                  f"exit {code}: out={out[:80]!r} err={err!r}")

        # Live probes against the installed cache: the real guards, the real gate.
        common = next(c for m, c in configured if m == "*")
        bash_cmd = next(c for m, c in configured if m == "Bash")

        never = {"tool_name": "Read", "session_id": "live-probe",
                 "agent_id": "agent-never-injected", "agent_type": "Explore",
                 "cwd": str(project), "tool_input": {"file_path": "README.md"}}
        code, _, out, err = run(common, root, never, project, data)
        ok = code == 0 and '"deny"' in out and "contract" in out
        check(ok, "live: subagent with no receipt is denied",
              f"exit {code}: out={out[:160]!r} err={err!r}")

        main_session = {"tool_name": "Read", "session_id": "live-probe",
                        "cwd": str(project),
                        "tool_input": {"file_path": "README.md"}}
        code, _, out, err = run(common, root, main_session, project, data)
        check(code == 0 and '"allow"' in out, "live: main session needs no receipt",
              f"exit {code}: out={out[:160]!r}")

        destructive = {"tool_name": "Bash", "session_id": "live-probe",
                       "cwd": str(project),
                       "tool_input": {"command": "rm -rf ."}}
        code, _, out, err = run(bash_cmd, root, destructive, project, data)
        check(code == 0 and '"deny"' in out, "live: recursive delete is denied",
              f"exit {code}: out={out[:160]!r}")

        protected = {"tool_name": "Edit", "session_id": "live-probe",
                     "cwd": str(project),
                     "tool_input": {"file_path": str(project / ".claude" /
                                                     "settings.json")}}
        code, _, out, err = run(common, root, protected, project, data)
        check(code == 0 and '"deny"' in out, "live: protected config edit is denied",
              f"exit {code}: out={out[:160]!r}")
    finally:
        shutil.rmtree(work, ignore_errors=True)

    return check.finish()


if __name__ == "__main__":
    sys.exit(main())

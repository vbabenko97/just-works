#!/usr/bin/env python3
"""The exact command strings from hooks.json, run against the installed cache copy.

Ported from test_configured_gate.py, which existed because testing the gate by
calling it directly proves the wrapper is sound and proves nothing about what Claude
Code actually runs. That distinction found the only fail-open the in-process tests
could not see.

Two things are deliberate here. The command strings are read out of the *installed*
`hooks/hooks.json`, not the checkout's, so this tests the copy that is enforcing. And
the pristine controls run against the real cache directory, while sabotage runs
against a copy of it — the installed plugin is never modified.

A staleness check compares installed and checkout manifests. If it fails, the cache
is behind: push, `claude plugin marketplace update`, `claude plugin update
reliability@just-works`, then rerun.
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


def installed_root() -> pathlib.Path | None:
    try:
        record = json.loads(INSTALLED_RECORD.read_text())
        entries = record["plugins"]["reliability@just-works"]
        return pathlib.Path(entries[0]["installPath"])
    except Exception:
        return None


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
    root = installed_root()
    check = Checks()
    if root is None or not root.is_dir():
        print("FAIL: reliability@just-works is not installed; nothing to test")
        return 1

    work = pathlib.Path(tempfile.mkdtemp(prefix="jw-manifest-"))
    try:
        data = work / "data"
        data.mkdir()
        project = build(work, "policed", manifest=VALID_MANIFEST)

        check(str(root).startswith(str(CACHE_ROOT)),
              "the installed plugin runs from the versioned cache", str(root))
        installed_hooks = (root / "hooks" / "hooks.json").read_text()
        check(installed_hooks == (CHECKOUT / "hooks" / "hooks.json").read_text(),
              "the installed manifest matches the checkout (cache is current)",
              "cache is stale: push, marketplace update, plugin update, rerun")

        configured = commands(root)
        check(len(configured) >= 2, f"hooks.json declares PreToolUse commands "
                                    f"({len(configured)})")
        print("\ncommands taken verbatim from the installed hooks.json:")
        for matcher, command in configured:
            print(f"  [{matcher}] {command}")
        print()

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
        for label, (action, rel, body) in SABOTAGE.items():
            for matcher, command in configured:
                shutil.rmtree(replica)
                shutil.copytree(root, replica)
                victim = replica / rel
                if action == "write":
                    victim.write_text(body)
                else:
                    victim.unlink()
                # The configured command appends `|| exit 2`, which is what covers a
                # launcher that cannot start at all.
                code, elapsed, out, err = run(command, replica,
                                              payload_for(matcher, project), project,
                                              data)
                ok = code == 2
                if ok and "hangs" in label:
                    ok = elapsed < 25
                check(ok, f"{label} [{matcher}] -> exit 2",
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

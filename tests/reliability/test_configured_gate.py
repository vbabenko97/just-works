#!/usr/bin/env python3
"""Acceptance test for the outermost gate: the exact command in settings.json.

Testing hook_gate.py by calling it directly proves the wrapper is sound. It does
not prove the thing Claude Code actually runs is sound, and that is where the last
fail-open lived: if hook_gate.py itself will not start — syntax error, bad import,
crash, hang, or simply absent — the process exits non-zero, which Claude Code was
measured to treat as "no opinion", and the tool call proceeds.

So every case here reads the command string out of .claude/settings.json and runs
that string through a shell, with CLAUDE_PROJECT_DIR pointed at a sabotaged replica
of the repository. Nothing is stubbed and nothing is called in-process. The real
files are never modified; only the replica is broken.

A control case runs the same command against a pristine replica and requires exit
0, so an exit 2 elsewhere cannot be dismissed as the command being broken all along.
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

REPO = pathlib.Path(__file__).resolve().parents[2]
SETTINGS = REPO / ".claude" / "settings.json"

GATE_FILES = ["hook_gate.py", "subagent_receipts.py", "run_gate.sh"]
GUARD_FILES = ["reliability_paths.py", "maintenance_auth.py",
               "guard_destructive_bash.py", "guard_protected_paths.py"]

SABOTAGE = {
    "syntax error in hook_gate.py": ("write", "def broken(:\n    return 1\n"),
    "hook_gate.py missing": ("unlink", None),
    "hook_gate.py import failure": ("write", "import definitely_not_a_real_module_xyz\n"),
    "hook_gate.py exits 1": ("write", "import sys\nsys.exit(1)\n"),
    "hook_gate.py exits 127": ("write", "import sys\nsys.exit(127)\n"),
    "hook_gate.py prints junk and exits 0": ("write", 'print("not a decision")\n'),
    "hook_gate.py hangs past every deadline": ("write", "import time\ntime.sleep(45)\n"),
    "run_gate.sh missing (failure to start)": ("unlink_launcher", None),
    "run_gate.sh unparseable by bash": ("write_launcher", "this ( is not ( valid bash\n"),
}


def configured_commands() -> list[tuple[str, str]]:
    """(matcher, command) for every PreToolUse hook that routes through the gate."""
    settings = json.loads(SETTINGS.read_text())
    found = []
    for entry in settings["hooks"]["PreToolUse"]:
        for hook in entry["hooks"]:
            command = hook.get("command", "")
            if "run_gate.sh" in command:
                found.append((entry.get("matcher", "?"), command))
    return found


def make_replica(root: pathlib.Path) -> pathlib.Path:
    replica = root / "replica"
    (replica / "scripts" / "hooks").mkdir(parents=True)
    (replica / ".claude" / "hooks").mkdir(parents=True)
    for name in GATE_FILES:
        shutil.copy2(REPO / "scripts" / "hooks" / name,
                     replica / "scripts" / "hooks" / name)
    for name in GUARD_FILES:
        shutil.copy2(REPO / ".claude" / "hooks" / name,
                     replica / ".claude" / "hooks" / name)
    shutil.copy2(REPO / ".claude" / "allowed-scripts.json",
                 replica / ".claude" / "allowed-scripts.json")
    return replica


def restore(replica: pathlib.Path) -> None:
    for name in GATE_FILES:
        shutil.copy2(REPO / "scripts" / "hooks" / name,
                     replica / "scripts" / "hooks" / name)


def apply_sabotage(replica: pathlib.Path, action: str, body: str | None) -> None:
    gate = replica / "scripts" / "hooks" / "hook_gate.py"
    launcher = replica / "scripts" / "hooks" / "run_gate.sh"
    if action == "write":
        gate.write_text(body)
    elif action == "unlink":
        gate.unlink()
    elif action == "unlink_launcher":
        launcher.unlink()
    elif action == "write_launcher":
        launcher.write_text(body)


def run_command(command: str, replica: pathlib.Path, payload: dict,
                deadline: str = "2") -> tuple[int, float, str]:
    env = os.environ.copy()
    env["CLAUDE_PROJECT_DIR"] = str(replica)
    env["RELIABILITY_GATE_DEADLINE"] = deadline
    started = time.time()
    proc = subprocess.run(["bash", "-c", command], input=json.dumps(payload),
                          capture_output=True, text=True, timeout=120, env=env)
    return proc.returncode, time.time() - started, (proc.stderr or "")[:200]


def payload_for(matcher: str) -> dict:
    base = {"session_id": "s-accept", "cwd": str(REPO)}
    if matcher == "Bash":
        return {**base, "tool_name": "Bash", "tool_input": {"command": "ls -la"}}
    if matcher.startswith("Write"):
        return {**base, "tool_name": "Write",
                "tool_input": {"file_path": str(REPO / "README.md"), "content": "x"}}
    return {**base, "tool_name": "Read", "tool_input": {"file_path": "README.md"}}


def main() -> int:
    commands = configured_commands()
    if not commands:
        print("FAIL: no gate command found in .claude/settings.json")
        return 1

    root = pathlib.Path(tempfile.mkdtemp(prefix="jw-accept-"))
    failures = []
    checks = 0
    try:
        replica = make_replica(root)

        print("commands taken verbatim from .claude/settings.json:")
        for matcher, command in commands:
            print(f"  [{matcher}] {command}")
        print()

        # Control: the real thing must work, or every 2 below proves nothing.
        print(f"{'EXIT':5} {'WANT':5} CASE")
        print("-" * 78)
        for matcher, command in commands:
            code, _, err = run_command(command, replica, payload_for(matcher))
            checks += 1
            ok = code == 0
            print(f"{code:<5} {0:<5} control, pristine replica [{matcher}]"
                  f"{'' if ok else '   <-- FAIL'}")
            if not ok:
                failures.append((f"control {matcher}", 0, code, err))

        # Every sabotage, against every configured command.
        for label, (action, body) in SABOTAGE.items():
            for matcher, command in commands:
                apply_sabotage(replica, action, body)
                code, elapsed, err = run_command(command, replica,
                                                 payload_for(matcher))
                restore(replica)
                checks += 1
                ok = code == 2
                # The hang must be cut short by the launcher's own deadline, well
                # inside the 30s hook timeout configured in settings.json.
                if ok and "hangs" in label:
                    ok = elapsed < 20
                print(f"{code:<5} {2:<5} {label} [{matcher}]"
                      f"{'' if ok else '   <-- FAIL'}")
                if not ok:
                    failures.append((f"{label} {matcher}", 2, code,
                                     f"{elapsed:.1f}s {err}"))
        # Live probes against the real repository, not a replica: the same command
        # string, the real receipts directory, the real guards. An agent_id that
        # never had a receipt issued is precisely what a broken or skipped
        # SubagentStart hook leaves behind, and SubagentStart cannot refuse to
        # create the subagent — so this is the only place the failure can be caught.
        receipt_command = next(c for m, c in commands if m == "*")
        broken = {"tool_name": "Read", "session_id": "live-probe-session",
                  "agent_id": "a-never-injected", "agent_type": "Explore",
                  "cwd": str(REPO), "tool_input": {"file_path": "README.md"}}
        code, _, err = run_command(receipt_command, REPO, broken)
        checks += 1
        ok = code == 2 and "no contract receipt" in err
        print(f"{code:<5} {2:<5} live: subagent with no receipt is refused"
              f"{'' if ok else '   <-- FAIL'}")
        if not ok:
            failures.append(("live broken injection", 2, code, err))

        main_session = {"tool_name": "Read", "session_id": "live-probe-session",
                        "cwd": str(REPO), "tool_input": {"file_path": "README.md"}}
        code, _, err = run_command(receipt_command, REPO, main_session)
        checks += 1
        ok = code == 0
        print(f"{code:<5} {0:<5} live: main session needs no receipt"
              f"{'' if ok else '   <-- FAIL'}")
        if not ok:
            failures.append(("live main session", 0, code, err))
    finally:
        shutil.rmtree(root, ignore_errors=True)

    print(f"\n{checks - len(failures)}/{checks} passed")
    for row in failures:
        print(f"  FAIL {row}")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())

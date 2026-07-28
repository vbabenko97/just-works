#!/usr/bin/env python3
"""Every way a guard can fail must become a refusal, not permission.

Each fake guard below reproduces one measured fail-open shape from Claude Code
2.1.220. The measurements are recorded in hook_gate.py; this suite proves the
wrapper converts each of them into exit 2, and that it does not damage the two
shapes that already worked.
"""
from __future__ import annotations

import json
import pathlib
import shutil
import subprocess
import sys
import tempfile

REPO = pathlib.Path(__file__).resolve().parents[2]
GATE = REPO / "scripts" / "hooks" / "hook_gate.py"

ALLOW_JSON = ('{"hookSpecificOutput": {"hookEventName": "PreToolUse", '
              '"permissionDecision": "allow", "permissionDecisionReason": "fake allow"}}')
DENY_JSON = ('{"hookSpecificOutput": {"hookEventName": "PreToolUse", '
             '"permissionDecision": "deny", "permissionDecisionReason": "fake deny"}}')
ASK_JSON = ('{"hookSpecificOutput": {"hookEventName": "PreToolUse", '
            '"permissionDecision": "ask", "permissionDecisionReason": "fake ask"}}')

GUARDS = {
    "g_allow.py": f'print({ALLOW_JSON!r})\n',
    "g_deny.py": f'print({DENY_JSON!r})\n',
    "g_ask.py": f'print({ASK_JSON!r})\n',
    "g_unknown.py": ('print(\'{"hookSpecificOutput": {"hookEventName": "PreToolUse",'
                     ' "permissionDecision": "maybe"}}\')\n'),
    "g_exit2.py": ('import sys\n'
                   'print("fake guard refuses on purpose", file=sys.stderr)\n'
                   'sys.exit(2)\n'),
    "g_exit1.py": ('import sys\n'
                   'print("fake guard crashed", file=sys.stderr)\nsys.exit(1)\n'),
    "g_exit127.py": "import sys\nsys.exit(127)\n",
    "g_malformed.py": 'print("{ this is not valid json")\n',
    "g_text.py": 'print("plain text, no decision at all")\n',
    "g_silent.py": "pass\n",
    "g_syntax.py": "def broken(:\n    return 1\n",
    "g_import.py": "import definitely_not_a_real_module_xyz\n",
    "g_sleep.py": f'import time\ntime.sleep(5)\nprint({ALLOW_JSON!r})\n',
}

# Guards whose stdout must reach Claude Code byte-for-byte.
PASSTHROUGH = {"g_allow.py": ALLOW_JSON, "g_deny.py": DENY_JSON}

PAYLOAD = {"tool_name": "Bash", "cwd": str(REPO),
           "session_id": "s-main", "tool_input": {"command": "ls"}}

# (guard, expected exit, substring required in stderr, note)
CASES = [
    ("g_allow.py", 0, "", "a valid allow passes through"),
    ("g_deny.py", 0, "", "a valid deny passes through"),
    ("g_exit2.py", 2, "refuses on purpose", "exit 2 is propagated as a denial"),
    ("g_ask.py", 2, "upgraded to a refusal", "ask is not dependable, so it denies"),
    ("g_unknown.py", 2, "unknown decision", "an unrecognised decision denies"),
    ("g_exit1.py", 2, "exited 1", "exit 1 denies instead of failing open"),
    ("g_exit127.py", 2, "exited 127", "exit 127 denies instead of failing open"),
    ("g_malformed.py", 2, "not a hook decision", "malformed JSON denies"),
    ("g_text.py", 2, "not a hook decision", "unexpected stdout denies"),
    ("g_silent.py", 2, "printed no decision", "exit 0 with no output denies"),
    ("g_syntax.py", 2, "exited 1", "a syntax error in the guard denies"),
    ("g_import.py", 2, "exited 1", "a failed import in the guard denies"),
    ("g_missing.py", 2, "guard script is missing", "a missing guard denies"),
]


def run(guard: str, payload_text: str, timeout_env: str | None = None):
    import os
    env = os.environ.copy()
    env["CLAUDE_PROJECT_DIR"] = str(REPO)
    if timeout_env:
        env["RELIABILITY_GUARD_TIMEOUT"] = timeout_env
    proc = subprocess.run([sys.executable, str(GATE), guard], input=payload_text,
                          capture_output=True, text=True, timeout=60, env=env)
    return proc


def main() -> int:
    tmp = pathlib.Path(tempfile.mkdtemp(prefix="jw-gate-"))
    failures = []
    try:
        for name, body in GUARDS.items():
            (tmp / name).write_text(body)

        payload_text = json.dumps(PAYLOAD)
        print(f"{'EXIT':5} {'WANT':5} CASE")
        print("-" * 74)
        for guard, want_code, needle, note in CASES:
            proc = run(str(tmp / guard), payload_text)
            ok = proc.returncode == want_code and needle in proc.stderr
            if ok and guard in PASSTHROUGH:
                # "passes through unchanged" means byte-for-byte, not merely a
                # decision the wrapper agrees with.
                ok = proc.stdout.strip() == PASSTHROUGH[guard].strip()
            print(f"{proc.returncode:<5} {want_code:<5} {note}"
                  f"{'' if ok else '   <-- FAIL'}")
            if not ok:
                failures.append((note, want_code, proc.returncode,
                                 proc.stderr.strip()[:160]))

        # Timeout: measured live as a fail-open in Claude Code, so the wrapper must
        # impose its own deadline rather than trusting the harness.
        proc = run(str(tmp / "g_sleep.py"), payload_text, timeout_env="1")
        ok = proc.returncode == 2 and "did not answer within" in proc.stderr
        print(f"{proc.returncode:<5} {2:<5} a hanging guard denies after the deadline"
              f"{'' if ok else '   <-- FAIL'}")
        if not ok:
            failures.append(("timeout", 2, proc.returncode, proc.stderr.strip()[:160]))

        # A payload the wrapper cannot parse must not become permission either.
        proc = run(str(tmp / "g_allow.py"), "{ not json at all")
        ok = proc.returncode == 2 and "could not be parsed" in proc.stderr
        print(f"{proc.returncode:<5} {2:<5} an unparseable payload denies"
              f"{'' if ok else '   <-- FAIL'}")
        if not ok:
            failures.append(("bad payload", 2, proc.returncode,
                             proc.stderr.strip()[:160]))

        # Every refusal must say which guard failed, or the operator cannot tell
        # which protection stopped applying.
        proc = run(str(tmp / "g_exit1.py"), payload_text)
        ok = "failing guard:" in proc.stderr and "g_exit1.py" in proc.stderr
        print(f"{'-':<5} {'-':<5} the refusal names the failing guard"
              f"{'' if ok else '   <-- FAIL'}")
        if not ok:
            failures.append(("names the guard", "named", "not named",
                             proc.stderr.strip()[:160]))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    total = len(CASES) + 4
    print(f"\n{total - len(failures)}/{total} passed")
    for row in failures:
        print(f"  FAIL {row}")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())

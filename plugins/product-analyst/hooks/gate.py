#!/usr/bin/env python3
"""Run an analyst hook guard and turn all guard failures into a denial.

Claude Code treats a failed hook as no opinion.  This supervisor has a shorter
deadline than the hook declaration and always emits a syntactically valid reply.
An empty object is intentionally preserved: it means the guard has no opinion.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
GUARD_TIMEOUT = 8


def deny(reason: str) -> None:
    print(
        json.dumps(
            {
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": "deny",
                    "permissionDecisionReason": f"[product-analyst] Blocked: {reason}",
                }
            }
        )
    )


def valid_reply(stdout: str) -> bool:
    try:
        parsed = json.loads(stdout)
    except json.JSONDecodeError:
        return False
    if parsed == {}:
        return True
    if not isinstance(parsed, dict):
        return False
    output = parsed.get("hookSpecificOutput")
    # The guard only restricts. An "allow" would skip the user's permission prompt,
    # so it counts as an invalid reply and becomes a denial.
    return (
        isinstance(output, dict)
        and output.get("hookEventName") == "PreToolUse"
        and output.get("permissionDecision") == "deny"
    )


def main() -> int:
    if len(sys.argv) != 2:
        deny("hook supervisor needs exactly one guard")
        return 0
    raw = sys.stdin.read()
    try:
        payload = json.loads(raw)
        if not isinstance(payload, dict):
            raise ValueError("payload is not an object")
    except (json.JSONDecodeError, ValueError) as exc:
        deny(f"invalid hook payload ({exc})")
        return 0

    guard_arg = sys.argv[1]
    guard = Path(guard_arg) if "/" in guard_arg else HERE / guard_arg
    if not guard.is_file():
        deny(f"guard is missing: {guard_arg}")
        return 0
    try:
        proc = subprocess.run(
            [sys.executable, str(guard)],
            input=raw,
            text=True,
            capture_output=True,
            timeout=GUARD_TIMEOUT,
        )
    except subprocess.TimeoutExpired:
        deny(f"guard did not answer within {GUARD_TIMEOUT:g}s")
        return 0
    except OSError as exc:
        deny(f"guard could not run ({exc})")
        return 0
    if proc.returncode != 0:
        deny(f"guard exited {proc.returncode}")
        return 0
    if not valid_reply(proc.stdout):
        deny("guard returned an invalid decision")
        return 0
    sys.stdout.write(proc.stdout)
    return 0


if __name__ == "__main__":
    try:
        exit_code = main()
    except Exception as exc:  # The supervisor itself must fail closed.
        deny(f"hook supervisor failed ({type(exc).__name__})")
        exit_code = 0
    raise SystemExit(exit_code)

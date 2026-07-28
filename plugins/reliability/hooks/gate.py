#!/usr/bin/env python3
"""Fail-closed wrapper. A guard that cannot run is a refusal, not permission.

Measured on Claude Code 2.1.220 with --permission-mode acceptEdits, where a hook with
no opinion lets the write through:

  exit 0 + allow JSON        proceeds
  exit 0 + deny JSON         blocked
  exit 0 + ask JSON          blocked headless, satisfied silently interactively
  exit 2 + stderr            blocked
  exit 0, no output          proceeds        <- reference
  exit 1 + stderr            PROCEEDS        <- fail open
  exit 127                   PROCEEDS        <- fail open
  exit 0 + malformed JSON    PROCEEDS        <- fail open
  exit 0 + plain text        PROCEEDS        <- fail open
  exceeded hook timeout      PROCEEDS        <- fail open

So a syntax error, a bad import, a crash, a hang or a typo silently disables a guard
and nothing reports that protection stopped applying. This converts every one of
those into exit 2 naming the guard that failed.

`ask` is upgraded to a refusal because `ask` was measured to be unreliable: six
interactive `ask` verdicts proceeded with no prompt. See docs/upstream-ask-divergence.md.

The deadline here must stay shorter than the timeout configured for the hook, or
Claude Code gives up first and fails open. Nesting: guard 10s < launcher 15s < hook 30s.
"""
from __future__ import annotations

import json
import os
import pathlib
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
DEFAULT_TIMEOUT = float(os.environ.get("RELIABILITY_GUARD_TIMEOUT", "10"))


def refuse(guard: str, reason: str) -> int:
    print(f"[reliability-gate] BLOCKED: {reason}\n"
          f"[reliability-gate] failing guard: {guard}\n"
          "[reliability-gate] A guard that cannot run is treated as a refusal, not "
          "as permission. Fix the guard, or have the owner disable the plugin "
          "deliberately.", file=sys.stderr)
    return 2


def main() -> int:
    args = sys.argv[1:]
    if not args:
        return refuse("gate.py", "no guard argument was given")
    guard_arg = args[0]
    # Resolved next to this file, so the gate and its guards are always the same
    # installed copy. An absolute path is honoured for tests.
    guard = guard_arg if "/" in guard_arg else str(HERE / guard_arg)

    raw = sys.stdin.read()
    try:
        payload = json.loads(raw)
        if not isinstance(payload, dict):
            raise ValueError("payload is not an object")
    except Exception as exc:
        return refuse(guard_arg, f"the hook payload could not be parsed ({exc})")

    if not os.path.isfile(guard):
        return refuse(guard_arg, f"the guard is missing: {guard}")

    try:
        proc = subprocess.run([sys.executable, guard], input=raw, capture_output=True,
                              text=True, timeout=DEFAULT_TIMEOUT)
    except subprocess.TimeoutExpired:
        return refuse(guard_arg,
                      f"the guard did not answer within {DEFAULT_TIMEOUT:g}s")
    except Exception as exc:
        return refuse(guard_arg, f"the guard could not be run ({exc})")

    if proc.returncode == 2:
        # A deliberate refusal by the guard: propagate it unchanged.
        if proc.stderr:
            print(proc.stderr, file=sys.stderr, end="")
        return 2
    if proc.returncode != 0:
        return refuse(guard_arg, f"the guard exited {proc.returncode} instead of 0 "
                                 f"or 2. stderr: {(proc.stderr or '').strip()[:300]}")

    if not proc.stdout.strip():
        return refuse(guard_arg, "the guard exited 0 without printing a decision")

    try:
        decision = json.loads(proc.stdout)["hookSpecificOutput"]
        event = decision["hookEventName"]
        verdict = decision["permissionDecision"]
    except Exception as exc:
        return refuse(guard_arg, f"the guard printed something that is not a "
                                 f"PreToolUse decision ({exc})")
    if event != "PreToolUse":
        return refuse(guard_arg, f"the guard answered for {event}, not PreToolUse")
    if verdict == "ask":
        return refuse(guard_arg, "the guard returned `ask`, which was measured not to "
                                 "prompt in an interactive acceptEdits session; "
                                 "treating it as a refusal")
    if verdict not in ("allow", "deny"):
        return refuse(guard_arg, f"the guard returned an unknown decision {verdict!r}")

    sys.stdout.write(proc.stdout)
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:
        sys.exit(refuse("gate.py", f"the gate itself failed ({exc})"))

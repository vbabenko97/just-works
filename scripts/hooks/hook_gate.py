#!/usr/bin/env python3
"""Fail-closed wrapper for every PreToolUse enforcement hook.

Measured on Claude Code 2.1.220, with `--permission-mode acceptEdits` so that a
hook with no opinion lets the write through. Each row is a real run; the reference
row is a hook that exits 0 silently:

  exit 0 + allow JSON        proceeds
  exit 0 + deny JSON         blocked
  exit 0 + ask JSON          blocked here, but satisfied silently in an
                             interactive acceptEdits session, so not dependable
  exit 2 + stderr            blocked
  exit 0, no output          proceeds        <- reference
  exit 1 + stderr            PROCEEDS        <- fail open
  exit 127                   PROCEEDS        <- fail open
  exit 0 + malformed JSON    PROCEEDS        <- fail open
  exit 0 + plain text        PROCEEDS        <- fail open
  exceeded its timeout       PROCEEDS        <- fail open ("Slow PreToolUse
                             hooks: 2021ms for Write (1 hooks)")
  missing script             blocked, but only because python3 exits 2 for
                             "can't open file" — an interpreter that exits 1
                             would fail open

So a syntax error, a bad import, a crash, a hang or a typo in a guard silently
disables it, and nothing in the transcript says the protection stopped applying.
This wrapper converts every one of those into a refusal that names the guard.

  valid exit 0 output   passed through unchanged
  exit 2                propagated, still a denial
  ask                   upgraded to a denial, because ask is not dependable
  anything else         exit 2 with a reason naming the guard

It also enforces contract delivery to subagents: a PreToolUse call carrying an
agent_id must present a matching receipt from SubagentStart, or it is refused.

Usage:
  hook_gate.py <guard-file-or-path>   run a guard behind the wrapper
  hook_gate.py --receipt-only         receipt enforcement with no guard
"""
from __future__ import annotations

import json
import os
import pathlib
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import subagent_receipts  # noqa: E402

DEFAULT_TIMEOUT = float(os.environ.get("RELIABILITY_GUARD_TIMEOUT", "10"))
VALID_DECISIONS = {"allow", "deny", "ask"}


def project_dir() -> str:
    env = os.environ.get("CLAUDE_PROJECT_DIR")
    if env and os.path.isdir(env):
        return os.path.realpath(env)
    return str(HERE.parents[1])


def contract_version(project: str) -> str:
    """Read the version from the guard module's shared paths file, so the wrapper
    and the guards cannot disagree about which contract is current."""
    try:
        sys.path.insert(0, os.path.join(project, ".claude", "hooks"))
        import reliability_paths
        return reliability_paths.CONTRACT_VERSION
    except Exception:
        return "unknown"


def refuse(guard_label: str, reason: str) -> int:
    """Exit 2 with the reason on stderr — the one channel measured to block a tool
    call regardless of permission mode."""
    print(f"[hook_gate] BLOCKED: {reason}\n"
          f"[hook_gate] failing guard: {guard_label}\n"
          "[hook_gate] A guard that cannot run is treated as a refusal, not as "
          "permission. Fix the guard, or have the repository owner disable this "
          "matcher deliberately.", file=sys.stderr)
    return 2


def main() -> int:
    args = sys.argv[1:]
    if not args:
        return refuse("hook_gate.py", "no guard argument was given")
    receipt_only = args[0] == "--receipt-only"
    guard_arg = None if receipt_only else args[0]
    guard_label = guard_arg or "--receipt-only"

    raw = sys.stdin.read()
    try:
        payload = json.loads(raw)
        if not isinstance(payload, dict):
            raise ValueError("payload is not an object")
    except Exception as exc:
        return refuse(guard_label, f"the hook payload could not be parsed ({exc})")

    project = project_dir()

    # Contract delivery to subagents. Main-session calls carry no agent_id and are
    # not subject to this.
    if subagent_receipts.is_subagent(payload):
        ok, why = subagent_receipts.verify(payload=payload, project=project,
                                           contract_version=contract_version(project))
        if not ok:
            return refuse(guard_label, f"subagent contract not delivered: {why}")

    if receipt_only:
        print(json.dumps({"hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "allow",
            "permissionDecisionReason": "[hook_gate] receipt verified"}}))
        return 0

    guard = guard_arg if "/" in guard_arg else os.path.join(
        project, ".claude", "hooks", guard_arg)
    if not os.path.isfile(guard):
        return refuse(guard_label, f"the guard script is missing: {guard}")

    try:
        proc = subprocess.run([sys.executable, guard], input=raw,
                              capture_output=True, text=True,
                              timeout=DEFAULT_TIMEOUT)
    except subprocess.TimeoutExpired:
        return refuse(guard_label,
                      f"the guard did not answer within {DEFAULT_TIMEOUT:g}s")
    except FileNotFoundError as exc:
        return refuse(guard_label, f"the interpreter could not be started ({exc})")
    except Exception as exc:
        return refuse(guard_label, f"the guard could not be run ({exc})")

    if proc.returncode == 2:
        # An intentional refusal by the guard. Propagate it unchanged.
        sys.stderr.write(proc.stderr)
        return 2
    if proc.returncode != 0:
        detail = (proc.stderr or proc.stdout or "").strip().splitlines()
        tail = detail[-1][:200] if detail else "no output"
        return refuse(guard_label,
                      f"the guard exited {proc.returncode} instead of 0 or 2 "
                      f"(last output: {tail})")

    if not proc.stdout.strip():
        return refuse(guard_label, "the guard exited 0 but printed no decision")

    try:
        parsed = json.loads(proc.stdout)
        decision = parsed["hookSpecificOutput"]["permissionDecision"]
    except Exception as exc:
        head = proc.stdout.strip().splitlines()[0][:200]
        return refuse(guard_label,
                      f"the guard printed output that is not a hook decision "
                      f"({exc}; first line: {head})")

    if decision not in VALID_DECISIONS:
        return refuse(guard_label, f"the guard returned an unknown decision "
                                   f"{decision!r}")
    if decision == "ask":
        reason = parsed["hookSpecificOutput"].get("permissionDecisionReason", "")
        return refuse(guard_label,
                      "the guard answered `ask`, which was measured to be "
                      "satisfied silently in an interactive acceptEdits session; "
                      f"upgraded to a refusal. Guard said: {reason[:300]}")

    # allow and deny both pass through byte-for-byte.
    sys.stdout.write(proc.stdout)
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:  # never let the wrapper itself fail open
        print(f"[hook_gate] BLOCKED: the wrapper raised {type(exc).__name__}: {exc}",
              file=sys.stderr)
        sys.exit(2)

#!/usr/bin/env python3
"""PreToolUse entry point for Bash. Classification lives in engine/rules/policy.

Deliberately does not consult an authorization. The Bash gate is never relaxed by
maintenance: an authorization covers file-editing tools only, so `rm` on a protected
path stays refused no matter what has been issued. That is what keeps dismantling the
harness an owner operation rather than something the agent can be talked into.
"""
from __future__ import annotations

import json
import os
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

import engine  # noqa: E402
import observe  # noqa: E402
import policy as policy_mod  # noqa: E402

HINT = (
    "This gate classifies commands; it does not estimate how many files yours would "
    "touch.\nUniversal denials cannot be relaxed by repository policy or by a "
    "maintenance authorization. Ask the owner to run it outside Claude."
)


def emit(decision: str, reason: str, layer: str) -> None:
    print(json.dumps({"hookSpecificOutput": {
        "hookEventName": "PreToolUse",
        "permissionDecision": decision,
        "permissionDecisionReason": (
            f"[reliability/{layer}] {reason}" if decision == "allow"
            else f"[reliability/{layer}] Blocked: {reason}.\n{HINT}")}}))


def main() -> int:
    raw = sys.stdin.read()
    payload = json.loads(raw)
    if not isinstance(payload, dict):
        raise ValueError("payload is not an object")

    command = (payload.get("tool_input") or {}).get("command") or ""
    if payload.get("tool_name") != "Bash" or not command:
        emit("allow", "not a Bash command", engine.DEFAULT)
        return 0

    cwd = payload.get("cwd") or os.getcwd()
    project = os.environ.get("CLAUDE_PROJECT_DIR") or cwd
    decision, reason, layer = engine.decide_bash(command, cwd, project)
    observe.record("PreToolUse:Bash", payload, project, decision=decision,
                   layer=layer, policy=policy_mod.load(project).state)
    emit(decision, reason, layer)
    return 0


if __name__ == "__main__":
    # No try/except: the gate turns any failure here into a refusal, and swallowing
    # it would turn a broken guard into a silent allow.
    sys.exit(main())

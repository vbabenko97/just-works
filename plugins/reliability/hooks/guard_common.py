#!/usr/bin/env python3
"""PreToolUse entry point for every tool. Two jobs, in this order.

  1. Contract receipts. Any call carrying an `agent_id` must present the receipt
     written when the contract was delivered to that agent. Checked first, and for
     every tool including reads, because a subagent that never received the rules
     should not be gathering context under them either.

  2. Protected paths, for file-editing tools, where an owner authorization can apply.

Main-session calls carry no `agent_id` and are never asked for a receipt — measured,
not assumed: SubagentStart and subagent PreToolUse payloads carry `agent_id` and
`agent_type`, main-session PreToolUse carries neither.
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
import receipts  # noqa: E402

PATH_TOOLS = {"Write": ("file_path",), "Edit": ("file_path",),
              "MultiEdit": ("file_path",), "NotebookEdit": ("notebook_path",)}


def emit(decision: str, reason: str, layer: str) -> None:
    print(json.dumps({"hookSpecificOutput": {
        "hookEventName": "PreToolUse",
        "permissionDecision": decision,
        "permissionDecisionReason": (
            f"[reliability/{layer}] {reason}" if decision == "allow"
            else f"[reliability/{layer}] Blocked: {reason}")}}))


def target_paths(tool: str, tool_input: dict) -> list[str]:
    found = []
    for key in PATH_TOOLS.get(tool, ()):
        value = tool_input.get(key)
        if isinstance(value, str) and value:
            found.append(value)
    for edit in tool_input.get("edits") or []:
        if isinstance(edit, dict) and isinstance(edit.get("file_path"), str):
            found.append(edit["file_path"])
    return found


def main() -> int:
    payload = json.loads(sys.stdin.read())
    if not isinstance(payload, dict):
        raise ValueError("payload is not an object")

    tool = payload.get("tool_name") or ""
    tool_input = payload.get("tool_input") or {}
    cwd = payload.get("cwd") or os.getcwd()
    project = os.environ.get("CLAUDE_PROJECT_DIR") or cwd
    pol = policy_mod.load(project)

    if receipts.is_subagent(payload):
        required, why = engine.receipt_required(project)
        if required:
            ok, detail = receipts.verify(payload, project, pol.contract_version)
            if not ok:
                observe.record("PreToolUse:receipt", payload, project,
                               decision="deny", layer=engine.POLICY,
                               policy=pol.state, detail=detail)
                emit("deny", f"subagent contract not delivered: {detail}",
                     engine.POLICY)
                return 0
        else:
            detail = why

    if tool in PATH_TOOLS:
        paths_wanted = target_paths(tool, tool_input)
        if paths_wanted:
            decision, reason, layer = engine.decide_paths(tool, paths_wanted, cwd,
                                                          project)
            observe.record("PreToolUse:paths", payload, project, decision=decision,
                           layer=layer, policy=pol.state)
            emit(decision, reason, layer)
            return 0

    observe.record("PreToolUse:any", payload, project, decision="allow",
                   layer=engine.DEFAULT, policy=pol.state)
    emit("allow", f"{tool or 'tool'} carries no gated target", engine.DEFAULT)
    return 0


if __name__ == "__main__":
    sys.exit(main())

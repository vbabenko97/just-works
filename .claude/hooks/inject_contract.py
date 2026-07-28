#!/usr/bin/env python3
"""SubagentStart hook: inject the reliability contract into every subagent.

The built-in Explore and Plan agents skip CLAUDE.md, per the Claude Code docs:
"Explore and Plan skip your CLAUDE.md files and the parent session's git status
to keep research fast and inexpensive." Those two do the searching that produces
false-absence claims, so they are exactly the agents that need rule 1.

Writes an append-only receipt log so contract delivery can be proven per agent
type rather than assumed.
"""
from __future__ import annotations

import json
import os
import pathlib
import sys
import time

HERE = pathlib.Path(__file__).resolve().parent
CONTRACT = HERE.parent / "reliability-contract.md"
LOG = pathlib.Path(os.environ.get("RELIABILITY_LOG",
                                 pathlib.Path.home() / ".claude" / "contract-receipts.jsonl"))
VERSION = "tier1-2026-07-28"


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except Exception:
        payload = {}

    agent_type = (payload.get("agent_type") or payload.get("subagent_type")
                  or payload.get("agent") or "unknown")

    try:
        text = CONTRACT.read_text()
    except Exception as exc:
        # Never block a subagent because the contract file is missing.
        print(json.dumps({"hookSpecificOutput": {
            "hookEventName": "SubagentStart",
            "additionalContext": f"(reliability contract unavailable: {exc})"}}))
        return 0

    try:
        LOG.parent.mkdir(parents=True, exist_ok=True)
        with LOG.open("a") as fh:
            fh.write(json.dumps({
                "timestamp": int(time.time()),
                "agent_type": agent_type,
                "contract_version": VERSION,
                "contract_bytes": len(text),
                "session_id": payload.get("session_id"),
                "cwd": payload.get("cwd") or os.getcwd(),
            }) + "\n")
    except Exception:
        pass  # logging must not break the subagent

    # Issue the receipt that PreToolUse will demand. This is the enforceable half:
    # the append-only log above proves delivery after the fact, but nothing reads
    # it, so a failed injection was invisible. SubagentStart cannot refuse to
    # create the subagent — if this write does not happen, the subagent still
    # starts, and hook_gate.py then refuses its first tool call.
    try:
        sys.path.insert(0, str(HERE.parents[1] / "scripts" / "hooks"))
        import subagent_receipts
        subagent_receipts.issue(str(HERE.parents[1]), payload, VERSION, len(text))
    except Exception as exc:
        # Deliberately not fatal here: emitting the contract still helps, and the
        # missing receipt is what enforces the failure downstream.
        print(json.dumps({"hookSpecificOutput": {
            "hookEventName": "SubagentStart",
            "additionalContext": (f"<!-- reliability-contract {VERSION} -->\n{text}\n"
                                  f"<!-- receipt not issued: {exc} -->"),
        }}))
        return 0

    print(json.dumps({"hookSpecificOutput": {
        "hookEventName": "SubagentStart",
        "additionalContext": f"<!-- reliability-contract {VERSION} -->\n{text}",
    }}))
    return 0


if __name__ == "__main__":
    sys.exit(main())

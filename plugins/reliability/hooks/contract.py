#!/usr/bin/env python3
"""SubagentStart: deliver the rules, and record that they were delivered.

Explore and Plan do not read CLAUDE.md, so for them the injected text is the only
copy of the rules they ever see. SubagentStart cannot refuse to create the subagent,
so delivery alone guarantees nothing — the receipt written here is what
guard_common.py requires before the subagent may use any tool.

Whether a receipt is *required* is policy: a repository with no manifest gets the
contract text and no enforcement, and one that sets require_subagent_receipts gets
both. The receipt is written either way, so switching the flag on does not strand
agents that started before it.
"""
from __future__ import annotations

import json
import os
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

import observe  # noqa: E402
import paths  # noqa: E402
import policy as policy_mod  # noqa: E402
import receipts  # noqa: E402


def main() -> int:
    try:
        payload = json.loads(sys.stdin.read())
        if not isinstance(payload, dict):
            payload = {}
    except Exception:
        payload = {}

    cwd = payload.get("cwd") or os.getcwd()
    project = os.environ.get("CLAUDE_PROJECT_DIR") or cwd
    pol = policy_mod.load(project)
    composed = paths.compose_contract(project, pol)

    written = None
    if receipts.is_subagent(payload) and composed.ok:
        written = receipts.issue(project, payload, pol.contract_version, composed)

    observe.record("SubagentStart", payload, project, policy=pol.state,
                   contract_ok=composed.ok,
                   contract_source="+".join(composed.sources) if composed.ok else "",
                   contract_bytes=len(composed.text), contract_error=composed.error,
                   receipt=str(written) if written else None)

    if composed.ok:
        context_text = composed.text
    else:
        # No placeholder pretending to be contract content, and — critically — no
        # receipt was issued above, so the very next gated tool call denies on "no
        # contract receipt". This text only explains why, it grants nothing.
        context_text = (
            f"[reliability] Contract delivery failed: {composed.error}. No valid "
            f"receipt was issued. Every gated tool call will be denied until this "
            f"is fixed and a new subagent is started. Report this to whoever is "
            f"reading your output; do not attempt to route around it.")

    print(json.dumps({"hookSpecificOutput": {
        "hookEventName": "SubagentStart",
        "additionalContext": context_text}}))
    return 0


if __name__ == "__main__":
    # Never fails the session: a subagent that starts without a receipt is stopped at
    # its first tool call instead, which is the enforceable point.
    try:
        sys.exit(main())
    except Exception:
        sys.exit(0)

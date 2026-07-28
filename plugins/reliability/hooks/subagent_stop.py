#!/usr/bin/env python3
"""SubagentStop: a stateless safe-failure protocol.

A subagent that never received a valid contract cannot fix that from inside
itself — SubagentStart already fired once and will not fire again. This does not
track state across stop attempts (no marker files, no identity-keyed anything):
every invocation independently checks whether the *current* receipt is valid, and
if it isn't, whether the *current* payload's `last_assistant_message` already
carries the exact canonical CONTRACT_UNVERIFIED notice.

That works without persisted state because the payload itself carries what the
subagent just said. If it complied with a prior instruction to emit the notice,
this stop event's `last_assistant_message` already reflects that — nothing needs
to be remembered between calls. Missing agent_id, malformed identity, a
composition failure, and an unmatched stop event all fail receipts.verify() for
their own reason and are treated identically from there: check the message,
approve or block.

`last_assistant_message` is read directly from the payload only — no
transcript_path fallback. If it's missing, not a string, or doesn't match
exactly, that is non-compliance, and non-compliance blocks. Uncertainty must not
resolve to approval.

Deliberately no blanket `except Exception: sys.exit(0)`. An uncaught exception
must exit non-zero, because the outer launcher (run_stop_gate.sh) converts any
non-zero exit, any malformed output, and any timeout into a hardcoded block
decision. Fail-closed lives in the launcher; this script fails closed by not
swallowing its own errors into a quiet success.
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

CONTRACT_UNVERIFIED_NOTICE = (
    "CONTRACT_UNVERIFIED: This subagent's reliability contract could not be "
    "verified before it stopped. No conclusion in this session should be treated "
    "as reviewed or acted on. Re-run this work in a fresh subagent."
)


def block(reason: str) -> dict:
    return {"decision": "block", "reason": f"[reliability] {reason}"}


def main() -> int:
    try:
        payload = json.loads(sys.stdin.read())
        if not isinstance(payload, dict):
            payload = {}
    except Exception:
        payload = {}

    cwd = payload.get("cwd") or os.getcwd()
    project = os.environ.get("CLAUDE_PROJECT_DIR") or cwd

    # Live payload probe: which keys a real SubagentStop payload actually carries
    # — agent_id/agent_type per current docs; last_assistant_message read directly
    # below on the strength of this session's instruction, logged here so it stays
    # checkable against a real payload once this ships.
    observe.record("SubagentStop:payload", payload, project,
                   payload_keys=sorted(payload.keys()))

    pol = policy_mod.load(project)
    composed = paths.compose_contract(project, pol)
    ok, detail = receipts.verify(payload, project, pol.contract_version, composed)

    if ok:
        observe.record("SubagentStop", payload, project, policy=pol.state,
                       decision="approve", detail=detail)
        return 0

    last_message = payload.get("last_assistant_message")
    if isinstance(last_message, str) and last_message.strip() == CONTRACT_UNVERIFIED_NOTICE:
        observe.record("SubagentStop", payload, project, policy=pol.state,
                       decision="approve", detail=f"safe-failure notice matched "
                       f"(receipt invalid: {detail})")
        return 0

    observe.record("SubagentStop", payload, project, policy=pol.state,
                   decision="block", detail=detail)
    print(json.dumps(block(
        f"this subagent's contract could not be verified ({detail}). Return "
        f"exactly this notice and nothing else, then stop: "
        f"{CONTRACT_UNVERIFIED_NOTICE!r}")))
    return 0


if __name__ == "__main__":
    sys.exit(main())

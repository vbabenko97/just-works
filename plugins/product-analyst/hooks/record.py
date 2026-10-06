#!/usr/bin/env python3
"""Record outcomes for analyst reads after Claude Code has executed them.

PostToolUse is deliberately observational. A failure to write the ledger cannot
undo a tool call, so it reports context rather than pretending to enforce access.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Mapping

sys.path.insert(0, str(Path(__file__).resolve().parent))
import policy  # noqa: E402


def emit(event: str, message: str) -> None:
    print(
        json.dumps(
            {
                "hookSpecificOutput": {
                    "hookEventName": event,
                    "additionalContext": message,
                }
            }
        )
    )


def source_and_operation(payload: Mapping[str, object]) -> tuple[str, dict[str, object]] | None:
    tool_name = payload.get("tool_name")
    tool_input = payload.get("tool_input")
    if not isinstance(tool_name, str) or not isinstance(tool_input, dict):
        return None
    posthog_operation = policy.posthog_operation(tool_name, tool_input, payload.get("mcp_server"))
    if posthog_operation not in ("", None):
        return "posthog", policy.posthog_evidence_operation(
            tool_name, tool_input, posthog_operation
        )
    if tool_name == "Bash":
        classified = policy.quicksight_command(tool_input.get("command"))
        if classified is not None and classified[0]:
            return "quicksight", {"command": tool_input["command"], "operation": classified[1]}
    return None


def response_is_error(response: object) -> bool:
    """Recognise Claude Code's top-level transport error flag only."""
    return isinstance(response, dict) and (
        response.get("isError") is True or response.get("is_error") is True
    )


def main() -> int:
    event = "PostToolUse"
    try:
        payload = json.loads(sys.stdin.read())
        if not isinstance(payload, dict):
            raise ValueError("payload is not an object")
        raw_event = payload.get("hook_event_name") or payload.get("hookEventName")
        if isinstance(raw_event, str) and raw_event in {"PostToolUse", "PostToolUseFailure"}:
            event = raw_event
        root = policy.root_from(payload)
        if not policy.is_analyst_project(root):
            return 0
        tool_name = payload.get("tool_name")
        mcp_server = payload.get("mcp_server")
        server_name = mcp_server.get("name") if isinstance(mcp_server, dict) else ""
        if (
            isinstance(tool_name, str)
            and (
                "posthog" in policy.normalise(tool_name)
                or "posthog" in policy.normalise(str(server_name))
                or tool_name == "Bash"
            )
            and not isinstance(payload.get("tool_input"), dict)
        ):
            emit(event, "Analyst result was not recorded: invalid tool_input.")
            return 0
        found = source_and_operation(payload)
        if found is None:
            return 0
        session = payload.get("session_id")
        if not isinstance(session, str) or not session:
            emit(event, "Analyst result was not recorded: missing session_id.")
            return 0
        reservation = policy.ledger.reservation_for_request(
            root,
            policy.request_id(payload, session),
        )
        if not isinstance(reservation, dict):
            emit(event, "Analyst result was not recorded: no matching reservation.")
            return 0
        investigation = reservation.get("investigation_id")
        evidence = reservation.get("evidence_id")
        if not isinstance(investigation, str) or not isinstance(evidence, str):
            emit(event, "Analyst result was not recorded: invalid reservation.")
            return 0
        if event == "PostToolUseFailure":
            result = payload.get("error", payload.get("tool_response"))
            status = "error"
        else:
            result = payload.get("tool_response")
            status = "error" if response_is_error(result) else "ok"
        policy.ledger.complete(root, investigation, evidence, result, status=status)
        emit(event, f"Recorded {found[0]} evidence {evidence} ({status}).")
    except (json.JSONDecodeError, OSError, ValueError, KeyError, TypeError) as exc:
        # This hook cannot enforce after execution.  Return context instead of a
        # malformed reply that would hide the original tool result.
        emit(event, f"Analyst evidence recording failed: {exc}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

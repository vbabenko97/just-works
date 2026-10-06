#!/usr/bin/env python3
"""PreToolUse policy for the product-analyst plugin.

Hooks are an audit and ergonomics layer. Credentials and source-side roles are
the security boundary, so this guard defaults to no opinion for unrelated tools
and for every tool in a project without `.analyst/config.toml`. It only
restricts: a permitted call gets no opinion, never an approval, so the user's
own permission rules still apply to it.
"""

from __future__ import annotations

import json
import os
import re
import shlex
import sys
from pathlib import Path
from typing import Mapping

SERVER = Path(__file__).resolve().parents[1] / "server"
sys.path.insert(0, str(SERVER))
import config  # type: ignore  # noqa: E402
import ledger  # type: ignore  # noqa: E402

# This is deliberately a small exact allowlist. `check_posthog_tools.py`
# verifies every name against the checked-in PostHog generated inventory.
# Deployments should also configure PostHog's server-side `tools=` allowlist,
# but this plugin does not assume its connector has done so.
ALLOWED_POSTHOG_TOOLS = frozenset(
    {
        "execute-sql",
        "read-data-schema",
        "project-get",
        "docs-search",
        "generate-app-url",
        "metric-list",
        "metric-describe",
        # Runs a governed catalogue metric. The word "run" would otherwise deny it.
        "data-catalog-metric-run",
        "query-trends",
        "query-funnel",
        "query-retention",
        "query-paths",
        "query-stickiness",
        "query-lifecycle",
        "insight-get",
        "insight-query",
        "insights-list",
        "dashboard-get",
        "dashboards-get-all",
        "actions-get-all",
        "action-get",
        "annotation-retrieve",
        "annotations-list",
        "cohorts-list",
        "cohorts-retrieve",
        "experiment-get",
        "experiment-list",
        "experiment-results-get",
        "experiment-stats",
        "experiment-timeseries-results",
        "feature-flag-get-all",
        "feature-flag-get-definition",
        "feature-flag-get-definition-by-key",
        "notebooks-get",
        "notebooks-list",
    }
)
DISCOVERY_COMMANDS = frozenset({"learn", "search", "info", "schema", "tools"})
DENIED_WORDS = {
    "actor",
    "actors",
    "person",
    "persons",
    "create",
    "update",
    "delete",
    "remove",
    "patch",
    "write",
    "publish",
    "run",
    "feedback",
    "confirm",
    "archive",
    "destroy",
    "enable",
    "disable",
    "set",
    "reorder",
    "add",
    "copy",
    "launch",
    "pause",
    "resume",
    "unarchive",
    "freeze",
    "ship",
}
SHELL_META = re.compile(r"[|;&`$()<>\\\n\r]")
# AWS CLI global options that take no value; every other global option takes one.
AWS_FLAG_OPTIONS = frozenset(
    {
        "--debug",
        "--no-verify-ssl",
        "--no-paginate",
        "--no-sign-request",
        "--no-cli-pager",
        "--cli-auto-prompt",
        "--no-cli-auto-prompt",
    }
)


def emit(decision: str, reason: str) -> None:
    print(
        json.dumps(
            {
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": decision,
                    "permissionDecisionReason": f"[product-analyst] {reason}",
                }
            }
        )
    )


def noop() -> None:
    print("{}")


def root_from(payload: Mapping[str, object]) -> Path:
    raw = os.environ.get("CLAUDE_PROJECT_DIR") or payload.get("cwd") or os.getcwd()
    if not isinstance(raw, str):
        raise ValueError("cwd is invalid")
    return Path(raw).resolve()


def is_analyst_project(root: Path) -> bool:
    """Only projects configured for investigations are governed by this plugin."""
    return (root / ".analyst" / "config.toml").exists()


def normalise(value: str) -> str:
    return re.sub(r"-+", "-", value.strip().lower().replace("_", "-"))


def contains_denied_class(name: str) -> bool:
    tokens = set(filter(None, re.split(r"[^a-z0-9]+", normalise(name))))
    return bool(tokens & DENIED_WORDS) or name == "notebooks-run"


def posthog_exec_operation(command: str) -> str | None:
    """Parse PostHog's documented CLI wrapper without granting shell syntax."""
    # This string is parsed by PostHog, not a shell. Backslashes are required for
    # ordinary JSON arguments, but a line break would turn one wrapper call into
    # several commands on older server versions.
    if "\n" in command or "\r" in command:
        return None
    try:
        args = shlex.split(command)
    except ValueError:
        return None
    if not args:
        return None
    verb = normalise(args[0])
    if verb in {"learn", "search", "tools"}:
        return verb
    if verb in {"info", "schema"}:
        rest = [item for item in args[1:] if item != "--json"]
        return verb if len(rest) >= 1 else None
    if verb != "call":
        return None
    if "--confirm" in args:
        return "--confirm"
    rest = [item for item in args[1:] if item != "--json"]
    # `call <tool_name> <json_input>` is the documented wrapper grammar.
    if len(rest) != 2:
        return None
    try:
        body = json.loads(rest[1])
    except json.JSONDecodeError:
        return None
    if not isinstance(body, dict):
        return None
    return normalise(rest[0])


def posthog_operation(
    tool_name: str, tool_input: Mapping[str, object], mcp_server: object = None
) -> str | None:
    """Return the underlying PostHog operation, or None for an invalid wrapper."""
    server_name = mcp_server.get("name") if isinstance(mcp_server, dict) else ""
    if "posthog" not in normalise(str(server_name)) and "posthog" not in normalise(tool_name):
        return ""
    # Claude Code names MCP tools `mcp__<server>__<tool>`. Extracting the final
    # segment prevents a connector alias such as `posthog-prod` becoming part of
    # the operation and preserves policy enforcement for those aliases.
    parts = tool_name.rsplit("__", 1)
    if len(parts) != 2 or not parts[-1]:
        return None
    tool_operation = normalise(parts[-1])
    if tool_operation in {"exec", "execute"}:
        command = tool_input.get("command")
        if not isinstance(command, str) or not command.strip():
            return None
        return posthog_exec_operation(command)
    return tool_operation


def posthog_allowed(operation: str, extra: object) -> tuple[bool, str]:
    # The exact allowlist is reviewed name by name, so its entries are not subject to
    # the word heuristic below; `data-catalog-metric-run` only reads a metric.
    if operation in ALLOWED_POSTHOG_TOOLS or operation in DISCOVERY_COMMANDS:
        return True, operation
    if contains_denied_class(operation):
        return False, "PostHog mutations, person-level tools, confirmations and feedback are denied"
    allowed = False
    extras = (
        extra if isinstance(extra, list) and all(isinstance(item, str) for item in extra) else []
    )
    if operation in {normalise(item) for item in extras}:
        inventory_path = Path(__file__).resolve().parents[1] / "tests/fixtures/posthog-tools.json"
        try:
            inventory = json.loads(inventory_path.read_text())
            definition = inventory.get(operation) if isinstance(inventory, dict) else None
            annotations = definition.get("annotations") if isinstance(definition, dict) else None
            allowed = isinstance(annotations, dict) and annotations.get("readOnlyHint") is True
        except (OSError, json.JSONDecodeError):
            return False, "PostHog extra_read_tools inventory is unavailable"
    return (allowed, "PostHog operation is not in the configured read allowlist")


def quicksight_command(command: object) -> tuple[bool, str] | None:
    """Classify a Bash command that may call QuickSight through the AWS CLI.

    Commands that do not name both `aws` and `quicksight` get no opinion, so
    reading or searching files about QuickSight is unaffected. A command that names
    both must be one direct `aws [global options] quicksight <read operation>`.
    """
    if not isinstance(command, str):
        return None
    # Quotes and backslashes are removed first so `aws quick"sight"` is still seen.
    flattened = re.sub(r"[\"'\\]", "", command).lower()
    if "quicksight" not in flattened or not re.search(r"\baws\b", flattened):
        return None
    # Bash may interpret further syntax around this invocation. Hooks are only a
    # lexical layer, so accept the documented direct command spelling only.
    if SHELL_META.search(command) or '"' in command or "'" in command:
        return False, "QuickSight commands must be one direct aws command without shell syntax"
    args = command.split()
    if not args or args[0] != "aws":
        return False, "only direct aws quicksight commands are allowed"
    index = 1
    while index < len(args) and args[index].startswith("--"):
        option = args[index]
        index += 1 if option in AWS_FLAG_OPTIONS or "=" in option else 2
    if index < len(args) and args[index] != "quicksight":
        return None  # A direct call to another AWS service, such as an S3 bucket name.
    if index + 1 >= len(args):
        return False, "only direct aws quicksight commands are allowed"
    operation = args[index + 1]
    if not operation.startswith(("describe-", "list-", "search-")):
        return False, "only aws quicksight describe-, list- and search- commands are allowed"
    return True, operation


def request_id(payload: Mapping[str, object], session_id: str) -> str:
    raw = payload.get("tool_use_id") or payload.get("tool_call_id") or payload.get("request_id")
    if not isinstance(raw, str) or not raw:
        raise ValueError("relevant tool call has no tool_use_id")
    return f"{session_id}:{raw}"


def reserve(
    root: Path,
    payload: Mapping[str, object],
    source: str,
    operation: Mapping[str, object],
    limit: int | None,
) -> str:
    session = payload.get("session_id")
    if not isinstance(session, str) or not session:
        raise ValueError("relevant tool call has no session_id")
    investigation = ledger.current_investigation(root, session)
    if not investigation:
        raise ValueError("no active investigation for this session")
    return ledger.reserve(
        root, investigation, source, dict(operation), limit, request_id=request_id(payload, session)
    )


def posthog_evidence_operation(
    tool_name: str, tool_input: Mapping[str, object], operation: str
) -> dict[str, object]:
    command = tool_input.get("command")
    return {
        "tool": operation,
        # Preserve the exact wrapper command where one was used. The ledger hashes
        # this full operation object as part of its append-only evidence record.
        "command": command if isinstance(command, str) else tool_name,
        "arguments": dict(tool_input),
    }


def main() -> int:
    try:
        payload = json.loads(sys.stdin.read())
        if not isinstance(payload, dict):
            raise ValueError("payload is not an object")
        tool_name = payload.get("tool_name")
        tool_input = payload.get("tool_input")
        if not isinstance(tool_name, str) or not isinstance(tool_input, dict):
            raise ValueError("payload tool fields are invalid")

        operation = posthog_operation(tool_name, tool_input, payload.get("mcp_server"))
        relevant = operation != "" or (
            tool_name == "Bash" and quicksight_command(tool_input.get("command")) is not None
        )
        if not relevant or not is_analyst_project(root_from(payload)):
            noop()
            return 0

        if operation != "":
            if operation is None:
                emit("deny", "PostHog execute wrapper must contain exactly one plain command")
                return 0
            root = root_from(payload)
            try:
                settings = config.load_config(root)
                posthog = settings.get("posthog") if isinstance(settings, dict) else None
                extra = posthog.get("extra_read_tools", []) if isinstance(posthog, dict) else []
                budgets = settings.get("budgets") if isinstance(settings, dict) else {}
                limit = budgets.get("posthog_calls") if isinstance(budgets, dict) else None
                permitted, reason = posthog_allowed(operation, extra)
                if not permitted:
                    emit("deny", reason)
                    return 0
                reserve(
                    root,
                    payload,
                    "posthog",
                    posthog_evidence_operation(tool_name, tool_input, operation),
                    limit,
                )
            except (OSError, ValueError, KeyError, TypeError) as exc:
                emit("deny", f"PostHog policy unavailable: {exc}")
                return 0
            # No opinion: the user's permission rules still decide. record.py reports
            # the reserved evidence ID to the model after the call.
            noop()
            return 0

        if tool_name == "Bash":
            classified = quicksight_command(tool_input.get("command"))
            if classified is not None:
                permitted, detail = classified
                if not permitted:
                    emit("deny", detail)
                    return 0
                try:
                    reserve(
                        root_from(payload),
                        payload,
                        "quicksight",
                        {"command": tool_input["command"], "operation": detail},
                        None,
                    )
                except (OSError, ValueError, KeyError, TypeError) as exc:
                    emit("deny", f"QuickSight policy unavailable: {exc}")
                    return 0
                noop()
                return 0
        noop()
        return 0
    except (json.JSONDecodeError, ValueError, TypeError, OSError) as exc:
        emit("deny", f"policy failed closed: {exc}")
        return 0


if __name__ == "__main__":
    raise SystemExit(main())

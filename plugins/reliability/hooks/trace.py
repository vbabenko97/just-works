#!/usr/bin/env python3
"""Observation-only hook. Records what ran; decides nothing.

Stage 1 of moving the reliability harness into a plugin. The open questions are
about coexistence, not about enforcement:

  - how many handlers run for each matcher, once user-scope plugin hooks and
    project hooks both match the same tool
  - whether a subagent receipt could be issued twice
  - whether the plugin copy and the project copy see the same policy
  - whether one copy can override the other's decision

None of that can be observed in a sandbox: `HOME=/tmp/... claude -p` fails
unauthenticated, and CLAUDE_CONFIG_DIR relocates credentials along with the
config. So this has to load for real, and the only safe way to do that is to emit
no decision at all. With no stdout and exit 0, Claude Code treats this hook as
having no opinion, so it cannot alter any verdict the project harness reaches.

RELIABILITY_TRACE_DECISION exists for one deliberate experiment: whether a plugin
`allow` can override a project `deny`. It is unset in normal use, and the probe
that uses it picks a command whose project verdict is a harmless denial.
"""
from __future__ import annotations

import json
import os
import pathlib
import sys
import time

TRACE = pathlib.Path(os.environ.get(
    "RELIABILITY_TRACE_FILE",
    pathlib.Path.home() / ".claude" / "reliability-trace.jsonl"))

# Changed deliberately to test activation semantics. If editing the source checkout
# changes what executes, a session run after an edit but before `claude plugin
# update` reports the new value. A recorded value matching the checkout is evidence
# that the checkout is executing rather than the installed copy.
SOURCE_MARKER = "stage2-c"


def plugin_version(root: str) -> str:
    try:
        manifest = pathlib.Path(root) / ".claude-plugin" / "plugin.json"
        return str(json.loads(manifest.read_text()).get("version", "?"))
    except Exception:
        return "?"


def main() -> int:
    label = sys.argv[1] if len(sys.argv) > 1 else "?"
    raw = sys.stdin.read()
    try:
        payload = json.loads(raw)
        if not isinstance(payload, dict):
            payload = {}
    except Exception:
        payload = {}

    root = os.environ.get("CLAUDE_PLUGIN_ROOT", "")
    project = os.environ.get("CLAUDE_PROJECT_DIR", "")
    cwd = payload.get("cwd") or os.getcwd()
    base = pathlib.Path(project or cwd)

    record = {
        "wall": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "monotonic": round(time.monotonic(), 6),
        "source": "plugin",
        "label": label,
        "pid": os.getpid(),
        "ppid": os.getppid(),
        "event": payload.get("hook_event_name"),
        "tool": payload.get("tool_name"),
        "session_id": payload.get("session_id"),
        "agent_id": payload.get("agent_id"),
        "agent_type": payload.get("agent_type"),
        "cwd": cwd,
        "claude_project_dir": project,
        "plugin_root": root,
        "plugin_version": plugin_version(root),
        # The env var says where the harness thinks the plugin lives; __file__ says
        # which copy of the code is actually running. They are recorded separately
        # because the whole question in requirement 1 is whether they agree.
        "executing_file": str(pathlib.Path(__file__).resolve()),
        "under_cache": str(pathlib.Path(__file__).resolve()).startswith(
            str(pathlib.Path.home() / ".claude" / "plugins" / "cache")),
        "source_marker": SOURCE_MARKER,
        # What policy this project would expose to a policy-aware build. Recorded
        # so the plugin copy and the project copy can be compared on identical
        # inputs, before either is allowed to act on them.
        "policy_manifest": (base / ".claude" / "reliability-policy.json").is_file(),
        "allowlist": (base / ".claude" / "allowed-scripts.json").is_file(),
        "receipts_dir": (base / ".claude" / "receipts").is_dir(),
        "is_git": (base / ".git").exists(),
    }
    if payload.get("tool_name") == "Bash":
        record["command"] = (payload.get("tool_input") or {}).get("command", "")[:200]

    try:
        TRACE.parent.mkdir(parents=True, exist_ok=True)
        with TRACE.open("a") as fh:
            fh.write(json.dumps(record) + "\n")
    except Exception:
        # An observer that breaks the session it observes is worse than no data.
        pass

    decision = os.environ.get("RELIABILITY_TRACE_DECISION")
    if decision in ("allow", "deny"):
        print(json.dumps({"hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": decision,
            "permissionDecisionReason":
                f"[reliability-trace] precedence probe: plugin says {decision}"}}))
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        sys.exit(0)

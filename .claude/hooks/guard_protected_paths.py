#!/usr/bin/env python3
"""PreToolUse gate for Write, Edit and NotebookEdit.

The Bash gate is worthless if the agent can edit the Bash gate. It is equally
worthless if the agent can add its own script to the execution allowlist, or
delete the hook entry from settings.json. Those files are the trust anchor, so
ordinary file-editing tool calls do not reach them.

Decision is `deny`. `ask` was tried first and measured. In this interactive
session six `ask` verdicts were returned and all six tool calls proceeded with no
prompt, including edits to .claude/hooks/*.py. The transcript records exactly one
hook per call, exitCode 0, empty stderr and matcher `PreToolUse:Write`, so nothing
competed and nothing failed. The same hook output under
`claude -p --permission-mode acceptEdits` was refused, with the debug log showing
"Hook result has permissionBehavior=ask" then "Write tool permission denied" — so
the permission mode alone does not explain the interactive result, and `ask` is not
dependable here. `deny` blocked on both paths.

Maintenance does not require weakening this. A narrow authorization
(.claude/maintenance-auth.json, validated by maintenance_auth.py) can permit named
operations on named paths, bound to this repository, this HEAD, an expiry, a nonce
and a per-operation use budget. Anything it does not list stays denied, and it has
no effect whatsoever on the Bash gate.

Protocol: reads a PreToolUse payload on stdin, writes a decision to stdout.
"""
from __future__ import annotations

import json
import os
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from reliability_paths import CONTRACT_VERSION, is_protected, project_dir  # noqa: E402
import maintenance_auth  # noqa: E402

EDIT_TOOLS = {"Write", "Edit", "MultiEdit", "NotebookEdit", "Update"}


def emit(decision: str, reason: str) -> None:
    print(json.dumps({"hookSpecificOutput": {
        "hookEventName": "PreToolUse",
        "permissionDecision": decision,
        "permissionDecisionReason": reason,
    }}))


def target_paths(tool_input: dict) -> list[str]:
    keys = ("file_path", "notebook_path", "path", "filePath")
    found = [tool_input[k] for k in keys if isinstance(tool_input.get(k), str)]
    edits = tool_input.get("edits")
    if isinstance(edits, list):
        found += [e["file_path"] for e in edits
                  if isinstance(e, dict) and isinstance(e.get("file_path"), str)]
    return found


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except Exception:
        emit("deny", f"[{CONTRACT_VERSION}] guard_protected_paths.py could not parse "
                     "the hook payload; refusing rather than allowing.")
        return 0

    tool = payload.get("tool_name") or payload.get("tool") or ""
    tool_input = payload.get("tool_input") or {}
    if tool not in EDIT_TOOLS:
        emit("allow", "not a file-editing tool")
        return 0

    cwd = payload.get("cwd") or os.getcwd()
    project = project_dir()

    protected = []
    for raw in target_paths(tool_input):
        candidate = os.path.expanduser(raw)
        if not os.path.isabs(candidate):
            candidate = os.path.join(cwd, candidate)
        hit = is_protected(candidate, project)
        if hit:
            protected.append((raw, candidate, hit))

    if not protected:
        emit("allow", "target is not reliability infrastructure")
        return 0

    # Test every protected target before spending any use, so a MultiEdit naming
    # one authorized and one unauthorized path is refused whole.
    tested = [(raw, hit, maintenance_auth.check(project, tool, candidate))
              for raw, candidate, hit in protected]
    refused = [(raw, hit, why) for raw, hit, (ok, why) in tested if not ok]
    if refused:
        raw, hit, why = refused[0]
        emit("deny", (
            f"[{CONTRACT_VERSION}] {raw} is reliability infrastructure "
            f"(protected entry: {hit}).\n"
            "This file constrains what agents may do, so agents do not edit it.\n"
            f"No authorization covers this call: {why}.\n"
            "Print the intended diff for the repository owner to apply, or ask "
            "them to issue a narrow authorization from their own shell:\n"
            "  python3 scripts/verify/authorize_maintenance.py --minutes 30 "
            f"--reason '<why>' --op '{tool}:<repo-relative-path>:1'"
        ))
        return 0

    granted = []
    for raw, candidate, hit in protected:
        ok, why = maintenance_auth.check(project, tool, candidate, consume=True)
        if not ok:
            emit("deny", f"[{CONTRACT_VERSION}] {raw}: authorization lapsed "
                         f"between test and use: {why}")
            return 0
        granted.append(f"{raw}: {why}")
    emit("allow", f"[{CONTRACT_VERSION}] " + "; ".join(granted))
    return 0


if __name__ == "__main__":
    sys.exit(main())

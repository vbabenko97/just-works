#!/usr/bin/env python3
"""One trace line per hook process, so live behaviour can be checked afterwards.

Replaces the stage-1 trace hook. Folding it into the guards costs one process per
tool call instead of two, and records the decision alongside the context that
produced it.

SOURCE_MARKER is the instrument for the activation proofs: editing it in the checkout
and observing that live enforcement still reports the old value is what shows the
installed cache copy is executing, not the working tree.
"""
from __future__ import annotations

import json
import os
import pathlib
import sys
import time

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

import paths  # noqa: E402

SOURCE_MARKER = "step0-a"

TRACE = pathlib.Path(os.environ.get(
    "RELIABILITY_TRACE_FILE",
    pathlib.Path.home() / ".claude" / "reliability-trace.jsonl"))


def record(label: str, payload: dict, project: str, **extra) -> None:
    try:
        executing = str(pathlib.Path(__file__).resolve())
        cache = str(pathlib.Path.home() / ".claude" / "plugins" / "cache")
        row = {
            "wall": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "label": label,
            "pid": os.getpid(),
            "event": payload.get("hook_event_name"),
            "tool": payload.get("tool_name"),
            "session_id": payload.get("session_id"),
            "agent_id": payload.get("agent_id"),
            "agent_type": payload.get("agent_type"),
            "cwd": payload.get("cwd"),
            "project": project,
            "plugin_root": str(paths.plugin_root()),
            "plugin_data": str(paths.plugin_data()),
            "executing_file": executing,
            "under_cache": executing.startswith(cache),
            "revision": paths.installed_revision(),
            "source_marker": SOURCE_MARKER,
        }
        row.update(extra)
        if payload.get("tool_name") == "Bash":
            row["command"] = (payload.get("tool_input") or {}
                              ).get("command", "")[:200]
        TRACE.parent.mkdir(parents=True, exist_ok=True)
        with TRACE.open("a") as fh:
            fh.write(json.dumps(row) + "\n")
    except Exception:
        # An observer that breaks the session it observes is worse than no data.
        pass

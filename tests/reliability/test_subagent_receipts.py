#!/usr/bin/env python3
"""SubagentStart cannot block subagent creation, so delivery is proved at tool time.

The payload fields these tests rely on were measured, not assumed, by dumping real
hook payloads from a headless run that spawned an Explore agent:

  SubagentStart      session_id, agent_id, agent_type
  PreToolUse (sub)   session_id, agent_id, agent_type
  PreToolUse (main)  session_id, and no agent_id

Which is why "is this a subagent call" is decidable, and why a main-session call is
never asked for a receipt.
"""
from __future__ import annotations

import importlib.util
import json
import os
import pathlib
import shutil
import subprocess
import sys
import tempfile
import time

REPO = pathlib.Path(__file__).resolve().parents[2]
HOOKS = REPO / "scripts" / "hooks"
GATE = HOOKS / "hook_gate.py"
CONTRACT = "test-contract-1"

spec = importlib.util.spec_from_file_location("subagent_receipts",
                                              HOOKS / "subagent_receipts.py")
sr = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sr)

GUARD_ALLOW = ('print(\'{"hookSpecificOutput": {"hookEventName": "PreToolUse", '
               '"permissionDecision": "allow", "permissionDecisionReason": "guard ran"}}\')\n')


def build(root: pathlib.Path) -> pathlib.Path:
    project = root / "project"
    (project / ".claude" / "hooks").mkdir(parents=True)
    (project / ".claude" / "hooks" / "reliability_paths.py").write_text(
        f'CONTRACT_VERSION = "{CONTRACT}"\n')
    (project / ".claude" / "hooks" / "g_allow.py").write_text(GUARD_ALLOW)
    return project


def call(project: pathlib.Path, payload: dict, guard: str = "--receipt-only"):
    env = os.environ.copy()
    env["CLAUDE_PROJECT_DIR"] = str(project)
    proc = subprocess.run([sys.executable, str(GATE), guard],
                          input=json.dumps(payload), capture_output=True,
                          text=True, timeout=60, env=env)
    return proc


def sub_payload(session="s-1", agent="a-1", agent_type="Explore", tool="Read"):
    return {"tool_name": tool, "session_id": session, "agent_id": agent,
            "agent_type": agent_type, "cwd": "/tmp", "tool_input": {"file_path": "x"}}


def main() -> int:
    root = pathlib.Path(tempfile.mkdtemp(prefix="jw-receipt-"))
    failures = []

    def check(note, want_code, needle, proc):
        ok = proc.returncode == want_code and needle in (proc.stderr + proc.stdout)
        print(f"{proc.returncode:<5} {want_code:<5} {note}{'' if ok else '   <-- FAIL'}")
        if not ok:
            failures.append((note, want_code, proc.returncode,
                             (proc.stderr + proc.stdout).strip()[:170]))

    try:
        project = build(root)
        print(f"{'EXIT':5} {'WANT':5} CASE")
        print("-" * 76)

        # The main session carries no agent_id and must not need a receipt.
        check("a main-session call needs no receipt", 0, "receipt verified",
              call(project, {"tool_name": "Bash", "session_id": "s-1",
                             "cwd": "/tmp", "tool_input": {"command": "ls"}}))

        # A subagent with no receipt cannot act, even though it started.
        check("a subagent with no receipt is refused", 2, "no contract receipt",
              call(project, sub_payload()))

        # This is the broken-injection case: the guard would have allowed the call,
        # and the refusal still happens, before the guard is consulted.
        check("a broken injection refuses the subagent's first tool call", 2,
              "no contract receipt", call(project, sub_payload(tool="Bash"),
                                          guard="g_allow.py"))

        # After successful injection the same calls go through, for every agent type
        # that matters here.
        for agent_type in ("Explore", "Plan", "general-purpose", "python-code-writer"):
            payload = sub_payload(agent=f"a-{agent_type}", agent_type=agent_type)
            sr.issue(str(project), payload, CONTRACT, 1450)
            check(f"{agent_type} can use tools after injection", 0,
                  "receipt verified", call(project, payload))
            check(f"{agent_type} passes the real guard too", 0, "guard ran",
                  call(project, payload, guard="g_allow.py"))

        # Receipts are not transferable.
        good = sub_payload(session="s-A", agent="a-X", agent_type="Explore")
        sr.issue(str(project), good, CONTRACT, 1450)
        check("another session cannot reuse the receipt", 2, "no contract receipt",
              call(project, sub_payload(session="s-B", agent="a-X")))
        check("another agent cannot reuse the receipt", 2, "no contract receipt",
              call(project, sub_payload(session="s-A", agent="a-Y")))
        check("the same agent id under a different type is refused", 2,
              "issued for agent_type", call(project, sub_payload(
                  session="s-A", agent="a-X", agent_type="Plan")))

        # Contract version must match, or the subagent is working from old rules.
        stale_version = sub_payload(session="s-V", agent="a-V")
        sr.issue(str(project), stale_version, "some-older-contract", 1450)
        check("a receipt for another contract version is refused", 2,
              "receipt is for version", call(project, stale_version))

        # Corrupt and time-invalid receipts.
        broken = sub_payload(session="s-C", agent="a-C")
        path = pathlib.Path(sr.receipt_path(str(project), "s-C", "a-C"))
        sr.issue(str(project), broken, CONTRACT, 1450)
        path.write_text("{ not json")
        check("a malformed receipt is refused", 2, "malformed", call(project, broken))

        old = sub_payload(session="s-D", agent="a-D")
        sr.issue(str(project), old, CONTRACT, 1450)
        p = pathlib.Path(sr.receipt_path(str(project), "s-D", "a-D"))
        data = json.loads(p.read_text())
        data["issued_at"] = int(time.time()) - (sr.MAX_AGE_SECONDS + 120)
        p.write_text(json.dumps(data))
        check("a stale receipt is refused", 2, "stale", call(project, old))

        future = sub_payload(session="s-F", agent="a-F")
        sr.issue(str(project), future, CONTRACT, 1450)
        p = pathlib.Path(sr.receipt_path(str(project), "s-F", "a-F"))
        data = json.loads(p.read_text())
        data["issued_at"] = int(time.time()) + 3600
        p.write_text(json.dumps(data))
        check("a future-dated receipt is refused", 2, "future", call(project, future))

        check("a subagent call with no session_id is refused", 2,
              "without a session_id", call(project, {"tool_name": "Read",
                                                     "agent_id": "a-1",
                                                     "agent_type": "Explore",
                                                     "tool_input": {}}))
    finally:
        shutil.rmtree(root, ignore_errors=True)

    total = 4 + 2 * 4 + 3 + 1 + 3 + 1
    print(f"\n{total - len(failures)}/{total} passed")
    for row in failures:
        print(f"  FAIL {row}")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())

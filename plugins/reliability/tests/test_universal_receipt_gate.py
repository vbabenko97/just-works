#!/usr/bin/env python3
"""guard_common.py's PreToolUse receipt check is universal: any payload carrying
agent_id gets verified against the currently composed contract, regardless of
policy state and regardless of require_subagent_receipts. Only a payload with no
agent_id at all (a main-thread call) is unaffected.

Runs guard_common.py as the real subprocess — the same command hooks.json invokes
it through run_gate.sh with — not by calling its functions in-process.
"""
from __future__ import annotations

import json
import os
import pathlib
import shutil
import subprocess
import sys
import tempfile

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from _fixture import VALID_MANIFEST, Checks, build  # noqa: E402

HOOKS = pathlib.Path(__file__).resolve().parents[1] / "hooks"

NO_FLAG_MANIFEST = dict(VALID_MANIFEST)
NO_FLAG_MANIFEST["require_subagent_receipts"] = False


def payload_for(session="s1", agent="a1", agent_type="Explore", **extra) -> dict:
    row = {"session_id": session, "agent_id": agent, "agent_type": agent_type,
           "tool_name": "Read", "tool_input": {"file_path": "README.md"}}
    row.update(extra)
    return row


def main_thread_payload(**extra) -> dict:
    row = {"session_id": "s1", "tool_name": "Read",
           "tool_input": {"file_path": "README.md"}}
    row.update(extra)
    return row


def run_guard(project: pathlib.Path, payload: dict, env_extra: dict
             ) -> tuple[str, str]:
    """(permissionDecision, reason). guard_common.py directly — the launcher
    (run_gate.sh) is a separate concern already covered elsewhere."""
    env = os.environ.copy()
    env["CLAUDE_PROJECT_DIR"] = str(project)
    env.update(env_extra)
    proc = subprocess.run([sys.executable, str(HOOKS / "guard_common.py")],
                          input=json.dumps(payload), capture_output=True, text=True,
                          timeout=30, cwd=str(project), env=env)
    out = json.loads(proc.stdout)
    hso = out["hookSpecificOutput"]
    return hso["permissionDecision"], hso["permissionDecisionReason"]


def main() -> int:
    root = pathlib.Path(tempfile.mkdtemp(prefix="jw-universal-gate-"))
    data = root / "data"
    check = Checks()
    try:
        sys.path.insert(0, str(HOOKS))
        import paths  # noqa: E402
        import policy as policy_mod  # noqa: E402
        import receipts  # noqa: E402

        repos = {
            "absent": build(root, "absent", manifest=None),
            "valid": build(root, "valid", manifest=VALID_MANIFEST),
            "unflagged": build(root, "unflagged", manifest=NO_FLAG_MANIFEST),
            "invalid": build(root, "invalid", manifest='{"policy_version": 91}'),
        }

        for label, repo in repos.items():
            env_extra = {"RELIABILITY_DATA_DIR": str(data),
                        "RELIABILITY_TRACE_FILE": str(root / "trace.jsonl")}

            # ---- main-thread call: unaffected regardless of policy state -------
            decision, reason = run_guard(repo, main_thread_payload(), env_extra)
            check(decision == "allow",
                  f"[{label}] main-thread call (no agent_id) is unaffected",
                  reason)

            # ---- subagent without a receipt: universal deny --------------------
            fresh_payload = payload_for(session=f"s-{label}-noreceipt",
                                        agent=f"a-{label}-noreceipt")
            decision, reason = run_guard(repo, fresh_payload, env_extra)
            check(decision == "deny",
                  f"[{label}] subagent without a receipt is denied universally",
                  reason)

            # ---- subagent with a valid, current receipt: universal allow -------
            pol = policy_mod.load(str(repo))
            composed = paths.compose_contract(str(repo), pol)
            check(composed.ok, f"[{label}] composition succeeds for this fixture",
                  composed.error or "")
            live_payload = payload_for(session=f"s-{label}-live",
                                       agent=f"a-{label}-live")
            os.environ["RELIABILITY_DATA_DIR"] = str(data)
            written = receipts.issue(str(repo), live_payload, pol.contract_version,
                                     composed)
            check(written is not None, f"[{label}] a receipt could be issued for "
                                       f"this fixture", str(written))
            decision, reason = run_guard(repo, live_payload, env_extra)
            check(decision == "allow",
                  f"[{label}] subagent with a valid, current receipt is allowed "
                  f"universally", reason)

        # The "unflagged" fixture in the loop above has require_subagent_receipts
        # set to false and still gets denied/allowed identically to "valid" — that
        # comparison, not a separate assertion, is what proves the flag no longer
        # opts out.
    finally:
        shutil.rmtree(root, ignore_errors=True)

    return check.finish()


if __name__ == "__main__":
    sys.exit(main())

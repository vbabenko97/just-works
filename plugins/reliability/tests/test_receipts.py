#!/usr/bin/env python3
"""Contract delivery, enforced at tool time. Ported from test_subagent_receipts.py.

SubagentStart cannot refuse to create a subagent, so the receipt written at delivery
is the only enforceable proof. The key is (repository identity, session, agent, agent
type, contract version) — five bindings, each removing one way to borrow a receipt.

Changed from the project version: receipts live under ${CLAUDE_PLUGIN_DATA}, keyed by
canonical repository identity, not in `<repo>/.claude/receipts/`. A repository must
not hold the proof that its own rules were delivered — an agent that can write there
could otherwise manufacture it. One check asserts nothing is written into the
repository at all.
"""
from __future__ import annotations

import json
import os
import pathlib
import shutil
import subprocess
import sys
import tempfile
import time

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from _fixture import VALID_MANIFEST, Checks, build  # noqa: E402

HOOKS = pathlib.Path(__file__).resolve().parents[1] / "hooks"

SESSION = "sess-alpha"
AGENT = "agent-one"
CONTRACT = "tier1-2026-07-28"


def payload_for(session=SESSION, agent=AGENT, agent_type="Explore", **extra):
    row = {"session_id": session, "agent_id": agent, "agent_type": agent_type,
           "tool_name": "Read", "tool_input": {"file_path": "README.md"}}
    row.update(extra)
    return row


def main() -> int:
    root = pathlib.Path(tempfile.mkdtemp(prefix="jw-receipts-"))
    data = root / "data"
    os.environ["RELIABILITY_DATA_DIR"] = str(data)
    check = Checks()
    try:
        import engine  # noqa: E402  (after RELIABILITY_DATA_DIR is set)
        import paths  # noqa: E402
        import receipts  # noqa: E402

        policed = build(root, "policed", manifest=VALID_MANIFEST)
        plain = build(root, "plain", manifest=None)
        broken = build(root, "broken", manifest='{"policy_version": 91}')

        # ---- who must present one --------------------------------------------
        need, why = engine.receipt_required(str(policed))
        check(need is True, "valid policy with the flag requires receipts", why)
        need, why = engine.receipt_required(str(plain))
        check(need is False, "absent policy does not require receipts", why)
        need, why = engine.receipt_required(str(broken))
        check(need is False, "invalid policy does not require receipts", why)
        no_flag = dict(VALID_MANIFEST)
        no_flag["require_subagent_receipts"] = False
        unflagged = build(root, "unflagged", manifest=no_flag)
        need, why = engine.receipt_required(str(unflagged))
        check(need is False, "valid policy without the flag does not require them",
              why)

        check(receipts.is_subagent(payload_for()) is True,
              "a payload with agent_id is a subagent")
        check(receipts.is_subagent({"session_id": SESSION}) is False,
              "a main-session payload is not, so it is never asked for a receipt")

        # ---- issue, then verify ----------------------------------------------
        written = receipts.issue(str(policed), payload_for(), CONTRACT, 1234,
                                 "repository: contract.md")
        check(written is not None and written.is_file(), "issue writes a receipt",
              str(written))
        check(str(data) in str(written),
              "the receipt lives under the plugin data directory", str(written))
        check(not (policed / ".claude" / "receipts").exists(),
              "nothing is written into the repository")
        check(paths.repo_identity(str(policed)) != paths.repo_identity(str(plain)),
              "two repositories get different identities")

        ok, why = receipts.verify(payload_for(), str(policed), CONTRACT)
        check(ok, "a matching receipt verifies", why)
        check(receipts.count(str(policed), SESSION) == 1,
              "exactly one receipt for one agent")

        # ---- every way it must fail ------------------------------------------
        failures = {
            "no receipt at all": (payload_for(agent="agent-never"), str(policed),
                                  CONTRACT),
            "different session": (payload_for(session="sess-beta"), str(policed),
                                  CONTRACT),
            "different agent": (payload_for(agent="agent-two"), str(policed),
                                CONTRACT),
            "different agent type": (payload_for(agent_type="Plan"), str(policed),
                                     CONTRACT),
            "different contract version": (payload_for(), str(policed), "tier0-old"),
            "different repository": (payload_for(), str(plain), CONTRACT),
            "no session_id": ({"agent_id": AGENT, "agent_type": "Explore"},
                              str(policed), CONTRACT),
        }
        for label, (row, project, contract) in failures.items():
            ok, why = receipts.verify(row, project, contract)
            check(not ok, f"refused: {label}", why)

        # Tampering with the stored record.
        target = data / "receipts" / paths.repo_identity(str(policed)) / SESSION / \
            f"{AGENT}.json"
        original = target.read_text()

        target.write_text("{not json")
        ok, why = receipts.verify(payload_for(), str(policed), CONTRACT)
        check(not ok, "refused: unreadable receipt", why)

        record = json.loads(original)
        record["issued_at"] = int(time.time()) + 3600
        target.write_text(json.dumps(record))
        ok, why = receipts.verify(payload_for(), str(policed), CONTRACT)
        check(not ok, "refused: dated in the future", why)

        record["issued_at"] = int(time.time()) - receipts.MAX_AGE_SECONDS - 60
        target.write_text(json.dumps(record))
        ok, why = receipts.verify(payload_for(), str(policed), CONTRACT)
        check(not ok, "refused: stale", why)

        record["issued_at"] = int(time.time())
        record.pop("issued_at")
        target.write_text(json.dumps(record))
        ok, why = receipts.verify(payload_for(), str(policed), CONTRACT)
        check(not ok, "refused: no issue time", why)

        target.write_text(original)
        ok, why = receipts.verify(payload_for(), str(policed), CONTRACT)
        check(ok, "restoring the record verifies again", why)

        # ---- delivery through the real hook ----------------------------------
        env = os.environ.copy()
        env["RELIABILITY_DATA_DIR"] = str(data)
        env["CLAUDE_PROJECT_DIR"] = str(policed)
        env["RELIABILITY_TRACE_FILE"] = str(root / "trace.jsonl")
        start = payload_for(session="sess-live", agent="agent-live",
                            hook_event_name="SubagentStart")
        proc = subprocess.run([sys.executable, str(HOOKS / "contract.py")],
                              input=json.dumps(start), capture_output=True, text=True,
                              timeout=30, env=env)
        check(proc.returncode == 0, "contract.py exits 0", proc.stderr[:200])
        check("additionalContext" in proc.stdout,
              "contract.py emits the contract text", proc.stdout[:120])
        ok, why = receipts.verify(payload_for(session="sess-live", agent="agent-live"),
                                  str(policed), CONTRACT)
        check(ok, "the receipt it issued verifies", why)

        # A repository with no manifest still gets the contract, and its subagents
        # are not blocked for a receipt nobody requires.
        env["CLAUDE_PROJECT_DIR"] = str(plain)
        proc = subprocess.run([sys.executable, str(HOOKS / "contract.py")],
                              input=json.dumps(start), capture_output=True, text=True,
                              timeout=30, env=env)
        check("additionalContext" in proc.stdout,
              "an unpoliced repository still receives the contract")
    finally:
        shutil.rmtree(root, ignore_errors=True)

    return check.finish()


if __name__ == "__main__":
    sys.exit(main())

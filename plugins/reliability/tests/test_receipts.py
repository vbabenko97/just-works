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
        import policy as policy_mod  # noqa: E402
        import receipts  # noqa: E402

        policed = build(root, "policed", manifest=VALID_MANIFEST)
        plain = build(root, "plain", manifest=None)
        broken = build(root, "broken", manifest='{"policy_version": 91}')

        # Real composition against the real bundled files — this suite exercises
        # what actually ships, not a stand-in.
        composed = paths.compose_contract(str(policed), policy_mod.load(str(policed)))
        check(composed.ok, "composition succeeds for a policed repository",
              composed.error or "")
        composed_plain = paths.compose_contract(str(plain),
                                                 policy_mod.load(str(plain)))
        check(composed_plain.ok, "composition succeeds with no policy at all",
              composed_plain.error or "")

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
        written = receipts.issue(str(policed), payload_for(), CONTRACT, composed)
        check(written is not None and written.is_file(), "issue writes a receipt",
              str(written))
        check(str(data) in str(written),
              "the receipt lives under the plugin data directory", str(written))
        check(not (policed / ".claude" / "receipts").exists(),
              "nothing is written into the repository")
        check(paths.repo_identity(str(policed)) != paths.repo_identity(str(plain)),
              "two repositories get different identities")

        ok, why = receipts.verify(payload_for(), str(policed), CONTRACT, composed)
        check(ok, "a matching receipt verifies", why)
        check(receipts.count(str(policed), SESSION) == 1,
              "exactly one receipt for one agent")

        # issue() must refuse a composition that failed, on principle, not just for
        # repositories that happen to fail today.
        failed = paths.ComposedContract(False, "", (), None, composed.schema,
                                        "simulated composition failure")
        check(receipts.issue(str(policed), payload_for(agent="agent-refused"),
                             CONTRACT, failed) is None,
              "issue refuses to write a receipt for a failed composition")

        # ---- every way it must fail ------------------------------------------
        failures = {
            "no receipt at all": (payload_for(agent="agent-never"), str(policed),
                                  CONTRACT, composed),
            "different session": (payload_for(session="sess-beta"), str(policed),
                                  CONTRACT, composed),
            "different agent": (payload_for(agent="agent-two"), str(policed),
                                CONTRACT, composed),
            "different agent type": (payload_for(agent_type="Plan"), str(policed),
                                     CONTRACT, composed),
            "different contract version": (payload_for(), str(policed), "tier0-old",
                                           composed),
            "different repository": (payload_for(), str(plain), CONTRACT,
                                     composed_plain),
            "no session_id": ({"agent_id": AGENT, "agent_type": "Explore"},
                              str(policed), CONTRACT, composed),
            "composition currently unavailable": (payload_for(), str(policed),
                                                   CONTRACT, failed),
        }
        for label, (row, project, contract, comp) in failures.items():
            ok, why = receipts.verify(row, project, contract, comp)
            check(not ok, f"refused: {label}", why)

        # Tampering with the stored record.
        target = data / "receipts" / paths.repo_identity(str(policed)) / SESSION / \
            f"{AGENT}.json"
        original = target.read_text()

        target.write_text("{not json")
        ok, why = receipts.verify(payload_for(), str(policed), CONTRACT, composed)
        check(not ok, "refused: unreadable receipt", why)

        record = json.loads(original)
        record["issued_at"] = int(time.time()) + 3600
        target.write_text(json.dumps(record))
        ok, why = receipts.verify(payload_for(), str(policed), CONTRACT, composed)
        check(not ok, "refused: dated in the future", why)

        record["issued_at"] = int(time.time()) - receipts.MAX_AGE_SECONDS - 60
        target.write_text(json.dumps(record))
        ok, why = receipts.verify(payload_for(), str(policed), CONTRACT, composed)
        check(not ok, "refused: stale", why)

        record["issued_at"] = int(time.time())
        record.pop("issued_at")
        target.write_text(json.dumps(record))
        ok, why = receipts.verify(payload_for(), str(policed), CONTRACT, composed)
        check(not ok, "refused: no issue time", why)

        target.write_text(original)
        ok, why = receipts.verify(payload_for(), str(policed), CONTRACT, composed)
        check(ok, "restoring the record verifies again", why)

        # ---- every mandatory field, removed one at a time ---------------------
        for field in receipts.MANDATORY_FIELDS:
            record = json.loads(original)
            record.pop(field, None)
            target.write_text(json.dumps(record))
            ok, why = receipts.verify(payload_for(), str(policed), CONTRACT, composed)
            check(not ok, f"refused: receipt missing {field}", why)
        target.write_text(original)

        # An old-format receipt (pre-digest schema) is indistinguishable from one
        # missing every mandatory field at once — same refusal.
        record = json.loads(original)
        for field in receipts.MANDATORY_FIELDS:
            record.pop(field, None)
        record["contract_bytes"] = 1234
        record["contract_source"] = "repository: contract.md"  # old single-field shape
        target.write_text(json.dumps(record))
        ok, why = receipts.verify(payload_for(), str(policed), CONTRACT, composed)
        check(not ok, "refused: old-format (pre-digest) receipt", why)

        # Correct version, wrong digest: the exact gap a manually-bumped label
        # alone would miss.
        record = json.loads(original)
        record["contract_sha256"] = "0" * 64
        target.write_text(json.dumps(record))
        ok, why = receipts.verify(payload_for(), str(policed), CONTRACT, composed)
        check(not ok, "refused: correct version, wrong digest", why)

        # Wrong composition schema, correct everything else.
        record = json.loads(original)
        record["composition_schema"] = "some-older-scheme-v0"
        target.write_text(json.dumps(record))
        ok, why = receipts.verify(payload_for(), str(policed), CONTRACT, composed)
        check(not ok, "refused: composition schema mismatch", why)

        target.write_text(original)
        ok, why = receipts.verify(payload_for(), str(policed), CONTRACT, composed)
        check(ok, "restoring the record verifies again (post mandatory-field pass)",
              why)

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
                                  str(policed), CONTRACT, composed)
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

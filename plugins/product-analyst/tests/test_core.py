"""Contract, provenance, budget, and concurrent-session regression tests."""

import hashlib
import json
import sys
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "server"))
import config
import ledger

CONTRACT = {
    "metric": "activation",
    "metric_version": "1",
    "population": "new accounts",
    "window": {"start": "2026-09-21T00:00:00+02:00", "end": "2026-09-28T00:00:00+02:00"},
    "timezone": "Europe/Vienna",
    "comparison": "previous week",
}
UNCERTAINTY = dict.fromkeys(
    ("data_quality", "metric_definition", "magnitude", "cause"), "unverified"
)


class CoreTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        (self.root / ".analyst").mkdir()
        (self.root / ".analyst/config.toml").write_text(
            '[analysis]\ntimezone="Europe/Vienna"\ninternal_user_exclusion="exclude test accounts"\n[postgres]\nservice="analyst"\nschemas=["analytics"]\n'
        )

    def start(self, session="session-a"):
        return ledger.start(self.root, CONTRACT, session)["investigation_id"]

    def test_session_pointers_do_not_mix_evidence(self):
        first, second = self.start(), self.start("session-b")
        self.assertEqual(ledger.current_investigation(self.root, "session-a"), first)
        self.assertEqual(ledger.current_investigation(self.root, "session-b"), second)
        self.assertNotEqual(first, second)
        self.assertTrue(
            (self.root / ".analyst/.gitignore").read_text().count("investigations/") == 1
        )

    def test_request_binding_survives_new_investigation_in_same_session(self):
        first = self.start()
        evidence = ledger.reserve(
            self.root, first, "posthog", {"tool": "metric-list"}, 2, "session-a:call1"
        )
        second = self.start()
        self.assertEqual(ledger.current_investigation(self.root, "session-a"), second)
        self.assertEqual(
            ledger.reservation_for_request(self.root, "session-a:call1"),
            {
                "investigation_id": first,
                "evidence_id": evidence,
            },
        )
        with self.assertRaisesRegex(ValueError, "another investigation"):
            ledger.reserve(
                self.root, second, "posthog", {"tool": "metric-list"}, 2, "session-a:call1"
            )

    def test_contract_requires_ordered_aware_window(self):
        for window in (
            {"start": "2026-09-28", "end": "2026-09-29"},
            {"start": CONTRACT["window"]["end"], "end": CONTRACT["window"]["start"]},
        ):
            with self.subTest(window=window), self.assertRaises(ValueError):
                ledger.start(self.root, {**CONTRACT, "window": window}, "a")

    def test_budget_reserves_before_execution_and_counts_errors(self):
        inv = self.start()
        eid = ledger.reserve(self.root, inv, "posthog", {"command": "query-trends"}, 1, "call-1")
        self.assertEqual(
            ledger.reserve(self.root, inv, "posthog", {"command": "query-trends"}, 1, "call-1"), eid
        )
        ledger.complete(self.root, inv, eid, {"error": "timeout"}, status="error")
        with self.assertRaises(ledger.BudgetExceeded):
            ledger.reserve(self.root, inv, "posthog", {"command": "query-trends"}, 1)

    def test_concurrent_budget_has_no_overrun(self):
        inv = self.start()

        def reserve(_):
            try:
                return ledger.reserve(self.root, inv, "postgres", {"sql": "SELECT 1"}, 3)
            except ledger.BudgetExceeded:
                return None

        with ThreadPoolExecutor(max_workers=8) as pool:
            ids = [eid for eid in pool.map(reserve, range(16)) if eid]
        self.assertEqual(len(set(ids)), 3)

    def test_result_hash_covers_full_result_and_excerpt_is_bounded(self):
        inv = self.start()
        eid = ledger.reserve(self.root, inv, "postgres", {"sql": "SELECT 1"}, 2)
        result = {"value": "x" * 10000}
        row = ledger.complete(self.root, inv, eid, result)
        encoded = json.dumps(result, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
        self.assertEqual(row["result_sha256"], hashlib.sha256(encoded.encode()).hexdigest())
        self.assertLessEqual(len(row["result_excerpt"]), 2000)
        self.assertEqual(row["evidence_id"], eid)

    def test_claims_reject_missing_pending_and_error_evidence(self):
        inv = self.start()
        eid = ledger.reserve(self.root, inv, "postgres", {"sql": "SELECT 1"}, 2)
        findings = {
            "claims": [
                {
                    "id": "c1",
                    "text": "One account",
                    "evidence_ids": [eid],
                    "uncertainty": UNCERTAINTY,
                }
            ],
            "stop_reason": "SUPPORTED",
            "uncertainty": UNCERTAINTY,
        }
        self.assertFalse(ledger.check_claims(self.root, inv, findings)["valid"])
        ledger.complete(self.root, inv, eid, {"rows": [[1]]})
        self.assertTrue(ledger.check_claims(self.root, inv, findings)["valid"])
        findings["claims"][0]["evidence_ids"] = ["ev_missing"]
        self.assertFalse(ledger.check_claims(self.root, inv, findings)["valid"])

    def test_invalid_findings_do_not_replace_valid_file(self):
        inv = self.start()
        findings = {"claims": [], "stop_reason": "BUDGET_EXHAUSTED", "uncertainty": UNCERTAINTY}
        self.assertTrue(ledger.check_claims(self.root, inv, findings)["valid"])
        findings["stop_reason"] = "DONE"
        self.assertFalse(ledger.check_claims(self.root, inv, findings)["valid"])
        saved = json.loads(
            (self.root / ".analyst/investigations" / inv / "findings.json").read_text()
        )
        self.assertEqual(saved["stop_reason"], "BUDGET_EXHAUSTED")

    def test_supported_requires_claims_and_uncertainty(self):
        inv = self.start()
        self.assertFalse(
            ledger.check_claims(
                self.root,
                inv,
                {"claims": [], "stop_reason": "SUPPORTED", "uncertainty": UNCERTAINTY},
            )["valid"]
        )
        with self.assertRaises(ValueError):
            ledger.reserve(self.root, "../escape", "postgres", {}, 1)

    def test_config_rejects_unsafe_bounds_and_service_strings(self):
        self.assertEqual(config.load_config(self.root)["budgets"]["postgres_queries"], 30)
        for setting in (
            "row_cap = 0",
            "max_plan_cost = nan",
            "statement_timeout_ms = -1",
            'service = "host=attacker password=secret"',
        ):
            with self.subTest(setting=setting):
                (self.root / ".analyst/config.toml").write_text(
                    '[postgres]\nschemas=["analytics"]\n'
                    + ("" if setting.startswith("service") else 'service="analyst"\n')
                    + setting
                )
                with self.assertRaises(ValueError):
                    config.load_config(self.root)

    def test_config_or_metric_changes_require_new_investigation(self):
        inv = self.start()
        eid = ledger.reserve(self.root, inv, "postgres", {"sql": "SELECT 1"}, 2)
        ledger.complete(self.root, inv, eid, {"rows": [[1]]})
        findings = {"claims": [], "stop_reason": "INCONCLUSIVE", "uncertainty": UNCERTAINTY}
        self.assertTrue(ledger.check_claims(self.root, inv, findings)["valid"])
        for filename, content in (
            ("metrics.toml", "[metrics.activation]\nversion=2\n"),
            ("config.toml", "\n# Changed connection configuration\n"),
        ):
            path = self.root / ".analyst" / filename
            original = path.read_bytes() if path.exists() else None
            path.write_text((original.decode() if original else "") + content)
            with self.subTest(filename=filename):
                with self.assertRaisesRegex(ValueError, "changed"):
                    ledger.reserve(self.root, inv, "postgres", {"sql": "SELECT 2"}, 2)
                self.assertFalse(ledger.check_claims(self.root, inv, findings)["valid"])
            if original is None:
                path.unlink()
            else:
                path.write_bytes(original)

    def test_malformed_stop_reason_returns_validation_errors(self):
        inv = self.start()
        for invalid in ([], {}, None):
            self.assertFalse(
                ledger.check_claims(
                    self.root,
                    inv,
                    {
                        "claims": [],
                        "stop_reason": invalid,
                        "uncertainty": UNCERTAINTY,
                    },
                )["valid"]
            )


if __name__ == "__main__":
    unittest.main()

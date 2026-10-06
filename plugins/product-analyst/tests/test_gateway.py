"""Gateway provenance and metric catalogue behavior without database credentials."""

import json
import sys
import tempfile
import traceback
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "server"))
import gateway
import ledger
from test_core import CONTRACT


class GatewayTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        (self.root / ".analyst").mkdir()
        (self.root / ".analyst/config.toml").write_text(
            '[postgres]\nservice="test"\nschemas=["analytics"]\n[budgets]\npostgres_queries=1\n'
        )
        self.inv = ledger.start(self.root, CONTRACT, "test")["investigation_id"]

    def test_success_persists_query_and_returns_evidence_id(self):
        with patch(
            "postgres.execute_query",
            return_value={"rows": [[7]], "columns": ["count"], "plan_cost": 2.0, "row_count": 1},
        ):
            result = gateway.query(self.root, self.inv, "SELECT count(*) FROM analytics.accounts")
        state = ledger.get_investigation(self.root, self.inv)
        self.assertEqual(result["rows"], [[7]])
        self.assertEqual(
            state["evidence"][0]["operation"]["sql"], "SELECT count(*) FROM analytics.accounts"
        )
        self.assertEqual(state["evidence"][1]["evidence_id"], result["evidence_id"])
        with self.assertRaises(ledger.BudgetExceeded):
            gateway.query(self.root, self.inv, "SELECT 2")

    def test_failed_queries_count_without_leaking_exception_secrets(self):
        with patch("postgres.execute_query", side_effect=RuntimeError("password=do-not-log")):
            try:
                gateway.query(self.root, self.inv, "SELECT 1")
            except ValueError:
                self.assertNotIn("do-not-log", traceback.format_exc())
            else:
                self.fail("Query must fail")
        state = ledger.get_investigation(self.root, self.inv)
        self.assertEqual(state["evidence"][1]["status"], "error")
        self.assertNotIn("do-not-log", json.dumps(state))
        with self.assertRaises(ledger.BudgetExceeded):
            gateway.query(self.root, self.inv, "SELECT 2")

    def test_guard_and_gateway_reasons_reach_the_caller_and_ledger(self):
        # The guard runs before any connection, so no database is needed.
        with self.assertRaisesRegex(ValueError, "exactly one statement is allowed") as raised:
            gateway.query(self.root, self.inv, "SELECT 1; SELECT 2")
        self.assertIn("evidence_id=ev_", str(raised.exception))
        state = ledger.get_investigation(self.root, self.inv)
        self.assertEqual(state["evidence"][1]["status"], "error")
        self.assertIn("exactly one statement is allowed", state["evidence"][1]["result_excerpt"])

    def test_metric_version_and_mapping_preserved(self):
        (self.root / ".analyst/metrics.toml").write_text(
            '[metrics.activation]\nversion=2\ndenominator="new accounts"\nposthog_metric="activation-rate"\n[mappings.posthog_to_postgres]\nactivation_rate="activation"\n'
        )
        metric = gateway.metric_definition(self.root, "activation")
        self.assertEqual(metric["definition"]["version"], 2)
        self.assertEqual(metric["definition"]["posthog_metric"], "activation-rate")
        self.assertEqual(metric["mappings"]["posthog_to_postgres"]["activation_rate"], "activation")
        with self.assertRaises(ValueError):
            gateway.metric_definition(self.root, "undefined")

    def test_shipped_project_templates_load_without_iam_credentials(self):
        setup = Path(__file__).resolve().parents[1] / "setup"
        for name in ("config", "metrics"):
            (self.root / f".analyst/{name}.toml").write_bytes(
                (setup / f"{name}.example.toml").read_bytes()
            )
        settings = gateway.load_config(self.root)
        self.assertIsNone(settings["postgres"].get("iam"))
        self.assertGreater(settings["budgets"]["postgres_queries"], 0)
        metric = gateway.metric_definition(self.root, "activation_rate_v4")
        self.assertEqual(metric["definition"]["version"], "4")


if __name__ == "__main__":
    unittest.main()

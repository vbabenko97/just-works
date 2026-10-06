"""Disposable PostgreSQL 16 integration checks; run through run_postgres_integration.sh."""

import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "server"))
import postgres  # noqa: E402
from sqlguard import QueryGuardError  # noqa: E402

SERVICE = os.environ.get("ANALYST_TEST_SERVICE")
CONFIG = {
    "postgres": {
        "service": SERVICE,
        "schemas": ["analytics"],
        "statement_timeout_ms": 1000,
        "lock_timeout_ms": 200,
        "row_cap": 100,
    }
}


@unittest.skipUnless(SERVICE, "requires ANALYST_TEST_SERVICE from run_postgres_integration.sh")
class PostgresIntegrationTests(unittest.TestCase):
    def test_read_query_runs_as_dedicated_role(self):
        result = postgres.execute_query(
            CONFIG,
            "SELECT CASE WHEN count(*) FILTER (WHERE name ILIKE '%o%') % 2 = 0 THEN 1 ELSE 0 END AS even_matches FROM analytics.events",
        )
        self.assertEqual(result["columns"], ["even_matches"])
        self.assertEqual(result["rows"], [[1]])

    def test_login_role_has_default_read_only_settings(self):
        import psycopg

        with psycopg.connect(service=SERVICE, autocommit=True) as connection:
            values = {
                name: connection.execute(f"SHOW {name}").fetchone()[0]
                for name in ("default_transaction_read_only", "statement_timeout", "lock_timeout")
            }
        self.assertEqual(values["default_transaction_read_only"], "on")
        self.assertEqual(values["statement_timeout"], "15s")
        self.assertEqual(values["lock_timeout"], "2s")

    def test_attack_syntax_is_refused(self):
        queries = (
            "DROP TABLE analytics.events",
            "UPDATE analytics.events SET name = 'x'",
            "COMMIT; DELETE FROM analytics.events",
            "WITH changed AS (UPDATE analytics.events SET name = 'x' RETURNING *) SELECT * FROM changed",
            "COPY analytics.events TO PROGRAM 'id'",
            "SET ROLE postgres",
            "SET row_security = off",
            "SELECT set_config('default_transaction_read_only', 'off', false)",
            "SELECT 1 -- DELETE FROM analytics.events",
        )
        for query in queries:
            with self.subTest(query=query), self.assertRaises(QueryGuardError):
                postgres.execute_query(CONFIG, query)

    def test_grouped_boolean_conditions_run(self):
        result = postgres.execute_query(
            CONFIG,
            "WITH named(id, label) AS (SELECT id, name FROM analytics.events) "
            "SELECT count(*) FROM named WHERE id > %s AND (label = %s OR label = %s)",
            [0, "one", "three"],
        )
        self.assertEqual(result["rows"], [[2]])

    def test_prefixed_literal_cannot_smuggle_statements(self):
        with self.assertRaisesRegex(QueryGuardError, "prefixed"):
            postgres.execute_query(
                CONFIG, "SELECT E'\\'', 1; COMMIT; SET statement_timeout = 0; SELECT '"
            )

    def test_server_refuses_multiple_statements_if_the_guard_misses_them(self):
        # Disable the lexical guard to prove the prepared-statement layer on its own.
        with patch.object(postgres, "validate_read_query", lambda sql: sql):
            with self.assertRaisesRegex(postgres.PostgresGatewayError, "multiple commands"):
                postgres.execute_query(CONFIG, "SELECT 1; SELECT 2")

    def test_server_errors_are_reported_for_repair(self):
        with self.assertRaisesRegex(postgres.PostgresGatewayError, 'column "nme" does not exist'):
            postgres.execute_query(CONFIG, "SELECT nme FROM analytics.events")

    def test_timeout_and_row_cap_are_errors(self):
        timeout_config = {"postgres": {**CONFIG["postgres"], "statement_timeout_ms": 10}}
        with self.assertRaises(postgres.PostgresGatewayError):
            postgres.execute_query(
                timeout_config, "SELECT count(*) FROM generate_series(1, 1000000000)"
            )
        capped_config = {"postgres": {**CONFIG["postgres"], "row_cap": 2}}
        with self.assertRaisesRegex(postgres.PostgresGatewayError, "row cap"):
            postgres.execute_query(capped_config, "SELECT id FROM analytics.events ORDER BY id")

    def test_superuser_service_is_refused(self):
        unsafe_config = {"postgres": {**CONFIG["postgres"], "service": "unsafe"}}
        with self.assertRaisesRegex(postgres.PostgresGatewayError, "superuser"):
            postgres.execute_query(unsafe_config, "SELECT 1")

    def test_non_superuser_unsafe_roles_are_refused(self):
        cases = {
            "bypass": "BYPASSRLS",
            "owner": "ownership",
            "column_writer": "write privileges",
            "sequence_user": "write privileges",
        }
        for service, reason in cases.items():
            with (
                self.subTest(service=service),
                self.assertRaisesRegex(postgres.PostgresGatewayError, reason),
            ):
                postgres.execute_query(
                    {"postgres": {**CONFIG["postgres"], "service": service}}, "SELECT 1"
                )

    def test_select_grant_outside_configured_schema_is_refused(self):
        overgrant_config = {"postgres": {**CONFIG["postgres"], "service": "overgrant"}}
        with self.assertRaisesRegex(postgres.PostgresGatewayError, "SELECT outside"):
            postgres.execute_query(overgrant_config, "SELECT 1")

    def test_missing_schema_and_plan_cap_are_refused(self):
        with self.assertRaisesRegex(postgres.PostgresGatewayError, "schema missing"):
            postgres.execute_query(
                {"postgres": {**CONFIG["postgres"], "schemas": ["missing"]}}, "SELECT 1"
            )
        with self.assertRaisesRegex(postgres.PostgresGatewayError, "cost"):
            postgres.execute_query(
                {"postgres": {**CONFIG["postgres"], "max_plan_cost": 0.0001}},
                "SELECT count(*) FROM analytics.events",
            )

    def test_owner_default_privileges_cover_future_tables(self):
        result = postgres.execute_query(CONFIG, "SELECT id FROM analytics.future_events")
        self.assertEqual(result["rows"], [[1]])


if __name__ == "__main__":
    unittest.main()

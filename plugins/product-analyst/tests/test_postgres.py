"""Gateway behaviour without importing or requiring psycopg."""

import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "server"))
import postgres  # noqa: E402

CONFIG = {
    "postgres": {
        "service": "analyst",
        "schemas": ["analytics"],
        "statement_timeout_ms": 1000,
        "lock_timeout_ms": 200,
        "row_cap": 2,
        "max_plan_cost": 100,
    }
}


class Result:
    def __init__(self, one=None, many=None):
        self.one = one
        self.many = many or []

    def fetchone(self):
        return self.one

    def fetchmany(self, _count):
        return self.many


class Cursor(Result):
    def __init__(self, many):
        super().__init__(many=many)
        self.description = [type("Column", (), {"name": "value"})()]


class Transaction:
    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False


class ServerError(Exception):
    """Shaped like psycopg.Error: the server's message lives in `diag`."""

    def __init__(self):
        super().__init__("connection to host secret-host failed")
        self.diag = type(
            "Diagnostic",
            (),
            {
                "message_primary": 'column "nme" does not exist',
                "sqlstate": "42703",
                "message_hint": 'Perhaps you meant to reference the column "events.name".',
            },
        )()


class Connection:
    def __init__(
        self,
        audit=(True, False, False, False, False, False, False, False, False),
        rows=None,
        cost=3,
        explain_error=None,
    ):
        self.audit = audit
        self.rows = rows if rows is not None else [(1,), (2,)]
        self.cost = cost
        self.explain_error = explain_error
        self.calls = []
        self.prepared = {}

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def transaction(self, *, force_rollback=False):
        self.calls.append(("transaction", force_rollback))
        return Transaction()

    def execute(self, query, params=None, *, prepare=None):
        self.calls.append((query, params))
        self.prepared[query] = prepare
        if query == postgres._ROLE_AUDIT:
            return Result(self.audit)
        if query.startswith("EXPLAIN"):
            if self.explain_error is not None:
                raise self.explain_error
            return Result(([{"Plan": {"Total Cost": self.cost}}],))
        if query.startswith("SELECT"):
            return Cursor(self.rows)
        return Result()


class PostgresTests(unittest.TestCase):
    def test_execute_uses_transaction_guards_and_returns_rows(self):
        connection = Connection()
        with patch.object(postgres, "_connect", return_value=connection):
            result = postgres.execute_query(CONFIG, "SELECT 1")
        self.assertEqual(
            result, {"columns": ["value"], "rows": [[1], [2]], "plan_cost": 3.0, "row_count": 2}
        )
        queries = [query for query, _params in connection.calls if isinstance(query, str)]
        self.assertIn("SET LOCAL TRANSACTION READ ONLY", queries)
        self.assertIn("SET LOCAL row_security = on", queries)
        self.assertIn("SET LOCAL statement_timeout = '1000ms'", queries)
        self.assertIn("SET LOCAL lock_timeout = '200ms'", queries)
        self.assertIn("SET LOCAL standard_conforming_strings = on", queries)
        self.assertIn(("transaction", True), connection.calls)
        # Prepared statements make PostgreSQL itself refuse a second command.
        self.assertIs(connection.prepared["EXPLAIN (FORMAT JSON) SELECT 1"], True)
        self.assertIs(connection.prepared["SELECT 1"], True)

    def test_server_query_errors_are_described_for_repair(self):
        connection = Connection(explain_error=ServerError())
        with (
            patch.object(postgres, "_connect", return_value=connection),
            self.assertRaises(postgres.PostgresGatewayError) as raised,
        ):
            postgres.execute_query(CONFIG, "SELECT nme FROM events")
        message = str(raised.exception)
        self.assertIn('column "nme" does not exist', message)
        self.assertIn("42703", message)
        self.assertIn('"events.name"', message)
        self.assertNotIn("secret-host", message)

    def test_errors_without_server_diagnostics_stay_generic(self):
        connection = Connection(explain_error=RuntimeError("password=do-not-log"))
        with (
            patch.object(postgres, "_connect", return_value=connection),
            self.assertRaisesRegex(postgres.PostgresGatewayError, "^PostgreSQL query failed$"),
        ):
            postgres.execute_query(CONFIG, "SELECT 1")

    def test_refuses_unsafe_role_before_query(self):
        connection = Connection(audit=(True, False, True, False, False, False, False, False, False))
        with (
            patch.object(postgres, "_connect", return_value=connection),
            self.assertRaisesRegex(postgres.PostgresGatewayError, "BYPASSRLS"),
        ):
            postgres.execute_query(CONFIG, "SELECT 1")
        self.assertFalse(any(query == "SELECT 1" for query, _params in connection.calls))

    def test_row_cap_and_plan_limit_are_errors(self):
        with (
            patch.object(postgres, "_connect", return_value=Connection(rows=[(1,), (2,), (3,)])),
            self.assertRaisesRegex(postgres.PostgresGatewayError, "row cap"),
        ):
            postgres.execute_query(CONFIG, "SELECT 1")
        with (
            patch.object(postgres, "_connect", return_value=Connection(cost=101)),
            self.assertRaisesRegex(postgres.PostgresGatewayError, "cost"),
        ):
            postgres.execute_query(CONFIG, "SELECT 1")

    def test_core_module_loads_without_psycopg(self):
        self.assertNotIn("psycopg", sys.modules)


if __name__ == "__main__":
    unittest.main()

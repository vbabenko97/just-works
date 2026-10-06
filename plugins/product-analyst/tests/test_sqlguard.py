"""Regression cases for the intentionally narrow SQL guard."""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "server"))
from sqlguard import QueryGuardError, validate_read_query  # noqa: E402


class SqlGuardTests(unittest.TestCase):
    def test_allows_one_read_statement(self):
        for query in (
            "SELECT count(*) FROM analytics.events",
            "WITH recent AS (SELECT 1) SELECT * FROM recent",
            "SELECT CASE WHEN 1 = 1 THEN 1 ELSE 0 END",
            "VALUES (1), (2)",
            "TABLE analytics.events;",
        ):
            with self.subTest(query=query):
                self.assertTrue(validate_read_query(query))

    def test_refuses_mutation_and_multiple_statements(self):
        cases = (
            "DROP TABLE analytics.events",
            "UPDATE analytics.events SET name = 'changed'",
            "COMMIT; DELETE FROM analytics.events",
            "WITH deleted AS (DELETE FROM analytics.events RETURNING *) SELECT * FROM deleted",
            "COPY analytics.events TO PROGRAM 'id'",
            "SET ROLE admin",
            "SELECT 1; SELECT 2",
        )
        for query in cases:
            with self.subTest(query=query), self.assertRaises(QueryGuardError):
                validate_read_query(query)

    def test_allows_common_analytical_sql(self):
        cases = (
            "SELECT count(*) FROM t WHERE a = 1 AND (b = 2 OR c = 3)",
            "SELECT user_id FROM analytics.users WHERE (created_at >= %s AND created_at < %s) "
            "OR (created_at >= %s AND created_at < %s)",
            "WITH s(user_id) AS (SELECT 1), t(n) AS (SELECT 2) SELECT * FROM s, t",
            "WITH RECURSIVE r(n) AS (SELECT 1 UNION ALL SELECT n + 1 FROM r WHERE n < 3) "
            "SELECT n FROM r",
            "SELECT g.n FROM generate_series(1, 3) AS g(n)",
            "SELECT v.a FROM (VALUES (1, 2)) v(a, b)",
            "SELECT amount::numeric(10, 2), CAST(name AS varchar(20)) FROM orders",
            "SELECT percentile_cont(0.5) WITHIN GROUP (ORDER BY amount) FROM orders",
            "SELECT length(name), left(name, 3), split_part(email_domain, '.', 1) FROM accounts",
            "SELECT start, comment, set FROM sessions",
            "SELECT substring(name from 1 for 3) FROM accounts",
            "SELECT count(*) FILTER (WHERE status = 'it''s') FROM orders",
            "SELECT date_trunc('week', created_at) AS week, count(*) FROM orders "
            "GROUP BY ROLLUP (week)",
            # The period-comparison template from the design research.
            "WITH population AS (SELECT user_id, CASE WHEN created_at >= %s AND created_at < %s "
            "THEN 'current' WHEN created_at >= %s AND created_at < %s THEN 'baseline' END "
            "AS period, platform FROM analytics.users WHERE (created_at >= %s AND created_at < %s) "
            "OR (created_at >= %s AND created_at < %s)) SELECT period, platform, COUNT(*) AS users "
            "FROM population WHERE period IS NOT NULL GROUP BY period, platform "
            "ORDER BY period, users DESC",
        )
        for query in cases:
            with self.subTest(query=query):
                self.assertTrue(validate_read_query(query))

    def test_refuses_prefixed_literals_that_hide_statements(self):
        cases = (
            "SELECT E'\\'', 1; COMMIT; SELECT '",
            "SELECT e'\\'' AS x",
            "SELECT U&'d\\0061t\\+000061'",
            "SELECT B'101', X'1F', N'text'",
        )
        for query in cases:
            with self.subTest(query=query), self.assertRaisesRegex(QueryGuardError, "prefixed"):
                validate_read_query(query)

    def test_refuses_writes_and_locks_inside_read_statements(self):
        cases = (
            "SELECT * FROM analytics.events FOR UPDATE",
            "SELECT * FROM analytics.events FOR SHARE",
            "SELECT * FROM analytics.events FOR NO KEY UPDATE",
            "SELECT * INTO analytics.copy FROM analytics.events",
            "WITH x AS (INSERT INTO analytics.events VALUES (9, 'n') RETURNING *) SELECT * FROM x",
            "WITH x AS (SELECT 1) MERGE INTO analytics.events USING x ON true WHEN MATCHED THEN DO NOTHING",
            # Column-list positions do not exempt a call outside a WITH header.
            "WITH a AS (SELECT 1) SELECT 1, lo_get(1)",
            "SELECT * FROM (SELECT 1) AS pg_sleep(x)",
        )
        for query in cases:
            with self.subTest(query=query), self.assertRaises(QueryGuardError):
                validate_read_query(query)

    def test_refuses_comments_and_function_evasion(self):
        cases = (
            "SELECT 1 -- then DELETE FROM analytics.events",
            "SELECT /* set_config */ 1",
            "SELECT set_config('default_transaction_read_only', 'off', false)",
            "SELECT pg_catalog.pg_sleep(1)",
            "SELECT unsafe_schema.secret_reader()",
            "SELECT unsafe_schema.sum(1)",
            'SELECT "secret_reader"()',
        )
        for query in cases:
            with self.subTest(query=query), self.assertRaises(QueryGuardError):
                validate_read_query(query)


if __name__ == "__main__":
    unittest.main()

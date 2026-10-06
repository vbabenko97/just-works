"""Read-only PostgreSQL execution for the product analyst plugin."""

from __future__ import annotations

import json
import re
import subprocess
from collections.abc import Mapping, Sequence
from typing import TYPE_CHECKING, cast

from sqlguard import QueryGuardError, validate_read_query

if TYPE_CHECKING:
    from typing import Any


class PostgresGatewayError(RuntimeError):
    """Raised when the database gateway refuses or cannot execute a query."""


_IDENTIFIER = re.compile(r"[A-Za-z_][A-Za-z0-9_$]*\Z")
_ROLE_AUDIT = """
WITH RECURSIVE memberships(oid) AS (
    SELECT oid FROM pg_roles WHERE rolname = current_user
    UNION
    SELECT member_of.roleid
    FROM pg_auth_members AS member_of
    JOIN memberships ON member_of.member = memberships.oid
)
SELECT
    (SELECT count(*) FROM pg_namespace WHERE nspname = ANY(%s::text[])) = cardinality(%s::text[]),
    COALESCE((SELECT bool_or(rolsuper) FROM pg_roles WHERE oid IN (SELECT oid FROM memberships)), false),
    COALESCE((SELECT bool_or(rolbypassrls) FROM pg_roles WHERE oid IN (SELECT oid FROM memberships)), false),
    COALESCE((SELECT bool_or(rolcreaterole OR rolcreatedb OR rolreplication)
              FROM pg_roles WHERE oid IN (SELECT oid FROM memberships)), false),
    EXISTS(
        SELECT 1 FROM pg_class AS relation
        JOIN pg_namespace AS namespace ON namespace.oid = relation.relnamespace
        WHERE relation.relkind IN ('r', 'p', 'v', 'm', 'f')
          AND namespace.nspname !~ '^pg_'
          AND namespace.nspname <> 'information_schema'
          AND relation.relowner IN (SELECT oid FROM memberships)
    ),
    EXISTS(
        SELECT 1 FROM pg_namespace AS namespace
        WHERE namespace.nspname !~ '^pg_'
          AND namespace.nspname <> 'information_schema'
          AND has_schema_privilege(current_user, namespace.oid, 'CREATE')
    ),
    EXISTS(
        SELECT 1 FROM pg_class AS relation
        JOIN pg_namespace AS namespace ON namespace.oid = relation.relnamespace
        WHERE relation.relkind IN ('r', 'p', 'v', 'm', 'f', 'S')
          AND namespace.nspname !~ '^pg_'
          AND namespace.nspname <> 'information_schema'
          AND CASE WHEN relation.relkind = 'S' THEN
                  has_sequence_privilege(current_user, relation.oid, 'USAGE') OR
                  has_sequence_privilege(current_user, relation.oid, 'UPDATE')
              ELSE
                  has_table_privilege(current_user, relation.oid, 'INSERT') OR
                  has_table_privilege(current_user, relation.oid, 'UPDATE') OR
                  has_table_privilege(current_user, relation.oid, 'DELETE') OR
                  has_table_privilege(current_user, relation.oid, 'TRUNCATE') OR
                  has_table_privilege(current_user, relation.oid, 'REFERENCES') OR
                  has_table_privilege(current_user, relation.oid, 'TRIGGER') OR
                  has_any_column_privilege(current_user, relation.oid, 'INSERT') OR
                  has_any_column_privilege(current_user, relation.oid, 'UPDATE') OR
                  has_any_column_privilege(current_user, relation.oid, 'REFERENCES')
          END
    ),
    has_database_privilege(current_user, current_database(), 'CREATE'),
    EXISTS(
        SELECT 1 FROM pg_class AS relation
        JOIN pg_namespace AS namespace ON namespace.oid = relation.relnamespace
        WHERE relation.relkind IN ('r', 'p', 'v', 'm', 'f')
          AND namespace.nspname !~ '^pg_'
          AND namespace.nspname <> 'information_schema'
          AND namespace.nspname <> ALL(%s::text[])
          AND (
              has_table_privilege(current_user, relation.oid, 'SELECT') OR
              has_any_column_privilege(current_user, relation.oid, 'SELECT')
          )
    )
"""


def _postgres_config(config: Mapping[str, object]) -> Mapping[str, object]:
    raw = config.get("postgres", config)
    if not isinstance(raw, Mapping):
        raise PostgresGatewayError("postgres configuration must be an object")
    return cast(Mapping[str, object], raw)


def _positive_int(value: object, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise PostgresGatewayError(f"postgres.{name} must be a positive integer")
    return value


def _schemas(settings: Mapping[str, object]) -> list[str]:
    schemas = settings.get("schemas")
    if not isinstance(schemas, list) or not schemas:
        raise PostgresGatewayError("postgres.schemas must be a non-empty list")
    if not all(isinstance(schema, str) and _IDENTIFIER.fullmatch(schema) for schema in schemas):
        raise PostgresGatewayError("postgres.schemas contains an invalid identifier")
    return cast(list[str], schemas)


def _quote_identifier(identifier: str) -> str:
    return '"' + identifier.replace('"', '""') + '"'


def _import_psycopg() -> Any:
    try:
        import psycopg
    except ImportError as error:
        raise PostgresGatewayError("psycopg is required to execute PostgreSQL queries") from error
    return psycopg


def _iam_token(iam: Mapping[str, object]) -> tuple[str, int, str, str]:
    required = ("region", "host", "port", "user")
    if any(not iam.get(key) for key in required):
        raise PostgresGatewayError("postgres.iam requires region, host, port, and user")
    host, region, user = (str(iam["host"]), str(iam["region"]), str(iam["user"]))
    port = _positive_int(iam["port"], "iam.port")
    try:
        completed = subprocess.run(
            [
                "aws",
                "rds",
                "generate-db-auth-token",
                "--hostname",
                host,
                "--port",
                str(port),
                "--region",
                region,
                "--username",
                user,
            ],
            check=True,
            capture_output=True,
            text=True,
            timeout=15,
        )
    except (OSError, subprocess.SubprocessError) as error:
        raise PostgresGatewayError("could not generate RDS IAM authentication token") from error
    token = completed.stdout.strip()
    if not token:
        raise PostgresGatewayError("RDS IAM authentication returned an empty token")
    return host, port, user, token


def _connect(settings: Mapping[str, object]) -> Any:
    service = settings.get("service")
    if not isinstance(service, str) or not re.fullmatch(r"[A-Za-z0-9_.-]+", service):
        raise PostgresGatewayError("postgres.service must be a non-empty string")
    psycopg = _import_psycopg()
    kwargs: dict[str, object] = {"service": service}
    iam = settings.get("iam")
    if iam:
        if not isinstance(iam, Mapping):
            raise PostgresGatewayError("postgres.iam must be an object")
        host, port, user, token = _iam_token(cast(Mapping[str, object], iam))
        kwargs.update(
            {
                "host": host,
                "port": port,
                "user": user,
                "password": token,
                "sslmode": "verify-full",
                "connect_timeout": 10,
            }
        )
    try:
        return psycopg.connect(**kwargs)
    except Exception as error:
        raise PostgresGatewayError(
            "could not connect using PostgreSQL service configuration"
        ) from error


def _audit_role(connection: Any, schemas: Sequence[str]) -> None:
    row = connection.execute(_ROLE_AUDIT, [list(schemas), list(schemas), list(schemas)]).fetchone()
    if row is None or len(row) != 9:
        raise PostgresGatewayError("could not audit database role")
    if not row[0]:
        raise PostgresGatewayError("database role is unsafe: configured schema missing")
    labels = (
        "superuser",
        "BYPASSRLS",
        "role or database creation",
        "ownership",
        "schema CREATE",
        "write privileges",
        "database CREATE",
        "SELECT outside configured schemas",
    )
    unsafe = [label for label, present in zip(labels, row[1:], strict=True) if present]
    if unsafe:
        raise PostgresGatewayError("database role is unsafe: " + ", ".join(unsafe))


def _plan_cost(plan_value: object) -> float:
    if isinstance(plan_value, str):
        plan_value = json.loads(plan_value)
    if isinstance(plan_value, list):
        if not plan_value:
            raise PostgresGatewayError("EXPLAIN returned no plan")
        plan_value = plan_value[0]
    if not isinstance(plan_value, dict):
        raise PostgresGatewayError("EXPLAIN returned an invalid plan")
    plan = plan_value.get("Plan", plan_value)
    if not isinstance(plan, dict) or not isinstance(plan.get("Total Cost"), (int, float)):
        raise PostgresGatewayError("EXPLAIN plan has no total cost")
    return float(plan["Total Cost"])


def execute_query(config: dict, sql: str, params: list | None = None) -> dict:
    """Run one guarded read query and return JSON-friendly result metadata."""
    if params is not None and not isinstance(params, list):
        raise PostgresGatewayError("params must be a list or null")
    query = validate_read_query(sql)
    settings = _postgres_config(config)
    schemas = _schemas(settings)
    statement_timeout = _positive_int(settings.get("statement_timeout_ms"), "statement_timeout_ms")
    lock_timeout = _positive_int(settings.get("lock_timeout_ms"), "lock_timeout_ms")
    row_cap = _positive_int(settings.get("row_cap"), "row_cap")
    maximum_cost = settings.get("max_plan_cost")
    if maximum_cost is not None and (
        isinstance(maximum_cost, bool)
        or not isinstance(maximum_cost, (int, float))
        or maximum_cost <= 0
    ):
        raise PostgresGatewayError("postgres.max_plan_cost must be a positive number")
    search_path = ", ".join(["pg_catalog", *(_quote_identifier(schema) for schema in schemas)])

    with _connect(settings) as connection:
        try:
            with connection.transaction(force_rollback=True):
                connection.execute("SET LOCAL TRANSACTION READ ONLY")
                connection.execute("SET LOCAL row_security = on")
                # The query guard tokenizes plain string literals with standard rules.
                connection.execute("SET LOCAL standard_conforming_strings = on")
                connection.execute(f"SET LOCAL search_path = {search_path}")
                connection.execute(f"SET LOCAL statement_timeout = '{statement_timeout}ms'")
                connection.execute(f"SET LOCAL lock_timeout = '{lock_timeout}ms'")
                _audit_role(connection, schemas)
                # prepare=True sends a server-side prepared statement even without
                # parameters, and PostgreSQL refuses to prepare more than one command.
                plan_row = connection.execute(
                    "EXPLAIN (FORMAT JSON) " + query, params, prepare=True
                ).fetchone()
                if plan_row is None:
                    raise PostgresGatewayError("EXPLAIN returned no plan")
                cost = _plan_cost(plan_row[0])
                if maximum_cost is not None and cost > float(maximum_cost):
                    raise PostgresGatewayError(f"query plan cost {cost} exceeds configured limit")
                cursor = connection.execute(query, params, prepare=True)
                rows = cursor.fetchmany(row_cap + 1)
                if len(rows) > row_cap:
                    raise PostgresGatewayError(f"query result exceeds row cap of {row_cap}")
                columns = [column.name for column in cursor.description or []]
                return {
                    "columns": columns,
                    "rows": [list(row) for row in rows],
                    "plan_cost": cost,
                    "row_count": len(rows),
                }
        except QueryGuardError:
            raise
        except PostgresGatewayError:
            raise
        except Exception as error:
            raise PostgresGatewayError(_server_message(error)) from error


def _server_message(error: Exception) -> str:
    """Describe a server-side query error so the caller can repair the SQL.

    Connection failures are raised by `_connect` before this point; their messages
    can name hosts and users, so they stay generic there.
    """
    diag = getattr(error, "diag", None)
    primary = getattr(diag, "message_primary", None)
    if not isinstance(primary, str) or not primary:
        return "PostgreSQL query failed"
    message = f"PostgreSQL rejected the query: {primary}"
    sqlstate = getattr(diag, "sqlstate", None)
    if isinstance(sqlstate, str) and sqlstate:
        message += f" (SQLSTATE {sqlstate})"
    hint = getattr(diag, "message_hint", None)
    if isinstance(hint, str) and hint:
        message += f". Hint: {hint}"
    return message

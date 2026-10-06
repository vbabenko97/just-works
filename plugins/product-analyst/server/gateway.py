# /// script
# requires-python = ">=3.11"
# dependencies = ["mcp>=1.28,<2", "psycopg[binary]>=3.2,<4"]
# ///
"""Project-scoped MCP tools for bounded Postgres reads and analytical evidence."""

import json
import os
import tomllib
from pathlib import Path

import ledger
from config import load_config


def query(root: Path, investigation_id: str, sql: str, params: list | None = None) -> dict:
    import postgres

    config = load_config(root)
    evidence_id = ledger.reserve(
        root,
        investigation_id,
        "postgres",
        {"sql": sql, "params": params},
        config["budgets"]["postgres_queries"],
    )
    try:
        result = postgres.execute_query(config, sql, params)
    except Exception as exc:
        # The RPC boundary must persist every failed attempt, including driver
        # failures. Guard and gateway messages are written by this plugin and carry
        # no credentials, and the caller needs them to repair the query. Any other
        # exception could quote connection details, so it stays generic.
        if isinstance(exc, (postgres.QueryGuardError, postgres.PostgresGatewayError)):
            message = str(exc)
        else:
            message = "Postgres request failed; inspect the query, role, and service configuration."
        result = {"error_type": type(exc).__name__, "message": message}
        ledger.complete(root, investigation_id, evidence_id, result, status="error")
        raise ValueError(f"{message} (evidence_id={evidence_id})") from None
    ledger.complete(root, investigation_id, evidence_id, result)
    return json.loads(ledger.encoded({"evidence_id": evidence_id, **result}))


def metric_definition(root: Path, name: str) -> dict:
    with (root / ".analyst/metrics.toml").open("rb") as stream:
        catalogue = tomllib.load(stream)
    definitions = catalogue.get("metrics", {})
    if name not in definitions:
        raise ValueError(f"Metric {name!r} is not defined in .analyst/metrics.toml")
    return {
        "name": name,
        "definition": definitions[name],
        "mappings": catalogue.get("mappings", {}),
        "source": ".analyst/metrics.toml",
    }


def build_server(root: Path):
    from mcp.server.fastmcp import FastMCP

    server = FastMCP("product-analyst")

    @server.tool()
    def start_investigation(contract: dict, session_id: str) -> dict:
        """Record an analytical contract. Use the current Claude session ID."""
        load_config(root)
        return ledger.start(root, contract, session_id)

    @server.tool()
    def execute_read_query(investigation_id: str, sql: str, params: list | None = None) -> dict:
        """Execute one bounded read query, returning rows, plan cost, and evidence ID."""
        return query(root, investigation_id, sql, params)

    @server.tool()
    def describe_schema(investigation_id: str) -> dict:
        """Describe columns visible to the service role in configured schemas."""
        schemas = load_config(root)["postgres"]["schemas"]
        return query(
            root,
            investigation_id,
            "SELECT table_schema, table_name, column_name, data_type, is_nullable FROM information_schema.columns WHERE table_schema = ANY(%s) ORDER BY table_schema, table_name, ordinal_position",
            [schemas],
        )

    @server.tool()
    def get_metric_definition(name: str) -> dict:
        """Read the versioned local Postgres metric definition and source mappings."""
        return metric_definition(root, name)

    @server.tool()
    def get_investigation(investigation_id: str) -> dict:
        """Read the contract, evidence events, and findings for independent verification."""
        return ledger.get_investigation(root, investigation_id)

    @server.tool()
    def check_claims(investigation_id: str, findings: dict | None = None) -> dict:
        """Validate citations, stop reason, and uncertainty; persist valid findings."""
        return ledger.check_claims(root, investigation_id, findings)

    return server


if __name__ == "__main__":
    project = Path(os.environ["ANALYST_PROJECT_DIR"]).resolve()
    if not project.is_dir():
        raise ValueError("ANALYST_PROJECT_DIR is not a project directory")
    build_server(project).run(transport="stdio")

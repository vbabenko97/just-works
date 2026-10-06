# Product Analyst

Product Analyst is a Claude Code plugin for bounded, evidence-backed product investigations. It combines a read-only PostgreSQL gateway with read-only PostHog and Amazon QuickSight research. It creates no dashboards, insights, cohorts, analyses, exports, or other persistent analytics artefacts.

Use `/product-analyst:investigate` for a metric question or a suspected product change. The skill resolves an analytical contract before it queries, records evidence for each source call, sends material claims for independent verification, then checks reconciled claim citations.

## Install and configure

Register this plugin from the repository marketplace, then add `.analyst/config.toml` and `.analyst/metrics.toml` to the analysed project from the files in `setup/`. Replace all example values. The plugin requires Claude Code 2.1.281 or later, Python 3.11 or later on `PATH` for hooks, and `uv` for its MCP server. Its MCP server uses `${CLAUDE_PROJECT_DIR}` to scope configuration and investigation records to the analysed project. QuickSight use needs the AWS CLI. Docker is optional and used only for the PostgreSQL integration test. The gateway adds its local `.analyst/investigations/` ignore rule when it starts an investigation.

The plugin's hooks act only in a project that has `.analyst/config.toml`. In any other project they give no opinion, so enabling the plugin does not change how PostHog or the AWS CLI behave there.

For PostHog, configure a connector named `posthog` in the analysed project's `.mcp.json`; `skills/investigate/references/posthog.md` shows a read-only entry for PostHog's hosted server. The plugin does not change connector settings. Names containing `posthog` may also be classified by the hook, but use the required name instead of relying on alias matching. The skill supports the documented CLI discovery and `call` wrapper forms. A connector configured with `mode=tools` and a server-side `tools=` allowlist may expose only the exact direct read-tool list in `skills/investigate/references/posthog.md`; discovery remains available through the CLI wrapper.

The PostgreSQL MCP server takes a libpq service name. Put connection details in `~/.pg_service.conf` and credentials in `~/.pgpass`, not in the project or plugin configuration. A service name is a standard libpq indirection; see the [PostgreSQL documentation](https://www.postgresql.org/docs/current/libpq-pgservice.html).

Attach a database role that can only select approved schemas, a PostHog key scoped to the necessary read APIs, and the supplied QuickSight read-only IAM policy. Those credentials enforce access. The plugin's guards reduce accidental misuse but are not the primary security boundary.

## Investigation records

An investigation writes local evidence under `.analyst/investigations/<id>/`:

- `contract.json`: resolved metric, population, time window, timezone, and comparison;
- `sources.json`: fingerprints of the configuration and metric catalogue used by this investigation;
- `evidence.jsonl`: evidence records from gateway and allowed source calls;
- `findings.json`: claims, citations, uncertainty, and stop reason;
- `report.md`: the reader-facing result.

Keep these records local unless your team's evidence-retention policy says otherwise. Changes to `.analyst/config.toml` or `.analyst/metrics.toml` require a new investigation; the gateway rejects queries and final claim checks when their recorded fingerprints drift. It does not read or fingerprint libpq service and password files.

Keep the PostgreSQL service target and PostHog project connection stable during an investigation. Start a new investigation if either source connection changes because those external identities are outside the local source fingerprints.

## Limits

The gateway restricts database SQL to a narrow read-query subset and runs it as a single prepared statement in a read-only transaction, so PostgreSQL itself refuses a second statement. A refused query returns the reason to the caller; connection failures stay generic because their messages can name hosts and users. It does not make aggregate data non-sensitive. Database grants must enforce approved schemas, row-level security, and any small-cell or privacy policy.

The PostHog hook applies its read allowlist to recognised PostHog connector calls. The QuickSight hook permits literal, direct AWS CLI read commands only, and denies any other command that names both `aws` and `quicksight`. Permitted calls get no opinion from the hooks, so your own permission rules still decide whether they run. Shell aliases, constructed commands, encoded commands, unrelated connector aliases, disabled hooks, and outer hook launch failures or timeouts can bypass those classifiers. The pre-tool supervisor converts malformed input and child guard errors into a denial before its own deadline. Use least-privilege database grants, PostHog key scopes, and a QuickSight IAM principal restricted to the supplied read-only policy as the security boundary; hooks are a second layer.

## Verify the plugin

Run these commands from the repository root:

```sh
python3 -m unittest discover -s plugins/product-analyst/tests -p 'test_*.py'
python3 plugins/product-analyst/scripts/check_posthog_tools.py
ANALYST_TEST_MCP=1 python3 -m unittest discover -s plugins/product-analyst/tests -p 'test_mcp_runtime.py'
bash plugins/product-analyst/tests/run_postgres_integration.sh
```

The runtime smoke test uses the locked `uv` MCP environment without a database. The integration script starts a temporary PostgreSQL 16 Docker container and removes it when the script exits.

## References

- [Claude Code MCP configuration](https://docs.anthropic.com/en/docs/claude-code/mcp)
- [PostgreSQL read-only transactions](https://www.postgresql.org/docs/current/sql-set-transaction.html)
- [Amazon QuickSight API operations](https://docs.aws.amazon.com/quicksight/latest/developerguide/analysis-operations.html)

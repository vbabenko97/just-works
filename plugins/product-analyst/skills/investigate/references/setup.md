# Setup and scope

The analysed project supplies `.analyst/config.toml` and `.analyst/metrics.toml`. Copy the examples from this plugin, then replace every value marked `example` before an investigation. The files define analytical defaults; they do not grant access.

`.analyst/config.toml` also switches the plugin's hooks on for that project. In a project without it, the hooks give no opinion on any tool call, so PostHog and AWS CLI use there is governed only by your normal permission settings.

This plugin requires Claude Code 2.1.281 or later, Python 3.11 or later on `PATH` for hooks, and `uv` for the MCP gateway. Its MCP configuration expands `${CLAUDE_PROJECT_DIR}` into `ANALYST_PROJECT_DIR`, so the gateway reads configuration and writes investigation records in the analysed project rather than the plugin directory. Amazon QuickSight use also needs the AWS CLI. Docker is optional and used only for the PostgreSQL integration test.

`config.toml` has these sections:

- `[analysis]`: timezone and internal-user exclusion;
- `[postgres]`: libpq service name, permitted schemas, query timeouts, row cap, and an optional plan-cost ceiling;
- `[postgres.iam]`: optional RDS IAM authentication settings;
- `[budgets]`: PostgreSQL-query and PostHog-call limits per investigation. Both limits cover primary and independent verifier calls;
- `[posthog]`: an optional extra read-tool allowlist.

PostgreSQL credentials stay outside the repository. A libpq service name resolves connection parameters from a connection service file, normally `~/.pg_service.conf`; credentials can remain in `~/.pgpass`. See the [PostgreSQL connection service documentation](https://www.postgresql.org/docs/current/libpq-pgservice.html).

Run this command from the repository root in a trusted administrative session. `login_role` must name an existing dedicated restricted `LOGIN` or IAM-authenticated role. `owner_role` must name the role that creates the tables and therefore owns the default privileges. For example:

```sh
psql -d app -v db_name=app -v schema_name=analytics -v role_name=analytics_agent_readonly -v login_role=analytics_agent_login -v owner_role=app_migrator -f plugins/product-analyst/setup/readonly_role.sql
```

The gateway rejects a database role that is a superuser, has `BYPASSRLS`, owns tables, or has write privileges. The role, PostHog key scopes, and the QuickSight IAM policy are the security boundary. Hooks and query validation add another layer; they do not replace least privilege.

Investigation files belong under `.analyst/investigations/<id>/` and are local evidence, not source-controlled project content: `contract.json`, `sources.json`, `evidence.jsonl`, `findings.json`, and `report.md`. `sources.json` fingerprints the project configuration and metric catalogue at investigation start. A change to either file requires a new investigation; service and password files are neither read nor fingerprinted.

Keep the external sources stable for an investigation. The PostgreSQL service must continue to identify the same database and approved schema set, and the PostHog connector must continue to identify the same PostHog project. Start a new investigation if either connection changes; these external identities are outside the local source fingerprints.

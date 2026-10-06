# PostHog

Treat the PostHog metric catalogue as authoritative for PostHog-defined metrics. Call `metric-list` first, read a candidate's stored definition with `metric-describe`, and run an approved, non-drifted exact match with `data-catalog-metric-run`. Call `project-get` before relying on the project's timezone or test-account filter. Read the data schema before composing a query. Use aggregate query tools for counts, trends, funnels, retention, and breakdowns.

The fixed direct-read allowlist has these exact tools:

- project and documentation: `project-get`, `docs-search`, `generate-app-url`;
- metric catalogue: `metric-list`, `metric-describe`, `data-catalog-metric-run`;
- schema and SQL: `read-data-schema`, `execute-sql`;
- aggregate queries: `query-trends`, `query-funnel`, `query-retention`, `query-paths`, `query-stickiness`, `query-lifecycle`;
- saved analysis: `insight-get`, `insight-query`, `insights-list`, `dashboard-get`, `dashboards-get-all`, `notebooks-get`, `notebooks-list`;
- events and context: `actions-get-all`, `action-get`, `annotation-retrieve`, `annotations-list`, `cohorts-list`, `cohorts-retrieve`;
- experiments and flags: `experiment-get`, `experiment-list`, `experiment-results-get`, `experiment-stats`, `experiment-timeseries-results`, `feature-flag-get-all`, `feature-flag-get-definition`, `feature-flag-get-definition-by-key`.

The discovery forms are `learn`, `search`, and `tools`, plus `info <subject>` and `schema <subject>`. `[posthog].extra_read_tools` may add an exact tool only when the checked inventory marks it read-only and its name contains no mutation, person, or execution word.

Do not use a tool outside that allowlist. In particular, do not use person-level or actor tools, `notebooks-run`, `agent-feedback`, confirmation options, or create/update/delete operations. Do not infer that a tool is safe from its name.

Configure the connector in the analysed project's `.mcp.json` under the name `posthog`. PostHog's hosted server accepts a read-only flag:

```json
{
  "mcpServers": {
    "posthog": {
      "type": "http",
      "url": "https://mcp.posthog.com/mcp?readonly=true"
    }
  }
}
```

The hook also classifies other connector names containing `posthog`, such as `posthog-prod` or the claude.ai PostHog connector, but arbitrary aliases are not recognised. The CLI wrapper accepts exactly one plain command: `call <tool_name> <json_input>`, or one discovery form above. It does not allow shell syntax. A connector configured with `mode=tools` and a server-side `tools=` allowlist may instead expose the exact direct tools above. Hooks record the command, a hash, and a bounded result excerpt after each permitted call in a project that has `.analyst/config.toml`. Never edit the ledger, copy secrets into it, or treat an unrecorded source result as evidence. The PostHog key's server-side scopes remain the enforcement boundary.

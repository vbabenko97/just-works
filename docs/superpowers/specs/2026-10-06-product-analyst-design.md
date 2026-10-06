# Product Analyst design

Product Analyst is a Claude Code plugin for read-only product investigations. It answers a bounded question with a recorded analytical contract, evidence ledger, independent claim verification, and deterministic claim checks. Version one never creates or changes PostHog or QuickSight artefacts.

## User flow

`/product-analyst:investigate` resolves a contract before it queries. The contract contains a metric and version, population, current window, timezone, and comparison. The Postgres MCP gateway records that contract and returns an investigation ID. Calls may use a session-scoped active pointer, but an explicit investigation ID scopes every durable operation.

When a PostHog metric version is unknown, the workflow starts a bounded metadata preflight because, in a project with `.analyst/config.toml`, the hook requires an active investigation for every PostHog read. That preflight uses `unresolved (discovery only)` as the version and explicit assumptions only for catalogue, schema, and `learn` discovery. The workflow then starts a resolved investigation before analytical queries and repeats the material metric-definition lookup as evidence. It does not restart an investigation to evade a budget, policy refusal, or evidence requirement.

The investigator establishes a baseline, checks data quality and the numerator and denominator, tests competing explanations, and records each result as evidence. It stops as `SUPPORTED`, `REFUTED`, `INCONCLUSIVE`, `BUDGET_EXHAUSTED`, or `POLICY_BLOCKED`. A report contains the answer, contract, evidence IDs, four dimensions of uncertainty, and the stop reason.

The investigator prepares candidate findings, then the verifier reads the completed investigation and returns a separate verdict for each material claim: `supported`, `refuted`, or `unverified`. It uses independent query shapes or PostHog reads where the available sources allow it. The investigator reconciles those verdicts before it calls `check_claims` for final structural validation. A verifier result does not replace the original finding. Verifier calls count against the investigation's PostgreSQL-query and PostHog-call budgets.

## Plugin layout

```text
plugins/product-analyst/
  agents/analysis-verifier.md
  hooks/                    policy and evidence-recording hooks
  server/                   PostgreSQL MCP gateway
  setup/                    project and IAM templates
  skills/investigate/       investigation workflow and references
```

An analysed project holds configuration in `.analyst/config.toml` and metric definitions in `.analyst/metrics.toml`. Local investigation records live under `.analyst/investigations/<id>/` and should be ignored by Git. The plugin requires Claude Code 2.1.281 or later: its MCP configuration expands `${CLAUDE_PROJECT_DIR}` into `ANALYST_PROJECT_DIR`, keeping records and configuration scoped to that project.

## PostgreSQL gateway

The gateway exposes `start_investigation`, `execute_read_query`, `describe_schema`, `get_metric_definition`, `check_claims`, and `get_investigation`. `start_investigation` requires `contract` and `session_id`; all query calls take an explicit investigation ID.

The gateway obtains connection details through a libpq service name. The service file normally lives at `~/.pg_service.conf`, so the repository does not carry a database connection string. [PostgreSQL documents service names and the service file format.](https://www.postgresql.org/docs/current/libpq-pgservice.html)

Each query receives a new connection. The gateway accepts one read query beginning with `SELECT`, `WITH`, `VALUES`, or `TABLE`; explains it before execution; enforces configured plan-cost, statement-timeout, lock-timeout, and row-cap limits; and runs the query in a read-only transaction. PostgreSQL read-only transactions reject common data and schema changes, but database privileges remain the final enforcement boundary. [PostgreSQL documents the transaction rules.](https://www.postgresql.org/docs/current/sql-set-transaction.html)

The lexical guard refuses prefixed string literals such as `E'...'`, whose escape rules differ from plain literals, and the transaction sets `standard_conforming_strings` so plain literals follow the rules the guard assumes. Both the `EXPLAIN` and the query run as server-side prepared statements, which PostgreSQL refuses to create from more than one command, so a second statement fails even if the guard misses it. The guard limits keyword checks to words that can change data inside a read statement, and to reserved words that cannot be column names. It allows grouped conditions, column-name lists, type modifiers, and a list of common analytical functions.

A refused or failed query returns its reason to the caller: the guard rule, a gateway limit, or PostgreSQL's own message, hint, and SQLSTATE. The investigator needs that reason to repair its SQL. Connection failures stay generic because their messages can name hosts and users.

The gateway rejects unsafe effective roles: superusers, roles with `BYPASSRLS`, table owners, and roles with write privileges. It supports optional RDS IAM database authentication by obtaining a fresh token per connection.

## Source policies

The hooks act only in a project that has `.analyst/config.toml`. Elsewhere they give no opinion, so enabling the plugin does not change PostHog or AWS CLI behaviour in unrelated projects. Hook matchers cover only Bash and PostHog connector tools. A permitted call also gets no opinion rather than an approval, so the user's own permission rules still decide whether it runs.

PostHog permits discovery through `learn`, `search`, `tools`, and qualified `info` and `schema` calls. Its exact direct-read allowlist, listed in `skills/investigate/references/posthog.md`, covers project and documentation reads, the metric catalogue including `metric-describe` and `data-catalog-metric-run`, schema discovery and SQL, six aggregate query tools, saved insights, dashboards and notebooks, actions, annotations and cohorts, and experiment and feature-flag reads. Every entry was present in the live PostHog server's tool list on 2026-10-06 and is marked read-only in the checked inventory. Exact entries are not subject to the word heuristic, because `data-catalog-metric-run` only reads a metric. The CLI wrapper permits one plain `call <tool_name> <json_input>` command and rejects shell syntax. Person and actor tools, notebook execution, feedback, confirmation flags, and all mutation tools are denied for recognised calls. The project may add an exact tool in `[posthog].extra_read_tools` only when the checked PostHog inventory marks it read-only and its name contains no mutation, person, or execution word. The connector must be named `posthog`; names containing `posthog` are also recognised, but arbitrary aliases are not. A connector configured with `mode=tools` and a server-side `tools=` allowlist may expose only the direct list; discovery remains available through the CLI wrapper. The plugin does not modify a project's `.mcp.json`. A PostHog key scoped to required read APIs is the enforcement boundary. A hook records a request, result hash, and bounded result excerpt in the ledger after an allowed PostHog call.

QuickSight analysis uses literal direct `aws [global options] quicksight` operations whose names begin with `describe-`, `list-`, or `search-`. A Bash command that names both `aws` and `quicksight` in any other form is denied; commands that only mention QuickSight, such as reading a policy file, get no opinion. The hook lexically recognises those forms but cannot enforce every Bash execution: constructed, aliased, or encoded commands can evade classification. The supplied IAM policy must restrict the principal to `quicksight:Describe*`, `quicksight:List*`, and `quicksight:Search*`; AWS documents those operations in its [service authorization reference](https://docs.aws.amazon.com/service-authorization/latest/reference/list_quicksight.html).

The pre-tool supervisor returns a denial for malformed input, a child-policy crash, invalid policy output, or a child timeout, before its own shorter deadline. Its denial reason is visible to the model, so it contains only a policy explanation and an evidence ID, never credentials or query results. Disabled hooks and outer hook launch failures or timeouts can leave a call unclassified. Credentials and source permissions are the real access boundary: database grants, PostHog key scopes, and QuickSight IAM policy. The hooks provide defence in depth.

## Evidence and validation

Evidence records have stable IDs and include source, request metadata, time, result hash, and a bounded safe excerpt. `sources.json` records hashes of the project configuration and metric catalogue used at investigation start. Queries and `check_claims` reject drift in either file, requiring a new investigation; connection-service and password files are neither read nor hashed. The PostgreSQL service target and PostHog project connection must remain stable during an investigation because those external identities are outside the local source fingerprints. `check_claims` verifies that every claim cites completed successful evidence for the unchanged contract and sources, has a unique nonempty ID and text, and carries all four nonempty uncertainty fields. Findings also require all four global uncertainty fields and a valid stop reason. The structural check does not prove numerical or causal correctness.

The investigation skill invokes the `human-writing` skill before writing any text a person will read: the report, claims, titles, descriptions, and proposed analytics or dashboard wording. The plugin does not carry a copy, so the guidance cannot drift from the skill. When the skill is unavailable, the report says so and follows the reporting reference alone, which adds the investigation report structure.

## Out of scope for version one

Version one does not publish PostHog or QuickSight artefacts, provide a web user interface, schedule investigations, implement a Codex workflow, apply small-cell suppression, or live-test QuickSight in a customer account.

## Acceptance checks

- Unit tests cover SQL validation, PostHog and QuickSight classification, ledger operations, and `check_claims`.
- PostgreSQL 16 integration tests reject mutation and parser-bypass attempts, unsafe roles, over-cost plans, timeouts, and row-cap violations.
- Hook tests deny malformed payloads and hook failures.
- `claude plugin validate` accepts the plugin manifest.
- A manually configured environment can complete one bounded, read-only investigation without creating an external artefact.

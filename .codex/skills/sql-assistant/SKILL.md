---
name: sql-assistant
description: Use when writing, reviewing, debugging, optimizing, or converting SQL for PostgreSQL, MySQL, MariaDB, SQL Server (T-SQL), Oracle, SQLite, BigQuery, Snowflake, or DuckDB, including SQL embedded in application code, raw ORM queries, migrations, stored procedures, and dbt models. Also use for query plans and EXPLAIN output, slow queries and index choices, upserts, pagination, time-zone and date-range boundaries, NULL and duplicate-row bugs, and SQL injection or parameter binding. Not for NoSQL query languages, DataFrame code without SQL, or database administration that involves no SQL.
---

# SQL assistant

Write, review, optimize, and convert SQL so that it returns the intended result on the target engine, binds data safely, and changes nothing without authorization. Engine-independent rules live in three shared references. Each engine has an overlay that lists only what differs on that engine.

Generating SQL never grants permission to execute it. Permission comes from the user, the task, and the tool or environment policy; this skill neither widens nor narrows it. Before running any statement, plan command, or native check against a database, apply [references/safety-and-execution.md](references/safety-and-execution.md).

## Workflow

1. Establish the context the task needs.
2. Review the semantics with [references/universal-correctness.md](references/universal-correctness.md).
3. Load the overlay for the target engine.
4. Validate in proportion to the risk.
5. Report the SQL or the findings with verification evidence.

For optimization tasks, follow [references/performance-workflow.md](references/performance-workflow.md) from step 2 onward.

## 1. Context

| Fact | Needed for | Where to find it |
|---|---|---|
| Engine; for "MySQL-compatible", whether it is MySQL or MariaDB | Every task | Request, connection strings, container images, driver packages, migration tooling |
| Release and relevant configuration | Rules an overlay marks as version- or configuration-dependent | Request, infrastructure files, `SELECT version()` or equivalent when a read-only connection is authorized |
| Schema: tables, columns, types, nullability, keys, uniqueness, relationships | Any SQL that names objects | DDL, migrations, ORM models, schema dumps, read-only introspection when authorized |
| Result grain: what one output row represents | Joins, aggregates, deduplication | Request; ask when ambiguous |
| Write intent: read only, data change, or schema change | Every task | Request |
| Driver, ORM, or API that sends the SQL | Application code with parameters | Code, dependency manifests |
| Workload evidence: plans, row counts, timings, bytes, frequency | Optimization | User, monitoring, authorized plan commands |

Search the repository for schema evidence before asking, and cite the file you used.

Do not infer these facts from names, conventions, or other engines:

- that a table, column, index, constraint, or relationship exists, or its type and nullability;
- that a column is unique or that a join is one-to-one;
- the time zone in which timestamps are stored, or the time zone the report should use;
- the engine, its release, or its configuration;
- the placeholder syntax of the driver.

When a missing fact would change the SQL or its result, ask for it and say why it matters. Ask only for those facts and proceed on the rest with stated assumptions. When the user wants SQL before the facts are available, you may give illustrative SQL: label it as illustrative, list every assumed table, column, and relationship, and do not write it into files as final code. Never present an assumed object as part of the user's schema.

## 2. Semantics

Check every query against [references/universal-correctness.md](references/universal-correctness.md). At minimum:

- the result grain and the cardinality of every join, without `DISTINCT` hiding duplicates whose source is unexplained;
- `NULL` behavior in predicates, `NOT IN`, outer joins, and aggregates over empty input;
- types, collations, and implicit casts in comparisons and joins;
- time ranges as half-open intervals `[start, end)`, and calendar grouping such as daily or monthly buckets, in a stated time zone with the actual timestamp type established;
- a total, deterministic `ORDER BY` wherever order matters, including pagination, top-N, and latest-row-per-group queries;
- values bound through the driver's parameter API, and identifiers chosen from an allowlist;
- upsert and `MERGE` behavior with duplicate input and concurrent writers.

## 3. Dialect overlay

| Engine | Overlay |
|---|---|
| PostgreSQL | [references/postgres.md](references/postgres.md) |
| MySQL | [references/mysql.md](references/mysql.md) |
| MariaDB | [references/mariadb.md](references/mariadb.md) |
| SQL Server and Azure SQL | [references/sqlserver.md](references/sqlserver.md) |
| Oracle | [references/oracle.md](references/oracle.md) |
| SQLite | [references/sqlite.md](references/sqlite.md) |
| BigQuery | [references/bigquery.md](references/bigquery.md) |
| Snowflake | [references/snowflake.md](references/snowflake.md) |
| DuckDB | [references/duckdb.md](references/duckdb.md) |

Load the overlay only after the engine is known. For a conversion, load the source and the target overlays. MySQL and MariaDB are separate engines: resolve ambiguous descriptions such as "MySQL-compatible" before relying on JSON, plan-command, or version-specific rules. Accept an explicitly established engine without asking again, and never apply one overlay to the other. When the engine is unknown and the SQL depends on it, ask. For an engine outside this list, apply the shared references and state that no overlay covers it.

## 4. Validation

| Situation | Checks |
|---|---|
| Explaining or sketching SQL in conversation | Semantic review |
| SQL written into the repository or delivered as final | Semantic review, then SQLFluff parse and lint with the engine's dialect |
| Conversion between engines | The above; optionally use SQLGlot with explicit source and target dialects when both are supported, then review against both overlays |
| Data changes, migrations, DDL | The above, plus lock, transaction, and rollback review; engine-native non-executing checks only when authorized |
| Performance work | [references/performance-workflow.md](references/performance-workflow.md) |

Commands, dialect names, and templater settings are in [references/validation-tools.md](references/validation-tools.md). Do not install tools on your own initiative. When a tool is unavailable, report the check as skipped and give the command the user can run. A clean parse or lint does not show that the SQL is correct, that the referenced objects exist, or that it will run. Formatting and autofix commands rewrite files, so run them only when the task authorizes editing those files.

## 5. Report

For SQL you write:

1. The SQL in a fenced block for the target engine, with placeholders in the driver's syntax when known; otherwise label placeholders as illustrative and driver-dependent.
2. Assumptions and facts still needed, if any.
3. Semantic notes that affect the result: grain, `NULL` handling, ties, and time boundaries.
4. Verification: checks run with their results, checks skipped with the reason, and checks the user should run.

For reviews, list findings by severity. Each finding gives the location, the input that triggers it, the wrong result, and the fix.

For optimization, give the evidence observed, the hypotheses, each proposed change with the argument that it preserves results, how to measure it, and its costs. Give no speedup figure without before-and-after measurements.

Write explanations in the user's language. Keep SQL keywords and identifiers as they are.

Package provenance is in [SOURCES.md](SOURCES.md). Behavioral evaluation cases and their protocol are in [evals/evals.json](evals/evals.json); case definitions are expected behavior, not evidence that tests passed.

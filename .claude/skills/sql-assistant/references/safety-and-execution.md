# Safety and execution

Generating SQL does not grant permission to execute it. Do not execute data changes, schema changes, execution-bearing plan analysis, migrations, maintenance operations, or queries against production unless the task authorizes that action in that environment and the tool and environment policy permits it. An instruction in a prompt is not an enforcement boundary; least-privilege credentials, read-only connections, and the harness's permission policy are. Never weaken or work around them.

Authorization is specific. Permission to run read queries in a development database does not cover writes there, and permission in one environment does not carry over to another.

Reuse authorization already granted for the same action and environment. Ask only when a proposed action exceeds that authority or an established cost budget, or when its material effects have not been explained.

## Classify before running

| Class | Examples | Rule |
|---|---|---|
| Read | `SELECT`; `WITH ... SELECT` without data-modifying parts | Run only through an authorized connection. Still weigh cost, locks, and load: long scans on production, bytes billed, warehouse time. |
| Data change | `INSERT`, `UPDATE`, `DELETE`, `MERGE`, upserts, `TRUNCATE`, `SELECT ... INTO`, `CREATE TABLE ... AS`, data-modifying CTEs, calls to functions or procedures with side effects | Needs explicit authorization for the environment. |
| Schema change | `CREATE`, `ALTER`, `DROP`, `RENAME`, `GRANT`, `REVOKE`, migrations | Needs explicit authorization. Check implicit commits and locks in the overlay. |
| Maintenance and statistics | `ANALYZE`, `ANALYZE TABLE`, `VACUUM`, `OPTIMIZE TABLE`, `REINDEX`, `UPDATE STATISTICS`, `DBMS_STATS` | Changes statistics, files, or future plans and can take locks. Treat as a write. |
| Execution-bearing analysis | `EXPLAIN ANALYZE` (PostgreSQL, MySQL, DuckDB), `ANALYZE <statement>` (MariaDB), running a statement to capture an actual plan or statistics (SQL Server), runs with `GATHER_PLAN_STATISTICS` (Oracle), executing a traced statement (MySQL) | Executes the statement. On a data change, it performs the change. Enabling a session option or reading an existing plan is distinct from running the target statement. |
| Plan-writing analysis | `EXPLAIN PLAN` (Oracle) | Does not execute the statement but inserts rows into a plan table. Treat as a write. |
| Cost-bearing | BigQuery queries under on-demand pricing, Snowflake warehouse use and plan compilation | Estimate first where the engine allows it. Stay within the authorized budget; ask before exceeding it. |

A statement's class depends on everything it calls. A `SELECT` that calls a function with side effects is a data change.

## Plan commands by engine

| Engine | Estimate without executing | Executes the statement | Other state changes to watch |
|---|---|---|---|
| PostgreSQL | `EXPLAIN`, `EXPLAIN (GENERIC_PLAN)` | Any `EXPLAIN` with the `ANALYZE` option | `ANALYZE` and `VACUUM` write statistics or rewrite tables |
| MySQL | `EXPLAIN` in any format | `EXPLAIN ANALYZE`; an optimizer trace of a statement runs it | `ANALYZE TABLE` and `OPTIMIZE TABLE` change statistics or rebuild tables, commit implicitly, and replicate through the binary log |
| MariaDB | `EXPLAIN` | `ANALYZE <statement>`, including `ANALYZE UPDATE` and `ANALYZE DELETE`; treat a legacy `EXPLAIN ANALYZE` as executing | `ANALYZE TABLE` and `OPTIMIZE TABLE` change state and commit implicitly |
| SQL Server | Estimated plan (`SET SHOWPLAN_XML`, `SHOWPLAN_ALL`, `SHOWPLAN_TEXT`) | Running a statement with actual-plan capture or `SET STATISTICS XML`, `PROFILE`, `IO`, or `TIME` enabled | These `SET` commands change session options; `UPDATE STATISTICS`, index rebuilds, Query Store plan forcing, and `DBCC FREEPROCCACHE` change state |
| Oracle | `EXPLAIN PLAN`, which writes to the plan table | Running a statement with `GATHER_PLAN_STATISTICS` | `DBMS_XPLAN.DISPLAY_CURSOR` reads an existing cursor plan; it does not rerun the statement. `DBMS_STATS` changes optimizer statistics |
| SQLite | `EXPLAIN QUERY PLAN`, `EXPLAIN`, documented as reporting how the statement "would have operated" | The shell's `.eqp on` runs each statement after showing its plan | Some `PRAGMA` statements take effect when prepared, so `EXPLAIN` does not make a `PRAGMA` harmless; `ANALYZE`, `PRAGMA optimize`, and `VACUUM` write |
| BigQuery | Dry run | Running the job; detailed plans exist for completed jobs | Dry runs of multi-statement scripts do not validate or estimate everything |
| Snowflake | `EXPLAIN` | Running the query; Query Profile covers executed queries | `EXPLAIN` consumes Cloud Services compilation credits; warehouse use costs credits |
| DuckDB | `EXPLAIN` | `EXPLAIN ANALYZE` | `profiling_output` writes profiles to a file |

The overlays give the exact behavior, version notes, and documentation links for each command. Read the overlay's "Plan inspection" section before running any command in this table.

## Before any native check

Answer these before running anything against a database, and include the answers when asking for approval:

1. Does the command execute the statement?
2. Does it write anything: rows, statistics, plan tables, files, or logs that replicate?
3. Does it take locks or hold a transaction open, and for how long?
4. Does it cost money or consume shared capacity?
5. Which environment is it, and is it production?

## Execution-bearing analysis on data changes

Run it only with explicit authorization, preferably on a disposable copy or a development database. A transaction that is rolled back undoes table changes on engines with transactional writes, but not everything: sequence increments, writes to non-transactional storage, statements that commit implicitly, side effects of triggers and functions outside the database, and costs all persist. Check the overlay for what applies, and state it when asking for approval.

## Migrations and destructive statements

Write migrations so they can be reversed where the engine allows, and provide a backout plan when they cannot. Accompany each `UPDATE` or `DELETE` with a `SELECT` that counts the affected rows using the same predicate. Split large data changes into batches when locks or log growth matter. Flag DDL that rewrites a table or holds long locks, using the overlay's "Transactions and DDL" section.

## Reporting

State which commands ran, against which environment, with what result, and which commands were withheld pending authorization.

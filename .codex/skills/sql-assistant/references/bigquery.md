# BigQuery

This overlay covers BigQuery GoogleSQL. Its documentation is continuously updated rather than release-pinned; checked against the official documentation on 2026-10-13. Load it after the shared references.

## Version and configuration

Confirm that the job uses GoogleSQL, not legacy SQL. They are distinct dialects; set `useLegacySql` to `false` where the caller exposes that option. Do not infer a project, location, reservation, default dataset, or billing model from SQL text. They can change availability, names resolved by unqualified references, queueing, and cost ([Introduction to SQL](https://cloud.google.com/bigquery/docs/introduction-sql), [Run a query](https://cloud.google.com/bigquery/docs/running-queries)).

For a script, establish whether it needs a transaction, uses temporary objects, or calls procedures. A multi-statement query has shared state and can contain DDL and DML; each statement can still have separate permissions and a later failure does not make prior non-transactional changes disappear ([Work with multi-statement queries](https://cloud.google.com/bigquery/docs/multi-statement-queries)).

## Identifiers and quoting

Use backticks for quoted identifiers, including a fully qualified table path: `` `project.dataset.table` ``. Single and double quotes are string syntax, not identifier quotes. Unquoted names have narrower character rules, and a reserved keyword needs quoting when it is a standalone identifier ([Lexical structure](https://cloud.google.com/bigquery/docs/reference/standard-sql/lexical)).

Keywords, column names, field names, and query aliases are case-insensitive. Dataset and table names are case-sensitive unless the dataset has `is_case_insensitive = TRUE`; do not change the spelling of an existing path while converting SQL. User-defined function names are case-sensitive ([Lexical structure](https://cloud.google.com/bigquery/docs/reference/standard-sql/lexical)).

## Types and casts

Use explicit `CAST` or `SAFE_CAST` at input boundaries and comparisons where conversion can fail. `SAFE_CAST` returns `NULL` for a runtime conversion error, which can silently remove rows in a predicate; decide whether invalid input should be rejected, counted, or treated as missing ([Conversion functions](https://cloud.google.com/bigquery/docs/reference/standard-sql/conversion_functions)).

`INT64 / INT64` produces `FLOAT64`. Use `DIV` for integer division and `NUMERIC` or `BIGNUMERIC` when decimal precision matters; do not rely on an implicit conversion chosen for another engine ([Mathematical functions](https://cloud.google.com/bigquery/docs/reference/standard-sql/mathematical_functions), [Data types](https://cloud.google.com/bigquery/docs/reference/standard-sql/data-types)).

## Time zones and temporal types

`TIMESTAMP` is an absolute microsecond-precision instant, independent of a time zone. `DATE`, `TIME`, and `DATETIME` are civil values and carry no zone. A zone is required when converting between a civil value and an instant; use an IANA zone name where daylight-saving rules matter ([Data types](https://cloud.google.com/bigquery/docs/reference/standard-sql/data-types)).

Use a half-open instant range after deriving the local calendar boundaries. For example, convert two civil midnights with `TIMESTAMP(DATETIME '2026-10-25 00:00:00', 'Europe/Vienna')` and the following local midnight. Do not filter an event `TIMESTAMP` with a bare `DATE` if the report's zone is not explicitly UTC.

## Pagination

`LIMIT` does not give deterministic results without a total `ORDER BY`; include a unique tie-breaker. `OFFSET` is evaluated after ordering and can require work for skipped rows, so use keyset pagination for deep navigation ([Query syntax: LIMIT and OFFSET](https://cloud.google.com/bigquery/docs/reference/standard-sql/query-syntax#limit_and_offset_clause)).

State `NULLS FIRST` or `NULLS LAST` if null placement affects a cursor. BigQuery's default is `NULLS FIRST` for ascending order and `NULLS LAST` for descending order ([Query syntax: ORDER BY](https://cloud.google.com/bigquery/docs/reference/standard-sql/query-syntax#order_by_clause)).

## JSON

The native `JSON` type validates JSON and has different duplicate-key handling from a JSON-formatted `STRING`: when an object has duplicate keys, `JSON` preserves the first key found. Keep the distinction between SQL `NULL`, JSON `null`, and a missing key explicit; JSON functions can return SQL `NULL` for different cases depending on their input type and mode ([Data types](https://cloud.google.com/bigquery/docs/reference/standard-sql/data-types), [JSON functions](https://cloud.google.com/bigquery/docs/reference/standard-sql/json_functions)).

Use `JSON_VALUE` for a scalar SQL string and `JSON_QUERY` for a JSON value. Cast extracted text deliberately before numeric or temporal comparison; do not compare a JSON string to a number by accident.

## CTEs and window functions

A non-recursive CTE is a named subquery, not a materialization promise. BigQuery can evaluate a CTE each time it is referenced; use a temporary table or materialized intermediate only when measured workload evidence supports it ([Performance best practices: avoid multiple evaluations](https://cloud.google.com/bigquery/docs/best-practices-performance-compute#avoid_multiple_evaluations_of_the_same_ctes)).

`QUALIFY` filters window-function results after `WINDOW` and before `ORDER BY`. For latest-row-per-group, add a unique tie-breaker inside the window `ORDER BY`; `ROW_NUMBER` without an order, or with ties, is nondeterministic ([Query syntax: QUALIFY](https://cloud.google.com/bigquery/docs/reference/standard-sql/query-syntax#qualify_clause), [Numbering functions](https://cloud.google.com/bigquery/docs/reference/standard-sql/numbering_functions)).

## Upsert

`MERGE` matches source and target before applying its clauses. If multiple source rows match one target row and a matched `UPDATE` or `DELETE` would run, the statement raises a runtime error. Deduplicate or aggregate the source to one row per target key before `MERGE` ([DML syntax: MERGE](https://cloud.google.com/bigquery/docs/reference/standard-sql/dml-syntax#merge_statement)).

Do not infer primary-key enforcement or concurrency semantics from a declared key. Confirm table constraints and the write workload, then design idempotency and retries around the actual job behavior.

## Transactions and DDL

Use `BEGIN TRANSACTION` only when the related DML must commit or roll back together. Permanent-entity DDL is not allowed inside a multi-statement transaction. Without session mode or an exception handler, an error fails the query and rolls back its transaction. An exception handler can choose to commit or roll back; in session mode an unhandled error can leave the transaction active until explicit rollback or session termination. Handle failure and release resources deliberately. Conflicting transactions are cancelled; BigQuery can rerun conflicting standalone mutating DML, which is a different retry scope. A caller can submit a fresh, idempotent transaction after resolving the failure ([Multi-statement transactions](https://cloud.google.com/bigquery/docs/transactions), [DML conflicts](https://cloud.google.com/bigquery/docs/data-manipulation-language#dml_statement_conflicts)).

Outside a transaction, DDL and DML are execution-bearing operations. Treat scripts with `CREATE`, `DROP`, `ALTER`, or `EXECUTE IMMEDIATE` as writes even when the final statement is a `SELECT`.

## Plan inspection and performance

BigQuery has no user-managed B-tree indexes for ordinary analytical tables. Start with result-preserving reductions in bytes read: select required columns, filter partition columns with a qualifying predicate, and consider clustering only from workload evidence. Partition pruning skips partitions and reduces billed bytes; clustering can block-prune, but its final bytes read are not exactly known before execution ([Query partitioned tables](https://cloud.google.com/bigquery/docs/querying-partitioned-tables), [Clustered tables](https://cloud.google.com/bigquery/docs/clustered-tables)).

`LIMIT` on `SELECT *` does not reduce bytes read. Do not claim a speedup from a rewrite without comparable job evidence. Review the query plan and timeline from a completed job, where stage output, shuffle, slots, and contention are observable ([Optimize query computation](https://cloud.google.com/bigquery/docs/best-practices-performance-compute), [Query plan and timeline](https://cloud.google.com/bigquery/docs/query-plan-explanation)).

A dry run validates and estimates bytes without slots or query charges, but it is a best-effort preflight, not a runtime proof or exact cost. A federated query can report a zero-byte lower bound. In scripts, it validates only a `CALL` signature then stops; validates only the first DDL; does not support `CREATE TEMP TABLE`; skips dynamic SQL after validating only the `EXECUTE IMMEDIATE` expression; and stops at `FOR`, `IF`, and `WHILE`. Variable-dependent partition filters and time-travel expressions can also distort estimates ([Run a query](https://cloud.google.com/bigquery/docs/running-queries), [Work with multi-statement queries](https://cloud.google.com/bigquery/docs/multi-statement-queries)).

## Parameter binding

GoogleSQL accepts named `@name` or positional `?` query parameters, but a statement must not mix them. Bind values through the client library's parameter API. Parameters cannot replace table names, column names, or SQL syntax, and cannot appear in `CREATE FUNCTION`, `CREATE VIEW`, `CREATE MATERIALIZED VIEW`, or `CREATE PROCEDURE` bodies ([Lexical structure: query parameters](https://cloud.google.com/bigquery/docs/reference/standard-sql/lexical#query_parameters)).

For a dynamic identifier, choose it from an application-controlled allowlist, quote the complete path safely, and bind the data values passed to `EXECUTE IMMEDIATE ... USING`; never concatenate untrusted values into SQL ([Procedural language: EXECUTE IMMEDIATE](https://cloud.google.com/bigquery/docs/reference/standard-sql/procedural-language#execute_immediate)).

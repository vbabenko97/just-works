# Snowflake

This overlay covers Snowflake SQL. Its documentation is continuously updated rather than release-pinned; checked against the official documentation on 2026-10-13. Load it after the shared references.

## Version and configuration

Establish the account edition, cloud region, warehouse, current role, database, schema, and session parameters before relying on behavior. Those settings affect object resolution, privileges, query resources, case handling, time conversion, and `MERGE` failures. Use `CURRENT_*` functions or `SHOW PARAMETERS` only when the connection is authorized ([Session variables and parameters](https://docs.snowflake.com/en/sql-reference/session-variables), [Parameters](https://docs.snowflake.com/en/sql-reference/parameters)).

Confirm the table kind before offering key, constraint, or index advice. Standard tables do not enforce `PRIMARY KEY`, `UNIQUE`, or `FOREIGN KEY` constraints; `NOT NULL` and `CHECK` are enforced. Hybrid tables enforce these key constraints and require a primary key. Secondary indexes are a hybrid-table feature, not general standard-table tuning ([Constraints](https://docs.snowflake.com/en/sql-reference/constraints), [CREATE HYBRID TABLE](https://docs.snowflake.com/en/sql-reference/sql/create-hybrid-table)).

## Identifiers and quoting

Unquoted identifiers are stored and resolved in uppercase, so `orders`, `ORDERS`, and `Orders` refer to the same object. Double-quoted identifiers preserve case and resolve exactly, and therefore require their original quoting and spelling in later SQL ([Identifier requirements](https://docs.snowflake.com/en/sql-reference/identifiers-syntax)).

Check `QUOTED_IDENTIFIERS_IGNORE_CASE` before diagnosing a quoted-name failure. When it is true, alphabetic characters in newly created and resolved quoted identifiers are treated as uppercase; changing it can make existing mixed-case objects inaccessible by their old spelling ([Identifier requirements](https://docs.snowflake.com/en/sql-reference/identifiers-syntax)).

## Types and casts

`NUMBER` defaults to precision and scale `(38,0)`. `FLOAT` aliases an approximate type, while `DECIMAL` and `NUMERIC` alias `NUMBER`; choose deliberately for money and equality joins. Use `CAST`, `TRY_CAST`, or a named conversion function at input boundaries. `TRY_CAST` only accepts string expressions and returns `NULL` for conversion errors ([Data types](https://docs.snowflake.com/en/sql-reference/intro-summary-data-types), [TRY_CAST](https://docs.snowflake.com/en/sql-reference/functions/try_cast)).

`TIMESTAMP` is an alias controlled by `TIMESTAMP_TYPE_MAPPING`; do not use the alias when a column or literal must have a particular timestamp meaning ([Date and time types](https://docs.snowflake.com/en/sql-reference/data-types-datetime)).

## Time zones and temporal types

`TIMESTAMP_NTZ` stores a wall-clock time with no zone. `TIMESTAMP_LTZ` stores UTC and renders it in the session `TIMEZONE`; `TIMESTAMP_TZ` stores an offset with the value, but does not retain a named zone or automatically update that offset when daylight-saving rules later change. Set the intended `TIMEZONE` or convert with an explicit IANA name before binning or filtering ([Date and time types](https://docs.snowflake.com/en/sql-reference/data-types-datetime), [CONVERT_TIMEZONE](https://docs.snowflake.com/en/sql-reference/functions/convert_timezone)).

`TIMEZONE` is a session/account/user parameter and defaults to `America/Los_Angeles`; zone names are case-sensitive and Snowflake does not support most abbreviations because they are ambiguous. Use `Europe/Vienna`, not `CET` or `EST`, for a civil-date report ([Parameters: TIMEZONE](https://docs.snowflake.com/en/sql-reference/parameters#timezone)).

## Pagination

Use a total `ORDER BY` with a unique tie-breaker for `LIMIT`, `OFFSET`, `TOP`, and keyset pagination. Result order is not guaranteed without it. A deep `OFFSET` can still require the engine to produce skipped rows, so prefer a tested keyset predicate for deep navigation ([LIMIT / FETCH](https://docs.snowflake.com/en/sql-reference/constructs/limit)).

State null placement when it participates in a cursor: default null ordering is controlled by `DEFAULT_NULL_ORDERING`, so it is session-dependent ([ORDER BY](https://docs.snowflake.com/en/sql-reference/constructs/order-by)).

## JSON and semi-structured values

`VARIANT` can hold semi-structured values; use `PARSE_JSON` to store JSON text and path syntax such as `v:customer.id` to extract a value. Cast the extracted value before typed comparison. A JSON null stored in `VARIANT` is distinct from SQL `NULL`; `IS_NULL_VALUE` tests the former, while a missing path returns SQL `NULL` ([Semi-structured data types](https://docs.snowflake.com/en/sql-reference/data-types-semistructured), [IS_NULL_VALUE](https://docs.snowflake.com/en/sql-reference/functions/is_null_value)).

Avoid using a JSON path expression as proof that a key exists or has a particular scalar type. Use `TYPEOF`, `IS_*` predicates, and explicit casts when malformed or mixed data is possible ([Type predicates](https://docs.snowflake.com/en/sql-reference/functions/is)).

## CTEs and window functions

Do not assume a CTE is materialized or evaluated once. Let the optimizer choose unless an observed plan and a clear result-preserving reason require a persisted intermediate ([Working with CTEs](https://docs.snowflake.com/en/user-guide/queries-cte)).

`QUALIFY` filters after window functions and before `ORDER BY`. For one row per group, make the window `ORDER BY` complete: `row_number() over (partition by account_id order by created_at desc, id desc)`. `QUALIFY row_number() = 1` without a tie-breaker returns an arbitrary tied row ([QUALIFY](https://docs.snowflake.com/en/sql-reference/constructs/qualify)).

## Upsert

Deduplicate the source before `MERGE`. A merge is nondeterministic when one target row would be updated by multiple source rows or both updated and deleted. `ERROR_ON_NONDETERMINISTIC_MERGE` defaults to `TRUE`, which raises an error; if it is `FALSE`, Snowflake chooses an unspecified source row ([MERGE](https://docs.snowflake.com/en/sql-reference/sql/merge), [Parameters](https://docs.snowflake.com/en/sql-reference/parameters#error_on_nondeterministic_merge)).

Do not rely on a declared standard-table key to prevent duplicate source or target rows. For a hybrid table, the enforced key helps storage integrity but does not replace checking `MERGE` source cardinality.

If duplicate source rows have no target match, `WHEN NOT MATCHED THEN INSERT` inserts every copy; the nondeterministic matched-update setting does not deduplicate those inserts. Deduplicate incoming rows before matching, and audit existing standard-table targets independently ([MERGE: deterministic results for INSERT](https://docs.snowflake.com/en/sql-reference/sql/merge#deterministic-results-for-insert)).

## Transactions and DDL

Snowflake transactions are not nested. DDL statements implicitly commit the active transaction before they run and execute as their own transaction; an error does not undo the already committed preceding transaction. Keep data changes that must be atomic in explicit transaction-safe DML and keep DDL in a separately reviewed deployment step ([Transactions](https://docs.snowflake.com/en/sql-reference/transactions)).

Stored-procedure language and client behavior can set transaction scope. Confirm the caller and driver before assuming that an unqualified `BEGIN`/`COMMIT` owns all statements.

## Plan inspection and performance

`EXPLAIN` compiles a plan without executing the statement, but compilation consumes credits and its estimates use the current warehouse configuration. It is therefore a non-data-changing check, not a free check or a runtime measurement. The logical plan can differ from a prior or later execution ([EXPLAIN](https://docs.snowflake.com/en/sql-reference/sql/explain)).

Use Query Profile or Query History to investigate completed queries. They show historical execution, including elapsed time and operators, but do not predict an unexecuted query under another warehouse, cache state, data volume, or concurrency level ([Query Profile](https://docs.snowflake.com/en/user-guide/ui-query-profile), [Query History](https://docs.snowflake.com/en/user-guide/ui-history)).

For standard analytical tables, test pruning, projection, clustering, query shape, and warehouse sizing from measured evidence. Do not propose B-tree indexes. For hybrid tables, inspect its indexes and profile before adding one; indexable columns and supported operations are restricted, and indexes add write/storage cost ([Hybrid table limitations](https://docs.snowflake.com/en/user-guide/tables-hybrid-limitations), [Analyze hybrid query profiles](https://docs.snowflake.com/en/user-guide/tables-hybrid-read-query-profiles)).

For highly selective equality or other supported lookup predicates on standard tables, also evaluate Search Optimization. It requires Enterprise Edition or higher and maintains a persistent search access path with storage and maintenance compute costs. Compare Query Profile evidence, selectivity, and ongoing cost against clustering and the unchanged query before proposing that it be enabled; enabling it is a state-changing, cost-bearing action ([Search optimization service](https://docs.snowflake.com/en/user-guide/search-optimization-service)).

## Parameter binding

Bind values using the placeholder syntax and parameter API documented by the actual driver. Snowflake connector support varies: for example, some Python connector parameter styles are client-side while `qmark` and numeric forms use server-side binding. Do not copy placeholder syntax between drivers ([Python connector: binding](https://docs.snowflake.com/en/developer-guide/python-connector/python-connector-example#binding-parameters-to-variables)).

Bind ordinary data values; they cannot stand in for SQL keywords, sort directions, or arbitrary SQL fragments. Snowflake also supports a bound object identifier only through `IDENTIFIER(?)` or `IDENTIFIER(:variable)` in interfaces that support that bind syntax. Allowlist the object name before binding it, and bind every data value separately; do not interpolate SQL text ([IDENTIFIER() syntax](https://docs.snowflake.com/en/sql-reference/identifier-literal), [Snowflake Scripting: variables](https://docs.snowflake.com/en/developer-guide/snowflake-scripting/variables)).

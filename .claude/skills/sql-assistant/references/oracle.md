# Oracle

Baseline: Oracle AI Database SQL Language Reference, Release 26 (G57157-07, September 2026). It is a documentation baseline, not a claim about the server running a task. Checked against Oracle documentation on 2026-10-13. Older Oracle Database releases can differ materially, especially for JSON, pagination, and `QUALIFY`.

This overlay is loaded after the shared references and lists only Oracle-specific rules.

## Version and configuration

Establish the database release, `COMPATIBLE` value, session time zone, and relevant NLS settings before relying on the rules below. `COMPATIBLE` gates identifier length and the native `JSON` type; its value is a server configuration decision, not a SQL-mode setting ([Database Object Names and Qualifiers](https://docs.oracle.com/en/database/oracle/oracle-database/26/sqlrf/Database-Object-Names-and-Qualifiers.html), [JSON Data Type](https://docs.oracle.com/en/database/oracle/oracle-database/26/adjsn/json-data-type.html)).

- `NLS_DATE_FORMAT`, `NLS_TIMESTAMP_FORMAT`, `NLS_TIMESTAMP_TZ_FORMAT`, `NLS_DATE_LANGUAGE`, `NLS_NUMERIC_CHARACTERS`, and `NLS_CALENDAR` can change how character input and output are interpreted. Client settings can override an initialization value, so inspect the session rather than assuming a database default ([NLS_DATE_FORMAT](https://docs.oracle.com/en/database/oracle/oracle-database/26/refrn/NLS_DATE_FORMAT.html), [Format Models](https://docs.oracle.com/en/database/oracle/oracle-database/26/sqlrf/Format-Models.html)).
- `ALTER SESSION` changes connection-local behavior and does not implicitly commit. Set it only when the task authorizes changing the session, and restore or use a dedicated connection when pooling makes session state observable by later work ([Types of SQL Statements](https://docs.oracle.com/en/database/oracle/oracle-database/26/sqlrf/Types-of-SQL-Statements.html)).
- Check character set and collation when string comparison or ordering matters. Do not assume case-insensitive comparison from identifier rules.

## Identifiers and quoting

Unquoted identifiers are case-insensitive and are stored as uppercase. Quoted identifiers retain case and must be quoted exactly at every reference. Prefer ordinary unquoted names in new SQL; quoted names impose that permanent calling convention ([Database Object Names and Qualifiers](https://docs.oracle.com/en/database/oracle/oracle-database/26/sqlrf/Database-Object-Names-and-Qualifiers.html)).

With `COMPATIBLE` 12.2 or later, most identifiers can be 1 to 128 bytes; several object classes remain limited to 30 bytes. Do not generate a name at the limit without checking its object class and `COMPATIBLE` value (same source).

```sql
-- Example schema: orders(order_id, status).
SELECT order_id
FROM orders
WHERE status = :status;
```

Values use single quotes or binds. Never bind an identifier; choose a dynamic table, column, or sort key from a closed allowlist and quote it only when the confirmed schema requires quoting.

## Types and casts

`DATE` includes a time to the second. Use `TIMESTAMP` when fractional seconds matter, and use `TIMESTAMP WITH TIME ZONE` when an offset or region-aware instant must travel with the value ([Data Types](https://docs.oracle.com/en/database/oracle/oracle-database/26/sqlrf/Data-Types.html)).

Do not rely on implicit conversion between text, numbers, and dates: NLS settings can change its result or make it fail. Bind a value with the column's type, use ANSI date and timestamp literals where applicable, or use `TO_DATE`, `TO_TIMESTAMP`, and `TO_NUMBER` with an explicit format model and required NLS arguments ([Literals](https://docs.oracle.com/en/database/oracle/oracle-database/26/sqlrf/Literals.html), [SQL and PL/SQL Programming in a Global Environment](https://docs.oracle.com/en/database/oracle/oracle-database/26/nlspg/sql-and-plsql-programming-in-global-environment.html)).

Oracle currently treats a zero-length character string as `NULL`. Do not use `''` as a distinct empty value, and do not create logic that depends on this documented behavior remaining unchanged ([Nulls](https://docs.oracle.com/en/database/oracle/oracle-database/26/sqlrf/Nulls.html)).

## Time zones and temporal types

`TIMESTAMP WITH LOCAL TIME ZONE` is normalized to the database time zone and returned in the session time zone; it does not retain the original zone. `TIMESTAMP WITH TIME ZONE` represents an instant with zone information. Establish which type a column has before grouping or filtering it ([Data Types](https://docs.oracle.com/en/database/oracle/oracle-database/26/sqlrf/Data-Types.html)).

Use named regions, such as `Europe/Vienna`, when daylight-saving rules matter. `AT TIME ZONE` accepts a region, offset, `DBTIMEZONE`, or `SESSIONTIMEZONE`; `AT LOCAL` uses the current session zone. Region names depend on the installed Oracle time-zone file, so validate the deployed database rather than assuming a region exists ([Datetime Expressions](https://docs.oracle.com/en/database/oracle/oracle-database/26/sqlrf/Datetime-Expressions.html)).

```sql
-- Example column: events.created_at is TIMESTAMP WITH TIME ZONE.
-- The half-open boundaries describe 2026-10-25 in Europe/Vienna.
WHERE created_at >= FROM_TZ(TIMESTAMP '2026-10-25 00:00:00', 'Europe/Vienna')
  AND created_at <  FROM_TZ(TIMESTAMP '2026-10-26 00:00:00', 'Europe/Vienna')
```

Confirm how ambiguous local timestamps at a daylight-saving overlap are handled. `ERROR_ON_OVERLAP_TIME` is a session parameter relevant to that decision ([Data Types](https://docs.oracle.com/en/database/oracle/oracle-database/26/sqlrf/Data-Types.html)).

## Pagination

Use `OFFSET ... FETCH` with a total `ORDER BY`, including a unique tie-breaker. Oracle says row limiting needs an `ORDER BY` for consistent results. `OFFSET` accepts negative, null, and fractional values with non-obvious behavior, so validate or bind non-negative whole page sizes and offsets at the application boundary ([SELECT](https://docs.oracle.com/en/database/oracle/oracle-database/26/sqlrf/SELECT.html)).

`row_limiting_clause` cannot be combined with `FOR UPDATE`, cannot select `CURRVAL` or `NEXTVAL`, and requires unique aliases when selected column names repeat. For deep pages, use a verified keyset predicate when the sort columns are suitable; do not claim it is faster without a representative plan and measurements (same source).

## JSON

Oracle supports JSON stored as `VARCHAR2`, `CLOB`, or `BLOB`; use an `IS JSON` constraint when textual storage must reject malformed documents. The native binary `JSON` type, the `JSON` constructor, and `JSON_SCALAR` require `COMPATIBLE >= 20`; otherwise they raise an error ([JSON Data Type](https://docs.oracle.com/en/database/oracle/oracle-database/26/adjsn/json-data-type.html)).

Native `JSON` values cannot be directly compared with `=` or ordered or grouped. Extract a typed scalar with `JSON_VALUE` or dot notation plus an item method before comparison. Choose `NULL ON EMPTY` and `ON ERROR` explicitly when absent paths and malformed or mismatched values need different results ([JSON Data Type](https://docs.oracle.com/en/database/oracle/oracle-database/26/adjsn/json-data-type.html), [Empty-Field Clause](https://docs.oracle.com/en/database/oracle/oracle-database/26/adjsn/empty-field-clause-sql-json-query-functions.html)).

SQL `NULL` and JSON `null` are distinct for a non-null JSON value. Oracle SQL also cannot distinguish a character empty string from SQL `NULL`; preserve an intended JSON empty string explicitly when generating JSON ([Overview of JSON](https://docs.oracle.com/en/database/oracle/oracle-database/26/adjsn/overview-json-oracle-ai-database.html)).

## CTEs and window functions

A `WITH` query name can be referenced later in the same statement. Oracle may optimize it as an inline view or as a temporary table, so do not use a CTE as an execution-order or materialization guarantee ([SELECT](https://docs.oracle.com/en/database/oracle/oracle-database/26/sqlrf/SELECT.html)).

Analytic functions run after joins, `WHERE`, `GROUP BY`, and `HAVING`, and before the final `ORDER BY`. Filter an analytic result in an outer query unless the target release supports and the task deliberately uses `QUALIFY`. Include an explicit window frame whenever peer handling affects the result ([Analytic Functions](https://docs.oracle.com/en/database/oracle/oracle-database/26/sqlrf/Analytic-Functions.html)).

## Upsert with MERGE

Oracle `MERGE` is deterministic: one target row cannot be updated more than once in one statement. Deduplicate the source on the confirmed match key before a `MERGE`; otherwise the statement can fail rather than silently choose one source row ([MERGE](https://docs.oracle.com/en/database/oracle/oracle-database/26/sqlrf/MERGE.html)).

The `ON` condition defines matching, but it does not create a uniqueness guarantee. Back the intended key with an enforced unique or primary-key constraint, decide how duplicate source rows are rejected or selected, and handle uniqueness conflicts from concurrent writers in the application. Do not treat `MERGE` as a retry protocol.

```sql
-- Example schema: prices(sku primary key, amount).
-- The source must contain at most one row per sku.
MERGE INTO prices p
USING (SELECT :sku AS sku, :amount AS amount FROM dual) s
ON (p.sku = s.sku)
WHEN MATCHED THEN UPDATE SET p.amount = s.amount
WHEN NOT MATCHED THEN INSERT (sku, amount) VALUES (s.sku, s.amount);
```

## Transactions and DDL

DML does not implicitly commit. DDL implicitly commits the current transaction before and after it runs, so a later `ROLLBACK` cannot undo preceding DML or successful DDL. Treat schema changes as independent, lock-sensitive operations and plan rollback separately ([Types of SQL Statements](https://docs.oracle.com/en/database/oracle/oracle-database/26/sqlrf/Types-of-SQL-Statements.html)).

`ALTER SESSION` is session control, not DDL, and does not implicitly commit. It can still change NLS, time-zone, optimizer, or other connection behavior; use it only for a confirmed purpose and connection scope (same source).

## Plan inspection

Read [safety-and-execution.md](safety-and-execution.md) before a plan command.

- `EXPLAIN PLAN FOR ...` does **not** execute the explained statement, but it inserts plan rows into an output table. Oracle defines it as DML, requires insert privileges on that table, and does not implicitly commit it. It is therefore a write and requires authorization. Use a statement ID where plans can coexist, and commit or roll back the plan-table change according to the authorized workflow ([EXPLAIN PLAN](https://docs.oracle.com/en/database/oracle/oracle-database/26/sqlrf/EXPLAIN-PLAN.html)).
- `EXPLAIN PLAN` shows the optimizer's estimate in the explain environment, which can differ from the plan used by an executed cursor. Display it with `DBMS_XPLAN.DISPLAY`; treat it as an estimate, not runtime evidence ([Explaining and Displaying Execution Plans](https://docs.oracle.com/en/database/oracle/oracle-database/26/tgsql/generating-and-displaying-execution-plans.html)).
- `DBMS_XPLAN.DISPLAY_CURSOR` reads the plan and runtime statistics from a loaded cursor. It describes an execution that has already happened; producing that data requires an authorized execution, and reading it needs privileges on fixed views including `V$SQL_PLAN`, `V$SESSION`, and `V$SQL_PLAN_STATISTICS_ALL` ([DBMS_XPLAN](https://docs.oracle.com/en/database/oracle/oracle-database/26/arpls/DBMS_XPLAN.html)).
- Do not add `GATHER_PLAN_STATISTICS`, `MONITOR`, trace, `DBMS_STATS`, or similar instrumentation casually. They either execute the SQL or change monitoring or optimizer state; establish their effects and authorization first.

## Parameter binding

Oracle SQL and PL/SQL use named bind variables such as `:account_id`, but the placeholder syntax an application writes is driver-dependent. Get it from the application's driver or ORM documentation and bind values through its parameter API. Never build value literals by string concatenation.

Bind types deliberately, particularly for dates, timestamps, numbers, LOBs, and JSON. A client that supports Oracle's native `JSON` type can bind JSON instances directly; otherwise textual JSON is converted according to the target column and its constraints ([Overview of Inserting, Updating, and Loading JSON Data](https://docs.oracle.com/en/database/oracle/oracle-database/26/adjsn/overview-inserting-updating-and-loading-json-data.html)).

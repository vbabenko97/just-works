# SQL Server

Baseline: the SQL Server 2025 (17.x) documentation on learn.microsoft.com, pinned to `view=sql-server-ver17`. It is the newest release in the documentation: compatibility level 170 is the highest listed ([ALTER DATABASE Compatibility Level](https://learn.microsoft.com/en-us/sql/t-sql/statements/alter-database-transact-sql-compatibility-level?view=sql-server-ver17)), and the 2025 page (updated 2026-09-28) does not mention a later release ([What's New in SQL Server 2025](https://learn.microsoft.com/en-us/sql/sql-server/what-s-new-in-sql-server-2025?view=sql-server-ver17)). Azure SQL Database and Azure SQL Managed Instance get some features first, and this file says so where it matters. Checked against the official documentation on 2026-10-13.

This overlay is loaded after [universal-correctness.md](universal-correctness.md), [safety-and-execution.md](safety-and-execution.md), and [performance-workflow.md](performance-workflow.md), and lists only what differs on SQL Server (Transact-SQL, or T-SQL).

## Version and configuration

Establish these before relying on the rules below.

- Release (`SELECT @@VERSION`). SQL Server 2025 (17.x) adds the native `json` type, the `||` string concatenation operator, regular expression functions such as `REGEXP_LIKE`, `JSON_OBJECTAGG`, `JSON_ARRAYAGG`, and `CURRENT_DATE` ([What's New in SQL Server 2025](https://learn.microsoft.com/en-us/sql/sql-server/what-s-new-in-sql-server-2025?view=sql-server-ver17)). Earlier releases reject them. `OFFSET ... FETCH` needs SQL Server 2012 (11.x) ([ORDER BY Clause](https://learn.microsoft.com/en-us/sql/t-sql/queries/select-order-by-clause-transact-sql?view=sql-server-ver17)). Query Store is on by default for new databases from SQL Server 2022 (16.x) ([Query Store](https://learn.microsoft.com/en-us/sql/relational-databases/performance/monitoring-performance-by-using-the-query-store?view=sql-server-ver17)).
- Database compatibility level (`SELECT name, compatibility_level FROM sys.databases`). The default is 170 for SQL Server 2025, 160 for 2022, 150 for 2019, 140 for 2017, and 130 for 2016. It is set per database. Level 130 or higher gates `STRING_SPLIT`, and new optimizer fixes and cardinality estimator changes apply only at the default level of each release ([ALTER DATABASE Compatibility Level](https://learn.microsoft.com/en-us/sql/t-sql/statements/alter-database-transact-sql-compatibility-level?view=sql-server-ver17)). The JSON functions need level 130 ([Work with JSON Data](https://learn.microsoft.com/en-us/sql/relational-databases/json/json-data-sql-server?view=sql-server-ver17)), and reserved words depend on the level ([Database Identifiers](https://learn.microsoft.com/en-us/sql/relational-databases/databases/database-identifiers?view=sql-server-ver17)).
- Collation of the instance, the database, and each compared column. It gates string equality, ordering, and identifier case sensitivity ([Collation and Unicode Support](https://learn.microsoft.com/en-us/sql/relational-databases/collations/collation-and-unicode-support?view=sql-server-ver17)).
- `QUOTED_IDENTIFIER` for the connection. It gates the meaning of `"` ([SET QUOTED_IDENTIFIER](https://learn.microsoft.com/en-us/sql/t-sql/statements/set-quoted-identifier-transact-sql?view=sql-server-ver17)).
- `IMPLICIT_TRANSACTIONS` and `XACT_ABORT` for the session, and the database options `READ_COMMITTED_SNAPSHOT` and `ALLOW_SNAPSHOT_ISOLATION`. They gate transaction scope, error rollback, blocking, and stable paging.

## Identifiers and quoting

Brackets always delimit an identifier; a `]` inside the name is written `]]`. Double quotes delimit identifiers only while `QUOTED_IDENTIFIER` is ON, which is the default for most connections. With it OFF, double quotes delimit string literals. Identifiers hold 1 to 128 characters ([Database Identifiers](https://learn.microsoft.com/en-us/sql/relational-databases/databases/database-identifiers?view=sql-server-ver17)).

`QUOTED_IDENTIFIER` must be ON to create indexed views, filtered indexes, and indexes on computed columns. ODBC and OLE DB connections set it ON; connections from DB-Library default to OFF ([SET QUOTED_IDENTIFIER](https://learn.microsoft.com/en-us/sql/t-sql/statements/set-quoted-identifier-transact-sql?view=sql-server-ver17)).

Identifiers take the collation of their level, so in a case-sensitive database two tables can differ only in case, and in a case-insensitive database they cannot ([Database Identifiers](https://learn.microsoft.com/en-us/sql/relational-databases/databases/database-identifiers?view=sql-server-ver17)).

## Types and casts

When an operator combines two types, the lower-precedence type is converted to the higher one. `nvarchar` outranks `varchar`, and `int` outranks both, so `@int + ' text'` fails with a conversion error unless the number is cast to a string first ([Data Type Precedence](https://learn.microsoft.com/en-us/sql/t-sql/data-types/data-type-precedence-transact-sql?view=sql-server-ver17), [Data Type Conversion](https://learn.microsoft.com/en-us/sql/t-sql/data-types/data-type-conversion-database-engine?view=sql-server-ver17)).

Comparing a `varchar` column with an `nvarchar` parameter therefore converts the column side. Whether that costs an index seek depends on the collation and the plan, so look for `CONVERT_IMPLICIT` on the column in the plan. Declare the parameter with the column's type, as in the Parameter binding section.

`datetime` rounds to increments of .000, .003, and .007 seconds, and a literal such as `23:59:59.999` rounds up to the next day. Use `datetime2` (precision 0 to 7, default 7, range 0001 to 9999) for new work ([datetime](https://learn.microsoft.com/en-us/sql/t-sql/data-types/datetime-transact-sql?view=sql-server-ver17), [datetime2](https://learn.microsoft.com/en-us/sql/t-sql/data-types/datetime2-transact-sql?view=sql-server-ver17)). Under compatibility level 130 or higher, implicit `datetime` to `datetime2` conversion keeps the fractional milliseconds, so cast explicitly in mixed comparisons (same `datetime2` page).

## Time zones and temporal types

`datetime` and `datetime2` store no offset and are not daylight-saving aware; `datetimeoffset` stores an offset ([datetime](https://learn.microsoft.com/en-us/sql/t-sql/data-types/datetime-transact-sql?view=sql-server-ver17), [datetime2](https://learn.microsoft.com/en-us/sql/t-sql/data-types/datetime2-transact-sql?view=sql-server-ver17)). `AT TIME ZONE` takes a Windows time zone name listed in `sys.time_zone_info` and returns `datetimeoffset`. An input without an offset is assumed to already be in the target zone; a `datetimeoffset` input is converted ([AT TIME ZONE](https://learn.microsoft.com/en-us/sql/t-sql/queries/at-time-zone-transact-sql?view=sql-server-ver17), [sys.time_zone_info](https://learn.microsoft.com/en-us/sql/relational-databases/system-catalog-views/sys-time-zone-info-transact-sql?view=sql-server-ver17)).

```sql
-- Example column: created_utc is a datetime2 that holds UTC.
SELECT created_utc AT TIME ZONE 'UTC' AT TIME ZONE 'Central European Standard Time' AS created_local
FROM dbo.orders;
-- Without the first AT TIME ZONE, created_utc would be treated as already local to the target zone.
```

A local time in a spring-forward gap gets the offset after the change; a time in a fall-back overlap gets the offset before the change (the daylight saving offset). Zone rules live outside SQL Server, so the function is nondeterministic (same `AT TIME ZONE` page). `AT TIME ZONE 'LOCAL'` is available only in Azure SQL Database and Fabric SQL database (same page).

## Pagination

`ORDER BY ... OFFSET n ROWS FETCH NEXT m ROWS ONLY` needs the `ORDER BY`; `FETCH` needs `OFFSET`; the counts can be variables or parameters; and it cannot be combined with `TOP` in one query. Pages are stable only if the data does not change between requests (or all requests run in one transaction under snapshot or serializable isolation) and the `ORDER BY` columns are unique ([ORDER BY Clause](https://learn.microsoft.com/en-us/sql/t-sql/queries/select-order-by-clause-transact-sql?view=sql-server-ver17)).

`TOP` without `ORDER BY` returns rows in an undefined order. `TOP ... WITH TIES` requires `ORDER BY` and can return more rows than requested. In `INSERT`, `UPDATE`, `MERGE`, and `DELETE`, `TOP` picks arbitrary rows and cannot take `ORDER BY` directly. `TOP` is applied before the `ORDER BY` of a `UNION`, so order each branch in a subselect ([TOP](https://learn.microsoft.com/en-us/sql/t-sql/queries/top-transact-sql?view=sql-server-ver17)).

```sql
-- Problem: deletes any 10 matching rows, and ORDER BY is not allowed here.
DELETE TOP (10) FROM dbo.jobs WHERE state = 'done';
-- Corrected (example table): choose the rows in a subselect that orders by a unique key.
DELETE FROM dbo.jobs
WHERE job_id IN (SELECT TOP (10) job_id FROM dbo.jobs WHERE state = 'done' ORDER BY created_at, job_id);
```

T-SQL does not support the PostgreSQL-style ordering comparison `(created_at, id) > (@time, @id)`. For ascending keyset paging, use `created_at > @time OR (created_at = @time AND id > @id)` with `ORDER BY created_at, id`, assuming non-null sort keys and a confirmed unique `id`. Reverse the relevant comparisons for descending keys ([Comparison operators](https://learn.microsoft.com/en-us/sql/t-sql/language-elements/comparison-operators-transact-sql?view=sql-server-ver17)).

## JSON

The native `json` type is available in SQL Server 2025 (17.x), Azure SQL Database, Azure SQL Managed Instance (with the SQL Server 2025 or Always-up-to-date update policy), and Fabric SQL database, under any compatibility level. It stores a binary format and accepts only a JSON object or array: `'true'`, `'1234.56'`, `'"text"'`, and `'null'` are invalid for it ([JSON Data Type](https://learn.microsoft.com/en-us/sql/t-sql/data-types/json-data-type?view=sql-server-ver17)). By default, `ISJSON` also accepts only an object or array. SQL Server 2022+ adds the optional `VALUE`, `ARRAY`, `OBJECT`, or `SCALAR` constraint; `VALUE` includes JSON literals such as `true` and `null`, while `SCALAR` tests a top-level number or string ([ISJSON](https://learn.microsoft.com/en-us/sql/t-sql/functions/isjson-transact-sql?view=sql-server-ver17)).

Before SQL Server 2025, JSON is commonly stored as text in `nvarchar` columns. `OPENJSON` normally requires compatibility level 130+, while other JSON functions are available at all compatibility levels on releases that provide them. Verify documented configuration exceptions for the deployed release ([OPENJSON](https://learn.microsoft.com/en-us/sql/t-sql/functions/openjson-transact-sql?view=sql-server-ver17)). The `json` type converts only explicitly, and only to and from `char`, `varchar`, `nchar`, and `nvarchar`. Many clients see it as `varchar(max)` or `nvarchar(max)` (same `JSON Data Type` page).

`JSON_VALUE(expr, path)` returns a scalar as `nvarchar(4000)`. In lax mode a missing path, or a path to an object or array, gives `NULL`; strict mode raises an error. A value over 4,000 characters gives `NULL` in lax mode, so use `OPENJSON` for long values. SQL Server 2025 adds `RETURNING data_type`, valid only when the input is of type `json`. `JSON_QUERY` returns objects and arrays ([JSON_VALUE](https://learn.microsoft.com/en-us/sql/t-sql/functions/json-value-transact-sql?view=sql-server-ver17)).

## CTEs and window functions

The statement before `WITH` must end with a semicolon. A CTE is not materialized: each reference re-runs its definition, so use a temporary table when several references would repeat expensive work. The definition cannot contain `ORDER BY` (unless with `TOP` or `OFFSET`), `INTO`, an `OPTION` clause, or a nested `WITH` ([WITH common_table_expression](https://learn.microsoft.com/en-us/sql/t-sql/queries/with-common-table-expression-transact-sql?view=sql-server-ver17)).

A recursive CTE stops after 100 levels unless `OPTION (MAXRECURSION n)` on the outer statement says otherwise; 0 means no limit. The recursive member cannot use `DISTINCT`, `GROUP BY`, `TOP`, outer joins, scalar aggregation, or subqueries, and its column types must match the anchor member (same page).

Without `ORDER BY`, a window covers its whole partition. With `ORDER BY` and no frame, aggregate window functions use `RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW`, so tied rows share a running total; use `ROWS` for a per-row running total. Ranking functions take no frame, `DISTINCT` aggregates cannot be used with `OVER`, and `RANGE` does not accept `n PRECEDING` or `n FOLLOWING` ([OVER Clause](https://learn.microsoft.com/en-us/sql/t-sql/queries/select-over-clause-transact-sql?view=sql-server-ver17)).

## Upsert

Do not convert another engine's upsert mechanically to `MERGE`. Establish the enforced unique key, duplicate-source policy, and concurrency requirements first. For a simple upsert, consider explicit `UPDATE`/`INSERT` logic in a transaction with locking or isolation that also protects the missing-key case; a transaction alone does not prevent concurrent insert races. Use `MERGE` when its matching semantics fit and have been tested under the expected concurrency. It must end with a semicolon. A `MERGE` matched update raises an error if multiple source rows would update the same target row ([MERGE](https://learn.microsoft.com/en-us/sql/t-sql/statements/merge-transact-sql?view=sql-server-ver17)).

Under concurrency, `HOLDLOCK` (a synonym for `SERIALIZABLE`) prevents unique key violations in some scenarios. The manual adds that `MERGE` uses different locking from separate statements, can create complicated concurrency issues at scale, and that separate `INSERT`, `UPDATE`, and `DELETE` statements may block less under heavy concurrency (same page). Test either form under concurrent load.

```sql
-- Example table: dbo.counters(name PRIMARY KEY, hits).
MERGE dbo.counters WITH (HOLDLOCK) AS t
USING (VALUES (@name, 1)) AS s (name, hits) ON t.name = s.name
WHEN MATCHED THEN UPDATE SET hits = t.hits + s.hits
WHEN NOT MATCHED THEN INSERT (name, hits) VALUES (s.name, s.hits);   -- the semicolon is required
```

## Transactions and DDL

The default mode is autocommit: each statement is its own transaction. `BEGIN TRANSACTION` starts an explicit one, and a rollback of an inner transaction rolls back the outer one unless a savepoint is named ([Transactions](https://learn.microsoft.com/en-us/sql/t-sql/language-elements/transactions-transact-sql?view=sql-server-ver17), [BEGIN TRANSACTION](https://learn.microsoft.com/en-us/sql/t-sql/language-elements/begin-transaction-transact-sql?view=sql-server-ver17)). With `IMPLICIT_TRANSACTIONS ON`, statements such as `INSERT`, `UPDATE`, `DELETE`, `SELECT` from a table, `CREATE`, and `DROP` open a transaction that stays open until `COMMIT` or `ROLLBACK`. The setting is OFF by default for SqlClient, ODBC, and OLE DB, and `SET ANSI_DEFAULTS ON` turns it on ([SET IMPLICIT_TRANSACTIONS](https://learn.microsoft.com/en-us/sql/t-sql/statements/set-implicit-transactions-transact-sql?view=sql-server-ver17)).

With `XACT_ABORT OFF` (the default in a batch), a run-time error may roll back only the failing statement and let the transaction continue; with `ON`, the whole transaction rolls back. `THROW` honors `XACT_ABORT`; `RAISERROR` does not ([SET XACT_ABORT](https://learn.microsoft.com/en-us/sql/t-sql/statements/set-xact-abort-transact-sql?view=sql-server-ver17)).

Explicit transactions accept all Transact-SQL statements except a short list that includes `CREATE DATABASE`, `ALTER DATABASE`, `BACKUP`, `RESTORE`, and `RECONFIGURE`. Table DDL is not on that list. Under snapshot isolation, `ALTER TABLE` and `CREATE INDEX` are not permitted after `BEGIN TRANSACTION` ([Transaction Locking and Row Versioning Guide](https://learn.microsoft.com/en-us/sql/relational-databases/sql-server-transaction-locking-and-row-versioning-guide?view=sql-server-ver17)). Unlike MySQL and MariaDB, where DDL commits implicitly, SQL Server allows table DDL inside an explicit transaction. The manual does not state rollback behavior statement by statement, so test a migration's rollback on a disposable database.

## Plan inspection

Read this section before running any plan or maintenance command. Each entry states whether the statement runs, what state changes, and what is safe on a data change.

- Estimated plan: `SET SHOWPLAN_XML ON` (also `SHOWPLAN_ALL` and `SHOWPLAN_TEXT`, and Display Estimated Execution Plan in SSMS). SQL Server does not execute the statements and returns estimated costs and row counts with no runtime data. The `SET SHOWPLAN` statements must be alone in a batch and stay on until set OFF. Objects created in the same batch do not exist, so later statements that use them fail. It needs permission to run the statements plus `SHOWPLAN`. It writes nothing and is the form to use on a data change ([SET SHOWPLAN_XML](https://learn.microsoft.com/en-us/sql/t-sql/statements/set-showplan-xml-transact-sql?view=sql-server-ver17), [SET SHOWPLAN_ALL](https://learn.microsoft.com/en-us/sql/t-sql/statements/set-showplan-all-transact-sql?view=sql-server-ver17), [SET SHOWPLAN_TEXT](https://learn.microsoft.com/en-us/sql/t-sql/statements/set-showplan-text-transact-sql?view=sql-server-ver17), [Display the Estimated Execution Plan](https://learn.microsoft.com/en-us/sql/relational-databases/performance/display-the-estimated-execution-plan?view=sql-server-ver17)).
- `sys.dm_exec_query_plan(plan_handle)` returns the compile-time plan XML of a cached or running batch. It reads the plan cache only. It returns `NULL` once the plan is evicted, and it needs `VIEW SERVER STATE` (`VIEW SERVER PERFORMANCE STATE` from SQL Server 2022) ([sys.dm_exec_query_plan](https://learn.microsoft.com/en-us/sql/relational-databases/system-dynamic-management-objects/sys-dm-exec-query-plan-transact-sql?view=sql-server-ver17)).
- Actual plan: Include Actual Execution Plan in SSMS, or `SET STATISTICS XML ON`. The statements execute and the plan, with runtime information, is generated after they finish. On a data change, they perform it. They need permission to run the statements plus `SHOWPLAN` ([Display an Actual Execution Plan](https://learn.microsoft.com/en-us/sql/relational-databases/performance/display-an-actual-execution-plan?view=sql-server-ver17), [SET STATISTICS XML](https://learn.microsoft.com/en-us/sql/t-sql/statements/set-statistics-xml-transact-sql?view=sql-server-ver17)).
- `SET STATISTICS PROFILE ON` runs each query and returns its results followed by a profile with actual `Rows` and `Executes` ([SET STATISTICS PROFILE](https://learn.microsoft.com/en-us/sql/t-sql/statements/set-statistics-profile-transact-sql?view=sql-server-ver17)). `SET STATISTICS IO ON` and `SET STATISTICS TIME ON` report reads and compile and execution times for statements that run normally, and need no `SHOWPLAN` permission ([SET STATISTICS IO](https://learn.microsoft.com/en-us/sql/t-sql/statements/set-statistics-io-transact-sql?view=sql-server-ver17), [SET STATISTICS TIME](https://learn.microsoft.com/en-us/sql/t-sql/statements/set-statistics-time-transact-sql?view=sql-server-ver17)). Treat all of these as execution-bearing: run them on a data change only with authorization for the change itself, preferably on a disposable copy. Rolling back the transaction undoes the data change, but the locks are held until the rollback and effects outside the database are not undone.
- Query Store records the queries, plans, and runtime statistics of statements that execute, including your own test runs. Reading the `sys.query_store_*` views is read-only. `sp_query_store_force_plan`, `sp_query_store_unforce_plan`, `sp_query_store_remove_plan`, `sp_query_store_remove_query`, `sp_query_store_reset_exec_stats`, and `ALTER DATABASE ... SET QUERY_STORE` change state, and forcing a plan changes how queries run. Treat them as writes ([Query Store](https://learn.microsoft.com/en-us/sql/relational-databases/performance/monitoring-performance-by-using-the-query-store?view=sql-server-ver17)).
- `UPDATE STATISTICS` (and `sp_updatestats`) rewrites optimizer statistics. It needs `ALTER` on the table, can use `tempdb`, `FULLSCAN` reads every row, and updating statistics can cause cached plans to recompile. Treat it as a write ([UPDATE STATISTICS](https://learn.microsoft.com/en-us/sql/t-sql/statements/update-statistics-transact-sql?view=sql-server-ver17)).
- `ALTER INDEX ... REBUILD` drops and re-creates the index and updates its statistics with a full scan. An offline rebuild takes a schema modification lock that blocks all access to the table; `ONLINE = ON` keeps the data available but still takes brief locks at the start and end. Treat it as a write ([ALTER INDEX](https://learn.microsoft.com/en-us/sql/t-sql/statements/alter-index-transact-sql?view=sql-server-ver17)).
- `DBCC FREEPROCCACHE` evicts all cached plans (or one plan by handle), so incoming queries compile again and performance drops temporarily. It needs `ALTER SERVER STATE`. Never use it to get a "cold" timing on a shared server ([DBCC FREEPROCCACHE](https://learn.microsoft.com/en-us/sql/t-sql/database-console-commands/dbcc-freeproccache-transact-sql?view=sql-server-ver17)).

## Parameter binding

In T-SQL, `sp_executesql` takes a Unicode statement with `@name` markers, a Unicode definition list with a type for each marker, and one value per marker. The statement must be a Unicode constant or variable, not a concatenation expression. Runtime-built statements can be injected, so parameterize them ([sp_executesql](https://learn.microsoft.com/en-us/sql/relational-databases/system-stored-procedures/sp-executesql-transact-sql?view=sql-server-ver17)).

```sql
-- Example table: dbo.customers(email varchar(100), indexed).
EXEC sp_executesql
    N'SELECT customer_id FROM dbo.customers WHERE email = @email',
    N'@email varchar(100)',
    @email = 'a@example.com';
-- Declaring @email as nvarchar(100) would convert the varchar column side (data type precedence).
```

Identifiers cannot be parameters. Check a name against an allowlist, then wrap it in `QUOTENAME()`, which adds brackets, doubles any `]`, and returns `NULL` for input over 128 characters ([QUOTENAME](https://learn.microsoft.com/en-us/sql/t-sql/functions/quotename-transact-sql?view=sql-server-ver17)). Size variables that hold quoted names generously, because `QUOTENAME()` and `REPLACE()` truncate silently and truncation can enable injection. Never build `EXEC (@sql)` from concatenated input ([SQL Injection](https://learn.microsoft.com/en-us/sql/relational-databases/security/sql-injection?view=sql-server-ver17)).

SqlClient names parameters `@name` and runs parameterized statements through `sp_executesql`. The OLE DB and ODBC providers use positional `?` markers and need parameters added in marker order. SqlClient infers a .NET `String` as `NVarChar`, so set `SqlDbType.VarChar` and a length for `varchar` columns ([Configuring parameters and parameter data types](https://learn.microsoft.com/en-us/dotnet/framework/data/adonet/configuring-parameters-and-parameter-data-types)). ODBC binds each marker before execution ([Binding Parameters ODBC](https://learn.microsoft.com/en-us/sql/odbc/reference/develop-app/binding-parameters-odbc?view=sql-server-ver17)).

## Other differences

`NOLOCK` is the same as `READUNCOMMITTED`: it allows dirty reads, can show rows twice or not at all, and can return data that is later rolled back. It does not remove schema stability locks, so DDL still blocks it. The manual points to `READ_COMMITTED_SNAPSHOT` or `SNAPSHOT` isolation for less blocking without dirty reads. Do not offer `NOLOCK` as a performance fix ([Table Hints](https://learn.microsoft.com/en-us/sql/t-sql/queries/hints-transact-sql-table?view=sql-server-ver17)).

# MySQL

Baseline: the MySQL 8.4 LTS reference manual. MySQL ships Long-Term Support (LTS) series and Innovation releases ([MySQL 8.4: MySQL Releases](https://dev.mysql.com/doc/refman/8.4/en/mysql-releases.html)). A newer LTS series, 9.7, exists (9.7.0 was released on 2026-04-21, per the [MySQL 9.7 release notes](https://dev.mysql.com/doc/relnotes/mysql/9.7/en/)), and releases after 9.7 use calendar versions such as 26.7. The manual does not say which track 26.7 belongs to. The pages cited here were read for 8.4. The 9.7 pages for `EXPLAIN`, `ANALYZE TABLE`, SQL modes, and `INSERT ... ON DUPLICATE KEY UPDATE` were also read and match unless this file says otherwise. Nothing was checked for 26.x. Checked against the official documentation on 2026-10-13.

This overlay is loaded after [universal-correctness.md](universal-correctness.md), [safety-and-execution.md](safety-and-execution.md), and [performance-workflow.md](performance-workflow.md), and lists only what differs on MySQL.

MySQL and MariaDB are different engines with diverging syntax, JSON storage, and plan commands. If the server is MariaDB, this file does not apply: load [mariadb.md](mariadb.md) instead.

## Version and configuration

Establish these before relying on the rules below.

- Server version (`SELECT VERSION()`). Common table expressions and window functions need 8.0 or later ([MySQL 8.0: What Is New in MySQL 8.0](https://dev.mysql.com/doc/refman/8.0/en/mysql-nutshell.html)). `JSON_TABLE()` needs 8.0.4 (same page). The row alias form of the upsert needs 8.0.19 ([MySQL 8.0.19 release notes](https://dev.mysql.com/doc/relnotes/mysql/8.0/en/news-8-0-19.html)).
- `@@sql_mode`. The 8.4 default includes `ONLY_FULL_GROUP_BY`, `STRICT_TRANS_TABLES`, `NO_ZERO_IN_DATE`, `NO_ZERO_DATE`, `ERROR_FOR_DIVISION_BY_ZERO`, and `NO_ENGINE_SUBSTITUTION`. It gates grouping rules, whether invalid values are rejected or adjusted, and the meaning of `"` and `||`. A session can change it, so read it from the connection that will run the SQL ([MySQL 8.4: Server SQL Modes](https://dev.mysql.com/doc/refman/8.4/en/sql-mode.html)).
- `@@lower_case_table_names`. It gates table name case sensitivity and can be set only when the server is initialized ([MySQL 8.4: Identifier Case Sensitivity](https://dev.mysql.com/doc/refman/8.4/en/identifier-case-sensitivity.html)).
- `@@time_zone`, `@@system_time_zone`, and whether the time zone tables are loaded. They gate named zones in `SET time_zone` and `CONVERT_TZ()` ([MySQL 8.4: Time Zone Support](https://dev.mysql.com/doc/refman/8.4/en/time-zone-support.html)).
- `@@character_set_server`, `@@collation_server`, and the collation of each compared column. They gate equality and ordering of strings.
- `@@cte_max_recursion_depth` (recursive CTE limit) and `@@autocommit` (transaction mode).

## Identifiers and quoting

Quote identifiers with backticks and double a backtick inside a name ([MySQL 8.4: Schema Object Names](https://dev.mysql.com/doc/refman/8.4/en/identifiers.html)). Double quotes delimit string literals unless `ANSI_QUOTES` is in `sql_mode`; with it, double quotes delimit identifiers and strings must use single quotes ([MySQL 8.4: Server SQL Modes](https://dev.mysql.com/doc/refman/8.4/en/sql-mode.html)).

```sql
-- Example table. Under the default sql_mode, "status" is a string literal.
SELECT "status" FROM orders;   -- returns the text status on every row
SELECT `status` FROM orders;   -- returns the column
```

`||` means `OR` unless `PIPES_AS_CONCAT` is set; use `CONCAT()` to join strings ([MySQL 8.4: Server SQL Modes](https://dev.mysql.com/doc/refman/8.4/en/sql-mode.html)).

Database and table names follow `lower_case_table_names`: 0 on Unix (case-sensitive), 1 on Windows, 2 on macOS. Column names and column aliases are not case-sensitive on any platform, while table aliases are case-sensitive on Unix by default. SQL written on macOS or Windows can fail on Linux for this reason ([MySQL 8.4: Identifier Case Sensitivity](https://dev.mysql.com/doc/refman/8.4/en/identifier-case-sensitivity.html)).

## Types and casts

`utf8` is a deprecated alias for `utf8mb3`, which is expected to be removed; use `utf8mb4` ([MySQL 8.4: The utf8mb3 Character Set](https://dev.mysql.com/doc/refman/8.4/en/charset-unicode-utf8.html)). The server default is `utf8mb4` with `utf8mb4_0900_ai_ci` ([MySQL 8.4: Server Character Set and Collation](https://dev.mysql.com/doc/refman/8.4/en/charset-server.html)).

`utf8mb4_0900_ai_ci` is accent-insensitive and case-insensitive, so `=` treats `'a'` and `'Á'` as equal. It also has the `NO PAD` attribute, so trailing spaces count in comparisons, unlike `PAD SPACE` collations such as `utf8mb4_general_ci`. Use a `_as_cs` or `_bin` collation when exact matching is required ([MySQL 8.4: Unicode Character Sets](https://dev.mysql.com/doc/refman/8.4/en/charset-unicode-sets.html)).

Comparing a string with a number converts both sides to floating point, so unrelated strings can compare equal to a number. A string column compared with a number cannot use its index ([MySQL 8.4: Type Conversion in Expression Evaluation](https://dev.mysql.com/doc/refman/8.4/en/type-conversion.html)).

```sql
SELECT 0 = 'x6';                       -- 1, because 'x6' converts to 0
SELECT * FROM t WHERE str_col = 1;     -- full scan; also matches '1', ' 1', and '1a'
SELECT * FROM t WHERE str_col = '1';   -- can use the index on str_col
```

In strict mode an invalid value in `INSERT` or `UPDATE` is an error (for transactional tables under `STRICT_TRANS_TABLES`); otherwise it is adjusted and produces a warning. In `SELECT`, invalid values produce warnings even in strict mode ([MySQL 8.4: Server SQL Modes](https://dev.mysql.com/doc/refman/8.4/en/sql-mode.html)). Division by zero returns `NULL` with a warning in `SELECT`, and is an error in `INSERT` or `UPDATE` when `ERROR_FOR_DIVISION_BY_ZERO` and strict mode are both on. `ERROR_FOR_DIVISION_BY_ZERO`, `NO_ZERO_DATE`, and `NO_ZERO_IN_DATE` are deprecated (same page).

## Time zones and temporal types

`TIMESTAMP` is converted from the session time zone to UTC on storage and back on retrieval, and covers `1970-01-01 00:00:01` UTC to `2038-01-19 03:14:07` UTC. `DATETIME` is not converted and covers `1000-01-01` to `9999-12-31` ([MySQL 8.4: The DATE, DATETIME, and TIMESTAMP Types](https://dev.mysql.com/doc/refman/8.4/en/datetime.html)). Changing `time_zone` therefore changes what a `TIMESTAMP` column returns but not what a `DATETIME` column returns ([MySQL 8.4: Time Zone Support](https://dev.mysql.com/doc/refman/8.4/en/time-zone-support.html)).

`time_zone` accepts `SYSTEM` (the default), an offset from `-13:59` to `+14:00`, or a named zone. Named zones work only after the time zone tables are populated, for example with `mysql_tzinfo_to_sql`; otherwise `SET time_zone = 'UTC'` fails with error 1298 ([MySQL 8.4: Time Zone Support](https://dev.mysql.com/doc/refman/8.4/en/time-zone-support.html), [MySQL 8.4: mysql_tzinfo_to_sql](https://dev.mysql.com/doc/refman/8.4/en/mysql-tzinfo-to-sql.html)). `CONVERT_TZ()` returns `NULL` when an argument is invalid, and named zones need the tables. The manual does not say what an unloaded named zone returns, so test a known conversion before trusting the result ([MySQL 8.4: Date and Time Functions](https://dev.mysql.com/doc/refman/8.4/en/date-and-time-functions.html)).

The time zone page does not say how ambiguous or nonexistent local times around a daylight saving change are resolved. Store UTC (`TIMESTAMP`, or `DATETIME` that holds UTC by convention) and convert at the edges.

`NOW()` returns the statement start time and `SYSDATE()` returns the time at which it runs; `SYSDATE()` is unsafe for statement-based replication ([MySQL 8.4: Date and Time Functions](https://dev.mysql.com/doc/refman/8.4/en/date-and-time-functions.html)). Fractional seconds go up to 6 digits ([MySQL 8.4: The DATE, DATETIME, and TIMESTAMP Types](https://dev.mysql.com/doc/refman/8.4/en/datetime.html)).

## Pagination

Use `LIMIT row_count OFFSET offset` or `LIMIT offset, row_count`. The arguments must be nonnegative integer constants, or `?` placeholders in prepared statements ([MySQL 8.4: SELECT Statement](https://dev.mysql.com/doc/refman/8.4/en/select.html)). The `SELECT` page documents no `OFFSET ... FETCH` form, so convert it to `LIMIT`.

When rows tie on the `ORDER BY` columns, the server may return them in any order, and the order can differ between a query with `LIMIT` and one without. Add a unique column to `ORDER BY` ([MySQL 8.4: LIMIT Query Optimization](https://dev.mysql.com/doc/refman/8.4/en/limit-optimization.html)).

For keyset pagination, a row constructor such as `(created_at, id) > (?, ?)` is equivalent to the expanded condition, but the optimizer is less likely to use an index when the constructor does not cover an index prefix. The manual advises not mixing row constructors with `AND` and `OR` ([MySQL 8.4: Row Constructor Expression Optimization](https://dev.mysql.com/doc/refman/8.4/en/row-constructor-optimization.html)).

```sql
-- Example: PRIMARY KEY (tenant_id, created_at, id).
-- Row constructor after an equality: the manual's analogous example used only the first key part.
WHERE tenant_id = 1 AND (created_at, id) > (@ts, @id)
-- Expanded form: the manual's analogous example used every key part.
WHERE tenant_id = 1 AND (created_at > @ts OR (created_at = @ts AND id > @id))
```

## JSON

`JSON` is a native type that validates documents on insert (invalid text is an error) and stores them in a binary format. A document is limited by `max_allowed_packet`. When a key repeats, the last value wins, and the server sorts object keys, so do not rely on key order ([MySQL 8.4: The JSON Data Type](https://dev.mysql.com/doc/refman/8.4/en/json.html)).

`col->'$.a'` is `JSON_EXTRACT()` and keeps JSON quotes around strings; `col->>'$.a'` removes them. Use `->>` when comparing with an SQL string ([MySQL 8.4: The JSON Data Type](https://dev.mysql.com/doc/refman/8.4/en/json.html)).

`JSON_TABLE(expr, path COLUMNS (...)) AS alias` returns a relational table. The alias is required, and a missing value or an error yields `NULL` by default ([MySQL 8.4: JSON Table Functions](https://dev.mysql.com/doc/refman/8.4/en/json-table-functions.html)).

A `JSON` column cannot be indexed directly. Index a generated column that extracts a scalar, or create a multi-valued index on a JSON array with `CAST(... AS ... ARRAY)` (InnoDB only, one multi-valued key part per index). The optimizer uses it for `MEMBER OF()`, `JSON_CONTAINS()`, and `JSON_OVERLAPS()` ([MySQL 8.4: CREATE INDEX Statement](https://dev.mysql.com/doc/refman/8.4/en/create-index.html)).

## CTEs and window functions

`WITH` can start `SELECT`, `UPDATE`, and `DELETE` statements, with one `WITH` clause per level. A recursive CTE needs the `RECURSIVE` keyword, and leaving it out gives error 1146 ([MySQL 8.4: WITH (Common Table Expressions)](https://dev.mysql.com/doc/refman/8.4/en/with.html)).

Recursion stops after `cte_max_recursion_depth` levels, 1000 by default. The recursive part cannot contain aggregates, window functions, `GROUP BY`, `ORDER BY`, or `DISTINCT`, and the CTE cannot be on the right side of a `LEFT JOIN` there (same page). A large CTE result can spill to an on-disk temporary table.

Window functions are allowed only in the select list and `ORDER BY`, so filter on one through a subquery or CTE ([MySQL 8.4: Window Function Concepts and Syntax](https://dev.mysql.com/doc/refman/8.4/en/window-functions-usage.html)). `ROW_NUMBER()` is nondeterministic without `ORDER BY` and gives tied rows different numbers; `RANK()` gives ties the same rank and leaves gaps ([MySQL 8.4: Window Function Descriptions](https://dev.mysql.com/doc/refman/8.4/en/window-function-descriptions.html)). Add a unique tie-breaker when the numbering must be repeatable.

## Upsert

`INSERT ... ON DUPLICATE KEY UPDATE` fires on a duplicate in the primary key or any unique index. If one insert conflicts with several rows through different unique indexes, only one row is updated, and the manual says to avoid the statement on tables with multiple unique indexes. It is also unsafe for statement-based replication ([MySQL 8.4: INSERT ... ON DUPLICATE KEY UPDATE](https://dev.mysql.com/doc/refman/8.4/en/insert-on-duplicate.html)).

The affected-rows count per row is 1 for an insert, 2 for an update, and 0 when the existing row already holds the new values, unless the client sets `CLIENT_FOUND_ROWS` (same page).

`VALUES()` in the `UPDATE` clause is deprecated. Use a row alias (8.0.19 or later) ([MySQL 8.4: INSERT ... ON DUPLICATE KEY UPDATE](https://dev.mysql.com/doc/refman/8.4/en/insert-on-duplicate.html)).

```sql
-- Example table: counters(name UNIQUE, hits).
INSERT INTO counters (name, hits) VALUES (?, 1) AS new
ON DUPLICATE KEY UPDATE hits = counters.hits + new.hits;
-- Deprecated: ON DUPLICATE KEY UPDATE hits = hits + VALUES(hits)
```

`REPLACE` deletes the conflicting old row and then inserts the new one. Columns not listed get their defaults, and the affected-rows count is rows deleted plus rows inserted ([MySQL 8.4: REPLACE Statement](https://dev.mysql.com/doc/refman/8.4/en/replace.html)). The `REPLACE` page does not describe delete triggers or `ON DELETE` actions, so check them before using `REPLACE` on tables that have either.

`INSERT IGNORE` turns ignorable errors into warnings, discards duplicate-key rows, and adjusts invalid values, which hides data problems ([MySQL 8.4: INSERT Statement](https://dev.mysql.com/doc/refman/8.4/en/insert.html)).

## Transactions and DDL

Autocommit is on for each new connection. `START TRANSACTION` or `BEGIN` opens an explicit transaction, and a session with autocommit off that ends without committing is rolled back ([MySQL 8.4: autocommit, COMMIT, and ROLLBACK](https://dev.mysql.com/doc/refman/8.4/en/innodb-autocommit-commit-rollback.html)).

DDL ends the current transaction with an implicit commit, even though 8.0 and later make InnoDB DDL atomic. Atomic DDL is not transactional DDL, so a `ROLLBACK` does not undo it, and only InnoDB supports it ([MySQL 8.4: Atomic Data Definition Statement Support](https://dev.mysql.com/doc/refman/8.4/en/atomic-ddl.html)). Do not wrap a migration in `BEGIN` and `ROLLBACK` and expect schema changes to revert.

The implicit-commit list includes `ALTER TABLE`, `CREATE INDEX`, `CREATE TABLE`, `DROP TABLE`, `RENAME TABLE`, `TRUNCATE TABLE`, account statements such as `GRANT` and `CREATE USER`, `LOCK TABLES`, `SET autocommit = 1` (when it was not already 1), and the maintenance statements `ANALYZE TABLE`, `OPTIMIZE TABLE`, `REPAIR TABLE`, and `FLUSH`. `CREATE TEMPORARY TABLE` and `DROP TEMPORARY TABLE` do not commit, but they cannot be rolled back either ([MySQL 8.4: Statements That Cause an Implicit Commit](https://dev.mysql.com/doc/refman/8.4/en/implicit-commit.html)).

## Plan inspection

Read this section before running any plan or maintenance command. Each entry states whether the statement runs, what state changes, and what is safe on a data change.

- `EXPLAIN <statement>` (`FORMAT=TRADITIONAL`, the default, or `JSON` or `TREE`) shows the plan the optimizer would use and works with `SELECT`, `DELETE`, `INSERT`, `REPLACE`, `UPDATE`, and `TABLE`. The manual presents only `EXPLAIN ANALYZE` as the form that runs the statement and has no sentence saying plain `EXPLAIN` skips execution, so read it as the estimate-only form. It writes nothing and is the form to use on a data change. It needs the privileges required to run the statement ([MySQL 8.4: EXPLAIN Statement](https://dev.mysql.com/doc/refman/8.4/en/explain.html)).
- `EXPLAIN FOR CONNECTION <id>` shows the plan of a statement already running in another connection. It needs the `PROCESS` privilege for another user's connection and cannot be combined with `ANALYZE` (same page).
- `EXPLAIN ANALYZE <statement>` runs the statement and reports actual timing and row counts. In 8.4 the output is always `TREE`; 9.7 also accepts `FORMAT=JSON` when `explain_json_format_version` is 2 ([MySQL 9.7: EXPLAIN Statement](https://dev.mysql.com/doc/refman/9.7/en/explain.html)). The manual lists `SELECT`, multi-table `UPDATE` and `DELETE`, and `TABLE` as supported, and does not list single-table `UPDATE` or `DELETE`, `INSERT`, or `REPLACE`. Treat it as execution-bearing: on a multi-table `UPDATE` or `DELETE`, assume it performs the change. Do not run it on a data change without authorization for the change itself, and prefer a disposable copy. A rollback does not undo statements that commit implicitly (see Transactions and DDL). `KILL QUERY` stops it ([MySQL 8.4: EXPLAIN Statement](https://dev.mysql.com/doc/refman/8.4/en/explain.html)).
- `ANALYZE TABLE` is not a plan command; it changes the statistics later plans use. It stores key distribution, holds a read lock on `InnoDB` and `MyISAM` tables during the analysis, needs `SELECT` and `INSERT` privileges, and is written to the binary log so it replicates, unless `NO_WRITE_TO_BINLOG` or `LOCAL` is given. `ANALYZE TABLE ... UPDATE HISTOGRAM ON col WITH N BUCKETS` creates or replaces column histograms in the data dictionary, and `DROP HISTOGRAM` removes them ([MySQL 8.4: ANALYZE TABLE Statement](https://dev.mysql.com/doc/refman/8.4/en/analyze-table.html)). It also commits implicitly. Treat it as a write.
- `OPTIMIZE TABLE` rebuilds the table. For `InnoDB` it maps to `ALTER TABLE ... FORCE`, runs as online DDL with brief exclusive locks at the start and end, and falls back to a table copy when `old_alter_table` is on or the table has `FULLTEXT` indexes. It is binary-logged unless `NO_WRITE_TO_BINLOG` or `LOCAL` is given, and that option needs the `OPTIMIZE_LOCAL_TABLE` privilege ([MySQL 8.4: OPTIMIZE TABLE Statement](https://dev.mysql.com/doc/refman/8.4/en/optimize-table.html)). It also commits implicitly. Treat it as a write.
- The optimizer trace (`SET optimizer_trace="enabled=ON"`, run the statement, read `INFORMATION_SCHEMA.OPTIMIZER_TRACE`) works per session and traces the statement you execute ([MySQL 8.4: Typical Usage](https://dev.mysql.com/doc/refman/8.4/en/optimizer-tracing-typical-usage.html)). Tracing a bare data change runs it. To trace one without running it, trace `EXPLAIN <statement>`, which the manual lists as traceable ([MySQL 8.4: Traceable Statements](https://dev.mysql.com/doc/refman/8.4/en/traceable-statements.html)).

## Parameter binding

Server-side prepared statements use `?` markers, which are valid only where a data value appears, never for identifiers or keywords. Do not put quotes around `?` ([MySQL 8.4: PREPARE Statement](https://dev.mysql.com/doc/refman/8.4/en/prepare.html)). `LIMIT` accepts markers in prepared statements ([MySQL 8.4: SELECT Statement](https://dev.mysql.com/doc/refman/8.4/en/select.html)).

`PREPARE stmt FROM '...'`, `EXECUTE stmt USING @v`, and `DEALLOCATE PREPARE` are a SQL-level interface for scripts and stored procedures. `USING` accepts only user variables, and a prepared statement belongs to the session that created it ([MySQL 8.4: EXECUTE Statement](https://dev.mysql.com/doc/refman/8.4/en/execute.html), [MySQL 8.4: Prepared Statements](https://dev.mysql.com/doc/refman/8.4/en/sql-prepared-statements.html)). This is not the client driver's binding API. The client/server protocol sends prepared statement parameters separately in a binary protocol ([MySQL C API: Prepared Statement Interface](https://dev.mysql.com/doc/c-api/8.4/en/c-api-prepared-statement-interface.html)), but each driver chooses its own placeholder syntax, so use the driver's documented form.

Pass a table or column name only after checking it against an allowlist, then quote it with backticks and double any backtick inside it.

## Other differences

A statement cannot modify a table and select from the same table in a subquery, unless the table is read through a materialized derived table (`NO_MERGE` hint can force it). `LIMIT` is not supported inside `IN`, `ALL`, `ANY`, or `SOME` subqueries and fails with error 1235 ([MySQL 8.4: Restrictions on Subqueries](https://dev.mysql.com/doc/refman/8.4/en/subquery-restrictions.html)).

`UPDATE` reports the rows it actually changed, not the rows it matched, so setting a column to its current value counts as 0. Single-table `UPDATE` accepts `ORDER BY` and `LIMIT`; multi-table `UPDATE` does not. `LIMIT` there counts rows matched, whether or not they changed ([MySQL 8.4: UPDATE Statement](https://dev.mysql.com/doc/refman/8.4/en/update.html)).

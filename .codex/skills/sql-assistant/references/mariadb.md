# MariaDB

Baseline: the MariaDB Server documentation at mariadb.com/docs, read for the 12.3 series. MariaDB 12.3 (12.3.3, stable, released 2026-08-24) is a long-term release maintained until June 2029 ([MariaDB 12.3.3 release notes](https://mariadb.com/docs/release-notes/community-server/12.3/12.3.3)). Newer series exist: 13.0 is the current rolling release (13.0.2, stable), 13.1 is a release candidate (13.1.1, not for production), and 13.2 is a preview ([MariaDB Community Server releases](https://mariadb.com/docs/release-notes/community-server), [All Releases](https://mariadb.com/docs/release-notes/community-server/all-releases)). The documentation site has one unversioned page per topic, so this file states a version wherever a page gives one. Checked against the official documentation on 2026-10-13.

This overlay is loaded after [universal-correctness.md](universal-correctness.md), [safety-and-execution.md](safety-and-execution.md), and [performance-workflow.md](performance-workflow.md), and lists only what differs on MariaDB.

MariaDB and MySQL are different engines with diverging syntax, JSON storage, and plan commands. If the server is MySQL, this file does not apply: load [mysql.md](mysql.md) instead.

## Version and configuration

Establish these before relying on the rules below.

- Server version (`SELECT VERSION()`). Version gates in this file: window functions and CTEs 10.2, sequences and system-versioned tables 10.3 ([MariaDB versus MySQL - Features](https://mariadb.com/docs/release-notes/community-server/about/compatibility-and-differences/mariadb-vs-mysql-features)), `INSERT ... RETURNING`, `REPLACE ... RETURNING`, and `INET6` 10.5 ([MariaDB 10.5 Changes & Improvements](https://mariadb.com/docs/release-notes/community-server/old-releases/10.5/what-is-mariadb-105)), `JSON_TABLE` and `OFFSET ... FETCH` 10.6, `UUID` 10.7, `INET4` 10.10, the 2106 `TIMESTAMP` limit 11.5, the `utf8mb4` default 11.6, and the `->` and `->>` operators 13.1.
- `@@sql_mode`. The manual's default list is `STRICT_TRANS_TABLES`, `ERROR_FOR_DIVISION_BY_ZERO`, `NO_AUTO_CREATE_USER`, and `NO_ENGINE_SUBSTITUTION`. It does not include `ONLY_FULL_GROUP_BY`, which MySQL enables by default, so a `GROUP BY` that MySQL rejects can run here. The mode gates grouping rules, strictness, the meaning of `"` and `||`, and (with `ORACLE`) much of the syntax ([MariaDB: SQL_MODE](https://mariadb.com/docs/server/server-management/variables-and-modes/sql_mode)).
- `@@time_zone` and whether the time zone tables are populated. They gate named zones ([MariaDB: Time Zones](https://mariadb.com/docs/server/reference/data-types/string-data-types/character-sets/internationalization-and-localization/time-zones)).
- Default character set and collation: before 11.6 they are `latin1` and `latin1_swedish_ci`; from 11.6 they are `utf8mb4` and `utf8mb4_uca1400_ai_ci`. Comparisons are case-insensitive by default ([MariaDB: Character Set and Collation Overview](https://mariadb.com/docs/server/reference/data-types/string-data-types/character-sets/character-set-and-collation-overview)).
- `@@max_recursive_iterations`, the recursion limit for CTEs (the manual's `WITH` page does not state its default).
- `@@explicit_defaults_for_timestamp`. It gates the automatic `TIMESTAMP` defaults described under time zones.

## Identifiers and quoting

Quote identifiers with backticks. Double quotes quote identifiers only when `ANSI_QUOTES` is in `sql_mode`; otherwise `CREATE TABLE "SELECT"` is a syntax error. Database, table, and column names are limited to 64 characters ([MariaDB: Identifier Names](https://mariadb.com/docs/server/reference/sql-structure/sql-language-structure/identifier-names)).

`PIPES_AS_CONCAT` makes `||` a concatenation operator, and `sql_mode=ORACLE` includes it, together with `ANSI_QUOTES`. Use `CONCAT()` in portable SQL ([MariaDB: SQL_MODE](https://mariadb.com/docs/server/server-management/variables-and-modes/sql_mode)).

## Types and casts

A string compared with an integer is compared as decimals; other mixed comparisons use floating point. A string column compared with a number cannot use its index: in the manual's example `a = 3` on a `VARCHAR` column scans, and `a = '3'` uses the index ([MariaDB: Type Conversion](https://mariadb.com/docs/server/reference/sql-functions/string-functions/type-conversion)).

With `ERROR_FOR_DIVISION_BY_ZERO` unset, division by zero returns `NULL`; when set (it is in the default list), updating a column with `1/0` is an error. In strict mode a statement with invalid data is aborted and rolled back, but on non-transactional engines a bad value after the first row is adjusted ([MariaDB: SQL_MODE](https://mariadb.com/docs/server/server-management/variables-and-modes/sql_mode)).

`UUID` (10.7) is stored in an index-friendly byte order, and it rejects `UUID_SHORT()` output and values in braces ([MariaDB: UUID Data Type](https://mariadb.com/docs/server/reference/data-types/string-data-types/uuid-data-type)). `INET6` stores 16 bytes ([MariaDB: INET6](https://mariadb.com/docs/server/reference/data-types/string-data-types/inet6)). `INET4` (10.10) stores 4 bytes ([MariaDB: INET4](https://mariadb.com/docs/server/reference/data-types/string-data-types/inet4)).

## Time zones and temporal types

`TIMESTAMP` values are converted from the session time zone to UTC on storage and back on retrieval, and no zone identifier is stored. The range ends at `2038-01-19 03:14:07` UTC before 11.5 and at `2106-02-07 06:28:15` UTC from 11.5 ([MariaDB: TIMESTAMP](https://mariadb.com/docs/server/reference/data-types/date-and-time-data-types/timestamp)). The 11.8 comparison page adds that the extended range applies on 64-bit platforms ([MariaDB 11.8 and MySQL 8.0 differences](https://mariadb.com/docs/release-notes/community-server/about/compatibility-and-differences/incompatibilities-and-feature-differences-between-mariadb-11-8-and-mysql-8)). `DATETIME` values are not converted ([MariaDB: Time Zones](https://mariadb.com/docs/server/reference/data-types/string-data-types/character-sets/internationalization-and-localization/time-zones)).

When `explicit_defaults_for_timestamp` is not set, the first `TIMESTAMP` column in a table gets `DEFAULT CURRENT_TIMESTAMP` and `ON UPDATE CURRENT_TIMESTAMP`. Unset was the default until 10.10 ([MariaDB: TIMESTAMP](https://mariadb.com/docs/server/reference/data-types/date-and-time-data-types/timestamp)). Name the default and the update behavior explicitly in DDL.

`time_zone` is `SYSTEM` by default, accepts offsets such as `+5:00`, and accepts named zones only after the time zone tables are populated; they are created empty. Populate them with `mariadb-tzinfo-to-sql` on Unix-like systems ([MariaDB: Time Zones](https://mariadb.com/docs/server/reference/data-types/string-data-types/character-sets/internationalization-and-localization/time-zones)). `CONVERT_TZ()` returns `NULL` for invalid arguments and when named zones are not loaded ([MariaDB: CONVERT_TZ](https://mariadb.com/docs/server/reference/sql-functions/date-time-functions/convert_tz)). `TIMESTAMP` accepts 0 to 6 fractional digits ([MariaDB: TIMESTAMP](https://mariadb.com/docs/server/reference/data-types/date-and-time-data-types/timestamp)).

## Pagination

`LIMIT row_count OFFSET offset` and `LIMIT offset, row_count` both work. `LIMIT ... ROWS EXAMINED` is a MariaDB feature that stops a `SELECT` that examines too many rows. An `UPDATE` with `LIMIT` is not safe for replication ([MariaDB: LIMIT](https://mariadb.com/docs/server/reference/sql-statements/data-manipulation/selecting-data/limit)).

`OFFSET start ROWS FETCH FIRST n ROWS ONLY` is available from 10.6 and also supports `WITH TIES`. `ORDER BY` is required only with `WITH TIES`; the error is "FETCH ... WITH TIES requires ORDER BY clause to be present". Paging still needs a deterministic `ORDER BY` ([MariaDB: SELECT ... OFFSET ... FETCH](https://mariadb.com/docs/server/reference/sql-statements/data-manipulation/selecting-data/select-offset-fetch)).

## JSON

`JSON` is an alias for `LONGTEXT COLLATE utf8mb4_bin`, and the alias adds an automatic `JSON_VALID()` check constraint. There is no separate binary type, and the assigned text is kept verbatim ([MariaDB: JSON Data Type](https://mariadb.com/docs/server/reference/data-types/string-data-types/json), [MariaDB: JSON_VALID](https://mariadb.com/docs/server/reference/sql-functions/special-functions/json-functions/json_valid)).

This differs from MySQL in ways that change query results. JSON strings compare as ordinary strings, except that `JSON_EXTRACT()` unescapes strings before comparison. For a duplicated key, only the first pair is accessible, where MySQL keeps the last ([MariaDB: JSON Data Type](https://mariadb.com/docs/server/reference/data-types/string-data-types/json)).

MariaDB cannot read MySQL's binary JSON format. Row-based replication of MySQL `JSON` columns to MariaDB does not work; the manual lists statement-based replication, converting the column to `TEXT` in MySQL, or an intermediate replica as workarounds. For migration it lists the `mysql_json` plugin, a `TEXT` conversion, or `mysqldump` (same page).

`JSON_VALUE(doc, path)` returns a scalar, or `NULL` for no match or an invalid document ([MariaDB: JSON_VALUE](https://mariadb.com/docs/server/reference/sql-functions/special-functions/json-functions/json_value)). `JSON_TABLE` is available from 10.6, and a missing value or an error gives `NULL` by default ([MariaDB: JSON_TABLE](https://mariadb.com/docs/server/reference/sql-functions/special-functions/json-functions/json_table)).

The `->` and `->>` operators exist only from 13.1, which is a release candidate on 2026-10-13. The path must be a string literal, so a column, variable, or `?` placeholder fails to parse, and the operators do not chain without parentheses ([MariaDB: JSON Arrow Operators](https://mariadb.com/docs/server/reference/sql-functions/special-functions/json-functions/json-arrow-operators)). Series before 13.1 do not have them; the 11.8 comparison page says so explicitly ([MariaDB 11.8 and MySQL 8.0 differences](https://mariadb.com/docs/release-notes/community-server/about/compatibility-and-differences/incompatibilities-and-feature-differences-between-mariadb-11-8-and-mysql-8)). Write `JSON_UNQUOTE(JSON_EXTRACT(col, '$.a'))` instead of `col->>'$.a'`.

```sql
-- Example table events(doc JSON). Fails on every series before 13.1:
SELECT doc->>'$.name' FROM events;
-- Works wherever the JSON functions exist:
SELECT JSON_UNQUOTE(JSON_EXTRACT(doc, '$.name')) FROM events;
```

## CTEs and window functions

Both arrived in 10.2 ([MariaDB versus MySQL - Features](https://mariadb.com/docs/release-notes/community-server/about/compatibility-and-differences/mariadb-vs-mysql-features)). `WITH [RECURSIVE]` works in subqueries and with `EXPLAIN`. The `max_recursive_iterations` variable limits recursion; MySQL's `cte_max_recursion_depth` does not appear on the page ([MariaDB: WITH](https://mariadb.com/docs/server/reference/sql-statements/data-manipulation/selecting-data/common-table-expressions/with)).

A window function cannot appear in `WHERE`; filter on one through a subquery or CTE. For aggregate window functions, `OVER (ORDER BY ...)` defaults to a running `RANGE` frame. MariaDB has no `GROUPS` frames, no frame exclusion, and no `NULLS FIRST` or `NULLS LAST`; aggregate window functions do not accept `DISTINCT`; and `RANGE` frames do not support `DATE` or `DATETIME` arithmetic ([MariaDB: Window Functions Overview](https://mariadb.com/docs/server/reference/sql-functions/special-functions/window-functions/window-functions-overview)). Rewrite SQL that uses these.

## Upsert

`INSERT ... ON DUPLICATE KEY UPDATE` fires on a duplicate primary or unique key. If more than one unique index matches, only the first is updated, and the manual advises against the statement on tables with several unique indexes. The documented affected-rows value is 1 for an insert and 2 for an update, unless the client sets `CLIENT_FOUND_ROWS`. For a table with an `AUTO_INCREMENT` primary key, `LAST_INSERT_ID()` returns that key when the statement inserts or updates a row ([MariaDB: INSERT ON DUPLICATE KEY UPDATE](https://mariadb.com/docs/server/reference/sql-statements/data-manipulation/inserting-loading-data/insert-on-duplicate-key-update)).

Refer to the new values with `VALUES(col)`, which is valid only inside the `ON DUPLICATE KEY UPDATE` clause. The page documents no row alias, so do not emit MySQL's `AS new` form (same page).

```sql
-- Example table: counters(name UNIQUE, hits). MariaDB form.
INSERT INTO counters (name, hits) VALUES (?, 1)
ON DUPLICATE KEY UPDATE hits = hits + VALUES(hits);
```

`REPLACE` deletes the conflicting row before inserting. It fires `DELETE` and `INSERT` triggers and runs `ON DELETE` foreign key actions ([MariaDB: REPLACE](https://mariadb.com/docs/server/reference/sql-statements/data-manipulation/changing-deleting-data/replace)).

`RETURNING` returns the affected rows in the same statement: `INSERT ... RETURNING` and `REPLACE ... RETURNING` from 10.5 ([MariaDB: INSERT ... RETURNING](https://mariadb.com/docs/server/reference/sql-statements/data-manipulation/inserting-loading-data/insertreturning), [MariaDB: REPLACE ... RETURNING](https://mariadb.com/docs/server/reference/sql-statements/data-manipulation/changing-deleting-data/replacereturning)), and `DELETE ... RETURNING` for single-table deletes, without aggregate functions ([MariaDB: DELETE](https://mariadb.com/docs/server/reference/sql-statements/data-manipulation/changing-deleting-data/delete)). The `INSERT` page does not say whether rows changed by the `ON DUPLICATE KEY UPDATE` branch are returned, so do not combine them without testing.

## Transactions and DDL

Autocommit is on by default, and `START TRANSACTION` or `SET autocommit = 1` commits any open transaction ([MariaDB: START TRANSACTION](https://mariadb.com/docs/server/reference/sql-statements/transactions/start-transaction)).

Many statements commit implicitly before they run, even if they then fail: `ALTER`, `CREATE`, and `DROP` for tables, indexes, views, sequences, users, roles, and routines, plus `RENAME TABLE`, `TRUNCATE TABLE`, `ANALYZE TABLE`, `OPTIMIZE TABLE`, `REPAIR TABLE`, `FLUSH`, and `LOCK TABLES`. `CREATE TEMPORARY TABLE` and `DROP TEMPORARY TABLE` do not commit, but `TRUNCATE TABLE` and index DDL on a temporary table still do ([MariaDB: Statements Causing an Implicit Commit](https://mariadb.com/docs/server/reference/sql-statements/transactions/sql-statements-that-cause-an-implicit-commit)). That page does not describe atomic or crash-safe DDL, so do not assume schema changes in a transaction can be rolled back.

## Plan inspection

Read this section before running any plan or maintenance command. Do not confuse `ANALYZE <statement>` with `ANALYZE TABLE`.

```sql
-- Example table orders. Estimate only; this is the form to use on an UPDATE:
EXPLAIN UPDATE orders SET status = 'shipped' WHERE id = 7;
-- Executes the statement and performs the update:
ANALYZE UPDATE orders SET status = 'shipped' WHERE id = 7;
```

- `EXPLAIN [EXTENDED | PARTITIONS | FORMAT=JSON] <SELECT | UPDATE | DELETE>` shows the optimizer's plan. The manual contrasts it with `ANALYZE`, which "runs the query rather than only estimating the execution path". It writes nothing and is the form to use on an `UPDATE` or `DELETE`. It can take metadata locks like a `SELECT`. The syntax on the page does not list `INSERT` or `REPLACE` ([MariaDB: EXPLAIN](https://mariadb.com/docs/server/reference/sql-statements/administrative-sql-statements/analyze-and-explain-statements/explain)).
- `EXPLAIN FOR CONNECTION <id>` is an alias for `SHOW EXPLAIN FOR <id>`. It reports the plan of a statement that is already running in another thread (same page).
- `ANALYZE <statement>` and `ANALYZE FORMAT=JSON <statement>` execute the statement and return `EXPLAIN` output with measured values (`r_rows`, `r_filtered`, and in JSON `r_loops` and `r_total_time_ms`) instead of the result set. The manual states that "ANALYZE UPDATE or ANALYZE DELETE will actually make updates/deletes", and a `SELECT` is run and its result discarded. It accepts any statement `EXPLAIN` accepts. Treat it as execution-bearing: on a data change it performs the change, so run it only with authorization for the change itself, preferably on a disposable copy ([MariaDB: ANALYZE Statement](https://mariadb.com/docs/server/reference/sql-statements/administrative-sql-statements/analyze-and-explain-statements/analyze-statement), [MariaDB: ANALYZE FORMAT=JSON](https://mariadb.com/docs/server/reference/sql-statements/administrative-sql-statements/analyze-and-explain-statements/analyze-format-json)).
- `EXPLAIN ANALYZE` is listed as outdated syntax: the manual says it "was changed to `ANALYZE statement`". It does not say whether the old form is still accepted or whether it runs the statement, so write `ANALYZE <statement>`, and assume any existing `EXPLAIN ANALYZE` executes ([MariaDB: EXPLAIN ANALYZE](https://mariadb.com/docs/server/reference/sql-statements/administrative-sql-statements/analyze-and-explain-statements/explain-analyze)).
- `ANALYZE TABLE` stores key distribution and can collect engine-independent statistics and histograms (kept in `mysql.column_stats`; `histogram_size` 0 disables them). It needs `SELECT` and `INSERT` privileges and is written to the binary log, so it replicates, unless `NO_WRITE_TO_BINLOG` or `LOCAL` is given. From 10.6.16 it is non-blocking, and before that it was blocking. It also commits implicitly. Treat it as a write ([MariaDB: ANALYZE TABLE](https://mariadb.com/docs/server/reference/sql-statements/table-statements/analyze-table), [MariaDB: Histogram-Based Statistics](https://mariadb.com/docs/server/ha-and-performance/optimization-and-tuning/query-optimizations/statistics-for-optimizing-queries/histogram-based-statistics)).
- `OPTIMIZE TABLE` reclaims space and defragments, needs `SELECT` and `INSERT` privileges, and is binary-logged by default unless `NO_WRITE_TO_BINLOG` or `LOCAL` is given. Engines without support do nothing. The page does not describe how an `InnoDB` table is rebuilt or locked, and notes InnoDB defragmentation was removed in 11.1, so check the server version before running it. It also commits implicitly. Treat it as a write ([MariaDB: OPTIMIZE TABLE](https://mariadb.com/docs/server/ha-and-performance/optimization-and-tuning/optimizing-tables/optimize-table)).
- The optimizer trace (`SET optimizer_trace='enabled=on'`, off by default) keeps the trace of the last statement each connection ran, readable in `INFORMATION_SCHEMA.OPTIMIZER_TRACE`. The page does not say whether tracing runs the statement, so assume it does for a data change ([MariaDB: Optimizer Trace Overview](https://mariadb.com/docs/server/ha-and-performance/optimization-and-tuning/query-optimizer/optimizer-trace/optimizer-trace-overview)).

## Parameter binding

Prepared statements use `?` markers, valid only where an expression appears, never for keywords or identifiers. Do not quote `?`. From 10.6.2 any statement except `PREPARE`, `EXECUTE`, and `DEALLOCATE` can be prepared; earlier versions allow only a fixed list ([MariaDB: PREPARE Statement](https://mariadb.com/docs/server/reference/sql-statements/prepared-statements/prepare-statement)).

`EXECUTE stmt USING ...` accepts arbitrary expressions, not only user variables as in MySQL, and must name as many expressions as there are markers ([MariaDB: EXECUTE Statement](https://mariadb.com/docs/server/reference/sql-statements/prepared-statements/execute-statement)). `EXECUTE IMMEDIATE statement USING ...` prepares and runs a statement in one step ([MariaDB: EXECUTE IMMEDIATE](https://mariadb.com/docs/server/reference/sql-statements/prepared-statements/execute-immediate)). These are SQL-level commands, not the driver API. The client protocol's prepare command counts `?` placeholders in the statement text ([MariaDB: COM_STMT_PREPARE](https://mariadb.com/docs/server/reference/clientserver-protocol/3-binary-protocol-prepared-statements/com_stmt_prepare)), but each driver chooses its own placeholder syntax, so use the driver's documented form.

Pass a table or column name only after checking it against an allowlist, then quote it with backticks and double any backtick inside it.

## Other differences

`sql_mode=ORACLE` changes syntax: it enables `PIPES_AS_CONCAT` and `ANSI_QUOTES` among other flags, and makes the server accept a large subset of PL/SQL in stored routines. Check the mode before reading unfamiliar SQL ([MariaDB: SQL_MODE](https://mariadb.com/docs/server/server-management/variables-and-modes/sql_mode)).

Sequences (`CREATE SEQUENCE`, `NEXT VALUE FOR seq`) exist from 10.3 ([MariaDB: CREATE SEQUENCE](https://mariadb.com/docs/server/reference/sql-structure/sequences/create-sequence)). A system-versioned table (`WITH SYSTEM VERSIONING`, 10.3) returns only current rows unless the query uses `FOR SYSTEM_TIME` ([MariaDB: System-Versioned Tables](https://mariadb.com/docs/server/reference/sql-structure/temporal-tables/system-versioned-tables)).

Compared with MySQL 8.0, MariaDB 11.8 has no lateral derived tables, spells shared row locks `LOCK IN SHARE MODE` instead of `FOR SHARE`, and uses PCRE for regular expressions ([MariaDB 11.8 and MySQL 8.0 differences](https://mariadb.com/docs/release-notes/community-server/about/compatibility-and-differences/incompatibilities-and-feature-differences-between-mariadb-11-8-and-mysql-8)).

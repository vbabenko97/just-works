# DuckDB

The baseline is the DuckDB documentation at `duckdb.org/docs/current`, which does not name its version. The release calendar lists 1.5.6 (2026-09-28) as the latest release, and a newer major release, 2.0.0, is scheduled but was not released when this was checked ([DuckDB: Release Calendar](https://duckdb.org/release_calendar)). Checked against the official documentation on 2026-10-13.

This overlay is loaded after the shared references and lists only what differs on DuckDB. DuckDB's dialect follows PostgreSQL's with listed exceptions, so do not assume PostgreSQL behavior holds; check the exceptions page ([DuckDB: PostgreSQL Compatibility](https://duckdb.org/docs/current/sql/dialect/postgresql_compatibility)).

## Version and configuration

Establish the DuckDB version and the settings below before relying on a rule. `SELECT version();` returns the version and `SELECT current_setting('TimeZone');` returns a setting's value ([DuckDB: Utility Functions](https://duckdb.org/docs/current/sql/functions/utility)).

- Release lines: 1.5.x is current, and 1.4.x is a long-term support line (latest 1.4.5 LTS) with an end-of-life date of 2026-11-17. The 2.0.0 date of 2026-10-21 is tentative ([DuckDB: Release Calendar](https://duckdb.org/release_calendar)). The site has no version-pinned documentation URLs (a `/docs/1.5/` URL returned 404), so version requirements are stated in the rules.
- `MERGE INTO` exists since 1.4.0 ([DuckDB: Announcing DuckDB 1.4.0](https://duckdb.org/2025/09/16/announcing-duckdb-140.html)).
- The arrow operators `->` and `->>` bind loosely before 2.0.0, and the documentation says they bind tighter from 2.0.0 on ([DuckDB: JSON Processing Functions](https://duckdb.org/docs/current/data/json/json_functions)).
- For recursive CTEs with `USING KEY`, the `UNION` form is deprecated since 1.5.0 in favor of `UNION ALL`, and 2.0.0 disables it by default ([DuckDB: WITH Clause](https://duckdb.org/docs/current/sql/query_syntax/with)).
- Named time zones need the ICU extension. Depending on the client build, it may be bundled or autoloaded on first use; otherwise installing and loading it is an additional action ([DuckDB: ICU Extension](https://duckdb.org/docs/current/core_extensions/icu), [DuckDB: Timestamp Types](https://duckdb.org/docs/current/sql/data_types/timestamp)). The JSON extension also supports autoloading ([DuckDB: JSON Overview](https://duckdb.org/docs/current/data/json/overview)). Check extension availability before a query that depends on it. Automatic or manual installation can download executable code and write extension files; keep those effects within the task's authorization and network policy ([Extension security](https://duckdb.org/docs/current/operations_manual/securing_duckdb/securing_extensions)).
- `TimeZone` defaults to the system time zone, `default_null_order` to `NULLS_LAST`, and `preserve_identifier_case` to `true`. Set `access_mode=READ_ONLY` when opening the database; `enable_external_access` and `lock_configuration` control later in-process access and configuration changes ([DuckDB: Configuration](https://duckdb.org/docs/current/configuration/overview)).
- Implicit casts to `VARCHAR` have been removed since 0.10.0; the `old_implicit_casting` setting restores them and is planned for deprecation ([DuckDB: Typecasting](https://duckdb.org/docs/current/sql/data_types/typecasting)).

## Identifiers and quoting

Identifiers are case-insensitive, including quoted ones, and DuckDB keeps the case as written. PostgreSQL treats quoted identifiers as case-sensitive. If two identifiers differ only by case, DuckDB picks one at random. `preserve_identifier_case = false` lowercases all identifiers ([DuckDB: Keywords and Identifiers](https://duckdb.org/docs/current/sql/dialect/keywords_and_identifiers), [DuckDB: PostgreSQL Compatibility](https://duckdb.org/docs/current/sql/dialect/postgresql_compatibility)).

Quote an identifier with double quotes. An unquoted identifier cannot be a reserved keyword, so `SELECT 123 AS SELECT` fails ([DuckDB: Keywords and Identifiers](https://duckdb.org/docs/current/sql/dialect/keywords_and_identifiers)).

## Types and casts

On two integers, `/` returns a floating-point result and `//` performs integer division: `5 / 2` is `2.5` and `5 // 2` is `2`. PostgreSQL's `/` on integers truncates, so converting SQL between the two changes results ([DuckDB: Numeric Functions](https://duckdb.org/docs/current/sql/functions/numeric), [DuckDB: PostgreSQL Compatibility](https://duckdb.org/docs/current/sql/dialect/postgresql_compatibility)).

Equality checks add implicit casts: `'1.1' = 1` and `true = 1` return true in DuckDB, while PostgreSQL raises an error. There is no setting for stricter comparison type checking ([DuckDB: Comparison Operators](https://duckdb.org/docs/current/sql/expressions/comparison_operators), [DuckDB: PostgreSQL Compatibility](https://duckdb.org/docs/current/sql/dialect/postgresql_compatibility)). Compare a column with a value of the column's own type so that no cast is added silently.

`CAST` raises an error when a value overflows or text cannot be parsed. `TRY_CAST` returns `NULL` instead ([DuckDB: Typecasting](https://duckdb.org/docs/current/sql/data_types/typecasting)). `==` is accepted as equality but is not portable ([DuckDB: PostgreSQL Compatibility](https://duckdb.org/docs/current/sql/dialect/postgresql_compatibility)).

## Time zones and temporal types

`TIMESTAMP` is a naive timestamp. `TIMESTAMP WITH TIME ZONE` (`TIMESTAMPTZ`) stores only an `INT64` count of microseconds since the Unix epoch, not a zone. A zone-less string cast to `TIMESTAMPTZ` is read in the configured `TimeZone`, and `TIMESTAMPTZ` values are displayed with that zone's offset ([DuckDB: Timestamp Types](https://duckdb.org/docs/current/sql/data_types/timestamp)).

In the documented examples, `AT TIME ZONE` applied to a `TIMESTAMP` returns a `TIMESTAMPTZ`, and applied to a `TIMESTAMPTZ` it returns a `TIMESTAMP`. Numeric zones such as `'0200'` are rejected, so use zone names ([DuckDB: Timestamp with Time Zone Functions](https://duckdb.org/docs/current/sql/functions/timestamptz)).

```sql
-- Example schema: events(id, created_at TIMESTAMPTZ). Requires the ICU extension.
-- Events on 2026-10-25 in Europe/Vienna, a 25-hour day. Boundaries are converted, not the column.
SELECT id FROM events
WHERE created_at >= TIMESTAMP '2026-10-25 00:00' AT TIME ZONE 'Europe/Vienna'
  AND created_at <  TIMESTAMP '2026-10-26 00:00' AT TIME ZONE 'Europe/Vienna';
```

Arithmetic and binning on `TIMESTAMPTZ` use the configured zone. A local result that falls in a daylight saving gap is moved forward, as in PostgreSQL. The documentation shows `TIMESTAMPTZ '2025-03-29 02:30:00+01' + INTERVAL '1 day'` returning `2025-03-30 03:30:00+02` ([DuckDB: Timestamp with Time Zone Functions](https://duckdb.org/docs/current/sql/functions/timestamptz)). If daylight saving bins look wrong, check the `TimeZone` and `Calendar` settings ([DuckDB: Timestamp Types](https://duckdb.org/docs/current/sql/data_types/timestamp)).

## Pagination

`LIMIT` and `OFFSET` work as usual, `LIMIT 10%` takes a share of the rows, and results are not deterministic without `ORDER BY` ([DuckDB: LIMIT and OFFSET](https://duckdb.org/docs/current/sql/query_syntax/limit)). The documentation says nothing about `OFFSET` cost, so do not assume it is cheap.

DuckDB sorts `NULLS LAST` by default for both `ASC` and `DESC`. PostgreSQL puts nulls first on `DESC`, and `default_null_order = 'NULLS_LAST_ON_ASC_FIRST_ON_DESC'` matches it. Text sorts by binary UTF-8 values unless a `COLLATE` is given ([DuckDB: ORDER BY](https://duckdb.org/docs/current/sql/query_syntax/orderby)).

Comparisons of `STRUCT` values are lexicographic, and a row written as `(a, b)` is a `STRUCT`. In those comparisons `NULL` is treated as larger than every other value, which differs from the unknown result of a SQL row comparison in PostgreSQL ([DuckDB: STRUCT Type](https://duckdb.org/docs/current/sql/data_types/struct)). The documentation shows no keyset pagination example, so use the expanded predicate from [universal-correctness.md](universal-correctness.md) unless the row form has been tested on the target version.

## JSON

`->` returns a `JSON` value, so a string result keeps its quotes. `->>` returns `VARCHAR`. Both work only when the input has the `JSON` logical type, not plain `VARCHAR` ([DuckDB: JSON Processing Functions](https://duckdb.org/docs/current/data/json/json_functions)).

The arrow operators have low precedence. Parenthesize them in comparisons; in a `WHERE` clause, `AND` and `OR` bind more tightly than the arrow, so `WHERE 1 = 1 AND j->>'field' IS NOT NULL` fails. `json_extract_string` avoids the problem ([DuckDB: JSON Processing Functions](https://duckdb.org/docs/current/data/json/json_functions)).

```sql
-- Example schema: orders(j JSON).
SELECT * FROM orders WHERE (j ->> '$.status') = 'paid';
SELECT * FROM orders WHERE json_extract_string(j, '$.status') = 'paid';
```

DuckDB supports two path syntaxes, JSONPath (`$.duck[0]`, with `[#-1]` for the last element) and JSON Pointer (`/duck/0`), and the documentation advises picking one. It does not support the full JSONPath syntax. JSON values are indexed from 0, while `LIST` and `ARRAY` values are indexed from 1 ([DuckDB: JSON Overview](https://duckdb.org/docs/current/data/json/overview), [DuckDB: JSON Processing Functions](https://duckdb.org/docs/current/data/json/json_functions)).

## CTEs and window functions

DuckDB materializes a CTE by default. It inlines one only when all of these hold: it is referenced once, contains no `VOLATILE` function, is declared `AS NOT MATERIALIZED`, and performs no grouped aggregation. Even then inlining is not always possible. `AS MATERIALIZED` forces materialization, and the documentation advises against explicit hints in general. This differs from PostgreSQL 12 and later, which inlines a single-use CTE by default ([DuckDB: WITH Clause](https://duckdb.org/docs/current/sql/query_syntax/with)).

A recursive CTE must be written so that it terminates, and cyclic graphs need explicit cycle detection. Mutually recursive CTEs are not supported ([DuckDB: WITH Clause](https://duckdb.org/docs/current/sql/query_syntax/with)).

`QUALIFY` filters the results of window functions, much as `HAVING` filters aggregates. It follows the `WINDOW` clause and precedes `ORDER BY`, and it replaces a wrapping subquery ([DuckDB: QUALIFY Clause](https://duckdb.org/docs/current/sql/query_syntax/qualify)).

```sql
-- Example schema: orders(id, customer_id, created_at). Latest order per customer.
SELECT customer_id, id AS order_id, created_at,
       row_number() OVER (PARTITION BY customer_id ORDER BY created_at DESC, id DESC) AS rn
FROM orders
QUALIFY rn = 1;
```

## Upsert

`INSERT ... ON CONFLICT` acts on conflicts from `UNIQUE` or `PRIMARY KEY` constraints, with `DO NOTHING` or `DO UPDATE`. The conflict target is the column group of an index or uniqueness constraint, and without one the table's `PRIMARY KEY` is the target. `EXCLUDED` holds the row proposed for insertion. `INSERT OR REPLACE` updates every column of the existing row. `RETURNING` returns the inserted rows ([DuckDB: INSERT Statement](https://duckdb.org/docs/current/sql/statements/insert)).

`MERGE INTO` (1.4.0 and later) is an alternative that needs no primary key. It supports `WHEN MATCHED` with `UPDATE` or `DELETE`, `WHEN NOT MATCHED` with `INSERT` (also `BY NAME`), `WHEN NOT MATCHED BY SOURCE THEN DELETE`, and `RETURNING merge_action` ([DuckDB: MERGE INTO Statement](https://duckdb.org/docs/current/sql/statements/merge_into)). The page does not say what happens when several source rows match one target row, so deduplicate the source first.

Updates to an indexed column run as a delete followed by an insert, one chunk of 2048 rows at a time. A bulk update that changes primary key values, such as incrementing a key across 3,000 rows, can fail with a duplicate key error because the checks run before later chunks are processed. Foreign key checks can also be evaluated too eagerly ([DuckDB: Indexes](https://duckdb.org/docs/current/sql/indexes), [DuckDB: Constraints](https://duckdb.org/docs/current/sql/constraints)). The indexes page describes a workaround.

## Transactions and DDL

DuckDB supports ACID transactions with snapshot isolation, and the documentation says it guarantees repeatable reads. A multi-statement batch runs in one implicit transaction, and a failing statement rolls back the earlier statements of the batch ([DuckDB: Transactions](https://duckdb.org/docs/current/sql/statements/transactions)). The transactions page does not say whether `CREATE`, `ALTER`, or `DROP` roll back, so do not assume they do.

One process can read and write a database, or many processes can read it, but not both. Several writer threads inside one process are allowed. Two transactions that change the same row conflict, and the later one fails with a conflict error that is handled by rerunning the transaction. Appends never conflict. Writing from several processes needs the Quack remote protocol, which the documentation marks as beta ([DuckDB: Concurrency](https://duckdb.org/docs/current/connect/concurrency)).

Indexes work differently from transactional row stores. DuckDB creates an ART index automatically for each `PRIMARY KEY` or `UNIQUE` constraint, and an explicit one mainly serves constraint checks and very selective (under about 0.1% of rows) point queries. Indexes slow loading and updates, and an ART index must fit in memory while it is created. Min-max (zonemap) indexes are created automatically for general-purpose types ([DuckDB: Indexes](https://duckdb.org/docs/current/sql/indexes)). Do not carry index advice over from PostgreSQL, and see the analytical levers in [performance-workflow.md](performance-workflow.md).

## Plan inspection

Read this section before running any plan command. The command class is in [safety-and-execution.md](safety-and-execution.md).

- `EXPLAIN <query>` shows the plan without executing the query, with estimated cardinalities per operator. It is the form to use on `INSERT`, `UPDATE`, `DELETE`, and `MERGE` ([DuckDB: EXPLAIN](https://duckdb.org/docs/current/sql/statements/profiling)).
- `EXPLAIN ANALYZE <query>` executes the query and reports actual cardinalities and cumulative wall-clock time per operator ([DuckDB: EXPLAIN](https://duckdb.org/docs/current/sql/statements/profiling), [DuckDB: EXPLAIN ANALYZE](https://duckdb.org/docs/current/guides/meta/explain_analyze)). The documentation does not discuss `INSERT`, `UPDATE`, `DELETE`, or `MERGE` under it. Because the documented behavior is that it runs the query, treat `EXPLAIN ANALYZE` of a data change as performing the change. The time shown for operators can add up to more than the total time because operators run in parallel.
- `ROLLBACK` discards the changes a transaction made ([DuckDB: Transactions](https://duckdb.org/docs/current/sql/statements/transactions)). The documentation does not say what rollback covers outside the database's tables, so keep `EXPLAIN ANALYZE` off statements that write files or call external state.
- `EXPLAIN` and `EXPLAIN ANALYZE` accept `FORMAT` with `text`, `graphviz`, `html`, `json`, or `mermaid` ([DuckDB: Profiling](https://duckdb.org/docs/current/dev/profiling)).
- `PRAGMA enable_profiling` accepts the formats `query_tree` (default), `json`, `query_tree_optimizer`, and `no_output`. `profiling_output` sends the output to a file, so it writes a file. `profiling_mode` selects `standard`, `detailed`, or `all` metrics. The documentation says `EXPLAIN ANALYZE` executes the query and makes no such statement about the profiling pragmas ([DuckDB: Profiling](https://duckdb.org/docs/current/dev/profiling)).
- Open a database that must not be changed with `access_mode=READ_ONLY`; do not assume a writable connection can be made read-only after opening it. Where authorized, use `enable_external_access=false` to restrict extension installation/loading and external file operations, then `lock_configuration=true` to prevent later configuration changes ([DuckDB: Configuration](https://duckdb.org/docs/current/configuration/overview), [C connection configuration](https://duckdb.org/docs/current/clients/c/config)). These controls do not replace the shared authorization rules.

## Parameter binding

DuckDB prepared statements accept three placeholder styles: `?` (taken in order), `$1` (positional), and `$name` (named). `EXECUTE` supplies values positionally or as `name := value`. Not every client supports every style; the JDBC client supports only `?`. `DEALLOCATE` drops a prepared statement ([DuckDB: Prepared Statements](https://duckdb.org/docs/current/sql/query_syntax/prepared_statements)).

The page does not say whether styles can be mixed in one statement or whether a placeholder can stand in for an identifier. Use one style per statement and take table and column names from an allowlist ([universal-correctness.md](universal-correctness.md)). Take the placeholder syntax an application writes from its client library's documentation.

## Other differences

`regexp_extract` returns an empty string, not `NULL`, when nothing matches. The PostgreSQL date formatting function `to_date` does not exist; use `strptime`. A `UNION` of a boolean and an integer succeeds through a forced cast, where PostgreSQL fails ([DuckDB: PostgreSQL Compatibility](https://duckdb.org/docs/current/sql/dialect/postgresql_compatibility)).

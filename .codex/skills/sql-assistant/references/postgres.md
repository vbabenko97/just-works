# PostgreSQL

The baseline is the PostgreSQL 18 documentation, the current stable release on 2026-10-13; PostgreSQL 19 is in beta and was not used ([PostgreSQL: Documentation](https://www.postgresql.org/docs/)). Checked against the official documentation on 2026-10-13.

This overlay is loaded after the shared references and lists only what differs on PostgreSQL.

## Version and configuration

Establish the server version before relying on a version-gated rule. `version()` returns the version string, and `server_version_num` is the machine-readable form ([PostgreSQL: Information Functions](https://www.postgresql.org/docs/18/functions-info.html)). The features below depend on it:

- PostgreSQL 12 and later inline a non-recursive, side-effect-free CTE that is referenced once ([PostgreSQL 12 release notes](https://www.postgresql.org/docs/release/12.0/)).
- `MERGE` exists since 15 ([PostgreSQL 15 release notes](https://www.postgresql.org/docs/release/15.0/)).
- `MERGE ... RETURNING` with `merge_action()`, `WHEN NOT MATCHED BY SOURCE`, `JSON_TABLE`, and `JSON_VALUE`, `JSON_QUERY`, `JSON_EXISTS` exist since 17 ([PostgreSQL 17 release notes](https://www.postgresql.org/docs/release/17.0/)).
- `RETURNING old.col, new.col` exists since 18, and `EXPLAIN ANALYZE` includes `BUFFERS` automatically since 18 ([PostgreSQL 18 release notes](https://www.postgresql.org/docs/release/18.0/)).

Settings that change results or guard execution; read the current values before relying on them:

- `TimeZone` controls how `timestamptz` values are displayed and how zone-less input is read. Its built-in default is `GMT`, but `postgresql.conf` usually overrides it ([PostgreSQL: Client Connection Defaults](https://www.postgresql.org/docs/18/runtime-config-client.html)).
- `statement_timeout` and `lock_timeout` default to 0, which means no limit. A DDL statement that waits for a lock waits indefinitely unless `lock_timeout` is set ([PostgreSQL: Client Connection Defaults](https://www.postgresql.org/docs/18/runtime-config-client.html), [PostgreSQL: Explicit Locking](https://www.postgresql.org/docs/18/explicit-locking.html)).
- `default_transaction_read_only` only sets the default for new transactions ([PostgreSQL: Client Connection Defaults](https://www.postgresql.org/docs/18/runtime-config-client.html)).
- `plan_cache_mode` decides whether a prepared statement uses generic or custom plans ([PostgreSQL: PREPARE](https://www.postgresql.org/docs/18/sql-prepare.html)).
- `pg_stat_statements` is an extension. It needs `shared_preload_libraries`, a server restart, `compute_query_id` set to `auto` or `on`, and `CREATE EXTENSION` in each database where its view is read ([PostgreSQL: pg_stat_statements](https://www.postgresql.org/docs/18/pgstatstatements.html)).

## Identifiers and quoting

Unquoted identifiers fold to lower case, and a quoted identifier is case-sensitive. `FOO`, `foo`, and `"foo"` are the same name, while `"Foo"` is a different one ([PostgreSQL: Lexical Structure](https://www.postgresql.org/docs/18/sql-syntax-lexical.html)). A table created as `"Orders"` must be written `"Orders"` in every later reference, because an unquoted `Orders` folds to `orders`.

Identifiers longer than 63 bytes are truncated by default (`NAMEDATALEN` is 64). A double quote inside a quoted identifier is written as two double quotes, and a quoted identifier is never a key word, so `"select"` is a valid column name ([PostgreSQL: Lexical Structure](https://www.postgresql.org/docs/18/sql-syntax-lexical.html)).

## Types and casts

Integer division truncates toward zero: `5 / 2` is `2` and `(-5) / 2` is `-2`. If either operand is `numeric`, the result keeps the fraction: `5.0 / 2` is `2.5000000000000000` ([PostgreSQL: Mathematical Functions](https://www.postgresql.org/docs/18/functions-math.html)).

`CAST(x AS type)` is the SQL standard form, and `x::type` is historical PostgreSQL syntax with the same meaning ([PostgreSQL: Value Expressions](https://www.postgresql.org/docs/18/sql-expressions.html)).

Implicit conversions follow general rules and the casts stored in the system catalogs, and an untyped string literal starts as type `unknown` and is resolved from context ([PostgreSQL: Type Conversion](https://www.postgresql.org/docs/18/typeconv-overview.html)). When a parameter type is not given, the server infers it from the first place the parameter is used, so add an explicit cast such as `$1::bigint` where the type matters ([PostgreSQL: PREPARE](https://www.postgresql.org/docs/18/sql-prepare.html), [PostgreSQL: Command Execution Functions](https://www.postgresql.org/docs/18/libpq-exec.html)).

## Time zones and temporal types

`timestamp` means `timestamp without time zone` and `timestamptz` means `timestamp with time zone`. Input for `timestamp` silently drops any zone in the string: `TIMESTAMP '2004-10-19 10:23:54+02'` is read as `2004-10-19 10:23:54`. A `timestamptz` value is stored as UTC and displayed in the session `TimeZone` ([PostgreSQL: Date/Time Types](https://www.postgresql.org/docs/18/datatype-datetime.html)).

`AT TIME ZONE` converts in both directions. Applied to a `timestamp`, it reads the value as local time in the named zone and returns a `timestamptz`. Applied to a `timestamptz`, it returns the `timestamp` that a clock in that zone shows ([PostgreSQL: Date/Time Functions](https://www.postgresql.org/docs/18/functions-datetime.html)). Without `AT TIME ZONE`, conversions between the two types use the session `TimeZone` ([PostgreSQL: Date/Time Types](https://www.postgresql.org/docs/18/datatype-datetime.html)).

```sql
-- Example schema: events(id, created_at timestamptz).
-- Events on 2026-10-25 in Europe/Vienna, a 25-hour day. Boundaries are converted, not the column.
SELECT id FROM events
WHERE created_at >= TIMESTAMP '2026-10-25 00:00' AT TIME ZONE 'Europe/Vienna'
  AND created_at <  TIMESTAMP '2026-10-26 00:00' AT TIME ZONE 'Europe/Vienna';
```

Use IANA zone names such as `America/New_York`. They carry daylight saving rules, while an abbreviation such as `EST` is a fixed offset, and POSIX-style zone strings use the opposite sign of ISO 8601 offsets. `TimeZone` cannot be set to an abbreviation ([PostgreSQL: Date/Time Types](https://www.postgresql.org/docs/18/datatype-datetime.html)). For a day bucket in a named zone, `date_trunc('day', ts, 'Europe/Vienna')` accepts a zone as the third argument, but only for `timestamptz` input ([PostgreSQL: Date/Time Functions](https://www.postgresql.org/docs/18/functions-datetime.html)).

An `interval` stores months, days, and microseconds separately because a day can be 23 or 25 hours at a daylight saving change. The `time with time zone` type is not recommended, because it cannot follow daylight saving rules ([PostgreSQL: Date/Time Types](https://www.postgresql.org/docs/18/datatype-datetime.html)). The input strings `now`, `today`, and `tomorrow` are converted to a fixed value when read, so in prepared statements, views, and function bodies they go stale; use `CURRENT_DATE` or `CURRENT_TIMESTAMP` there ([PostgreSQL: Date/Time Types](https://www.postgresql.org/docs/18/datatype-datetime.html)).

For calendar grouping, two-argument `date_trunc('month', value)` on a `timestamptz` uses the session `TimeZone`; on a `timestamp without time zone`, it truncates the wall-clock value without applying a zone. The database host's time zone does not establish the connection's setting. Confirm the column type and reporting zone, then use an explicit supported zone conversion or the version-supported time-zone argument to `date_trunc` ([PostgreSQL: Date/Time Functions](https://www.postgresql.org/docs/18/functions-datetime.html#FUNCTIONS-DATETIME-TRUNC)).

## Pagination

`LIMIT` without an `ORDER BY` that gives a unique order returns an unpredictable subset, and a different `LIMIT` or `OFFSET` can change the plan and the row order. Rows skipped by `OFFSET` are still computed, so a large `OFFSET` is slow ([PostgreSQL: LIMIT and OFFSET](https://www.postgresql.org/docs/18/queries-limit.html)). `FETCH FIRST n ROWS ONLY` is the standard spelling, and `WITH TIES` requires `ORDER BY` ([PostgreSQL: SELECT](https://www.postgresql.org/docs/18/sql-select.html)).

A row-value comparison compares left to right and stops at the first unequal or null pair. A null in that pair makes the result unknown, so the row is dropped ([PostgreSQL: Row and Array Comparisons](https://www.postgresql.org/docs/18/functions-comparisons.html)). The short keyset form `WHERE (created_at, id) > ($1, $2) ORDER BY created_at, id` is therefore correct only when every sort column is `NOT NULL` and all are sorted in the same direction. Otherwise use the expanded form from [universal-correctness.md](universal-correctness.md).

By default, nulls sort as larger than any other value: `NULLS LAST` for `ASC` and `NULLS FIRST` for `DESC` ([PostgreSQL: Sorting Rows](https://www.postgresql.org/docs/18/queries-order.html)).

## JSON

Prefer `jsonb` unless the exact input text or key order must be kept. `json` stores the input text with its whitespace, key order, and duplicate keys. `jsonb` drops whitespace, does not keep key order, keeps only the last value of a duplicate key, prints numbers without E notation (`1.230e-5` becomes `0.00001230`), and rejects `\u0000` ([PostgreSQL: JSON Types](https://www.postgresql.org/docs/18/datatype-json.html)).

`->` returns `json` or `jsonb`, and `->>` returns `text`. Extraction returns `NULL` instead of failing when the key or element does not exist ([PostgreSQL: JSON Functions](https://www.postgresql.org/docs/18/functions-json.html)). Cast the `->>` result before a numeric comparison.

```sql
-- Example schema: orders(payload jsonb).
WHERE payload ->> 'qty' > 10              -- ->> returns text, not a number
WHERE (payload ->> 'qty')::int > 10       -- numeric comparison
WHERE payload @> '{"status": "paid"}'     -- containment, jsonb only
```

Containment (`@>`) exists only for `jsonb`. Array element order does not matter, and a document does not contain a nested value unless the nesting matches ([PostgreSQL: JSON Types](https://www.postgresql.org/docs/18/datatype-json.html)). The default GIN operator class `jsonb_ops` supports `?`, `?|`, `?&`, `@>`, `@?`, and `@@`. `jsonb_path_ops` is usually smaller but does not support the key-exists operators ([PostgreSQL: JSON Types](https://www.postgresql.org/docs/18/datatype-json.html)). Whether an index helps a given query needs a plan ([performance-workflow.md](performance-workflow.md)).

## CTEs and window functions

A non-recursive, side-effect-free CTE referenced once is folded into the parent query. A CTE referenced more than once is evaluated once as written, and the parent's restrictions are not pushed into it. `MATERIALIZED` and `NOT MATERIALIZED` override both defaults ([PostgreSQL: WITH Queries](https://www.postgresql.org/docs/18/queries-with.html)).

A data-modifying CTE runs exactly once and to completion, whether or not the main query reads it. All sub-statements share one snapshot and cannot see each other's changes, so only `RETURNING` output passes rows between them, and their order is unpredictable. Updating the same row twice in one statement is not supported ([PostgreSQL: WITH Queries](https://www.postgresql.org/docs/18/queries-with.html)). A recursive CTE needs a guaranteed end; `UNION` does not stop a cycle when rows differ in a depth or path column. Use `CYCLE` on PostgreSQL 14+ or explicit visited-path detection on older releases ([PostgreSQL: WITH Queries](https://www.postgresql.org/docs/18/queries-with.html), [PostgreSQL 14 release notes](https://www.postgresql.org/docs/release/14.0/)).

With `ORDER BY`, the default window frame ends at the last peer of the current row, so tied rows share one value. Without `ORDER BY`, the frame is the whole partition ([PostgreSQL: Value Expressions](https://www.postgresql.org/docs/18/sql-expressions.html)).

```sql
WITH vals(v) AS (VALUES (1), (2), (2), (3))
SELECT v,
       sum(v) OVER (ORDER BY v)                        AS peer_total,  -- 1, 5, 5, 8
       sum(v) OVER (ORDER BY v ROWS UNBOUNDED PRECEDING) AS row_total   -- 1, 3, 5, 8
FROM vals;
```

`DISTINCT ON (a)` keeps the first row per `a`, which is unpredictable without an `ORDER BY` that starts with the same expressions ([PostgreSQL: SELECT](https://www.postgresql.org/docs/18/sql-select.html)). `count(*) FILTER (WHERE ...)` restricts the rows one aggregate sees ([PostgreSQL: Value Expressions](https://www.postgresql.org/docs/18/sql-expressions.html)).

## Upsert

`INSERT ... ON CONFLICT DO UPDATE` needs a conflict target. The arbiter must be a non-deferrable unique index or unique constraint; exclusion constraints are not supported as arbiters with `DO UPDATE`, and an inference that finds no matching index raises an error. `DO NOTHING` accepts an omitted target and then handles conflicts with all usable constraints. `EXCLUDED` holds the row proposed for insertion ([PostgreSQL: INSERT](https://www.postgresql.org/docs/18/sql-insert.html)).

If the proposed rows repeat the same key, `DO UPDATE` raises a cardinality violation, because one statement may not affect a row twice. Deduplicate the input first ([PostgreSQL: INSERT](https://www.postgresql.org/docs/18/sql-insert.html)).

```sql
-- Example schema: prices(sku text primary key, amount numeric).
INSERT INTO prices (sku, amount) VALUES ('a', 1), ('a', 2)   -- repeated key: error
ON CONFLICT (sku) DO UPDATE SET amount = EXCLUDED.amount;
```

`DO UPDATE` guarantees an atomic insert or update even under concurrency. `RETURNING` lists only rows that were inserted or updated, and a `DO UPDATE ... WHERE` that is false still locks the row but does not return it ([PostgreSQL: INSERT](https://www.postgresql.org/docs/18/sql-insert.html), [PostgreSQL: Transaction Isolation](https://www.postgresql.org/docs/18/transaction-iso.html)). The statement computes `nextval` defaults before detecting a conflict, so sequences develop gaps ([PostgreSQL: Sequence Functions](https://www.postgresql.org/docs/18/functions-sequence.html)).

`MERGE` (15 and later) does not guarantee that an insert or an update happens. If a concurrent transaction inserts a conflicting row, `MERGE` raises a unique violation and does not retry its `MATCHED` conditions. The two statements are not interchangeable ([PostgreSQL: Transaction Isolation](https://www.postgresql.org/docs/18/transaction-iso.html), [PostgreSQL: MERGE](https://www.postgresql.org/docs/18/sql-merge.html)). When one target row matches several source rows, a repeated insert causes a unique violation and a repeated update or delete causes a cardinality violation ([PostgreSQL: MERGE](https://www.postgresql.org/docs/18/sql-merge.html)).

## Transactions and DDL

The default isolation level is Read Committed. At Repeatable Read and Serializable, the application must retry on serialization failures, which return SQLSTATE `40001` ([PostgreSQL: Transaction Isolation](https://www.postgresql.org/docs/18/transaction-iso.html)).

`TRUNCATE` rolls back with its transaction, but it is not MVCC-safe, and it takes an `ACCESS EXCLUSIVE` lock that blocks all other access to the table ([PostgreSQL: TRUNCATE](https://www.postgresql.org/docs/18/sql-truncate.html)). Locks are held until the transaction ends ([PostgreSQL: Explicit Locking](https://www.postgresql.org/docs/18/explicit-locking.html)).

`ALTER TABLE` takes an `ACCESS EXCLUSIVE` lock unless its documentation says otherwise. `SET STATISTICS` and `VALIDATE CONSTRAINT` take `SHARE UPDATE EXCLUSIVE`, and `ADD FOREIGN KEY` takes `SHARE ROW EXCLUSIVE`. `ADD COLUMN` with a non-volatile default does not rewrite the table, while a volatile default or a column type change usually does. Adding a constraint as `NOT VALID` and validating it afterwards avoids a long exclusive lock ([PostgreSQL: ALTER TABLE](https://www.postgresql.org/docs/18/sql-altertable.html)).

Plain `CREATE INDEX` blocks writes to the table while it builds. `CREATE INDEX CONCURRENTLY` allows writes, takes longer, and cannot run inside a transaction block. If it fails it leaves an `INVALID` index that still adds update cost, so drop it and retry, or use `REINDEX INDEX CONCURRENTLY` ([PostgreSQL: CREATE INDEX](https://www.postgresql.org/docs/18/sql-createindex.html)). `VACUUM` also cannot run in a transaction block, and `VACUUM FULL` rewrites the table under an `ACCESS EXCLUSIVE` lock ([PostgreSQL: VACUUM](https://www.postgresql.org/docs/18/sql-vacuum.html)).

## Plan inspection

Read this section before running any plan command. The command class is in [safety-and-execution.md](safety-and-execution.md).

- `EXPLAIN <statement>` plans the statement and does not execute it. The `ANALYZE` option defaults to `FALSE`, and only `ANALYZE` makes the statement run. Because the statement is only planned, it changes no table data, so it is the form to use on `INSERT`, `UPDATE`, `DELETE`, `MERGE`, and `CREATE TABLE AS`. Check the option list first: `EXPLAIN (ANALYZE)`, `EXPLAIN ANALYZE`, and `EXPLAIN (ANALYZE true)` all execute ([PostgreSQL: EXPLAIN](https://www.postgresql.org/docs/18/sql-explain.html)).
- `EXPLAIN (GENERIC_PLAN)` accepts `$1`, `$2` placeholders and shows a plan that does not depend on their values. It does not execute the statement and cannot be combined with `ANALYZE` ([PostgreSQL: EXPLAIN](https://www.postgresql.org/docs/18/sql-explain.html)).
- `EXPLAIN ANALYZE` executes the statement. It discards the rows a `SELECT` would return, but all other side effects happen, so on `INSERT`, `UPDATE`, `DELETE`, `MERGE`, `CREATE TABLE AS`, or `EXECUTE` it changes data, takes the locks the statement takes, and costs what it costs. A `SELECT` that calls a function with side effects runs that function ([PostgreSQL: EXPLAIN](https://www.postgresql.org/docs/18/sql-explain.html)). It adds timing overhead, and on PostgreSQL 18 it includes `BUFFERS` automatically ([PostgreSQL 18 release notes](https://www.postgresql.org/docs/release/18.0/)).
- Wrapping `EXPLAIN ANALYZE` in `BEGIN; ... ROLLBACK;` is the documented way to keep table changes from persisting ([PostgreSQL: EXPLAIN](https://www.postgresql.org/docs/18/sql-explain.html)). The rollback does not return sequence values obtained with `nextval`, and `setval` changes are not undone ([PostgreSQL: Sequence Functions](https://www.postgresql.org/docs/18/functions-sequence.html)). Effects outside the transaction, such as a function that calls an external service, are not documented as undone. Locks stay held until the rollback.
- In a read-only transaction, `EXPLAIN ANALYZE` of an `INSERT`, `UPDATE`, `DELETE`, or `MERGE` that writes to a non-temporary table, or of `CREATE TABLE AS`, is rejected. Starting with `BEGIN READ ONLY` guards against an accidental write, but the documentation calls this a high-level notion of read-only that does not prevent all writes to disk ([PostgreSQL: SET TRANSACTION](https://www.postgresql.org/docs/18/sql-set-transaction.html)). This is a guard rail, not a permission boundary; the enforcement boundary is a database role without write privileges.
- Set `statement_timeout` before any command that executes a statement. It aborts any statement that runs longer than the limit, and setting it in `postgresql.conf` is not recommended because it affects all sessions ([PostgreSQL: Client Connection Defaults](https://www.postgresql.org/docs/18/runtime-config-client.html)).
- The `ANALYZE` command (without `EXPLAIN`) collects statistics and stores them in `pg_statistic`, so it writes. It needs only a read lock on the table ([PostgreSQL: ANALYZE](https://www.postgresql.org/docs/18/sql-analyze.html)). Treat it, `VACUUM`, and `VACUUM (ANALYZE)` as maintenance writes.
- Reading the `pg_stat_statements` view only reads statistics. Its normalized query text shows `$1` in place of constants. `pg_stat_statements_reset()` discards the collected statistics and is a write, executable by superusers by default ([PostgreSQL: pg_stat_statements](https://www.postgresql.org/docs/18/pgstatstatements.html)).

## Parameter binding

Server-side placeholders are `$1`, `$2`, and so on. They are used in `PREPARE` and in the extended query protocol, where `Parse` takes the text and `Bind` supplies the values ([PostgreSQL: PREPARE](https://www.postgresql.org/docs/18/sql-prepare.html), [PostgreSQL: Message Flow](https://www.postgresql.org/docs/18/protocol-flow.html)). With `PQexecParams`, the values travel separately from the command text, so they need no quoting or escaping, and the string may hold at most one command ([PostgreSQL: Command Execution Functions](https://www.postgresql.org/docs/18/libpq-exec.html)).

The placeholder syntax an application writes belongs to its driver and can differ from `$n`. Take it from the driver's own documentation, which is outside the PostgreSQL manual.

A prepared statement lasts only for its session. After five executions, the server chooses between a custom plan for the given values and a generic plan, based on estimated cost ([PostgreSQL: PREPARE](https://www.postgresql.org/docs/18/sql-prepare.html)). Check the plan for both when a parameterized query is slow for some values.

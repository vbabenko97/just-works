# SQLite

The baseline is the SQLite documentation for release 3.54.0 (2026-10-09), the latest release listed on 2026-10-13; no newer release is listed ([SQLite: Release History](https://www.sqlite.org/changes.html)). The SQLite site does not publish version-pinned copies of its documentation, so every version requirement below is stated in the rule. Checked against the official documentation on 2026-10-13.

This overlay is loaded after the shared references and lists only what differs on SQLite.

## Version and configuration

SQLite runs inside the application, so the version that matters is the one the application links, which can differ from the command-line shell's. `SELECT sqlite_version();` returns it ([SQLite: Core Functions](https://www.sqlite.org/lang_corefunc.html)), and `PRAGMA compile_options;` lists the compile-time options of that build ([SQLite: PRAGMA](https://www.sqlite.org/pragma.html)). Check these before using a feature:

- Row values, 3.15.0 ([SQLite: Row Values](https://www.sqlite.org/rowvalue.html)).
- `ON CONFLICT` upsert, 3.24.0; several `ON CONFLICT` clauses, 3.35.0 ([SQLite: UPSERT](https://www.sqlite.org/lang_upsert.html)).
- Window functions, 3.25.0; `GROUPS` frames and `EXCLUDE`, 3.28.0 ([SQLite: Window Functions](https://www.sqlite.org/windowfunctions.html)).
- `NULLS FIRST` and `NULLS LAST`, 3.30.0 ([SQLite 3.30.0 release notes](https://www.sqlite.org/releaselog/3_30_0.html)).
- `RETURNING`, 3.35.0 ([SQLite: RETURNING](https://www.sqlite.org/lang_returning.html)). `MATERIALIZED` hints on CTEs, 3.35.0 ([SQLite: WITH](https://www.sqlite.org/lang_with.html)).
- `STRICT` tables, 3.37.0. A database file that contains one can only be read by 3.37.0 or later ([SQLite: STRICT Tables](https://www.sqlite.org/stricttables.html)).
- Built-in JSON functions and the `->` and `->>` operators, 3.38.0, unless built with `SQLITE_OMIT_JSON`; JSONB, 3.45.0; negative array indexes in `->`, 3.47.0 ([SQLite: JSON Functions](https://www.sqlite.org/json1.html)).
- Runtime control of double-quoted string literals, 3.29.0 ([SQLite: Quirks](https://www.sqlite.org/quirks.html)).

Per-connection and per-build settings that change behavior: `PRAGMA foreign_keys` is off by default and must be set on every connection, or the build must use `SQLITE_DEFAULT_FOREIGN_KEYS=1` ([SQLite: Quirks](https://www.sqlite.org/quirks.html)). The journal mode defaults to `DELETE`, and `OFF` disables rollback ([SQLite: PRAGMA](https://www.sqlite.org/pragma.html)).

## Identifiers and quoting

A name in double quotes is an identifier, and a value in single quotes is a string literal. Square brackets and backticks are accepted for compatibility with other engines ([SQLite: Keywords](https://www.sqlite.org/lang_keywords.html)).

SQLite also treats a double-quoted token that matches no identifier as a string literal, so a misspelled column silently becomes text. Writing string literals with single quotes avoids it. The misfeature can be disabled at compile time with `-DSQLITE_DQS=0` and at runtime with `SQLITE_DBCONFIG_DQS_DDL` and `SQLITE_DBCONFIG_DQS_DML`; the shell disables it by default since 3.41.0 ([SQLite: Quirks](https://www.sqlite.org/quirks.html)).

```sql
-- Example schema: users(id, name).
SELECT "nme" FROM users;   -- typo: with the misfeature enabled, returns the text 'nme' for every row
SELECT name FROM users WHERE name = 'Ann';
```

Many keywords work as unquoted identifiers, which can give surprising parses, so quote any name that is also a keyword ([SQLite: Quirks](https://www.sqlite.org/quirks.html)).

## Types and casts

The datatype belongs to the value, not the column, and the declared column type is advisory. Inserting `'wxyz'` into an `INTEGER` column stores the text without an error ([SQLite: Datatypes](https://www.sqlite.org/datatype3.html), [SQLite: Quirks](https://www.sqlite.org/quirks.html)).

A declared type sets the column affinity in this order: contains `INT` gives integer; contains `CHAR`, `CLOB`, or `TEXT` gives text; contains `BLOB` or is empty gives blob; contains `REAL`, `FLOA`, or `DOUB` gives real; anything else gives numeric. So `DECIMAL(10,2)`, `BOOLEAN`, and `DATETIME` all get numeric affinity, and numeric text that looks like a number is stored as a number, so `'000123'` becomes `123` ([SQLite: Datatypes](https://www.sqlite.org/datatype3.html), [SQLite: STRICT Tables](https://www.sqlite.org/stricttables.html)). Declare identifiers with leading zeros as `TEXT`.

A `STRICT` table accepts only the types `INT`, `INTEGER`, `REAL`, `TEXT`, `BLOB`, and `ANY`. It coerces by the affinity rules and raises `SQLITE_CONSTRAINT_DATATYPE` when a value cannot be converted without loss ([SQLite: STRICT Tables](https://www.sqlite.org/stricttables.html)).

Integer division truncates toward zero: `7/2` is `3` and `-7/2` is `-3`, while `7/2.0` is `3.5` ([SQLite: Expressions](https://www.sqlite.org/lang_expr.html)). There is no boolean type; true and false are `1` and `0`, and the keywords `TRUE` and `FALSE` exist since 3.23.0 ([SQLite: Quirks](https://www.sqlite.org/quirks.html)).

Text comparison uses `BINARY` collation unless a column or an explicit `COLLATE` says otherwise, with the left operand taking precedence. `NOCASE` and `LIKE` fold only the 26 ASCII letters ([SQLite: Datatypes](https://www.sqlite.org/datatype3.html), [SQLite: Expressions](https://www.sqlite.org/lang_expr.html)). With `d COLLATE NOCASE` and `a` binary, `d = a` ignores case but `a = d` does not.

## Time zones and temporal types

SQLite has no date or time type. Values are stored as ISO 8601 text, a Julian day number, or Unix seconds, and the date functions work in UTC internally ([SQLite: Date And Time Functions](https://www.sqlite.org/lang_datefunc.html)). Pick one representation and one zone, preferably UTC text in `YYYY-MM-DD HH:MM:SS` form, because text values compare as strings ([SQLite: Datatypes](https://www.sqlite.org/datatype3.html)).

The `localtime` modifier converts a UTC value to local time using the C library's `localtime_r()`, and `utc` converts back. Both are undefined on input that is not in the expected zone ([SQLite: Date And Time Functions](https://www.sqlite.org/lang_datefunc.html)). The result depends on the host's time zone. None of the documented modifiers takes a zone name. For a calendar day in a named zone, compute the two boundary instants in application code with a time zone database and bind them as UTC parameters.

```sql
-- Example schema: events(id, created_at TEXT) storing UTC as 'YYYY-MM-DD HH:MM:SS'.
-- Depends on the host zone: WHERE date(created_at, 'localtime') = '2026-10-25'
-- Boundaries for 2026-10-25 in Europe/Vienna (25 hours), computed outside SQLite:
SELECT id FROM events
WHERE created_at >= :start_utc   -- '2026-10-24 22:00:00'
  AND created_at <  :end_utc;    -- '2026-10-25 23:00:00'
```

A malformed or out-of-range modifier makes the whole function return `NULL`, and results are defined only from `0000-01-01` to `9999-12-31` ([SQLite: Date And Time Functions](https://www.sqlite.org/lang_datefunc.html)).

## Pagination

Use `LIMIT n OFFSET m`. Skipped rows still cost time: `OFFSET` takes time proportional to its value ([SQLite: Row Values](https://www.sqlite.org/rowvalue.html)).

Row values allow keyset pagination in one predicate, such as `WHERE (lastname, firstname, id) > (?1, ?2, ?3) ORDER BY lastname, firstname, id LIMIT 50`. With a suitable index it is much faster than `OFFSET`. A row-value comparison is `NULL` when substituting values for the `NULL`s could make it either true or false, so every sort column must be `NOT NULL` ([SQLite: Row Values](https://www.sqlite.org/rowvalue.html)).

`NULL` is smaller than every other value, so it sorts first in `ASC` and last in `DESC` order. `NULLS FIRST` and `NULLS LAST` change that from 3.30.0 on ([SQLite: Datatypes](https://www.sqlite.org/datatype3.html), [SQLite 3.30.0 release notes](https://www.sqlite.org/releaselog/3_30_0.html)).

## JSON

JSON is stored as ordinary text; there is no JSON column type. `json_valid(X)` accepts only strict RFC 8259 JSON by default, and flag `6` also accepts JSON5 and JSONB ([SQLite: JSON Functions](https://www.sqlite.org/json1.html)).

`->` returns JSON text, so a string result keeps its quotes. `->>` returns an SQL `TEXT`, `INTEGER`, `REAL`, or `NULL`. For a JSON `null`, `->` returns the text `'null'` and `->>` returns SQL `NULL` ([SQLite: JSON Functions](https://www.sqlite.org/json1.html)).

```sql
SELECT '{"a":"xyz"}' ->  '$.a';   -- '"xyz"' (JSON text)
SELECT '{"a":"xyz"}' ->> '$.a';   -- 'xyz' (SQL TEXT)
SELECT '{"a":null}'  ->> '$.a';   -- NULL
```

A path starts with `$`, and `[#-1]` selects the last array element. JSONB (3.45.0) is a binary format stored in a `BLOB`; its functions start with `jsonb_`, and applications should not read the format outside SQLite. Store JSON text as `TEXT`, because a `BLOB` that holds JSON text is ambiguous with JSONB ([SQLite: JSON Functions](https://www.sqlite.org/json1.html)).

## CTEs and window functions

Without a hint, SQLite chooses how to implement a CTE. `MATERIALIZED` (3.35.0) forces an ephemeral table, and `NOT MATERIALIZED` substitutes the CTE as a subquery at each use, which does not forbid materialization. Both are non-binding hints, and the documentation advises against them without a measured reason ([SQLite: WITH](https://www.sqlite.org/lang_with.html)). A recursive CTE needs a compound select, and its recursive part may not use aggregate or window functions. `UNION` drops repeated rows, and a `LIMIT` is a safety bound ([SQLite: WITH](https://www.sqlite.org/lang_with.html)).

Window functions (3.25.0) may appear only in the result columns and `ORDER BY` of a `SELECT`, so filter on them in an outer query, and they cannot use `DISTINCT`. The default frame with `ORDER BY` is `RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW`, which includes all peers of the current row ([SQLite: Window Functions](https://www.sqlite.org/windowfunctions.html)). `FILTER` on aggregates exists since 3.30.0 ([SQLite 3.30.0 release notes](https://www.sqlite.org/releaselog/3_30_0.html)).

## Upsert

`INSERT ... ON CONFLICT` needs a conflict target that is a `UNIQUE` or `PRIMARY KEY` constraint or a unique index. The target may be omitted only on the last `ON CONFLICT` clause. In `DO UPDATE`, an unqualified column name is the existing row's value, and `excluded.col` is the value that was proposed ([SQLite: UPSERT](https://www.sqlite.org/lang_upsert.html)). Upsert does not handle `NOT NULL`, `CHECK`, foreign key, or trigger-implemented constraint failures ([SQLite: UPSERT](https://www.sqlite.org/lang_upsert.html)).

When the insert takes its rows from a `SELECT`, the parser can read `ON` as a join clause. Give the `SELECT` a `WHERE`, even `WHERE true` ([SQLite: UPSERT](https://www.sqlite.org/lang_upsert.html)).

```sql
-- Example schema: t1(x primary key, y), t2(x, y).
INSERT INTO t1 SELECT x, y FROM t2 WHERE true
ON CONFLICT(x) DO UPDATE SET y = excluded.y;
```

`INSERT OR REPLACE` deletes the rows that cause the violation and then inserts the new row, so values of columns the statement omits are lost. Delete triggers fire only when recursive triggers are enabled ([SQLite: ON CONFLICT](https://www.sqlite.org/lang_conflict.html)). `INSERT OR IGNORE` skips the row without an error, except for foreign key violations ([SQLite: ON CONFLICT](https://www.sqlite.org/lang_conflict.html)).

`RETURNING` (3.35.0) reports inserted and updated rows of an upsert. SQLite does not guarantee the order of its rows, and the values shown do not include changes made by triggers. It cannot be used inside a trigger or as a subquery ([SQLite: RETURNING](https://www.sqlite.org/lang_returning.html)).

## Transactions and DDL

`BEGIN` is `DEFERRED` by default. A deferred transaction that starts with a read and later writes can fail with `SQLITE_BUSY` if another connection wrote first. `BEGIN IMMEDIATE` takes the write lock at the start. Only one write transaction exists at a time, and `BEGIN` does not nest, so use `SAVEPOINT` ([SQLite: Transactions](https://www.sqlite.org/lang_transaction.html)).

`ALTER TABLE` can rename a table, rename a column, add a column, and drop a column, with limits. `ADD COLUMN` cannot add a `PRIMARY KEY` or `UNIQUE` column or use `CURRENT_TIME`, `CURRENT_DATE`, `CURRENT_TIMESTAMP`, or a parenthesized expression as the default. `DROP COLUMN` fails when the column is indexed, a primary key, unique, in a foreign key, or used by a trigger or view ([SQLite: ALTER TABLE](https://www.sqlite.org/lang_altertable.html)). Other changes use the documented rebuild: with `PRAGMA foreign_keys=OFF` set before `BEGIN`, create `new_X`, copy the rows, drop `X`, rename `new_X` to `X`, recreate indexes, triggers, and views, run `PRAGMA foreign_key_check`, and commit. Renaming the old table first can corrupt references ([SQLite: ALTER TABLE](https://www.sqlite.org/lang_altertable.html)). The procedure runs its `CREATE`, `DROP`, and `RENAME` statements inside one transaction, so a failed rebuild can be rolled back.

`PRAGMA foreign_keys` has no effect inside a transaction. The parent key must be a primary key or unique, and an index on the child key columns is almost always worth having ([SQLite: Foreign Keys](https://www.sqlite.org/foreignkeys.html)).

## Plan inspection

Read this section before running any plan command. The command class is in [safety-and-execution.md](safety-and-execution.md).

- `EXPLAIN QUERY PLAN <statement>` returns a high-level plan, and `EXPLAIN <statement>` returns the virtual machine instructions. The documentation says the statement behaves as a query that returns information about how it "would have operated". It does not say "not executed" in those words, and it documents no write by these commands. The output is for interactive use only; its format changed in 3.24.0 and 3.36.0, so do not parse it ([SQLite: EXPLAIN](https://www.sqlite.org/lang_explain.html), [SQLite: EXPLAIN QUERY PLAN](https://www.sqlite.org/eqp.html)).
- Do not use `EXPLAIN` as a safety wrapper for a `PRAGMA`. Some pragmas do their work while the statement is prepared, `EXPLAIN` only changes what happens while the statement is stepped, and which pragmas run at prepare time depends on the pragma, its arguments, and the release. Those pragmas behave the same with or without the `EXPLAIN` prefix, and the documentation advises avoiding `EXPLAIN` on `PRAGMA` statements. Treat a state-changing `PRAGMA` as executed even when prefixed with `EXPLAIN` ([SQLite: EXPLAIN](https://www.sqlite.org/lang_explain.html), [SQLite: PRAGMA](https://www.sqlite.org/pragma.html)).
- In the shell, `.eqp on` runs `EXPLAIN QUERY PLAN` for each statement entered and then runs the statement itself, so it executes whatever is typed ([SQLite: EXPLAIN QUERY PLAN](https://www.sqlite.org/eqp.html)). `.explain` only changes the display format of `EXPLAIN` ([SQLite: Command Line Shell](https://www.sqlite.org/cli.html)).
- In `EXPLAIN QUERY PLAN` output, `SCAN` is a full-table scan, including one in index order, and `SEARCH` visits a subset of rows. `USING COVERING INDEX` reports that the covering-index optimization applies ([SQLite: EXPLAIN QUERY PLAN](https://www.sqlite.org/eqp.html)).
- `ANALYZE` stores statistics in the database (`sqlite_stat1`, and `sqlite_stat4` when built with `SQLITE_ENABLE_STAT4`), so it writes. `PRAGMA optimize` runs `ANALYZE` when needed and also writes; `PRAGMA optimize(-1)` lists what it would do without doing it ([SQLite: ANALYZE](https://www.sqlite.org/lang_analyze.html), [SQLite: PRAGMA](https://www.sqlite.org/pragma.html)).
- `VACUUM` rebuilds the database file and may need up to twice the database size in free disk space. It fails when the connection has an open transaction, and it can change rowids of tables without an explicit `INTEGER PRIMARY KEY`. `VACUUM INTO 'file'` leaves the original unchanged and writes a new file ([SQLite: VACUUM](https://www.sqlite.org/lang_vacuum.html)).
- `PRAGMA query_only` makes `CREATE`, `DELETE`, `DROP`, `INSERT`, and `UPDATE` fail with `SQLITE_READONLY`, but the database is not truly read-only: checkpoints and `COMMIT` still work ([SQLite: PRAGMA](https://www.sqlite.org/pragma.html)). The shell option `-readonly` opens the file read-only ([SQLite: Command Line Shell](https://www.sqlite.org/cli.html)). Neither stops another process with write access to the file; use file permissions as the enforcement boundary.

## Parameter binding

The C API accepts `?`, `?NNN`, `:name`, `@name`, and `$name` in place of literals. The leftmost parameter has index 1, a repeated named parameter reuses its first index, and `?NNN` has index NNN, up to 32766 by default. A parameter that is never bound is `NULL`, so `col = ?` with no value finds no rows ([SQLite: Binding Values](https://www.sqlite.org/c3ref/bind_blob.html), [SQLite: Expressions](https://www.sqlite.org/lang_expr.html)). A bare `?` takes the number after the largest assigned so far, so mixing the forms shifts indexes: in `WHERE a = ?2 AND b = ?`, the bare `?` is parameter 3.

The documentation describes parameters as replacing literals, so table and column names are not parameters and come from an allowlist ([SQLite: Binding Values](https://www.sqlite.org/c3ref/bind_blob.html), [universal-correctness.md](universal-correctness.md)). Wrapper libraries can differ in which forms they accept, so take the placeholder syntax from the wrapper's own documentation.

## Other differences

SQLite accepts an aggregate query whose result columns are not in `GROUP BY`. With a single `min()` or `max()`, the bare columns come from the row that held the minimum or maximum ([SQLite: Quirks](https://www.sqlite.org/quirks.html)). A query that relies on this fails or means something else on other engines.

The statement list has no `MERGE` and no `TRUNCATE` ([SQLite: SQL Language](https://www.sqlite.org/lang.html)). A column is an alias for the rowid only when its declared type is exactly `INTEGER` and it is the primary key; `INT PRIMARY KEY` is an ordinary column ([SQLite: CREATE TABLE](https://www.sqlite.org/lang_createtable.html)). A primary key column that is not an integer primary key can hold `NULL`, and `NULL` values count as distinct in `UNIQUE` constraints ([SQLite: Quirks](https://www.sqlite.org/quirks.html), [SQLite: CREATE TABLE](https://www.sqlite.org/lang_createtable.html)).

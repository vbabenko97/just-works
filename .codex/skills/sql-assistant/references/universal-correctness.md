# Universal correctness

These rules hold on every engine. Engine syntax and exceptions are in the overlays. Sources were checked on 2026-10-13.

## Result grain and joins

State what one output row represents before writing joins, for example "one row per customer" or "one row per order line".

For each join, establish whether it is one-to-one, one-to-many, or many-to-many from primary keys and unique constraints. Without a unique key on the joined side, the join can multiply rows. Some engines declare keys without enforcing them, so check the overlay before relying on a declared key.

When a query returns duplicates, find their source before changing it. Typical fixes are aggregating the many side before the join, using `EXISTS` when the other table only filters, or selecting one ranked row per group. `DISTINCT` is correct only when the duplicate rows are exact and their cause is understood; it also merges rows that are legitimately different but look identical in the selected columns.

Sums and counts after a one-to-many join count the "one" side once per match. Aggregate the many side in a subquery or CTE first, then join the result.

For "the latest row per group", rank rows with a window function partitioned by the group and ordered by the timestamp and a unique tie-breaker, then keep rank 1. Decide with the user whether ties should return one row or all tied rows (`ROW_NUMBER` versus `RANK`). A join to `MAX(created_at)` returns several rows when two rows share the maximum.

```sql
-- Example schema: customers(id), orders(id, customer_id, created_at).
SELECT customer_id, id AS order_id, created_at
FROM (
  SELECT o.*,
         ROW_NUMBER() OVER (PARTITION BY customer_id
                            ORDER BY created_at DESC, id DESC) AS rn
  FROM orders AS o
) AS ranked
WHERE rn = 1;
```

A predicate on the optional side of an outer join placed in `WHERE` removes unmatched rows if it rejects `NULL`, as `right.status = 'paid'` does. This can turn a `LEFT JOIN` into an inner join. Predicates such as `right.id IS NULL` behave differently. Put a filter in the `ON` clause when unmatched rows must stay. A condition in the `ON` clause of a `LEFT JOIN` does not remove rows from the preserved side.

These rewrites change results unless a constraint proves otherwise: `LEFT JOIN` to `INNER JOIN`, `IN (subquery)` to a join (the join adds duplicates), `OR` to `UNION` (removes duplicates) or to `UNION ALL` (duplicates rows matching both branches), and moving a predicate across an outer join.

## NULL and empty input

Comparisons with `NULL` yield unknown, and `WHERE` keeps only rows where the condition is true. `status <> 'closed'` therefore drops rows where `status` is `NULL`.

`x NOT IN (subquery)` yields `NULL`, not true, when the subquery returns any `NULL` and no match, so the query can return no rows at all. A nullable outer `x` also matters: with a nonempty subquery, `NULL NOT IN (...)` is unknown, while a correlated equality-based `NOT EXISTS` keeps that outer row. With an empty subquery, `NOT IN` is true even for a null outer value ([PostgreSQL: Subquery Expressions](https://www.postgresql.org/docs/18/functions-subquery.html)). A simple rewrite to equality-based `NOT EXISTS` preserves filtering when both compared values are non-null; otherwise establish the intended handling of outer and inner nulls and empty input explicitly.

```sql
-- Wrong when blocked_users.user_id can be NULL: returns no rows.
SELECT u.id FROM users AS u
WHERE u.id NOT IN (SELECT b.user_id FROM blocked_users AS b);

-- Returns users with no matching blocked row.
SELECT u.id FROM users AS u
WHERE NOT EXISTS (SELECT 1 FROM blocked_users AS b WHERE b.user_id = u.id);
```

In a `LEFT JOIN ... WHERE right.col IS NULL` anti-join, test a column that cannot be `NULL` in matched rows, such as the right table's primary key. Testing a nullable column also keeps matched rows whose value is `NULL`.

Equality never matches `NULL` to `NULL`, so join keys with `NULL` find no partner. Use the engine's null-safe comparison when `NULL` should match `NULL`.

Over empty input, `COUNT` returns 0 while `SUM`, `AVG`, `MIN`, and `MAX` return `NULL`. A query with `GROUP BY` over empty input returns no rows. Wrap with `COALESCE` only when 0 is the intended answer.

Guard divisions against zero denominators, for example with `NULLIF(denominator, 0)`, and check whether integer division truncates on the target engine.

## Types, collations, and casts

Establish the actual column types before writing comparisons, joins, or parameter bindings. Implicit conversions can change results, such as comparing text with numbers, and can stop the engine from using an index on the converted column.

Convert the constant or parameter to the column's type rather than wrapping the column in a cast or function. Add a cast only after deciding which semantic type is correct; a cast added just to silence an error usually hides a wrong comparison.

Use exact numeric types for money and state the rounding rule. Floating-point types do not represent most decimal fractions exactly.

Text equality, ordering, and uniqueness follow the collation. A case- or accent-insensitive collation makes `'Muller' = 'müller'` possible, and joins between columns with different collations can fail or convert.

Compare dates and timestamps as temporal types. Strings compare correctly only in a fixed, zero-padded ISO 8601 format stored as text by design.

## Time ranges and time zones

Filter time ranges as half-open intervals: `ts >= :start AND ts < :end`. `BETWEEN` includes the end value, and an end such as `23:59:59` misses fractional seconds.

Before filtering by a calendar period, establish three facts: whether the column stores an instant (a point in time) or a local date and time without a zone; the time zone in which local values were recorded; and the time zone the user's period refers to.

Apply the same check to calendar grouping, not only range filters. A monthly aggregate using `date_trunc` or its engine equivalent can place an instant in different months under different session or business zones. Establish the column type and the reporting zone before explaining or changing the bucket; see the target overlay for conversion behavior.

A calendar day in a named time zone is an interval of instants whose length can be 23, 24, or 25 hours. For example, 2026-10-25 in Europe/Vienna ends daylight saving time, so the day runs from 2026-10-24 22:00:00 UTC to 2026-10-25 23:00:00 UTC, which is 25 hours. A row at exactly 2026-10-25 23:00:00 UTC belongs to the next day.

Compute the boundaries either in SQL with the engine's zone conversion (see the overlay) or in application code with a time zone database, then compare the column with the two instants. Converting the parameters instead of the column keeps the predicate usable by indexes and partition pruning. Do not compare an instant type with a local type without an explicit conversion.

## Ordering and pagination

Without `ORDER BY`, the order of a result is unspecified, and a `LIMIT` or `TOP` without it returns arbitrary rows. When order matters, the `ORDER BY` must be total: append a unique column, such as the primary key, as the last sort key.

Keyset pagination continues after the last row of the previous page. Its predicate must use the same columns and directions as the `ORDER BY`:

```sql
-- Example schema: events(id primary key, created_at not null).
-- Illustrative placeholders and LIMIT syntax; adapt to the driver and engine.
SELECT id, created_at
FROM events
WHERE created_at > :last_created_at
   OR (created_at = :last_created_at AND id > :last_id)
ORDER BY created_at, id
LIMIT 50;
```

Some engines accept the shorter row-value form `(created_at, id) > (:last_created_at, :last_id)`; check the overlay. Mixed sort directions need the expanded form. Nullable sort columns need explicit handling because engines place `NULL` first or last differently.

Large `OFFSET` values can require processing many skipped rows; measure the cost on the target engine. Inserts or deletes between requests can shift offset pages, producing duplicates or gaps. Keyset pagination avoids that positional shift, but it does not provide a snapshot: newly inserted rows before the cursor are not visited, and updates to sort columns can move rows across it. Stable paging over one fixed dataset needs unchanging data or a single snapshot, plus a unique ordering ([SQL Server: ORDER BY clause](https://learn.microsoft.com/en-us/sql/t-sql/queries/select-order-by-clause-transact-sql?view=sql-server-ver17)).

## Parameters and dynamic SQL

Bind every value through the driver's parameter API. Do not build SQL by concatenating or interpolating user data, even escaped; escaping is fragile and cannot be relied on to prevent injection ([OWASP: SQL Injection Prevention Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/SQL_Injection_Prevention_Cheat_Sheet.html)).

Placeholder syntax belongs to the driver, not to the engine alone: `?`, `$1`, `%s`, `%(name)s`, `:name`, and `@name` all occur. When the driver is unknown, ask for it, or show the query with placeholders explicitly marked as driver-dependent. SQL-level `PREPARE` and `EXECUTE` statements are not the application's binding API.

An ordinary value placeholder cannot stand in for a table name, column name, sort direction, or keyword. Map user input to an allowlist of known names in code, then use the driver's identifier API or the engine's identifier quoting. An engine may offer a dedicated identifier-binding construct, such as Snowflake's `IDENTIFIER`; use it only as documented by its overlay and driver, with the same allowlist ([OWASP: SQL Injection Prevention Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/SQL_Injection_Prevention_Cheat_Sheet.html)).

Bind each element of an `IN` list, or use the driver's array support; do not join values into a comma-separated string. Stored procedures that build dynamic SQL by concatenation are injectable in the same way as application code.

A bound value used with `LIKE` still treats `%` and `_` as wildcards. Escape them when the user means literal text.

## Writes and upsert

Upsert syntax and semantics differ across engines, so no form is portable. Before writing one, establish the unique key that defines "the same row", what should happen when the input contains several rows for one key, and how the statement behaves with concurrent writers on the target engine.

When an `UPDATE` or `MERGE` joins to a source that can match a target row more than once, the result is an error on some engines and an arbitrary choice on others. Deduplicate the source first or prove the key is unique.

Before a data change, give the user a `SELECT` with the same predicate so they can check the affected rows. Running either statement still needs authorization ([safety-and-execution.md](safety-and-execution.md)).

## Query structure claims

CTEs, subqueries, temporary tables, window functions, correlated subqueries, `EXISTS`, `IN`, and `SELECT *` are not wrong or slow by rule. Choose the form that states the intent clearly. Any claim that one form is faster needs a plan from the target engine ([performance-workflow.md](performance-workflow.md)). `SELECT *` in application code couples the code to column order and new columns, and on columnar engines it reads every column.

## Dialect conversion

Conversion can change results without a syntax error. Review at least identifier case folding, integer division, empty strings and `NULL`, string concatenation with `NULL`, default collations, date and time types and their default zones, boolean handling, upsert semantics, and row limiting, against both the source and the target overlays. Transpiler output is a candidate until reviewed ([validation-tools.md](validation-tools.md)).

## Test inputs

When writing tests or reviewing a query, consider these inputs: `NULL` in every nullable column used in a predicate or join; empty tables and empty subquery results; duplicate keys and tied sort values; rows exactly on range boundaries; days with a daylight saving transition; one-to-many fan-out; text containing quotes, `%`, and `_`; and values at the maximum length or precision.

# PostgreSQL queries

Use the gateway for every database operation. It opens a new connection per query, validates a single read query, estimates it with `EXPLAIN (FORMAT JSON)`, and runs it in a read-only transaction with configured statement and lock timeouts.

Allowed top-level query forms are `SELECT`, `WITH`, `VALUES`, and `TABLE`. Parameterize values through the gateway's `params` argument. Do not interpolate user text into SQL. Use plain `'...'` string literals; `E'...'` and other prefixed literals are refused. Functions must be on the gateway's read-only list. A row-cap error is a failed query, not permission to use a truncated result.

A refused or failed query returns the reason, such as the guard rule, the row cap, or PostgreSQL's own error message, together with the evidence ID of the failed attempt. Repair the query from that reason; do not resend it unchanged.

Read-only transactions prohibit common writes such as `INSERT`, `UPDATE`, `DELETE`, DDL, and privilege changes, as documented by [PostgreSQL](https://www.postgresql.org/docs/current/sql-set-transaction.html). This is additional protection, not a reason to weaken role grants.

Use `describe_schema` before first querying an unfamiliar schema. Record the metric definition and filters used in the contract. Do not use `SELECT *` unless a narrow exploratory result is necessary and stays under the row cap.


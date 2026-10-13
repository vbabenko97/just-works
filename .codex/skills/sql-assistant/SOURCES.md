# Sources and authorship

Package: `sql-assistant` · Version 1.0.0 · Sources checked 2026-10-13

## Authorship

Written for this repository in October 2026. The workflow, references, and evaluation cases are original. The design follows a private research brief, which is not distributed. The brief reviewed several published SQL agent skills, including [supabase/agent-skills](https://github.com/supabase/agent-skills), [hmohamed01/SQL-Expert](https://github.com/hmohamed01/SQL-Expert), and the SQL skills in [github/awesome-copilot](https://github.com/github/awesome-copilot); its lessons shaped the structure (a small workflow, shared rules, one overlay per engine), and no text from those packages is included.

## Sources

Each overlay in `references/` names its documentation baseline and cites official documentation next to the rules it supports. The shared references cite the sources below.

| Source | URL | Used for |
|---|---|---|
| OWASP SQL Injection Prevention Cheat Sheet | https://cheatsheetseries.owasp.org/cheatsheets/SQL_Injection_Prevention_Cheat_Sheet.html | Bound parameters, allowlists for identifiers, escaping as a fragile defense |
| PostgreSQL 18: Subquery Expressions | https://www.postgresql.org/docs/18/functions-subquery.html | `NOT IN` with `NULL` in the subquery |
| SQL Server: ORDER BY clause | https://learn.microsoft.com/en-us/sql/t-sql/queries/select-order-by-clause-transact-sql?view=sql-server-ver17 | Conditions for stable `OFFSET`/`FETCH` paging |
| SQLFluff: Dialects Reference | https://docs.sqlfluff.com/en/stable/reference/dialects.html | Dialect labels, including separate `mariadb` and `duckdb` dialects |
| SQLFluff: CLI exit codes | https://docs.sqlfluff.com/en/stable/usage/cli | Success, lint findings, and operation failures |
| SQLFluff: Command reference | https://docs.sqlfluff.com/en/stable/reference/cli.html | `parse`, `lint`, and `fix` commands |
| SQLFluff: Placeholder templater | https://docs.sqlfluff.com/en/stable/configuration/templating/placeholder.html | Linting SQL with driver placeholders |
| SQLFluff: dbt templater | https://docs.sqlfluff.com/en/stable/configuration/templating/dbt.html | Compile-time database access |
| SQLGlot README | https://github.com/tobymao/sqlglot | Supported dialects (no MariaDB), lenient parser, `unsupported_level` |
| Agent Skills specification | https://agentskills.io/specification | Package layout and frontmatter |

## Maintenance

Engine documentation changes with each release, and BigQuery and Snowflake change continuously. When a target engine moves to a new release, re-check the rules in its overlay that carry a version, update the baseline line, and rerun the evaluation cases in `evals/evals.json`.

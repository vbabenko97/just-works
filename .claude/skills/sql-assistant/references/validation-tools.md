# Validation tools

SQLFluff and SQLGlot check SQL text against a dialect's grammar. They do not check that tables and columns exist, that joins have the intended cardinality, or that the statement will run. SQLGlot's parser is intentionally lenient and its authors describe it as "a transpiler, not a validator" ([SQLGlot README](https://github.com/tobymao/sqlglot)). Report every check as run with its result, skipped with the reason, or not applicable.

Sources were checked on 2026-10-13 against the SQLFluff stable documentation and the SQLGlot repository's main branch.

## Dialect names

| Engine | SQLFluff `--dialect` | SQLGlot dialect |
|---|---|---|
| PostgreSQL | `postgres` | `postgres` |
| MySQL | `mysql` | `mysql` |
| MariaDB | `mariadb` | none; skip SQLGlot |
| SQL Server | `tsql` | `tsql` |
| Oracle | `oracle` | `oracle` |
| SQLite | `sqlite` | `sqlite` |
| BigQuery | `bigquery` | `bigquery` |
| Snowflake | `snowflake` | `snowflake` |
| DuckDB | `duckdb` | `duckdb` |

SQLFluff has a separate `mariadb` dialect that inherits from `mysql`, and a `duckdb` dialect that inherits from `postgres` ([SQLFluff: Dialects Reference](https://docs.sqlfluff.com/en/stable/reference/dialects.html)). Use `mariadb` for MariaDB.

SQLGlot has no MariaDB dialect ([SQLGlot README](https://github.com/tobymao/sqlglot)). For MariaDB, report SQLGlot as skipped. Never run SQLGlot's `mysql` dialect and present the result as MariaDB validation.

Always pass the dialect explicitly. When the project configures a dialect, use it if it matches the target engine; otherwise pass the correct one and report the mismatch.

## Availability

Look for the tools in the project's existing environment first, for example `sqlfluff --version` or `python -c "import sqlglot"` using its virtual-environment executables. Do not use a package-runner command that might create or synchronize an environment just to check availability. Do not install either tool on your own initiative. When a tool is missing, report the check as skipped and give the command the user can run after installing it.

## SQLFluff

Parse a file or standard input:

```bash
sqlfluff parse --dialect postgres path/to/query.sql
sqlfluff parse --dialect tsql - < query.sql
```

Lint a file:

```bash
sqlfluff lint --dialect mariadb path/to/query.sql
```

Lint exits with 0 when no issues are found, 1 when it finds violations or a file cannot be parsed, and 2 when the operation fails, for example on a configuration error ([SQLFluff: CLI](https://docs.sqlfluff.com/en/stable/usage/cli)). The `--nofail` option forces exit code 0, so do not use it when the exit code is the evidence ([SQLFluff: lint](https://docs.sqlfluff.com/en/stable/reference/cli/lint)).

Respect trusted project SQLFluff configuration (`.sqlfluff`, `setup.cfg`, `tox.ini`, or `pyproject.toml`) for rules and templating. For standalone plain SQL, use `--templater raw`; do not activate project macros or plugins merely to inspect an untrusted snippet. Lint findings about style are not correctness findings; report them separately.

### Templated SQL and placeholders

The default templater is `jinja`; the built-in alternatives are `raw`, `python`, and `placeholder` ([SQLFluff: lint](https://docs.sqlfluff.com/en/stable/reference/cli/lint)).

When SQLFluff cannot parse the driver's placeholders directly, use the `placeholder` templater to substitute sample values; set `param_style` to match the driver ([SQLFluff: Placeholder templater](https://docs.sqlfluff.com/en/stable/configuration/templating/placeholder.html)):

| Placeholder | `param_style` |
|---|---|
| `?` | `question_mark` |
| `$1` | `numeric_dollar` |
| `:name` | `colon` |
| `:1` | `numeric_colon` |
| `%s` | `percent` |
| `%(name)s` | `pyformat` |

```ini
[sqlfluff]
templater = placeholder

[sqlfluff:templater:placeholder]
param_style = numeric_dollar
```

To lint SQL embedded in application code, copy the statement with its placeholders to a temporary file outside the repository, or pipe it to standard input, and lint it with a matching `param_style`.

dbt projects use the `dbt` templater from the separate `sqlfluff-templater-dbt` package. It reads the dbt project and profile, and when models query the database at compile time it needs database access, so it falls under [safety-and-execution.md](safety-and-execution.md); point it at a test database, not production ([SQLFluff: dbt templater](https://docs.sqlfluff.com/en/stable/configuration/templating/dbt.html)).

### Fix and format

`sqlfluff fix` and `sqlfluff format` rewrite files; since SQLFluff 3.0, applying fixes without confirmation is the default ([SQLFluff: fix](https://docs.sqlfluff.com/en/stable/reference/cli/fix)). Run them only when the task authorizes editing those files, and review the diff. Reject changes that add, remove, or re-case quoted identifiers on engines where quoting changes the name's meaning (see the overlay's "Identifiers and quoting" section).

## SQLGlot

Use SQLGlot for structural inspection, such as listing the tables a statement references, and for controlled transpilation between dialects. Name both dialects every time.

```python
import sqlglot
from sqlglot import exp

tree = sqlglot.parse_one(sql, dialect="postgres")
tables = sorted({table.sql(dialect="postgres") for table in tree.find_all(exp.Table)})

candidate = sqlglot.transpile(
    sql,
    read="postgres",
    write="snowflake",
    unsupported_level=sqlglot.ErrorLevel.RAISE,
)[0]
```

By default, SQLGlot warns about constructs it cannot translate; `unsupported_level=sqlglot.ErrorLevel.RAISE` makes them raise instead ([SQLGlot README](https://github.com/tobymao/sqlglot)). A successful transpilation produces candidate SQL. Review it against the source and target overlays for semantics that syntax translation does not cover, then lint it with SQLFluff using the target dialect.

When the source or target engine has no SQLGlot dialect, skip SQLGlot and convert by hand using both overlays.

## Engine-native checks

The engine's own parser and planner are the final static check. Their non-executing options are listed in [safety-and-execution.md](safety-and-execution.md#plan-commands-by-engine) and in each overlay. They need an authorized connection, and some of them write or cost money; answer the questions in [safety-and-execution.md](safety-and-execution.md#before-any-native-check) before running one.

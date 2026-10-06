"""Conservative read-query validation for the analyst gateway.

This is a deliberately small tokenizer, not a SQL parser or a security boundary.
The database role and read-only transaction are the security boundary; this module
rejects syntax the gateway has no reason to support.
"""

from __future__ import annotations

import re
from dataclasses import dataclass


class QueryGuardError(ValueError):
    """Raised when a query is outside the gateway's read-only subset."""


@dataclass(frozen=True)
class Token:
    kind: str
    value: str


_IDENTIFIER = re.compile(r"[A-Za-z_][A-Za-z0-9_$]*")
_SAFE_FUNCTIONS = frozenset(
    {
        "abs",
        "age",
        "any_value",
        "array_agg",
        "array_length",
        "array_position",
        "array_to_string",
        "avg",
        "bool_and",
        "bool_or",
        "cardinality",
        "ceil",
        "ceiling",
        "char_length",
        "coalesce",
        "concat",
        "concat_ws",
        "corr",
        "count",
        "covar_pop",
        "covar_samp",
        "cume_dist",
        "current_date",
        "current_time",
        "current_timestamp",
        "date",
        "date_bin",
        "date_part",
        "date_trunc",
        "dense_rank",
        "every",
        "exp",
        "extract",
        "first_value",
        "floor",
        "generate_series",
        "greatest",
        "grouping",
        "initcap",
        "isfinite",
        "json_agg",
        "json_array_elements",
        "json_array_elements_text",
        "json_array_length",
        "json_build_array",
        "json_build_object",
        "json_extract_path_text",
        "json_typeof",
        "jsonb_agg",
        "jsonb_array_elements",
        "jsonb_array_elements_text",
        "jsonb_array_length",
        "jsonb_build_array",
        "jsonb_build_object",
        "jsonb_each",
        "jsonb_extract_path_text",
        "jsonb_object_keys",
        "jsonb_typeof",
        "justify_days",
        "justify_interval",
        "lag",
        "last_value",
        "lead",
        "least",
        "left",
        "length",
        "ln",
        "log",
        "lower",
        "lpad",
        "make_date",
        "make_interval",
        "make_timestamp",
        "make_timestamptz",
        "max",
        "min",
        "mod",
        "mode",
        "now",
        "ntile",
        "nullif",
        "octet_length",
        "percent_rank",
        "percentile_cont",
        "percentile_disc",
        "position",
        "power",
        "rank",
        "regexp_match",
        "regexp_replace",
        "regexp_split_to_array",
        "regr_count",
        "regr_intercept",
        "regr_r2",
        "regr_slope",
        "replace",
        "reverse",
        "right",
        "round",
        "row_number",
        "rpad",
        "sign",
        "split_part",
        "sqrt",
        "stddev",
        "stddev_pop",
        "stddev_samp",
        "string_agg",
        "string_to_array",
        "strpos",
        "substring",
        "sum",
        "timezone",
        "to_char",
        "to_date",
        "to_json",
        "to_jsonb",
        "to_number",
        "to_timestamp",
        "trim",
        "trunc",
        "unnest",
        "upper",
        "variance",
        "var_pop",
        "var_samp",
        "width_bucket",
    }
)
# A single read statement can only change data through a data-modifying WITH
# entry or SELECT INTO. The remaining words are reserved, so they can never be
# column names, and they have no place in a read query.
_FORBIDDEN_WORDS = frozenset(
    {
        "analyse",
        "analyze",
        "create",
        "delete",
        "do",
        "grant",
        "insert",
        "into",
        "merge",
        "update",
    }
)
_LOCKING_WORDS = frozenset({"key", "no", "share", "update"})
_FORBIDDEN_FUNCTIONS = frozenset(
    {
        "current_setting",
        "dblink",
        "dblink_connect",
        "dblink_exec",
        "format",
        "lo_export",
        "lo_import",
        "pg_cancel_backend",
        "pg_conf_load_time",
        "pg_current_logfile",
        "pg_ls_dir",
        "pg_logdir_ls",
        "pg_read_binary_file",
        "pg_read_file",
        "pg_reload_conf",
        "pg_rotate_logfile",
        "pg_sleep",
        "pg_stat_file",
        "pg_terminate_backend",
        "set_config",
    }
)
# Keywords that may be followed by an opening parenthesis without calling a function.
_NON_FUNCTION_WORDS = frozenset(
    {
        "all",
        "and",
        "any",
        "array",
        "as",
        "between",
        "by",
        "case",
        "cast",
        "cube",
        "distinct",
        "else",
        "end",
        "except",
        "exists",
        "filter",
        "from",
        "group",
        "having",
        "ilike",
        "in",
        "intersect",
        "is",
        "join",
        "lateral",
        "like",
        "limit",
        "materialized",
        "not",
        "null",
        "offset",
        "on",
        "only",
        "or",
        "order",
        "over",
        "partition",
        "rollup",
        "row",
        "rows",
        "select",
        "sets",
        "similar",
        "some",
        "table",
        "then",
        "union",
        "using",
        "values",
        "when",
        "where",
        "window",
        "with",
        "zone",
    }
)
# Type names whose parenthesis holds a modifier, as in numeric(10, 2).
_TYPE_MODIFIER_WORDS = frozenset(
    {
        "bit",
        "bpchar",
        "char",
        "character",
        "decimal",
        "float",
        "interval",
        "numeric",
        "time",
        "timestamp",
        "timestamptz",
        "timetz",
        "varbit",
        "varchar",
        "varying",
    }
)


def _tokenize(sql: str) -> list[Token]:
    tokens: list[Token] = []
    index = 0
    length = len(sql)
    while index < length:
        char = sql[index]
        if char.isspace():
            index += 1
            continue
        if sql.startswith("--", index) or sql.startswith("/*", index):
            raise QueryGuardError("SQL comments are not allowed")
        if char == "'":
            # E'', U&'', B'', X'' and N'' literals follow different escape rules.
            # E'\'' hides a quote from this tokenizer, so refuse every prefix.
            if index and (sql[index - 1].isalnum() or sql[index - 1] in "_$&"):
                raise QueryGuardError(
                    "prefixed string literals such as E'...' are not allowed; use a plain "
                    "'...' literal or a query parameter"
                )
            index += 1
            while index < length:
                if sql[index] == "'":
                    index += 1
                    if index < length and sql[index] == "'":
                        index += 1
                        continue
                    break
                index += 1
            else:
                raise QueryGuardError("unterminated string literal")
            tokens.append(Token("string", ""))
            continue
        if char == '"':
            index += 1
            value: list[str] = []
            while index < length:
                if sql[index] == '"':
                    index += 1
                    if index < length and sql[index] == '"':
                        value.append('"')
                        index += 1
                        continue
                    break
                value.append(sql[index])
                index += 1
            else:
                raise QueryGuardError("unterminated quoted identifier")
            tokens.append(Token("quoted_identifier", "".join(value)))
            continue
        match = _IDENTIFIER.match(sql, index)
        if match:
            tokens.append(Token("word", match.group(0).lower()))
            index = match.end()
            continue
        if char == "$":
            parameter = re.match(r"\$[0-9]+", sql[index:])
            if parameter:
                tokens.append(Token("parameter", parameter.group(0)))
                index += len(parameter.group(0))
                continue
            raise QueryGuardError("dollar-quoted strings are not allowed")
        if char == ";":
            tokens.append(Token("semicolon", char))
            index += 1
            continue
        tokens.append(Token("symbol", char))
        index += 1
    return tokens


def _is_symbol(token: Token | None, value: str) -> bool:
    return token is not None and token.kind == "symbol" and token.value == value


def _opens_column_list(previous: Token | None, depth: int, in_with_prelude: bool) -> bool:
    """True when `name (` names columns rather than calling a function."""
    # `AS alias(a, b)` and `(subquery) alias(a, b)` name the columns of a relation.
    if previous is not None and previous.kind == "word" and previous.value == "as":
        return True
    if _is_symbol(previous, ")"):
        return True
    # `WITH name(a, b) AS (...)`, including later `, name(a, b) AS (...)` entries.
    return (
        in_with_prelude
        and depth == 0
        and previous is not None
        and (
            (previous.kind == "word" and previous.value in {"with", "recursive"})
            or _is_symbol(previous, ",")
        )
    )


def validate_read_query(sql: str) -> str:
    """Validate and return one read-only PostgreSQL statement.

    The accepted grammar is intentionally narrower than PostgreSQL.  Rejecting a
    query here does not imply it would mutate data; accepting it does not grant
    authority beyond the database role and transaction policy.
    """
    if not isinstance(sql, str) or not sql.strip():
        raise QueryGuardError("query must be a non-empty string")
    tokens = _tokenize(sql)
    if not tokens:
        raise QueryGuardError("query must be a non-empty string")
    semicolons = [i for i, token in enumerate(tokens) if token.kind == "semicolon"]
    if semicolons:
        if semicolons != [len(tokens) - 1]:
            raise QueryGuardError("exactly one statement is allowed")
        tokens = tokens[:-1]
    if (
        not tokens
        or tokens[0].kind != "word"
        or tokens[0].value
        not in {
            "select",
            "with",
            "values",
            "table",
        }
    ):
        raise QueryGuardError("query must start with SELECT, WITH, VALUES, or TABLE")

    depth = 0
    in_with_prelude = tokens[0].value == "with"
    for index, token in enumerate(tokens):
        if _is_symbol(token, "("):
            depth += 1
            continue
        if _is_symbol(token, ")"):
            depth -= 1
            continue
        if token.kind != "word":
            continue
        if depth == 0 and token.value in {"select", "values", "table"}:
            in_with_prelude = False
        if token.value in _FORBIDDEN_WORDS:
            raise QueryGuardError(f"{token.value.upper()} is not allowed in a read query")
        next_token = tokens[index + 1] if index + 1 < len(tokens) else None
        if (
            token.value == "for"
            and next_token is not None
            and next_token.kind == "word"
            and next_token.value in _LOCKING_WORDS
        ):
            raise QueryGuardError("row-locking clauses such as FOR SHARE are not allowed")
        if not _is_symbol(next_token, "("):
            continue
        if token.value in _FORBIDDEN_FUNCTIONS:
            raise QueryGuardError(f"function {token.value} is not allowed")
        previous = tokens[index - 1] if index else None
        if (
            token.value in _NON_FUNCTION_WORDS
            or token.value in _TYPE_MODIFIER_WORDS
            or _opens_column_list(previous, depth, in_with_prelude)
        ):
            continue
        if token.value not in _SAFE_FUNCTIONS:
            raise QueryGuardError(
                f"function {token.value} is not on the gateway's read-only function list"
            )
        if index >= 2 and _is_symbol(tokens[index - 1], "."):
            qualifier = tokens[index - 2]
            if qualifier.kind != "word" or qualifier.value != "pg_catalog":
                raise QueryGuardError("functions may only use the pg_catalog qualifier")
    for index, token in enumerate(tokens[:-1]):
        if token.kind == "quoted_identifier" and tokens[index + 1].value == "(":
            raise QueryGuardError("quoted function names are not allowed")
    return sql.strip().removesuffix(";").rstrip()

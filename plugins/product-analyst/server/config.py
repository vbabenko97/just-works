"""Project settings. Credentials belong in libpq's service and password files."""

import math
import re
import tomllib
from pathlib import Path
from zoneinfo import ZoneInfo


def load_config(root: Path) -> dict:
    with (root / ".analyst/config.toml").open("rb") as stream:
        config = tomllib.load(stream)
    for name in ("analysis", "postgres", "budgets", "posthog"):
        if not isinstance(config.setdefault(name, {}), dict):
            raise ValueError(f"{name} must be a TOML table")
    analysis = config["analysis"]
    timezone_name = analysis.setdefault("timezone", "UTC")
    if not isinstance(timezone_name, str) or not timezone_name.strip():
        raise ValueError("analysis.timezone must be a timezone name")
    ZoneInfo(timezone_name)
    analysis.setdefault("internal_user_exclusion", "Unspecified: resolve before querying")
    pg = config["postgres"]
    if not isinstance(pg.get("service"), str) or not re.fullmatch(
        r"[A-Za-z0-9_.-]+", pg["service"]
    ):
        raise ValueError("postgres.service must be a libpq service name, not a connection string")
    schemas = pg.get("schemas")
    if (
        not isinstance(schemas, list)
        or not schemas
        or any(
            not isinstance(s, str) or not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", s)
            for s in schemas
        )
    ):
        raise ValueError("postgres.schemas must list approved schema names")
    for target, defaults in (
        (pg, {"statement_timeout_ms": 15000, "lock_timeout_ms": 2000, "row_cap": 10000}),
        (config["budgets"], {"postgres_queries": 30, "posthog_calls": 60}),
    ):
        for name, default in defaults.items():
            value = target.setdefault(name, default)
            if type(value) is not int or value <= 0:
                raise ValueError(f"{name} must be a positive integer")
    cost = pg.get("max_plan_cost")
    if cost is not None and (
        type(cost) not in (int, float) or not math.isfinite(cost) or cost <= 0
    ):
        raise ValueError("max_plan_cost must be finite and positive")
    extra = config["posthog"].setdefault("extra_read_tools", [])
    if not isinstance(extra, list) or any(
        not isinstance(s, str) or not re.fullmatch(r"[a-z][a-z0-9-]*", s) for s in extra
    ):
        raise ValueError("extra_read_tools must contain exact command names")
    iam = pg.get("iam")
    if iam is not None:
        if not isinstance(iam, dict) or any(
            not isinstance(iam.get(key), str) or not iam[key].strip()
            for key in ("region", "host", "user")
        ):
            raise ValueError("postgres.iam needs region, host, and user")
        port = iam.setdefault("port", 5432)
        if type(port) is not int or not 1 <= port <= 65535:
            raise ValueError("postgres.iam.port must be a valid TCP port")
    return config

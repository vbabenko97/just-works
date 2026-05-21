#!/usr/bin/env python3
"""Compute portfolio allocation, drift, concentration, fees, and cash-only rebalancing.

Input: JSON file following references/input-schema.md
Output: JSON report to stdout
"""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any

DEFAULT_DRIFT_BAND = 0.05
DEFAULT_SINGLE_POSITION_LIMIT = 0.10
DEFAULT_BROKER_LIMIT = 0.50


def as_float(value: Any, default: float = 0.0) -> float:
    if value is None or value == "":
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def normalize_ratio(value: Any, default: float = 0.0) -> float:
    ratio = as_float(value, default)
    if ratio > 1.0:
        return ratio / 100.0
    return ratio


def money(value: float) -> float:
    return round(value, 2)


def pct(value: float) -> float:
    return round(value, 6)


@dataclass(frozen=True)
class Position:
    raw: dict[str, Any]
    value_base: float
    fx_missing: bool
    bucket: str


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as file:
        data = json.load(file)
    if not isinstance(data, dict):
        raise ValueError("top-level input must be a JSON object")
    return data


def convert_position(position: dict[str, Any], base_currency: str, fx_rates: dict[str, Any]) -> Position:
    currency = str(position.get("currency") or base_currency).upper()
    value = as_float(position.get("value"))
    fx_missing = False
    if currency == base_currency:
        rate = 1.0
    elif currency in fx_rates:
        rate = as_float(fx_rates[currency], 0.0)
        if rate <= 0:
            rate = 1.0
            fx_missing = True
    else:
        rate = 1.0
        fx_missing = True

    bucket = str(position.get("bucket") or position.get("asset_class") or "unmapped").strip().lower()
    return Position(raw=position, value_base=value * rate, fx_missing=fx_missing, bucket=bucket)


def aggregate_by(positions: list[Position], key: str, total_value: float) -> list[dict[str, Any]]:
    grouped: dict[str, float] = defaultdict(float)
    for position in positions:
        label = str(position.raw.get(key) or "unknown").strip().lower()
        grouped[label] += position.value_base
    return [
        {"name": label, "value": money(value), "weight": pct(value / total_value if total_value else 0.0)}
        for label, value in sorted(grouped.items(), key=lambda item: item[1], reverse=True)
    ]


def build_targets(target_rows: list[dict[str, Any]]) -> dict[str, dict[str, float]]:
    targets: dict[str, dict[str, float]] = {}
    for row in target_rows:
        bucket = str(row.get("bucket") or "").strip().lower()
        if not bucket:
            continue
        targets[bucket] = {
            "target_weight": normalize_ratio(row.get("target_weight")),
            "rebalance_band": normalize_ratio(row.get("rebalance_band"), DEFAULT_DRIFT_BAND),
        }
    return targets


def cash_deployment_plan(
    allocation_rows: list[dict[str, Any]],
    new_cash_base: float,
) -> list[dict[str, Any]]:
    if new_cash_base <= 0:
        return []

    underweights = [row for row in allocation_rows if row["money_to_target"] > 0]
    total_shortfall = sum(row["money_to_target"] for row in underweights)
    if total_shortfall <= 0:
        return []

    remaining_cash = new_cash_base
    plan: list[dict[str, Any]] = []
    for row in underweights:
        buy_amount = min(new_cash_base * row["money_to_target"] / total_shortfall, remaining_cash)
        if buy_amount > 0:
            plan.append(
                {
                    "bucket": row["bucket"],
                    "action": "buy with new cash",
                    "amount": money(buy_amount),
                    "reason": "bucket is under target allocation",
                }
            )
            remaining_cash -= buy_amount
    return plan


def main() -> None:
    parser = argparse.ArgumentParser(description="Compute portfolio rebalancing review metrics from JSON input.")
    parser.add_argument("input_json", type=Path, help="path to input JSON file")
    args = parser.parse_args()

    data = load_json(args.input_json)
    base_currency = str(data.get("base_currency") or "USD").upper()
    fx_rates = data.get("fx_rates_to_base") or {}
    if not isinstance(fx_rates, dict):
        raise ValueError("fx_rates_to_base must be an object mapping currency codes to rates")

    raw_positions = data.get("positions") or []
    if not isinstance(raw_positions, list):
        raise ValueError("positions must be a list")

    positions = [convert_position(position, base_currency, fx_rates) for position in raw_positions]
    total_value = sum(position.value_base for position in positions)

    targets = build_targets(data.get("targets") or [])
    bucket_values: dict[str, float] = defaultdict(float)
    for position in positions:
        bucket_values[position.bucket] += position.value_base

    all_buckets = sorted(set(bucket_values) | set(targets))
    allocation_rows: list[dict[str, Any]] = []
    for bucket in all_buckets:
        current_value = bucket_values.get(bucket, 0.0)
        current_weight = current_value / total_value if total_value else 0.0
        target_weight = targets.get(bucket, {}).get("target_weight", 0.0)
        band = targets.get(bucket, {}).get("rebalance_band", DEFAULT_DRIFT_BAND)
        drift = current_weight - target_weight
        if bucket not in targets:
            status = "missing target"
        elif abs(drift) <= band + 1e-12:
            status = "within band"
        elif drift < 0:
            status = "underweight"
        else:
            status = "overweight"
        allocation_rows.append(
            {
                "bucket": bucket,
                "current_value": money(current_value),
                "current_weight": pct(current_weight),
                "target_weight": pct(target_weight),
                "drift": pct(drift),
                "rebalance_band": pct(band),
                "money_to_target": money(target_weight * total_value - current_value),
                "status": status,
            }
        )

    weighted_fee_numerator = 0.0
    fee_known_value = 0.0
    missing_fee_positions: list[str] = []
    for position in positions:
        if "expense_ratio" in position.raw and position.raw.get("expense_ratio") not in (None, ""):
            er = normalize_ratio(position.raw.get("expense_ratio"))
            weighted_fee_numerator += er * position.value_base
            fee_known_value += position.value_base
        else:
            missing_fee_positions.append(str(position.raw.get("ticker") or position.raw.get("name") or "unknown"))

    position_concentration = []
    for position in sorted(positions, key=lambda item: item.value_base, reverse=True):
        weight = position.value_base / total_value if total_value else 0.0
        if weight >= DEFAULT_SINGLE_POSITION_LIMIT:
            position_concentration.append(
                {
                    "name": str(position.raw.get("ticker") or position.raw.get("name") or "unknown"),
                    "value": money(position.value_base),
                    "weight": pct(weight),
                    "flag": "single position concentration",
                }
            )

    new_cash = data.get("new_cash") or {}
    new_cash_amount = as_float(new_cash.get("amount") if isinstance(new_cash, dict) else 0.0)
    new_cash_currency = str(new_cash.get("currency") or base_currency).upper() if isinstance(new_cash, dict) else base_currency
    if new_cash_currency == base_currency:
        new_cash_base = new_cash_amount
        new_cash_fx_missing = False
    elif new_cash_currency in fx_rates:
        new_cash_base = new_cash_amount * as_float(fx_rates[new_cash_currency], 0.0)
        new_cash_fx_missing = new_cash_base <= 0
    else:
        new_cash_base = new_cash_amount
        new_cash_fx_missing = new_cash_amount > 0

    broker_concentration = aggregate_by(positions, "broker", total_value)
    broker_flags = [row for row in broker_concentration if row["weight"] >= DEFAULT_BROKER_LIMIT and row["name"] != "unknown"]

    output = {
        "base_currency": base_currency,
        "total_value": money(total_value),
        "allocation": allocation_rows,
        "concentration": {
            "positions_over_10_percent": position_concentration,
            "by_asset_class": aggregate_by(positions, "asset_class", total_value),
            "by_sector": aggregate_by(positions, "sector", total_value),
            "by_country": aggregate_by(positions, "country", total_value),
            "by_currency": aggregate_by(positions, "currency", total_value),
            "by_broker": broker_concentration,
            "brokers_over_50_percent": broker_flags,
        },
        "fees": {
            "weighted_average_expense_ratio_on_known_fees": pct(weighted_fee_numerator / fee_known_value if fee_known_value else 0.0),
            "fee_coverage_weight": pct(fee_known_value / total_value if total_value else 0.0),
            "positions_missing_expense_ratio": missing_fee_positions,
        },
        "new_cash": {
            "amount_base": money(new_cash_base),
            "fx_missing": new_cash_fx_missing,
            "cash_only_plan": cash_deployment_plan(allocation_rows, new_cash_base),
        },
        "data_quality_flags": {
            "positions_with_missing_fx": [
                str(position.raw.get("ticker") or position.raw.get("name") or "unknown")
                for position in positions
                if position.fx_missing
            ],
            "targets_sum": pct(sum(row["target_weight"] for row in targets.values())),
            "unmapped_value": money(bucket_values.get("unmapped", 0.0)),
        },
    }
    print(json.dumps(output, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()

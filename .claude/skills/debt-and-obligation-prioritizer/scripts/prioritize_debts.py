#!/usr/bin/env python3
"""Rank debts and obligations for the debt-and-obligation-prioritizer skill.

Input: JSON list or CSV file with fields such as:
name,balance,apr,minimum_payment,currency,income_currency,annual_fees,
annual_penalties,secured,days_late,due_in_days,fx_risk,stress_score,status,type

Output: JSON with estimated effective annual cost, band, risk flags, and ordering.
This is a conservative helper, not financial, legal, or tax advice.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Iterable


HIGH_COST_THRESHOLD = 0.08
MEDIUM_COST_THRESHOLD = 0.04


def _float(value: Any, default: float = 0.0) -> float:
    if value is None or value == "":
        return default
    try:
        return float(str(value).strip().replace("%", "")) / (100.0 if "%" in str(value) else 1.0)
    except ValueError:
        return default


def _money(value: Any, default: float = 0.0) -> float:
    if value is None or value == "":
        return default
    try:
        return float(str(value).strip().replace(",", ""))
    except ValueError:
        return default


def _bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes", "y", "high", "secured"}


def _int(value: Any, default: int = 0) -> int:
    if value is None or value == "":
        return default
    try:
        return int(float(str(value).strip()))
    except ValueError:
        return default


@dataclass
class RankedObligation:
    name: str
    type: str
    balance: float
    apr: float
    effective_annual_cost: float
    minimum_payment: float
    currency: str
    income_currency: str
    band: str
    secured: bool
    urgent: bool
    risk_flags: list[str]
    stress_score: int
    priority_score: float


def effective_annual_cost(balance: float, apr: float, annual_fees: float, annual_penalties: float) -> float:
    if balance <= 0:
        return 0.0
    baseline = max(apr, 0.0)
    fee_component = max(annual_fees, 0.0) / balance
    penalty_component = max(annual_penalties, 0.0) / balance
    return baseline + fee_component + penalty_component


def classify(eac: float, urgent: bool, risky_type: str) -> str:
    risky = risky_type.lower() in {"credit card", "payday", "overdraft", "microloan", "bnpl"}
    if urgent or risky or eac >= HIGH_COST_THRESHOLD:
        return "high-cost"
    if eac >= MEDIUM_COST_THRESHOLD:
        return "medium-cost"
    return "low-cost"


def rank_item(row: dict[str, Any]) -> RankedObligation:
    name = str(row.get("name") or row.get("debt") or "unnamed obligation").strip()
    obligation_type = str(row.get("type") or "other").strip().lower()
    balance = _money(row.get("balance"))
    apr = _float(row.get("apr") if row.get("apr") not in (None, "") else row.get("interest_rate"))
    minimum_payment = _money(row.get("minimum_payment"))
    annual_fees = _money(row.get("annual_fees"))
    annual_penalties = _money(row.get("annual_penalties"))
    secured = _bool(row.get("secured"))
    days_late = _int(row.get("days_late"))
    due_in_days = _int(row.get("due_in_days"), default=999)
    stress_score = max(1, min(10, _int(row.get("stress_score"), default=5)))
    status = str(row.get("status") or "").strip().lower()
    currency = str(row.get("currency") or "").strip().upper()
    income_currency = str(row.get("income_currency") or "").strip().upper()
    fx_risk = _bool(row.get("fx_risk")) or bool(currency and income_currency and currency != income_currency)

    eac = effective_annual_cost(balance, apr, annual_fees, annual_penalties)
    urgent = (
        days_late > 0
        or due_in_days <= 7
        or status in {"late", "delinquent", "collections", "legal", "default"}
        or obligation_type in {"rent", "tax", "insurance", "utility"} and due_in_days <= 14
    )

    risk_flags: list[str] = []
    if urgent:
        risk_flags.append("urgent deadline or delinquency")
    if secured:
        risk_flags.append("secured/collateral risk")
    if fx_risk:
        risk_flags.append("currency mismatch")
    if annual_penalties > 0:
        risk_flags.append("known annualized penalties")
    if apr >= HIGH_COST_THRESHOLD:
        risk_flags.append("high APR")

    band = classify(eac, urgent, obligation_type)

    priority_score = eac * 100
    if urgent:
        priority_score += 100
    if secured:
        priority_score += 20
    if fx_risk:
        priority_score += 15
    priority_score += stress_score * 1.5
    if balance > 0:
        priority_score += min(minimum_payment / balance, 0.2) * 10

    return RankedObligation(
        name=name,
        type=obligation_type,
        balance=round(balance, 2),
        apr=round(apr, 6),
        effective_annual_cost=round(eac, 6),
        minimum_payment=round(minimum_payment, 2),
        currency=currency,
        income_currency=income_currency,
        band=band,
        secured=secured,
        urgent=urgent,
        risk_flags=risk_flags,
        stress_score=stress_score,
        priority_score=round(priority_score, 3),
    )


def load_rows(path: Path) -> list[dict[str, Any]]:
    if path.suffix.lower() == ".json":
        data = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            data = data.get("debts") or data.get("obligations") or []
        if not isinstance(data, list):
            raise ValueError("JSON input must be a list or an object with debts/obligations list")
        return [dict(item) for item in data]
    if path.suffix.lower() == ".csv":
        with path.open("r", encoding="utf-8-sig", newline="") as f:
            return list(csv.DictReader(f))
    raise ValueError("Input must be .json or .csv")


def summarize(items: Iterable[RankedObligation]) -> dict[str, Any]:
    ranked = sorted(items, key=lambda item: (-item.priority_score, -item.effective_annual_cost, item.balance))
    return {
        "recommended_order": [asdict(item) for item in ranked],
        "totals": {
            "balance": round(sum(item.balance for item in ranked), 2),
            "minimum_payments": round(sum(item.minimum_payment for item in ranked), 2),
            "weighted_average_eac": round(
                sum(item.balance * item.effective_annual_cost for item in ranked) / sum(item.balance for item in ranked), 6
            ) if sum(item.balance for item in ranked) > 0 else 0.0,
        },
        "counts_by_band": {
            "high_cost": sum(1 for item in ranked if item.band == "high-cost"),
            "medium_cost": sum(1 for item in ranked if item.band == "medium-cost"),
            "low_cost": sum(1 for item in ranked if item.band == "low-cost"),
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Prioritize debts and obligations by cost and risk.")
    parser.add_argument("input", type=Path, help="Path to .json or .csv debt list")
    parser.add_argument("--pretty", action="store_true", help="Pretty-print JSON output")
    args = parser.parse_args()

    rows = load_rows(args.input)
    ranked = [rank_item(row) for row in rows]
    output = summarize(ranked)
    print(json.dumps(output, indent=2 if args.pretty else None, ensure_ascii=False))


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Calculate emergency fund targets and a layered storage plan.

Input is JSON from a file path argument or stdin. Example:
{
  "monthly_mandatory_expenses": 2000,
  "currency": "EUR",
  "current_liquid_savings": 5000,
  "monthly_contribution": 1000,
  "income_stability": "variable",
  "dependents": 0,
  "relocation_risk": "high",
  "war_blackout_risk": "medium",
  "bank_cash_access": "limited"
}
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from dataclasses import dataclass
from typing import Any, Mapping


RISK_VALUES = {
    "none": 0,
    "low": 0,
    "stable": 0,
    "reliable": 0,
    "medium": 1,
    "moderate": 1,
    "variable": 2,
    "contract": 2,
    "limited": 1,
    "high": 2,
    "unstable": 3,
    "disrupted": 2,
    "unknown": 1,
}


@dataclass(frozen=True)
class EmergencyFundInput:
    monthly_mandatory_expenses: float
    currency: str = "UNSPECIFIED"
    current_liquid_savings: float = 0.0
    monthly_contribution: float = 0.0
    income_stability: str = "unknown"
    dependents: int = 0
    debt_minimums: float = 0.0
    relocation_risk: str = "unknown"
    war_blackout_risk: str = "unknown"
    bank_cash_access: str = "unknown"


def _as_float(data: Mapping[str, Any], key: str, default: float = 0.0) -> float:
    value = data.get(key, default)
    if value in (None, ""):
        return default
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{key} must be numeric") from exc
    if number < 0:
        raise ValueError(f"{key} cannot be negative")
    return number


def _as_int(data: Mapping[str, Any], key: str, default: int = 0) -> int:
    value = data.get(key, default)
    if value in (None, ""):
        return default
    try:
        number = int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{key} must be an integer") from exc
    if number < 0:
        raise ValueError(f"{key} cannot be negative")
    return number


def parse_input(data: Mapping[str, Any]) -> EmergencyFundInput:
    mandatory = _as_float(data, "monthly_mandatory_expenses")
    if mandatory <= 0:
        raise ValueError("monthly_mandatory_expenses must be greater than zero")

    return EmergencyFundInput(
        monthly_mandatory_expenses=mandatory,
        currency=str(data.get("currency", "UNSPECIFIED") or "UNSPECIFIED").upper(),
        current_liquid_savings=_as_float(data, "current_liquid_savings"),
        monthly_contribution=_as_float(data, "monthly_contribution"),
        income_stability=str(data.get("income_stability", "unknown") or "unknown").lower(),
        dependents=_as_int(data, "dependents"),
        debt_minimums=_as_float(data, "debt_minimums"),
        relocation_risk=str(data.get("relocation_risk", "unknown") or "unknown").lower(),
        war_blackout_risk=str(data.get("war_blackout_risk", "unknown") or "unknown").lower(),
        bank_cash_access=str(data.get("bank_cash_access", "unknown") or "unknown").lower(),
    )


def risk_score(user_input: EmergencyFundInput) -> int:
    score = 0
    score += RISK_VALUES.get(user_input.income_stability, 1)
    score += RISK_VALUES.get(user_input.relocation_risk, 1)
    score += RISK_VALUES.get(user_input.war_blackout_risk, 1)
    score += RISK_VALUES.get(user_input.bank_cash_access, 1)

    if user_input.dependents >= 3:
        score += 2
    elif user_input.dependents > 0:
        score += 1

    if user_input.debt_minimums > 0:
        debt_ratio = user_input.debt_minimums / user_input.monthly_mandatory_expenses
        if debt_ratio >= 0.25:
            score += 1

    return score


def recommended_months(score: int) -> int:
    if score <= 1:
        return 3
    if score <= 3:
        return 6
    if score <= 5:
        return 9
    return 12


def months_to_goal(current: float, target: float, monthly_contribution: float) -> int | None:
    shortfall = max(target - current, 0.0)
    if shortfall == 0:
        return 0
    if monthly_contribution <= 0:
        return None
    return math.ceil(shortfall / monthly_contribution)


def relocation_months(relocation_risk: str) -> int:
    if relocation_risk == "high":
        return 3
    if relocation_risk in {"medium", "moderate"}:
        return 1
    return 0


def calculate(user_input: EmergencyFundInput) -> dict[str, Any]:
    mandatory = user_input.monthly_mandatory_expenses
    score = risk_score(user_input)
    rec_months = recommended_months(score)
    emergency_target = rec_months * mandatory
    relocation_target = relocation_months(user_input.relocation_risk) * mandatory

    cash_weeks = 2 if user_input.war_blackout_risk in {"high", "medium", "moderate"} or user_input.bank_cash_access in {"limited", "disrupted"} else 1
    cash_amount = mandatory * cash_weeks / 4.0
    cash_cap = emergency_target * 0.15
    if rec_months >= 6:
        cash_amount = min(cash_amount, cash_cap)

    layer_1_total_first_month = mandatory
    instant_access_amount = max(layer_1_total_first_month - cash_amount, 0.0)
    layer_2_amount = max(emergency_target - cash_amount - instant_access_amount, 0.0)

    current = user_input.current_liquid_savings
    contribution = user_input.monthly_contribution

    return {
        "currency": user_input.currency,
        "monthly_mandatory_expenses": round(mandatory, 2),
        "risk_score": score,
        "recommended_target_months": rec_months,
        "minimum_emergency_fund": round(mandatory, 2),
        "targets": {str(months): round(months * mandatory, 2) for months in (3, 6, 9, 12)},
        "recommended_emergency_target": round(emergency_target, 2),
        "relocation_buffer_target": round(relocation_target, 2),
        "total_survival_and_relocation_target": round(emergency_target + relocation_target, 2),
        "layered_plan": {
            "layer_0_cash": round(cash_amount, 2),
            "layer_1_instant_access_bank": round(instant_access_amount, 2),
            "layer_2_short_term_deposit_or_tbill_equivalent": round(layer_2_amount, 2),
            "layer_3_relocation_buffer": round(relocation_target, 2),
            "layer_4_long_term_investments_inside_emergency_fund": 0.0,
        },
        "funding_plan": {
            "current_liquid_savings": round(current, 2),
            "monthly_contribution": round(contribution, 2),
            "shortfall_to_minimum": round(max(mandatory - current, 0.0), 2),
            "shortfall_to_recommended_emergency_target": round(max(emergency_target - current, 0.0), 2),
            "shortfall_to_total_survival_and_relocation_target": round(max(emergency_target + relocation_target - current, 0.0), 2),
            "months_to_minimum": months_to_goal(current, mandatory, contribution),
            "months_to_recommended_emergency_target": months_to_goal(current, emergency_target, contribution),
            "months_to_total_survival_and_relocation_target": months_to_goal(current, emergency_target + relocation_target, contribution),
        },
        "potentially_investable_surplus_after_targets": round(max(current - emergency_target - relocation_target, 0.0), 2),
    }


def load_json(path: str | None) -> Mapping[str, Any]:
    raw = sys.stdin.read() if path in (None, "-") else open(path, "r", encoding="utf-8").read()
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid JSON: {exc}") from exc
    if not isinstance(data, dict):
        raise ValueError("input JSON must be an object")
    return data


def main() -> int:
    parser = argparse.ArgumentParser(description="Calculate emergency fund targets and layers.")
    parser.add_argument("input", nargs="?", help="Path to JSON input file. Use '-' or omit for stdin.")
    args = parser.parse_args()

    try:
        data = load_json(args.input)
        result = calculate(parse_input(data))
    except (OSError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

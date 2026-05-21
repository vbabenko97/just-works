#!/usr/bin/env python3
"""Deterministic personal finance stress-test helper.

Input: JSON file with a monthly finance snapshot.
Output: JSON scenario results with runway, cash gaps, and risk scores.

This script intentionally uses only the Python standard library.
"""

from __future__ import annotations

import argparse
import json
import math
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional


Number = float


@dataclass
class ScenarioResult:
    scenario: str
    stressed_monthly_income: Number
    stressed_monthly_expenses: Number
    accessible_liquidity: Number
    one_time_shock: Number
    monthly_deficit: Number
    runway_months: Optional[Number]
    cash_gap_3m: Number
    cash_gap_6m: Number
    cash_gap_9m: Number
    risk_score: int
    notes: List[str]


def _num(data: Mapping[str, Any], key: str, default: Number = 0.0) -> Number:
    value = data.get(key, default)
    if value is None or value == "":
        return float(default)
    if not isinstance(value, (int, float)):
        raise ValueError(f"{key} must be numeric")
    return float(value)


def _clamp_score(score: Number) -> int:
    return int(max(1, min(10, round(score))))


def _runway(liquidity: Number, monthly_deficit: Number, one_time_shock: Number = 0.0) -> Optional[Number]:
    available = liquidity - one_time_shock
    if available <= 0:
        return 0.0
    if monthly_deficit <= 0:
        return None
    return available / monthly_deficit


def _gap(liquidity: Number, monthly_deficit: Number, months: int, one_time_shock: Number = 0.0) -> Number:
    need = one_time_shock + max(0.0, monthly_deficit) * months
    return max(0.0, need - liquidity)


def _base_score(runway_months: Optional[Number]) -> int:
    if runway_months is None:
        return 2
    if runway_months > 12:
        return 2
    if runway_months >= 6:
        return 4
    if runway_months >= 3:
        return 6
    if runway_months >= 1:
        return 8
    return 10


def _adjustments(snapshot: Mapping[str, Any], expenses: Number, income: Number, liquidity: Number) -> List[str]:
    notes: List[str] = []
    required = _num(snapshot, "required_expenses")
    debt_min = _num(snapshot, "debt_minimums")
    largest_institution = _num(snapshot, "largest_single_institution_balance")
    if income > 0 and required / income > 0.60:
        notes.append("fixed-cost ratio exceeds 60 percent")
    if income > 0 and debt_min / income > 0.15:
        notes.append("debt minimums exceed 15 percent of income")
    if liquidity > 0 and largest_institution / liquidity > 0.50:
        notes.append("more than 50 percent of accessible liquidity is concentrated in one institution")
    if bool(snapshot.get("income_is_unstable", False)):
        notes.append("income is unstable or delayed")
    if bool(snapshot.get("material_fx_mismatch", False)):
        notes.append("material currency mismatch exists")
    if bool(snapshot.get("active_infrastructure_risk", False)):
        notes.append("active blackout, relocation, medical, legal, or war-risk exposure exists")
    return notes


def _score(snapshot: Mapping[str, Any], runway_months: Optional[Number], expenses: Number, income: Number, liquidity: Number) -> int:
    score = _base_score(runway_months)
    score += len(_adjustments(snapshot, expenses, income, liquidity))
    return _clamp_score(score)


def _result(
    snapshot: Mapping[str, Any],
    scenario: str,
    income: Number,
    expenses: Number,
    liquidity: Number,
    one_time_shock: Number = 0.0,
    extra_notes: Optional[List[str]] = None,
) -> ScenarioResult:
    monthly_deficit = max(0.0, expenses - income)
    runway_months = _runway(liquidity, monthly_deficit, one_time_shock)
    notes = _adjustments(snapshot, expenses, income, liquidity)
    if extra_notes:
        notes.extend(extra_notes)
    return ScenarioResult(
        scenario=scenario,
        stressed_monthly_income=round(income, 2),
        stressed_monthly_expenses=round(expenses, 2),
        accessible_liquidity=round(liquidity, 2),
        one_time_shock=round(one_time_shock, 2),
        monthly_deficit=round(monthly_deficit, 2),
        runway_months=None if runway_months is None else round(runway_months, 2),
        cash_gap_3m=round(_gap(liquidity, monthly_deficit, 3, one_time_shock), 2),
        cash_gap_6m=round(_gap(liquidity, monthly_deficit, 6, one_time_shock), 2),
        cash_gap_9m=round(_gap(liquidity, monthly_deficit, 9, one_time_shock), 2),
        risk_score=_score(snapshot, runway_months, expenses, income, liquidity),
        notes=notes,
    )


def run_stress_test(snapshot: Mapping[str, Any]) -> Dict[str, Any]:
    income = _num(snapshot, "monthly_income")
    required = _num(snapshot, "required_expenses")
    debt_min = _num(snapshot, "debt_minimums")
    survival = _num(snapshot, "survival_expenses", required + debt_min)
    liquidity = _num(snapshot, "accessible_liquidity")
    locked = _num(snapshot, "locked_institution_amount", _num(snapshot, "largest_single_institution_balance"))

    relocation = _num(snapshot, "relocation_cost")
    medical = _num(snapshot, "medical_or_family_cost")
    blackout = _num(snapshot, "blackout_or_equipment_cost")
    grant_delay_months = int(_num(snapshot, "income_delay_months", 0.0))

    required_inflation = required * 1.20 + debt_min
    income_cut = income * 0.70

    devaluation_rate = _num(snapshot, "devaluation_rate")
    fx_expense_share = min(1.0, max(0.0, _num(snapshot, "fx_expense_share", 1.0)))
    fx_exposed_expenses = survival * fx_expense_share
    local_expenses = survival - fx_exposed_expenses
    devalued_expenses = local_expenses + fx_exposed_expenses * (1.0 + devaluation_rate)

    scenarios: List[ScenarioResult] = [
        _result(snapshot, "100 percent income loss", 0.0, survival, liquidity),
        _result(snapshot, "30 percent income reduction", income_cut, required + debt_min, liquidity),
        _result(snapshot, "urgent relocation", income, survival, liquidity, relocation),
        _result(snapshot, "20 percent required expense increase", income, required_inflation, liquidity),
        _result(snapshot, "currency devaluation", income, devalued_expenses, liquidity, extra_notes=[f"devaluation rate modeled at {devaluation_rate:.0%}"] if devaluation_rate else []),
        _result(snapshot, "frozen bank or broker access", income, survival, max(0.0, liquidity - locked), extra_notes=[f"locked balance modeled as {locked:.2f}"]),
        _result(snapshot, "medical or family expense", income, survival, liquidity, medical),
    ]

    if blackout > 0:
        scenarios.append(_result(snapshot, "blackout or urgent equipment cost", income, survival, liquidity, blackout))

    if grant_delay_months > 0:
        scenarios.append(
            _result(
                snapshot,
                f"income delayed for {grant_delay_months} months",
                0.0,
                survival,
                liquidity,
                extra_notes=["delayed income is not counted as available liquidity"],
            )
        )

    target_months = int(_num(snapshot, "target_months", 6.0))
    near_term_shocks = relocation + medical + blackout
    target_liquidity = survival * target_months + near_term_shocks

    return {
        "baseline": {
            "monthly_income": round(income, 2),
            "required_expenses": round(required, 2),
            "debt_minimums": round(debt_min, 2),
            "survival_expenses": round(survival, 2),
            "accessible_liquidity": round(liquidity, 2),
            "target_months": target_months,
            "target_liquidity": round(target_liquidity, 2),
            "liquidity_gap_to_target": round(max(0.0, target_liquidity - liquidity), 2),
        },
        "scenarios": [asdict(item) for item in scenarios],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Run personal finance stress-test scenarios from a JSON snapshot.")
    parser.add_argument("input_json", type=Path, help="Path to input JSON snapshot")
    args = parser.parse_args()

    with args.input_json.open("r", encoding="utf-8") as handle:
        snapshot = json.load(handle)
    if not isinstance(snapshot, dict):
        raise ValueError("input JSON must be an object")

    result = run_stress_test(snapshot)
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Compute a personal cashflow and net worth audit from normalized JSON.

This script is intentionally dependency-free so it can run in constrained environments.
It is a calculation aid for the cashflow-and-net-worth-auditor skill, not a substitute
for professional legal, tax, accounting, or investment advice.
"""

from __future__ import annotations

import argparse
import json
import math
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

Number = int | float

EXPENSE_TYPES = {"expense", "fee", "interest"}
INCOME_TYPES = {"income"}
OFFSET_TYPES = {"refund", "reimbursement"}
NON_CONSUMPTION_TYPES = {"transfer", "asset_purchase"}
DEBT_PAYMENT_TYPES = {"debt_payment"}
HIGH_INTEREST_APR = 10.0
INCOME_CONCENTRATION_THRESHOLD = 0.80
UNCATEGORIZED_EXPENSE_THRESHOLD = 0.05
FIXED_EXPENSE_INCOME_THRESHOLD = 0.50


@dataclass(frozen=True)
class Money:
    amount: float
    currency: str


def as_float(value: Any, default: float = 0.0) -> float:
    if value is None or value == "":
        return default
    try:
        result = float(value)
    except (TypeError, ValueError):
        return default
    if math.isnan(result) or math.isinf(result):
        return default
    return result


def normalize_currency(value: Any, fallback: str = "UNKNOWN") -> str:
    if value is None:
        return fallback
    text = str(value).strip().upper()
    return text or fallback


def get_period_months(data: dict[str, Any]) -> float:
    period = data.get("period", {}) if isinstance(data.get("period"), dict) else {}
    months = as_float(period.get("months"), 0.0)
    if months > 0:
        return months
    # Default to one monthly period. The skill can override this narratively if needed.
    return 1.0


def add_money(bucket: dict[str, float], currency: str, amount: float) -> None:
    bucket[normalize_currency(currency)] += amount


def format_money_by_currency(values: dict[str, float]) -> str:
    if not values:
        return "n/a"
    parts = []
    for currency in sorted(values):
        amount = values[currency]
        parts.append(f"{currency} {amount:,.2f}")
    return "; ".join(parts)


def divide_money(numerator: dict[str, float], denominator: dict[str, float]) -> dict[str, float]:
    result: dict[str, float] = {}
    for currency, num in numerator.items():
        den = denominator.get(currency, 0.0)
        if den:
            result[currency] = num / den
    return result


def format_percent(value: float | None) -> str:
    if value is None:
        return "n/a"
    return f"{value * 100:.1f}%"


def format_percent_by_currency(values: dict[str, float]) -> str:
    if not values:
        return "n/a"
    return "; ".join(f"{format_percent(value)} of {currency} income" for currency, value in sorted(values.items()))


def iter_dicts(value: Any) -> Iterable[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    return (item for item in value if isinstance(item, dict))


def transaction_amount(txn: dict[str, Any]) -> float:
    amount = as_float(txn.get("amount"), 0.0)
    # The normalized contract prefers positive values. If signed bank exports leak through,
    # absolute value prevents expenses from reducing expense totals twice.
    return abs(amount)


def infer_expense_class(txn: dict[str, Any]) -> str:
    explicit = str(txn.get("expense_class") or "").strip().lower()
    if explicit:
        return explicit
    category = str(txn.get("category") or "").strip().lower()
    description = str(txn.get("description") or "").strip().lower()
    text = f"{category} {description}"
    if any(token in text for token in ["rent", "mortgage", "insurance", "subscription", "internet", "phone"]):
        return "fixed"
    if any(token in text for token in ["groceries", "utility", "utilities", "fuel", "transport", "medical", "pharmacy"]):
        return "variable"
    if any(token in text for token in ["restaurant", "bar", "shopping", "entertainment", "travel", "hobby"]):
        return "discretionary"
    if any(token in text for token in ["repair", "relocation", "tax", "equipment", "one-off", "one off"]):
        return "one_off"
    return "uncategorized"


def summarize_transactions(data: dict[str, Any]) -> dict[str, Any]:
    income_by_source: dict[str, dict[str, float]] = defaultdict(lambda: defaultdict(float))
    expenses_by_class: dict[str, dict[str, float]] = defaultdict(lambda: defaultdict(float))
    expenses_by_category: dict[str, dict[str, float]] = defaultdict(lambda: defaultdict(float))
    expenses_by_merchant: dict[str, dict[str, float]] = defaultdict(lambda: defaultdict(float))
    total_income: dict[str, float] = defaultdict(float)
    true_income: dict[str, float] = defaultdict(float)
    offsets: dict[str, float] = defaultdict(float)
    total_expenses: dict[str, float] = defaultdict(float)
    debt_payments: dict[str, float] = defaultdict(float)
    uncategorized_expenses: dict[str, float] = defaultdict(float)

    for txn in iter_dicts(data.get("transactions")):
        txn_type = str(txn.get("type") or "unknown").strip().lower()
        currency = normalize_currency(txn.get("currency"), data.get("period", {}).get("base_currency", "UNKNOWN"))
        amount = transaction_amount(txn)
        category = str(txn.get("category") or "uncategorized").strip().lower() or "uncategorized"
        merchant = str(txn.get("merchant") or txn.get("description") or "unknown").strip() or "unknown"

        if txn_type in INCOME_TYPES:
            source = category or "income"
            add_money(total_income, currency, amount)
            add_money(true_income, currency, amount)
            add_money(income_by_source[source], currency, amount)
        elif txn_type in OFFSET_TYPES:
            add_money(offsets, currency, amount)
        elif txn_type in EXPENSE_TYPES:
            expense_class = infer_expense_class(txn)
            add_money(total_expenses, currency, amount)
            add_money(expenses_by_class[expense_class], currency, amount)
            add_money(expenses_by_category[category], currency, amount)
            add_money(expenses_by_merchant[merchant], currency, amount)
            if category == "uncategorized" or expense_class == "uncategorized":
                add_money(uncategorized_expenses, currency, amount)
        elif txn_type in DEBT_PAYMENT_TYPES:
            add_money(debt_payments, currency, amount)
        elif txn_type in NON_CONSUMPTION_TYPES:
            continue
        else:
            # Unknown cash outflows are treated as uncategorized expenses only when negative_direction is supplied.
            direction = str(txn.get("direction") or "").strip().lower()
            if direction in {"out", "debit", "expense"}:
                add_money(total_expenses, currency, amount)
                add_money(expenses_by_class["uncategorized"], currency, amount)
                add_money(expenses_by_category[category], currency, amount)
                add_money(expenses_by_merchant[merchant], currency, amount)
                add_money(uncategorized_expenses, currency, amount)

    return {
        "income_by_source": income_by_source,
        "expenses_by_class": expenses_by_class,
        "expenses_by_category": expenses_by_category,
        "expenses_by_merchant": expenses_by_merchant,
        "total_income": total_income,
        "true_income": true_income,
        "offsets": offsets,
        "total_expenses": total_expenses,
        "debt_payments": debt_payments,
        "uncategorized_expenses": uncategorized_expenses,
    }


def summarize_balance_sheet(data: dict[str, Any]) -> dict[str, dict[str, float]]:
    opening_assets: dict[str, float] = defaultdict(float)
    closing_assets: dict[str, float] = defaultdict(float)
    opening_liabilities: dict[str, float] = defaultdict(float)
    closing_liabilities: dict[str, float] = defaultdict(float)

    for account in iter_dicts(data.get("accounts")):
        if account.get("included_in_assets", True) is False:
            continue
        currency = normalize_currency(account.get("currency"), data.get("period", {}).get("base_currency", "UNKNOWN"))
        add_money(opening_assets, currency, as_float(account.get("opening_balance"), 0.0))
        add_money(closing_assets, currency, as_float(account.get("closing_balance"), 0.0))

    for asset in iter_dicts(data.get("assets")):
        currency = normalize_currency(asset.get("currency"), data.get("period", {}).get("base_currency", "UNKNOWN"))
        add_money(opening_assets, currency, as_float(asset.get("opening_value"), 0.0))
        add_money(closing_assets, currency, as_float(asset.get("closing_value"), 0.0))

    for liability in iter_dicts(data.get("liabilities")):
        currency = normalize_currency(liability.get("currency"), data.get("period", {}).get("base_currency", "UNKNOWN"))
        add_money(opening_liabilities, currency, as_float(liability.get("opening_balance"), 0.0))
        add_money(closing_liabilities, currency, as_float(liability.get("closing_balance"), 0.0))

    opening_net_worth: dict[str, float] = defaultdict(float)
    closing_net_worth: dict[str, float] = defaultdict(float)
    net_worth_change: dict[str, float] = defaultdict(float)
    currencies = set(opening_assets) | set(closing_assets) | set(opening_liabilities) | set(closing_liabilities)
    for currency in currencies:
        opening_net_worth[currency] = opening_assets.get(currency, 0.0) - opening_liabilities.get(currency, 0.0)
        closing_net_worth[currency] = closing_assets.get(currency, 0.0) - closing_liabilities.get(currency, 0.0)
        net_worth_change[currency] = closing_net_worth[currency] - opening_net_worth[currency]

    return {
        "opening_assets": opening_assets,
        "closing_assets": closing_assets,
        "opening_liabilities": opening_liabilities,
        "closing_liabilities": closing_liabilities,
        "opening_net_worth": opening_net_worth,
        "closing_net_worth": closing_net_worth,
        "net_worth_change": net_worth_change,
    }


def top_items(nested_money: dict[str, dict[str, float]], limit: int = 10) -> list[tuple[str, dict[str, float]]]:
    def total_amount(item: tuple[str, dict[str, float]]) -> float:
        return sum(abs(value) for value in item[1].values())

    return sorted(nested_money.items(), key=total_amount, reverse=True)[:limit]


def compute_required_burn(summary: dict[str, Any]) -> dict[str, float]:
    required: dict[str, float] = defaultdict(float)
    for expense_class in ["fixed", "variable"]:
        for currency, amount in summary["expenses_by_class"].get(expense_class, {}).items():
            add_money(required, currency, amount)
    for currency, amount in summary["debt_payments"].items():
        add_money(required, currency, amount)
    return required


def monthly_average(values: dict[str, float], months: float) -> dict[str, float]:
    divisor = months if months > 0 else 1.0
    return {currency: amount / divisor for currency, amount in values.items()}


def calculate_runway(liquid_assets: dict[str, float], burn_rate: dict[str, float]) -> dict[str, float]:
    result: dict[str, float] = {}
    for currency, liquid in liquid_assets.items():
        burn = burn_rate.get(currency, 0.0)
        if burn > 0:
            result[currency] = liquid / burn
    return result


def liquid_assets_from_data(data: dict[str, Any]) -> dict[str, float]:
    explicit = data.get("liquid_emergency_assets")
    base_currency = normalize_currency(data.get("period", {}).get("base_currency", "UNKNOWN"))
    result: dict[str, float] = defaultdict(float)
    if isinstance(explicit, dict):
        for currency, amount in explicit.items():
            add_money(result, str(currency), as_float(amount, 0.0))
        return result
    if isinstance(explicit, (int, float)):
        add_money(result, base_currency, as_float(explicit, 0.0))
        return result

    for account in iter_dicts(data.get("accounts")):
        if account.get("liquid", True) is False:
            continue
        currency = normalize_currency(account.get("currency"), base_currency)
        add_money(result, currency, as_float(account.get("closing_balance"), 0.0))
    return result


def red_flags(data: dict[str, Any], summary: dict[str, Any], balance: dict[str, Any], required_burn: dict[str, float], full_burn: dict[str, float]) -> list[str]:
    flags: list[str] = []
    total_income = summary["true_income"]
    total_expenses = summary["total_expenses"]

    for currency in sorted(set(total_income) | set(total_expenses)):
        income = total_income.get(currency, 0.0)
        expenses = total_expenses.get(currency, 0.0)
        if income > 0 and expenses > income:
            flags.append(f"Negative cashflow in {currency}: expenses exceed true income.")

    for currency, change in balance["net_worth_change"].items():
        if change < 0:
            flags.append(f"Net worth declined in {currency}.")

    for source, money in summary["income_by_source"].items():
        for currency, amount in money.items():
            income = total_income.get(currency, 0.0)
            if income > 0 and amount / income >= INCOME_CONCENTRATION_THRESHOLD:
                flags.append(f"Income concentration risk: {source} provides {amount / income:.0%} of {currency} income.")

    for currency, uncategorized in summary["uncategorized_expenses"].items():
        expenses = total_expenses.get(currency, 0.0)
        if expenses > 0 and uncategorized / expenses >= UNCATEGORIZED_EXPENSE_THRESHOLD:
            flags.append(f"Uncategorized spending is {uncategorized / expenses:.0%} of {currency} expenses.")

    for currency, fixed in summary["expenses_by_class"].get("fixed", {}).items():
        income = total_income.get(currency, 0.0)
        if income > 0 and fixed / income >= FIXED_EXPENSE_INCOME_THRESHOLD:
            flags.append(f"Fixed expenses consume {fixed / income:.0%} of {currency} true income.")

    for liability in iter_dicts(data.get("liabilities")):
        apr = as_float(liability.get("apr"), 0.0)
        closing = as_float(liability.get("closing_balance"), 0.0)
        name = str(liability.get("name") or "liability")
        if apr >= HIGH_INTEREST_APR and closing > 0:
            flags.append(f"High-interest debt remains: {name} at {apr:.1f}% APR.")

    currencies = set()
    for key in ["true_income", "total_expenses"]:
        currencies.update(summary[key].keys())
    for key in ["closing_assets", "closing_liabilities"]:
        currencies.update(balance[key].keys())
    if len(currencies) > 1:
        flags.append("Multi-currency exposure exists; consolidate only with reliable period FX rates.")

    if not required_burn:
        flags.append("Required burn rate could not be calculated from the supplied categories.")
    if not full_burn:
        flags.append("Full burn rate could not be calculated from the supplied transactions.")

    return flags


def build_report(data: dict[str, Any]) -> str:
    period = data.get("period", {}) if isinstance(data.get("period"), dict) else {}
    label = period.get("label") or f"{period.get('start', 'unknown start')} to {period.get('end', 'unknown end')}"
    months = get_period_months(data)

    tx = summarize_transactions(data)
    bs = summarize_balance_sheet(data)
    required_burn_total = compute_required_burn(tx)
    full_burn_total = tx["total_expenses"]
    required_burn_monthly = monthly_average(required_burn_total, months)
    full_burn_monthly = monthly_average(full_burn_total, months)
    liquid_assets = liquid_assets_from_data(data)
    required_runway = calculate_runway(liquid_assets, required_burn_monthly)
    full_runway = calculate_runway(liquid_assets, full_burn_monthly)

    savings_num: dict[str, float] = defaultdict(float)
    for currency in set(tx["true_income"]) | set(tx["total_expenses"]):
        savings_num[currency] = tx["true_income"].get(currency, 0.0) - tx["total_expenses"].get(currency, 0.0)
    savings_rate = divide_money(savings_num, tx["true_income"])

    flags = red_flags(data, tx, bs, required_burn_monthly, full_burn_monthly)

    lines: list[str] = []
    lines.append(f"# Financial Audit for {label}")
    lines.append("")
    lines.append("## TL;DR")
    lines.append("")
    lines.append(
        "Closing net worth is "
        f"{format_money_by_currency(bs['closing_net_worth'])}; net worth change is "
        f"{format_money_by_currency(bs['net_worth_change'])}; net savings rate is "
        f"{format_percent_by_currency(savings_rate)}; full monthly burn is "
        f"{format_money_by_currency(full_burn_monthly)}."
    )
    lines.append("")
    lines.append("## 1. Net Worth")
    lines.append("")
    lines.append(f"- Opening assets: {format_money_by_currency(bs['opening_assets'])}")
    lines.append(f"- Opening liabilities: {format_money_by_currency(bs['opening_liabilities'])}")
    lines.append(f"- Opening net worth: {format_money_by_currency(bs['opening_net_worth'])}")
    lines.append(f"- Closing assets: {format_money_by_currency(bs['closing_assets'])}")
    lines.append(f"- Closing liabilities: {format_money_by_currency(bs['closing_liabilities'])}")
    lines.append(f"- Closing net worth: {format_money_by_currency(bs['closing_net_worth'])}")
    lines.append(f"- Net worth change: {format_money_by_currency(bs['net_worth_change'])}")
    lines.append("")
    lines.append("## 2. Income by Source")
    lines.append("")
    if tx["income_by_source"]:
        for source, money in top_items(tx["income_by_source"]):
            lines.append(f"- {source}: {format_money_by_currency(money)}")
    else:
        lines.append("- No income transactions found.")
    lines.append("")
    lines.append("## 3. Expenses by Type")
    lines.append("")
    if tx["expenses_by_class"]:
        for expense_class, money in top_items(tx["expenses_by_class"]):
            lines.append(f"- {expense_class}: {format_money_by_currency(money)}")
    else:
        lines.append("- No expense transactions found.")
    lines.append("")
    lines.append("## 4. Savings Rate")
    lines.append("")
    lines.append(f"- Net savings: {format_money_by_currency(savings_num)}")
    lines.append(f"- Net savings rate: {format_percent_by_currency(savings_rate)}")
    lines.append("- Gross savings rate: unavailable unless gross income is supplied separately.")
    lines.append("")
    lines.append("## 5. Burn Rate and Runway")
    lines.append("")
    lines.append(f"- Required monthly burn: {format_money_by_currency(required_burn_monthly)}")
    lines.append(f"- Full monthly burn: {format_money_by_currency(full_burn_monthly)}")
    lines.append(f"- Liquid emergency assets: {format_money_by_currency(liquid_assets)}")
    lines.append(f"- Required runway: {format_runway(required_runway)}")
    lines.append(f"- Full runway: {format_runway(full_runway)}")
    lines.append("")
    lines.append("## 6. Top 10 Expense Categories")
    lines.append("")
    if tx["expenses_by_category"]:
        for category, money in top_items(tx["expenses_by_category"]):
            lines.append(f"- {category}: {format_money_by_currency(money)}")
    else:
        lines.append("- No expense categories found.")
    lines.append("")
    lines.append("## 7. Top 10 Merchants or Counterparties")
    lines.append("")
    if tx["expenses_by_merchant"]:
        for merchant, money in top_items(tx["expenses_by_merchant"]):
            lines.append(f"- {merchant}: {format_money_by_currency(money)}")
    else:
        lines.append("- No merchant data found.")
    lines.append("")
    lines.append("## 8. Red Flags")
    lines.append("")
    if flags:
        for flag in flags:
            lines.append(f"- {flag}")
    else:
        lines.append("- No automatic red flags found in the normalized data.")
    lines.append("")
    lines.append("## 9. Investment Discussion Gate")
    lines.append("")
    lines.append("Do not move to investment recommendations until emergency fund coverage and debt burden are reviewed.")
    lines.append("")
    return "\n".join(lines)


def format_runway(values: dict[str, float]) -> str:
    if not values:
        return "n/a"
    return "; ".join(f"{currency} {months:.1f} months" for currency, months in sorted(values.items()))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Compute a cashflow and net worth audit from normalized JSON.")
    parser.add_argument("input", type=Path, help="Path to normalized input JSON.")
    parser.add_argument("--output", "-o", type=Path, help="Optional path for markdown output.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        data = json.loads(args.input.read_text(encoding="utf-8"))
    except FileNotFoundError:
        print(f"Input file not found: {args.input}")
        return 2
    except json.JSONDecodeError as exc:
        print(f"Invalid JSON: {exc}")
        return 2

    if not isinstance(data, dict):
        print("Input JSON must be an object at the top level.")
        return 2

    report = build_report(data)
    if args.output:
        args.output.write_text(report, encoding="utf-8")
    else:
        print(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

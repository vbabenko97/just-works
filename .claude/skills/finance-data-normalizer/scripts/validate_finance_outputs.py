#!/usr/bin/env python3
"""Validate normalized personal finance output CSV files.

This script checks structure and basic data quality only. It does not provide
financial, investment, tax, or legal advice.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Iterable

DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
MONTH_RE = re.compile(r"^\d{4}-\d{2}$")

REVIEW_STATUSES = {
    "ok",
    "needs_review",
    "duplicate_candidate",
    "transfer_candidate",
    "excluded",
    "unknown",
}

FLOW_BUCKETS = {
    "income",
    "fixed_expenses",
    "variable_expenses",
    "transfers",
    "investments",
    "taxes",
    "debt_payments",
}

REQUIRED_COLUMNS: dict[str, list[str]] = {
    "transactions.csv": [
        "transaction_id",
        "date",
        "source_account",
        "currency",
        "amount_original",
        "amount_base",
        "flow_bucket",
        "category",
        "subcategory",
        "merchant",
        "recurring_flag",
        "confidence",
        "review_status",
        "notes",
        "source_reference",
    ],
    "accounts.csv": [
        "account_id",
        "account_name",
        "account_type",
        "institution",
        "currency",
        "opening_balance",
        "closing_balance",
        "balance_date",
        "confidence",
        "review_status",
        "notes",
    ],
    "assets.csv": [
        "asset_id",
        "asset_type",
        "asset_name",
        "account_id",
        "currency",
        "value_original",
        "value_base",
        "valuation_date",
        "confidence",
        "review_status",
        "notes",
    ],
    "debts.csv": [
        "debt_id",
        "debt_type",
        "lender",
        "currency",
        "principal_original",
        "principal_base",
        "interest_rate",
        "minimum_payment",
        "due_date",
        "confidence",
        "review_status",
        "notes",
    ],
    "monthly_snapshot.csv": [
        "month",
        "base_currency",
        "income_total",
        "fixed_expenses_total",
        "variable_expenses_total",
        "taxes_total",
        "debt_payments_total",
        "investment_contributions_total",
        "transfers_net",
        "net_cashflow",
        "savings_rate",
        "unknown_amount",
        "unknown_share",
        "notes",
    ],
    "suspicious_or_unclear_operations.csv": [
        "item_id",
        "date",
        "source_account",
        "currency",
        "amount_original",
        "merchant",
        "issue_type",
        "confidence",
        "reason",
        "suggested_next_step",
        "source_reference",
    ],
}

NUMERIC_COLUMNS = {
    "amount_original",
    "amount_base",
    "opening_balance",
    "closing_balance",
    "value_original",
    "value_base",
    "principal_original",
    "principal_base",
    "interest_rate",
    "minimum_payment",
    "income_total",
    "fixed_expenses_total",
    "variable_expenses_total",
    "taxes_total",
    "debt_payments_total",
    "investment_contributions_total",
    "transfers_net",
    "net_cashflow",
    "savings_rate",
    "unknown_amount",
    "unknown_share",
}

DATE_COLUMNS = {"date", "balance_date", "valuation_date", "due_date"}


def read_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        headers = reader.fieldnames or []
        return headers, list(reader)


def is_decimal(value: str) -> bool:
    if value == "":
        return True
    try:
        Decimal(value)
        return True
    except InvalidOperation:
        return False


def validate_confidence(value: str) -> bool:
    if value == "":
        return False
    try:
        score = Decimal(value)
    except InvalidOperation:
        return False
    return Decimal("0") <= score <= Decimal("1")


def add_error(errors: list[dict[str, object]], file_name: str, row: int | None, field: str, message: str) -> None:
    errors.append({"file": file_name, "row": row, "field": field, "message": message})


def check_required_columns(file_name: str, headers: Iterable[str], errors: list[dict[str, object]]) -> None:
    header_set = set(headers)
    for column in REQUIRED_COLUMNS[file_name]:
        if column not in header_set:
            add_error(errors, file_name, None, column, "missing required column")


def validate_row(file_name: str, row_number: int, row: dict[str, str], errors: list[dict[str, object]]) -> None:
    for field, value in row.items():
        value = (value or "").strip()

        if field in NUMERIC_COLUMNS and not is_decimal(value):
            add_error(errors, file_name, row_number, field, "expected a decimal number or blank")

        if field == "confidence" and not validate_confidence(value):
            add_error(errors, file_name, row_number, field, "expected confidence between 0 and 1")

        if field == "review_status" and value and value not in REVIEW_STATUSES:
            add_error(errors, file_name, row_number, field, f"unknown review_status: {value}")

        if field == "flow_bucket" and value and value not in FLOW_BUCKETS:
            add_error(errors, file_name, row_number, field, f"unknown flow_bucket: {value}")

        if field in DATE_COLUMNS and value and not DATE_RE.match(value):
            add_error(errors, file_name, row_number, field, "expected date format yyyy-mm-dd")

        if field == "month" and value and not MONTH_RE.match(value):
            add_error(errors, file_name, row_number, field, "expected month format yyyy-mm")

        if field == "recurring_flag" and value and value.lower() not in {"true", "false"}:
            add_error(errors, file_name, row_number, field, "expected true, false, or blank")


def validate_directory(input_dir: Path) -> dict[str, object]:
    errors: list[dict[str, object]] = []
    warnings: list[dict[str, object]] = []
    files_checked: list[str] = []
    row_counts: dict[str, int] = {}

    for file_name in REQUIRED_COLUMNS:
        path = input_dir / file_name
        if not path.exists():
            warnings.append({"file": file_name, "message": "file not found"})
            continue

        headers, rows = read_csv(path)
        files_checked.append(file_name)
        row_counts[file_name] = len(rows)
        check_required_columns(file_name, headers, errors)

        for index, row in enumerate(rows, start=2):
            validate_row(file_name, index, row, errors)

    return {
        "ok": not errors,
        "files_checked": files_checked,
        "row_counts": row_counts,
        "warnings": warnings,
        "errors": errors,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate normalized finance CSV outputs.")
    parser.add_argument("--input-dir", required=True, help="Directory containing normalized CSV files.")
    parser.add_argument("--base-currency", default="", help="Optional expected base currency code for reporting context.")
    args = parser.parse_args()

    input_dir = Path(args.input_dir).expanduser().resolve()
    if not input_dir.exists() or not input_dir.is_dir():
        print(json.dumps({"ok": False, "errors": [{"message": "input directory not found"}]}, indent=2))
        return 2

    result = validate_directory(input_dir)
    if args.base_currency:
        result["base_currency"] = args.base_currency.upper()

    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())

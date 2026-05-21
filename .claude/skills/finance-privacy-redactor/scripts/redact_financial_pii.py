#!/usr/bin/env python3
"""Deterministic first-pass redactor for financial PII.

This utility is intentionally dependency-free so it can run in restricted
or offline environments. It is designed for text-like inputs: plain text,
CSV, JSON, exported statements, and copied document text.
"""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from pathlib import Path
from typing import Callable, Match

PLACEHOLDERS = {
    "iban": "[REDACTED_IBAN]",
    "card": "[REDACTED_CARD]",
    "email": "[REDACTED_EMAIL]",
    "phone": "[REDACTED_PHONE]",
    "tax_id": "[REDACTED_TAX_ID]",
    "passport_or_id": "[REDACTED_PASSPORT_OR_ID]",
    "account_number": "[REDACTED_ACCOUNT_NUMBER]",
    "address": "[REDACTED_ADDRESS]",
    "person_name": "[REDACTED_PERSON_NAME]",
}

EMAIL_RE = re.compile(r"(?<![\w.+-])[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}(?![\w.-])", re.I)

# Candidate phone numbers. The replacement function filters weak matches.
PHONE_RE = re.compile(
    r"(?<!\w)(?:\+?\d{1,3}[\s().-]*)?(?:\(?\d{2,4}\)?[\s().-]*){2,5}\d{2,4}(?!\w)"
)

IBAN_RE = re.compile(r"\b[A-Z]{2}\d{2}(?:[ \t-]?[A-Z0-9]){11,30}\b", re.I)

# Broad card candidate. Luhn validation filters most non-card digit sequences.
CARD_RE = re.compile(r"(?<!\d)(?:\d[ -]?){13,19}(?!\d)")

TAX_LABEL_RE = re.compile(
    r"\b(?:national\s+tax\s+number|taxpayer\s+(?:id|number|no\.?|code)|tax\s+(?:id|number|no\.?|code)|fiscal\s+code|vat\s*id|tin|ein|ssn|vat)\b[^\S\r\n]*[:#-]?[^\S\r\n]*([A-Z0-9][A-Z0-9 .\/-]{4,35})",
    re.I,
)

PASSPORT_ID_LABEL_RE = re.compile(
    r"\b(?:driver'?s?\s+licen[cs]e|identity\s+card|national\s+id|document\s+(?:id|number|no\.?)|id\s*(?:card|number|no\.?)|passport)\b[^\S\r\n]*[:#-]?[^\S\r\n]*([A-Z0-9][A-Z0-9 .\/-]{3,35})",
    re.I,
)

ACCOUNT_LABEL_RE = re.compile(
    r"\b(?:beneficiary\s+account|settlement\s+account|bank\s+account|account\s*(?:number|no\.?)|routing\s+number|sort\s+code|acct|account)\b[^\S\r\n]*[:#-]?[^\S\r\n]*([A-Z0-9][A-Z0-9 .\/-]{4,40})",
    re.I,
)

NAME_LABEL_RE = re.compile(
    r"\b(?:full\s+name|customer\s+name|employee\s+name|account\s+holder|holder\s+name|client\s+name|payer\s+name|payee\s+name)\b[^\S\r\n]*[:#-]?[^\S\r\n]*([^,;\n\r]{2,80})",
    re.I,
)

COUNTERPARTY_FIELD_RE = re.compile(
    r"\b(?P<label>counterparty|merchant|payer|payee|beneficiary|employer|broker)\b\s*[:=]\s*(?P<value>[^,;\n\r]{2,100})",
    re.I,
)

ADDRESS_LINE_RE = re.compile(
    r"(?ix)"
    r"\b\d{1,6}\s+[a-z0-9.' -]{2,60}\s+"
    r"(?:street|st\.?|avenue|ave\.?|road|rd\.?|boulevard|blvd\.?|lane|ln\.?|drive|dr\.?|court|ct\.?|square|sq\.?|way|place|pl\.?|highway|hwy\.?|apartment|apt\.?|flat|suite|ste\.?)\b"
    r"|\b(?:street|avenue|road|boulevard|lane|drive|apartment|apt\.?|suite|postal\s*code|zip\s*code)\b[^\n\r]{0,80}"
)

ADDRESS_LABEL_RE = re.compile(
    r"(?im)^([^\n\r]*\b(?:address|residential address|mailing address|billing address)\b[^:#=\n\r]*[:=][^\n\r]+)$"
)


def normalize_digits(value: str) -> str:
    return re.sub(r"\D", "", value)


def luhn_valid(digits: str) -> bool:
    if not 13 <= len(digits) <= 19 or len(set(digits)) == 1:
        return False
    total = 0
    parity = len(digits) % 2
    for idx, ch in enumerate(digits):
        digit = int(ch)
        if idx % 2 == parity:
            digit *= 2
            if digit > 9:
                digit -= 9
        total += digit
    return total % 10 == 0


def iban_mod97_valid(candidate: str) -> bool:
    compact = re.sub(r"[\s-]", "", candidate).upper()
    if not 15 <= len(compact) <= 34:
        return False
    if not re.match(r"^[A-Z]{2}\d{2}[A-Z0-9]+$", compact):
        return False
    rearranged = compact[4:] + compact[:4]
    numeric = ""
    for ch in rearranged:
        if ch.isdigit():
            numeric += ch
        elif "A" <= ch <= "Z":
            numeric += str(ord(ch) - 55)
        else:
            return False
    remainder = 0
    for ch in numeric:
        remainder = (remainder * 10 + int(ch)) % 97
    return remainder == 1


def replace_with_counter(
    text: str,
    pattern: re.Pattern[str],
    placeholder: str,
    audit: Counter[str],
    key: str,
    validator: Callable[[str], bool] | None = None,
) -> str:
    def repl(match: Match[str]) -> str:
        value = match.group(0)
        if validator is not None and not validator(value):
            return value
        audit[key] += 1
        return placeholder

    return pattern.sub(repl, text)


def redact_labeled_value(text: str, pattern: re.Pattern[str], placeholder: str, audit: Counter[str], key: str) -> str:
    def repl(match: Match[str]) -> str:
        audit[key] += 1
        prefix = match.group(0)[: match.start(1) - match.start(0)]
        return f"{prefix}{placeholder}"

    return pattern.sub(repl, text)


def redact_phone(text: str, audit: Counter[str]) -> str:
    def repl(match: Match[str]) -> str:
        value = match.group(0)
        digits = normalize_digits(value)
        # Avoid redacting dates, amounts, short IDs, and long account-like runs.
        if not 8 <= len(digits) <= 15:
            return value
        if re.search(r"\d{4}-\d{2}-\d{2}", value):
            return value
        audit["phone_numbers"] += 1
        return PLACEHOLDERS["phone"]

    return PHONE_RE.sub(repl, text)


def redact_address_lines(text: str, audit: Counter[str]) -> str:
    def label_repl(match: Match[str]) -> str:
        audit["addresses"] += 1
        line = match.group(1)
        prefix = re.split(r"[:=]", line, maxsplit=1)[0]
        separator = ":" if ":" in line else "="
        return f"{prefix}{separator} {PLACEHOLDERS['address']}"

    def inline_repl(match: Match[str]) -> str:
        audit["addresses"] += 1
        return PLACEHOLDERS["address"]

    text = ADDRESS_LABEL_RE.sub(label_repl, text)
    return ADDRESS_LINE_RE.sub(inline_repl, text)


def redact_counterparties(text: str, audit: Counter[str]) -> str:
    mapping: dict[str, str] = {}

    def token_for(value: str) -> str:
        key = re.sub(r"\s+", " ", value.strip()).lower()
        if key not in mapping:
            mapping[key] = f"[COUNTERPARTY_{len(mapping) + 1:03d}]"
        return mapping[key]

    def repl(match: Match[str]) -> str:
        label = match.group("label")
        value = match.group("value").strip()
        if value.startswith("[") and value.endswith("]"):
            return match.group(0)
        audit["exact_counterparties"] += 1
        return f"{label}: {token_for(value)}"

    return COUNTERPARTY_FIELD_RE.sub(repl, text)


def redact_text(text: str, redact_counterparty_names: bool = False) -> tuple[str, dict[str, int]]:
    audit: Counter[str] = Counter()

    text = replace_with_counter(text, IBAN_RE, PLACEHOLDERS["iban"], audit, "ibans", iban_mod97_valid)
    text = replace_with_counter(
        text,
        CARD_RE,
        PLACEHOLDERS["card"],
        audit,
        "payment_card_numbers",
        lambda candidate: luhn_valid(normalize_digits(candidate)),
    )
    text = replace_with_counter(text, EMAIL_RE, PLACEHOLDERS["email"], audit, "email_addresses")
    text = redact_labeled_value(text, TAX_LABEL_RE, PLACEHOLDERS["tax_id"], audit, "tax_ids")
    text = redact_labeled_value(text, PASSPORT_ID_LABEL_RE, PLACEHOLDERS["passport_or_id"], audit, "passport_or_id_numbers")
    text = redact_labeled_value(text, ACCOUNT_LABEL_RE, PLACEHOLDERS["account_number"], audit, "account_numbers")
    text = redact_labeled_value(text, NAME_LABEL_RE, PLACEHOLDERS["person_name"], audit, "personal_names")
    text = redact_phone(text, audit)
    text = redact_address_lines(text, audit)

    if redact_counterparty_names:
        text = redact_counterparties(text, audit)

    return text, dict(sorted(audit.items()))


def main() -> int:
    parser = argparse.ArgumentParser(description="Redact financial PII from text-like files.")
    parser.add_argument("input", type=Path, help="Input text-like file path")
    parser.add_argument("--output", type=Path, help="Output file path for redacted content")
    parser.add_argument("--audit", type=Path, help="Optional JSON audit output path")
    parser.add_argument(
        "--redact-counterparties",
        action="store_true",
        help="Replace labeled merchant/counterparty/payee/payer values with stable tokens",
    )
    parser.add_argument("--encoding", default="utf-8", help="Text encoding, default: utf-8")
    args = parser.parse_args()

    try:
        source = args.input.read_text(encoding=args.encoding)
    except UnicodeDecodeError as exc:
        raise SystemExit(f"Could not decode input with {args.encoding}: {exc}") from exc

    redacted, audit = redact_text(source, redact_counterparty_names=args.redact_counterparties)

    if args.output:
        args.output.write_text(redacted, encoding=args.encoding)
    else:
        print(redacted)

    if args.audit:
        args.audit.write_text(json.dumps(audit, indent=2, sort_keys=True), encoding="utf-8")
    else:
        print("\nRemoved data types:")
        if audit:
            for key, count in audit.items():
                print(f"- {key}: {count}")
        else:
            print("- none detected by deterministic pass")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

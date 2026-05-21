---
name: finance-privacy-redactor
description: redact and anonymize personally identifiable information from sensitive financial documents before analysis, upload, sharing, or use with external tools. use for bank statements, transaction exports, payroll records, tax documents, brokerage reports, invoices, reimbursement records, account snapshots, and any document containing financial data plus identifiers such as ibans, account numbers, card numbers, addresses, passport or id data, tax numbers, phone numbers, emails, names, or exact counterparties.
---

# Finance Privacy Redactor

## Objective

Redact personally identifiable information from financial documents while preserving analytical usefulness. The cleaned output must remain useful for cashflow analysis, budgeting, tax categorization, reconciliation, recurring-payment detection, merchant-category analysis, and transaction-type analysis.

## Core workflow

1. Identify the document type and structure: pasted text, table, CSV, JSON, statement-like text, payroll record, tax file, brokerage report, or invoice.
2. Detect and redact high-risk identifiers before doing any financial analysis.
3. Preserve analytical fields: dates, amounts, currencies, categories, merchant category, recurring flag, operation type, transaction direction, and normalized transaction labels when needed.
4. Replace exact identifiers with typed placeholders, not decorative masking.
5. Return the cleaned document plus a concise audit list of removed data types.
6. If uncertainty remains, state what may need manual review. Do not claim perfect anonymization.

## Redaction rules

Always redact:

- IBANs and domestic bank account numbers.
- Payment card numbers, even if separated by spaces or hyphens.
- Full addresses and address-like lines.
- Passport numbers, national ID numbers, driver license numbers, and document IDs.
- Tax identifiers, including taxpayer numbers, VAT IDs, TINs, EINs, SSNs, and local tax numbers.
- Phone numbers.
- Email addresses.
- Exact personal names.
- Exact counterparty names when the name is not needed for the analysis.

Prefer typed placeholders:

- `[REDACTED_IBAN]`
- `[REDACTED_ACCOUNT_NUMBER]`
- `[REDACTED_CARD]`
- `[REDACTED_ADDRESS]`
- `[REDACTED_PASSPORT_OR_ID]`
- `[REDACTED_TAX_ID]`
- `[REDACTED_PHONE]`
- `[REDACTED_EMAIL]`
- `[REDACTED_PERSON_NAME]`
- `[COUNTERPARTY_001]`, `[COUNTERPARTY_002]`, etc.

Use stable counterparty tokens inside one document when grouping repeat transactions matters. For example, replace the same recurring payee with the same `[COUNTERPARTY_001]` token. Do not create a reusable mapping that would allow re-identification unless the user explicitly asks for a local-only mapping.

## Preserve rules

Preserve these fields unless they directly contain PII:

- Dates and posting dates.
- Amounts, balances, fees, interest, taxes, quantities, prices, and exchange rates.
- Currencies.
- Broad categories such as groceries, rent, salary, utilities, brokerage, tax, healthcare, travel, transfer, cash withdrawal, refund, loan, insurance, subscription, or card payment.
- Merchant category codes and merchant category labels.
- Recurring flags and periodicity.
- Transaction type, direction, channel, and status.
- Security tickers, ISINs, asset classes, quantities, prices, and portfolio totals in brokerage reports, unless a field uniquely identifies the user or account.

## Output format

When redacting pasted content, return:

```text
Cleaned document:
<redacted content>

Removed data types:
- <type>: <count or "present">

Manual review notes:
- <only if needed>
```

Keep the cleaned document in the same general shape as the input. For tables, preserve columns and rows. For JSON, preserve valid JSON when practical. For CSV, preserve delimiter structure when practical.

## File workflow

For large plain-text, CSV, JSON, or statement-like files, use `scripts/redact_financial_pii.py` when available. This script performs deterministic first-pass redaction and produces an audit summary. Treat the script as a helper, not as a substitute for judgment.

Example:

```bash
python scripts/redact_financial_pii.py input.txt --output redacted.txt --audit audit.json --redact-counterparties
```

After running the script:

1. Inspect the cleaned output for missed identifiers or over-redaction.
2. Improve the result manually if needed.
3. Return the cleaned version and the removed-data audit.

For PDFs, scanned images, spreadsheets, DOCX, or broker/tax forms with layout, first extract readable text or tables using the appropriate document-processing tool available in the environment. Then apply this skill's redaction rules. If extraction quality is poor, flag manual review instead of pretending the fossilized pixels were magically solved.

## Quality checks before final response

Before returning a cleaned document, verify:

- No raw IBAN-like, card-like, account-like, passport-like, tax-ID-like, email-like, phone-like, or address-like text remains.
- No exact personal names remain unless the user explicitly required them.
- The cleaned output still preserves dates, amounts, currencies, categories, merchant category, recurring flag, and operation type.
- The removed-data list reflects what was actually removed.
- The result does not include a reversible mapping unless explicitly requested and safe for local use only.

## Reference

Use `references/redaction-policy.md` for examples, pattern guidance, placeholder policy, and common false-positive checks.

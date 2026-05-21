# Finance redaction policy

## Redaction philosophy

Financial documents often combine high-utility analytical fields with high-risk identifiers. The goal is not to make the document pretty. The goal is to remove identity, account, address, and contact data while keeping enough structure for financial analysis.

Use typed placeholders instead of partial masking. Partial masking such as keeping the last four digits can still leak information when combined with dates, merchants, or account snapshots. Preserve analytical semantics, not identifiers.

## High-risk data types

Redact these aggressively:

- IBANs: country code, check digits, and bank/account structure. They identify a real account and may include routing information.
- Domestic account numbers: especially when near labels such as account, acct, account no, routing, sort code, beneficiary account, settlement account, or payment account.
- Payment cards: validate likely primary account numbers with Luhn when possible; redact even if spaced or hyphenated.
- Government IDs: passport, ID card, national ID, driver license, SSN, EIN, TIN, taxpayer number, VAT ID, fiscal code, and local equivalents.
- Contact data: email, phone, postal address, precise location, and address-like lines.
- Names: personal names and household member names.
- Exact counterparties: redact when the analysis only needs category or recurring grouping.

## Preserve analytical value

Keep:

- Date, posting date, settlement date, tax year, pay period, and statement period.
- Amount, balance, fee, interest, dividend, tax withheld, exchange rate, unit price, and quantity.
- Currency and country-level jurisdiction when useful.
- Operation type: card payment, bank transfer, incoming transfer, salary, tax payment, ATM withdrawal, refund, fee, interest, dividend, buy, sell, deposit, withdrawal.
- Category and merchant category.
- Recurring flag or inferred recurrence.
- Account type, but not account number. Example: keep `checking account`; redact the actual account identifier.

## Placeholder guidance

Use the narrowest accurate placeholder:

- `[REDACTED_IBAN]` for validated or highly likely IBANs.
- `[REDACTED_CARD]` for likely payment cards.
- `[REDACTED_ACCOUNT_NUMBER]` for account or routing identifiers.
- `[REDACTED_TAX_ID]` for taxpayer, VAT, SSN, EIN, fiscal, or registration numbers.
- `[REDACTED_PASSPORT_OR_ID]` for government document identifiers.
- `[REDACTED_EMAIL]`, `[REDACTED_PHONE]`, `[REDACTED_ADDRESS]` for contact details.
- `[REDACTED_PERSON_NAME]` for personal names.
- `[COUNTERPARTY_001]` for exact merchant, payer, payee, employer, broker, or beneficiary names when grouping is useful.

Use stable tokens only within the current redacted document. Do not include the original mapping in the user-facing result unless explicitly requested for local-only use.

## False-positive checks

Be careful not to redact:

- Dates such as `2025-04-18`.
- Amounts such as `1,234.56` or `EUR 120.00`.
- Short reference codes that are not identity-bearing.
- ISINs and tickers in brokerage reports, unless they identify an account or person.
- Merchant categories, category labels, or operation types.

If a value could be either an identifier or an analytical code, use the surrounding label. For example, `account: 123456789` should be redacted, while `MCC: 5411` should be preserved.

## Recommended final response

Return the cleaned content first, then the removed-data audit. Keep the audit concise.

Example:

```text
Cleaned document:
2026-01-05, grocery, card payment, EUR -42.18, [COUNTERPARTY_001], recurring=false
2026-01-08, salary, incoming transfer, EUR 3200.00, [COUNTERPARTY_002], recurring=true

Removed data types:
- payment card numbers: 1
- iban/account numbers: 1
- personal names: present
- exact counterparties: 2 stable tokens

Manual review notes:
- One address-like free-text memo was redacted as a precaution.
```

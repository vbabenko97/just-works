# Review Rules

Use these rules to decide what must be surfaced for review.

## Always flag

- Missing or invalid date.
- Missing amount or currency.
- Currency conversion needed but no exchange rate is available.
- Merchant or counterparty is unreadable.
- Category confidence below `0.75`.
- Possible duplicate not safely resolvable.
- Possible transfer between owned accounts with incomplete account evidence.
- Large one-time transaction without clear category or merchant.
- Tax, debt, or investment transaction where the role of the payment is unclear.
- PDF extraction artifacts, broken rows, shifted columns, or OCR uncertainty.

## Duplicate candidate evidence

Strong duplicate candidate:

- same account, date, amount, currency, and merchant
- repeated import from the same source file or overlapping statement period

Near duplicate candidate:

- date within 1 to 3 days
- same amount and currency
- merchant text is similar
- card authorization and settlement both appear

## Transfer candidate evidence

Strong transfer candidate:

- opposite signs across two owned accounts
- same currency and amount
- dates within 0 to 3 days
- merchant or description contains transfer-like text

Possible transfer candidate:

- one side is missing
- currency exchange may be involved
- card payment, cash withdrawal, or brokerage deposit could be internal but ownership is not explicit

## Summary safeguards

- Exclude confirmed internal transfers from income and expense totals.
- Include debt payments separately from normal expenses.
- Include investment contributions separately from consumption expenses.
- Present unknown share so the user can see how much of the dataset remains unreliable.
- If review items materially change totals, label the summary as provisional.

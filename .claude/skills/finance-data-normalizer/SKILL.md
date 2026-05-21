---
name: finance-data-normalizer
description: normalize personal finance data from bank statements, csv, xlsx, pdf exports, salary records, freelance or grant income notes, investment reports, account lists, debt records, tax records, subscriptions, and manual notes into consistent transaction, account, asset, debt, monthly snapshot, and review tables. use when income, expenses, transfers, investments, taxes, debts, accounts, currencies, categories, recurring payments, duplicates, or unclear operations must be cleaned before cashflow, budget, emergency fund, tax, or investment analysis.
---

# Finance Data Normalizer

Normalize personal financial data into a clean, auditable dataset for later analysis. Do not provide investment recommendations, tax advice, or budget recommendations until the data has been cleaned and review items have been separated.

## Operating principles

- Treat normalization as data preparation, not financial planning.
- Preserve source facts. Never overwrite the original amount, currency, date text, account name, merchant text, or source filename if available.
- Avoid aggressive guessing. If a mapping, category, merchant, transfer match, or duplicate decision has confidence below `0.75`, mark it as `needs_review`.
- Separate known facts from inferred fields. Put uncertain reasoning in `notes`.
- Keep every output traceable to source rows, pages, or user notes whenever source identifiers are available.
- Use the user's provided base currency if specified. If no base currency is specified, ask for it before converting amounts. If exchange rates are missing, leave `amount_base` blank and mark the row as `needs_review`.
- Do not infer sensitive tax or legal conclusions. Normalize tax-related transactions and flag gaps only.

## Required workflow

1. Inventory the inputs.
   - Identify each source type: bank statement, card statement, salary record, investment report, loan record, account list, cash note, subscription list, or manual note.
   - Record the apparent date range, currency, account name, owner label if provided, and source filename or description.
   - Note any missing essentials: base currency, account list, opening or closing balances, exchange rates, or statement period.

2. Extract and standardize transactions.
   - Normalize dates to `yyyy-mm-dd` where possible.
   - Preserve original transaction amounts in `amount_original` and original currency in `currency`.
   - Use signed amounts consistently: positive for inflows, negative for outflows.
   - Normalize `amount_base` only when a base currency and conversion rate are available or explicitly provided.
   - Standardize merchant names conservatively. Keep raw merchant clues in `notes` when useful.

3. Classify transaction type and category.
   - Assign exactly one top-level flow bucket: `income`, `fixed_expenses`, `variable_expenses`, `transfers`, `investments`, `taxes`, or `debt_payments`.
   - Assign `category` and `subcategory` using the taxonomy in `references/category-taxonomy.md` when helpful.
   - Mark recurring transactions using `recurring_flag` only when a repeated pattern is supported by dates, amounts, merchant names, or user-provided subscription data.

4. Detect duplicates and internal transfers.
   - Detect exact duplicates by same date, amount, currency, merchant, and account.
   - Detect near duplicates by close date, equal or near-equal amount, same currency, similar merchant, or repeated imported source rows.
   - Detect internal transfers by matching opposite-signed amounts across user's own accounts within a reasonable date window.
   - Do not delete suspected duplicates or transfers silently. Flag them and explain the evidence in `notes`.

5. Build normalized output tables.
   - Produce the required tables listed in the output schema.
   - Add `needs_review` to rows where `confidence < 0.75` or where required fields are missing.
   - Keep unknown or unclear operations visible in the suspicious or unclear operations list.

6. Summarize data quality and cashflow.
   - Report income, expenses, savings rate, net cashflow, and unknown share from cleaned rows.
   - Separate confirmed metrics from provisional metrics when review items materially affect totals.
   - Explicitly state assumptions such as base currency, date range, excluded accounts, missing conversion rates, and whether transfers were excluded from income or expense totals.

## Output schema

Use the detailed schema in `references/output-schema.md` for column definitions. Unless the user requests another format, return outputs as markdown tables for small datasets and as downloadable CSV/XLSX files for larger datasets.

### transactions

Required columns:

`transaction_id`, `date`, `source_account`, `currency`, `amount_original`, `amount_base`, `flow_bucket`, `category`, `subcategory`, `merchant`, `recurring_flag`, `confidence`, `review_status`, `notes`, `source_reference`

### accounts

Required columns:

`account_id`, `account_name`, `account_type`, `institution`, `currency`, `opening_balance`, `closing_balance`, `balance_date`, `confidence`, `review_status`, `notes`

### assets

Required columns:

`asset_id`, `asset_type`, `asset_name`, `account_id`, `currency`, `value_original`, `value_base`, `valuation_date`, `confidence`, `review_status`, `notes`

### debts

Required columns:

`debt_id`, `debt_type`, `lender`, `currency`, `principal_original`, `principal_base`, `interest_rate`, `minimum_payment`, `due_date`, `confidence`, `review_status`, `notes`

### monthly_snapshot

Required columns:

`month`, `base_currency`, `income_total`, `fixed_expenses_total`, `variable_expenses_total`, `taxes_total`, `debt_payments_total`, `investment_contributions_total`, `transfers_net`, `net_cashflow`, `savings_rate`, `unknown_amount`, `unknown_share`, `notes`

### suspicious_or_unclear_operations

Required columns:

`item_id`, `date`, `source_account`, `currency`, `amount_original`, `merchant`, `issue_type`, `confidence`, `reason`, `suggested_next_step`, `source_reference`

## Summary format

Return a concise summary after the tables or files:

```text
Summary
- date range: [start] to [end]
- base currency: [currency or missing]
- income total: [amount]
- expense total: [amount]
- net cashflow: [amount]
- savings rate: [percent]
- unknown share: [percent]
- review items: [count]
- duplicate candidates: [count]
- internal transfer candidates: [count]
- key assumptions: [short list]
```

Use this formula for savings rate when income is positive:

`savings_rate = net_cashflow / income_total`

If income is zero or missing, leave savings rate blank and explain why in `notes`.

## Confidence scoring

Use this default scale:

- `0.95` to `1.00`: exact source value or explicit user-provided mapping.
- `0.85` to `0.94`: strong inference from repeated pattern, exact merchant match, or consistent statement structure.
- `0.75` to `0.84`: reasonable inference with minor ambiguity.
- `0.50` to `0.74`: plausible but uncertain; mark `needs_review`.
- below `0.50`: unknown or unreliable; mark `needs_review` and avoid using it in confirmed metrics unless clearly labeled provisional.

`review_status` must be one of: `ok`, `needs_review`, `duplicate_candidate`, `transfer_candidate`, `excluded`, `unknown`.

## File handling guidance

- For CSV or XLSX sources, inspect headers, sample rows, date formats, decimal separators, currencies, signs, and account identifiers before transforming.
- For PDFs, extract tables if possible and manually verify ambiguous rows against visible page layout when extraction looks unreliable.
- For scanned PDFs or image-only statements, state that OCR quality may affect confidence and mark low-confidence rows for review.
- For manual notes, preserve the original wording in `notes` when a value is inferred.

## Validation helper

After producing CSV files, use `scripts/validate_finance_outputs.py` when possible to check required columns, basic numeric fields, confidence bounds, review status values, date formats, and summary counts.

Example:

```bash
python scripts/validate_finance_outputs.py --input-dir ./normalized_finance --base-currency eur
```

The validator does not prove financial correctness. It catches structural errors, because apparently columns can rebel too.

## Hard limits

- Do not recommend securities, portfolio allocations, brokers, tax strategies, loans, or debt restructuring as part of this skill.
- Do not claim data is complete unless every source period, account, and balance reconciliation is supported.
- Do not hide unknowns to make summaries look cleaner.
- Do not merge currencies without explicit exchange rates or user approval.

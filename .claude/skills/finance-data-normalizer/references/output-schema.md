# Output Schema

Use these schemas as the default normalized output contract.

## Common rules

- Dates use `yyyy-mm-dd`; months use `yyyy-mm`.
- Currency codes use ISO-style uppercase codes such as `EUR`, `USD`, `UAH`, or `CAD` when known.
- Amounts are numeric, signed, and use dot decimal notation.
- `amount_original` preserves the transaction currency value.
- `amount_base` is converted into the declared base currency only when a conversion rate is available.
- `confidence` is a decimal between `0` and `1`.
- `review_status` is one of `ok`, `needs_review`, `duplicate_candidate`, `transfer_candidate`, `excluded`, or `unknown`.
- `source_reference` should identify the source file, page, sheet, row, transaction id, or user note when available.

## transactions.csv

Required columns:

- `transaction_id`: stable unique id assigned during normalization.
- `date`: transaction date in `yyyy-mm-dd`.
- `source_account`: normalized account name or id.
- `currency`: original transaction currency.
- `amount_original`: signed amount in original currency.
- `amount_base`: signed amount in base currency, blank if not available.
- `flow_bucket`: one of `income`, `fixed_expenses`, `variable_expenses`, `transfers`, `investments`, `taxes`, or `debt_payments`.
- `category`: normalized category.
- `subcategory`: normalized subcategory.
- `merchant`: normalized merchant or counterparty.
- `recurring_flag`: `true`, `false`, or blank if unknown.
- `confidence`: decimal confidence score.
- `review_status`: review status value.
- `notes`: short explanation of uncertainty, source quirks, or transformation decisions.
- `source_reference`: source trace.

## accounts.csv

Required columns:

- `account_id`: stable account id.
- `account_name`: user-facing account name.
- `account_type`: `checking`, `savings`, `credit_card`, `cash`, `brokerage`, `deposit`, `loan`, `mortgage`, `tax`, `other`, or `unknown`.
- `institution`: bank, broker, lender, wallet, or blank if unknown.
- `currency`: account currency.
- `opening_balance`: opening balance when known.
- `closing_balance`: closing balance when known.
- `balance_date`: balance date in `yyyy-mm-dd`.
- `confidence`: decimal confidence score.
- `review_status`: review status value.
- `notes`: account-level notes.

## assets.csv

Required columns:

- `asset_id`: stable asset id.
- `asset_type`: `cash`, `deposit`, `brokerage`, `security`, `fund`, `crypto`, `real_estate`, `other`, or `unknown`.
- `asset_name`: asset label.
- `account_id`: linked account id when available.
- `currency`: valuation currency.
- `value_original`: valuation in original currency.
- `value_base`: valuation in base currency when available.
- `valuation_date`: date of value.
- `confidence`: decimal confidence score.
- `review_status`: review status value.
- `notes`: valuation notes.

## debts.csv

Required columns:

- `debt_id`: stable debt id.
- `debt_type`: `credit_card`, `personal_loan`, `mortgage`, `student_loan`, `tax_debt`, `informal_debt`, `other`, or `unknown`.
- `lender`: lender or counterparty.
- `currency`: debt currency.
- `principal_original`: outstanding amount in original currency.
- `principal_base`: outstanding amount in base currency when available.
- `interest_rate`: annual rate if known, otherwise blank.
- `minimum_payment`: required payment if known, otherwise blank.
- `due_date`: next due date if known.
- `confidence`: decimal confidence score.
- `review_status`: review status value.
- `notes`: debt notes.

## monthly_snapshot.csv

Required columns:

- `month`: `yyyy-mm`.
- `base_currency`: base currency used.
- `income_total`: confirmed income total.
- `fixed_expenses_total`: confirmed fixed expenses total as a positive magnitude.
- `variable_expenses_total`: confirmed variable expenses total as a positive magnitude.
- `taxes_total`: confirmed taxes total as a positive magnitude.
- `debt_payments_total`: confirmed debt payments total as a positive magnitude.
- `investment_contributions_total`: confirmed investment contributions total as a positive magnitude.
- `transfers_net`: net transfers if relevant, usually zero across owned accounts.
- `net_cashflow`: income minus expenses, taxes, debt payments, and investment contributions according to stated assumptions.
- `savings_rate`: `net_cashflow / income_total` when income is positive.
- `unknown_amount`: absolute value of transactions that are unknown or need review.
- `unknown_share`: `unknown_amount / total_absolute_transaction_volume`.
- `notes`: assumptions and caveats.

## suspicious_or_unclear_operations.csv

Required columns:

- `item_id`: stable issue id.
- `date`: transaction date when available.
- `source_account`: account name or id.
- `currency`: original currency.
- `amount_original`: original signed amount.
- `merchant`: merchant or counterparty.
- `issue_type`: `unknown_category`, `unknown_currency`, `missing_amount`, `missing_date`, `duplicate_candidate`, `transfer_candidate`, `unusual_amount`, `possible_fee`, `possible_tax`, `possible_debt`, `source_parse_error`, or `other`.
- `confidence`: confidence score.
- `reason`: why the item needs review.
- `suggested_next_step`: concrete data clarification needed, not financial advice.
- `source_reference`: source trace.

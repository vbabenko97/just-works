# Category Taxonomy

Use this taxonomy as a default. Prefer user-provided categories when they are explicit and internally consistent.

## Flow buckets

Every transaction receives exactly one flow bucket:

- `income`
- `fixed_expenses`
- `variable_expenses`
- `transfers`
- `investments`
- `taxes`
- `debt_payments`

## Income categories

- `salary`: base salary, payroll, wage payments.
- `bonus`: bonus, commission, performance payout.
- `freelance`: contract work, consulting, client payments.
- `grant`: research grant, fellowship, stipend.
- `refund`: refunds that offset prior expenses; do not count as income unless the user wants gross inflows.
- `interest_income`: bank interest.
- `dividend_income`: dividends and distributions.
- `other_income`: income that does not fit above.

## Fixed expense categories

- `housing`: rent, mortgage service fees not counted as principal, building fees.
- `utilities`: electricity, gas, water, heating, internet, phone.
- `insurance`: health, home, car, travel, life.
- `subscriptions`: software, media, memberships, cloud services.
- `education_fixed`: tuition or recurring course fees.
- `childcare_or_family_support`: recurring care or support obligations.
- `other_fixed`: recurring fixed cost not otherwise classified.

## Variable expense categories

- `groceries`
- `restaurants`
- `transport`
- `fuel`
- `travel`
- `healthcare`
- `pharmacy`
- `clothing`
- `household`
- `electronics`
- `entertainment`
- `education_variable`
- `gifts_donations`
- `cash_withdrawal`
- `fees`
- `large_one_time_purchase`
- `other_variable`

## Transfers

Use `transfers` for money movement between accounts owned by the user, including:

- checking to savings
- bank to brokerage
- cash withdrawal if later represented as cash account inflow
- credit card payment from checking to card account
- currency exchange between owned accounts

If ownership is unclear, mark `transfer_candidate` or `needs_review`.

## Investments

Use `investments` for contributions, purchases, sales, and brokerage cash movements. Do not classify investment performance as income unless the report provides realized income such as dividends or interest.

Suggested subcategories:

- `brokerage_deposit`
- `brokerage_withdrawal`
- `security_purchase`
- `security_sale`
- `dividend`
- `interest`
- `brokerage_fee`
- `other_investment`

## Taxes

Use `taxes` for payroll tax, income tax, property tax, tax refunds, penalties, or tax authority payments. Normalize the transaction, but do not infer legal treatment.

Suggested subcategories:

- `income_tax`
- `payroll_tax`
- `property_tax`
- `tax_refund`
- `tax_penalty_or_interest`
- `other_tax`

## Debt payments

Use `debt_payments` for loan repayments, credit card minimum payments, mortgage principal and interest payments, and informal debt repayment when clear.

Suggested subcategories:

- `credit_card_payment`
- `loan_principal`
- `loan_interest`
- `mortgage_payment`
- `informal_debt_payment`
- `debt_fee`
- `other_debt_payment`

## Recurring detection

Mark `recurring_flag` as `true` only when at least one of these is true:

- same or similar merchant appears on a monthly, weekly, annual, or payroll-like cadence
- same amount repeats with a consistent label
- user provided a subscription or recurring payment list
- statement label explicitly indicates standing order, direct debit, subscription, salary, or recurring payment

If suspected but not supported, leave blank or `false` and add a note.

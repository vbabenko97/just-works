# Metric Definitions

Use these formulas consistently. When inputs are incomplete, calculate what is defensible and state the limitation.

## Net Worth

```text
net_worth = total_assets - total_liabilities
net_worth_change = closing_net_worth - opening_net_worth
net_worth_change_percent = net_worth_change / abs(opening_net_worth)
```

Use opening and closing values from balance-sheet snapshots. Cashflow alone is not enough to calculate net worth because market changes, debt changes, asset purchases, and missing accounts can distort the result.

## Income

```text
true_income = salary + freelance + business + interest + other earned or recurring income
cash_in = true_income + refunds + reimbursements + gifts + other non-recurring inflows
```

For financial health analysis, separate salary from other income. A high concentration in one employer or client is a stability risk.

## Expenses

```text
total_expenses = fixed + variable + discretionary + one_off + fees + interest_expense
required_expenses = fixed + essential_variable + minimum_debt_payments
```

Exclude transfers between owned accounts. Exclude asset purchases from consumption spending, but mention them as cash deployment. For loan payments, separate interest expense from principal repayment when data allows.

## Savings Rate

```text
gross_savings_rate = (gross_income - total_expenses) / gross_income
net_savings_rate = (net_income - total_expenses) / net_income
```

If only take-home income is available, report net savings rate only. If retirement contributions are excluded from take-home pay, note that visible savings rate understates total saving.

## Burn Rate

```text
required_burn_rate = fixed_expenses + essential_variable_expenses + minimum_debt_payments
full_burn_rate = total_expenses excluding transfers and non-consumption movements
```

For annual or quarterly periods, convert to monthly averages:

```text
monthly_average = period_total / number_of_months
```

## Runway

```text
required_runway_months = liquid_emergency_assets / required_burn_rate
full_runway_months = liquid_emergency_assets / full_burn_rate
```

If `liquid_emergency_assets` is unavailable, use clearly liquid cash-like accounts only if supplied. Do not include retirement accounts, illiquid property, restricted assets, or volatile speculative assets unless the user explicitly asks for a broader liquidation scenario.

## Debt Burden

Useful ratios:

```text
debt_to_assets = total_liabilities / total_assets
debt_to_income = total_liabilities / monthly_income
minimum_payment_to_income = monthly_minimum_debt_payments / monthly_income
high_interest_debt = debt with apr >= 10 percent
```

Thresholds are context dependent. Flag high-interest debt, growing balances, minimum-payment behavior, and debt payments that crowd out emergency savings.

## Budget Leak Heuristics

Flag likely leaks when one or more apply:

- recurring charge appears monthly but is not essential;
- subscription is duplicated across tools or services;
- fee or interest category is non-zero and avoidable;
- category grew faster than income compared with prior period;
- merchant has many small transactions that add up materially;
- cash withdrawals are frequent or unexplained;
- uncategorized spending exceeds 5 percent of expenses;
- discretionary spending exceeds the user's stated target;
- one-off spending repeats often enough to be a pattern;
- foreign exchange or payment fees appear repeatedly.

## Red Flag Heuristics

Always review:

- negative net cashflow;
- declining net worth;
- emergency fund below target months;
- high-interest debt outstanding;
- one income source provides more than 80 percent of true income;
- full burn rate increased while income was flat or down;
- fixed expenses consume more than half of net income;
- missing liabilities or missing account balances;
- multi-currency mismatch between income, expenses, debt, and assets;
- investment contributions while emergency fund is weak and high-interest debt remains.

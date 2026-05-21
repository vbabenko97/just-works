# Data Contract

Use this contract when transforming user-provided finance data into a normalized structure for repeatable monthly, quarterly, or annual audits.

## Preferred JSON Shape

```json
{
  "period": {
    "label": "2026-04",
    "start": "2026-04-01",
    "end": "2026-04-30",
    "base_currency": "USD"
  },
  "liquid_emergency_assets": 12000,
  "transactions": [
    {
      "date": "2026-04-01",
      "description": "Employer payroll",
      "merchant": "Employer",
      "amount": 5000,
      "currency": "USD",
      "type": "income",
      "category": "salary",
      "expense_class": null,
      "account": "checking",
      "tags": ["salary"]
    }
  ],
  "accounts": [
    {
      "name": "checking",
      "type": "bank",
      "currency": "USD",
      "opening_balance": 2500,
      "closing_balance": 3200,
      "included_in_assets": true,
      "liquid": true
    }
  ],
  "assets": [
    {
      "name": "brokerage",
      "type": "investment",
      "currency": "USD",
      "opening_value": 18000,
      "closing_value": 19200,
      "liquidity": "liquid"
    }
  ],
  "liabilities": [
    {
      "name": "credit card",
      "type": "credit_card",
      "currency": "USD",
      "opening_balance": 1400,
      "closing_balance": 900,
      "apr": 24.9,
      "minimum_payment": 50
    }
  ],
  "previous_period": {
    "label": "2026-03",
    "income_total": 5000,
    "expense_total": 3800,
    "savings_rate_net": 0.24,
    "closing_net_worth": 32000,
    "full_burn_rate": 3800,
    "required_burn_rate": 2400
  },
  "goals": {
    "emergency_fund_months": 6,
    "monthly_savings_target": 1000,
    "debt_payoff_priority": true
  }
}
```

## Transaction Field Rules

### Amount Sign Convention

Prefer positive amounts for both income and expenses, with `type` indicating direction. If the source uses signed amounts, normalize them before calculation.

Accepted transaction types:

- `income`
- `expense`
- `transfer`
- `debt_payment`
- `asset_purchase`
- `refund`
- `reimbursement`
- `fee`
- `interest`
- `unknown`

Treat `fee` as an expense unless context shows otherwise. Treat `refund` and `reimbursement` as offsets, not true income, unless the user explicitly wants cash received rather than economic income.

### Expense Classes

Accepted expense classes:

- `fixed`: recurring commitments such as rent, mortgage, insurance, subscriptions, required bills.
- `variable`: essential but usage-dependent categories such as groceries, utilities, transport, medicine.
- `discretionary`: optional lifestyle spending such as restaurants, shopping, entertainment, travel, hobbies.
- `one_off`: unusual or non-recurring items such as repairs, relocation, medical events, large equipment, taxes.

When class is missing, infer conservatively from category and merchant, then state the assumption.

## Balance Sheet Rules

### Accounts vs Assets

Cash and investment accounts are assets. If accounts are listed separately and also included in `assets`, avoid double counting by using either:

1. accounts with `included_in_assets = true` plus non-account assets; or
2. the explicit `assets` list only, if it already includes accounts.

State which approach is used.

### Liabilities

Use positive balances for amounts owed. A decrease in liability increases net worth. Include APR and minimum payment when available because debt burden and high-interest risk depend on them.

## Multi-Currency Rules

If data includes multiple currencies:

1. Use supplied FX rates if available and labeled by date or period.
2. If rates are missing, report per currency and mark consolidated totals as unavailable.
3. Flag currency mismatch when income, expenses, debts, and assets are materially denominated in different currencies.

## Data Quality Checklist

Before finalizing an audit, check:

- Are all active accounts included?
- Are credit cards and loans included as liabilities?
- Are opening and closing balances available?
- Are transfers excluded from consumption spending?
- Are refunds treated consistently?
- Are large uncategorized transactions reviewed?
- Are cash withdrawals explained?
- Are foreign currency transactions converted or separated?
- Is previous-period data available for comparison?

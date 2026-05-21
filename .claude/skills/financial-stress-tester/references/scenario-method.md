# Scenario Method

## Input Normalization

Convert all values to a single base currency before calculating runway. If currencies differ and no exchange rate is provided, ask for the rate or use clearly labeled placeholders.

Use monthly cadence:

- `monthly_income`: stable monthly net income after taxes.
- `required_expenses`: minimum recurring expenses that cannot be cut quickly.
- `reducible_expenses`: expenses that can be cut within 30 days.
- `survival_expenses`: required expenses after emergency cuts. If missing, use required expenses plus debt minimums.
- `accessible_liquidity`: cash and near-cash available within 7 days without major loss.
- `protected_reserve`: cash that should not be spent except for survival, medical, legal, or relocation needs.
- `locked_amount`: balance assumed unavailable in a frozen institution scenario.

## Core Formulas

Monthly deficit:

```text
monthly_deficit = max(0, stressed_monthly_expenses - stressed_monthly_income)
```

Runway in months:

```text
runway_months = accessible_liquidity / monthly_deficit
```

If monthly deficit is zero or negative, runway is not liquidity-limited under that scenario. Still discuss concentration, currency, and access risks.

Fixed-cost ratio:

```text
fixed_cost_ratio = required_expenses / monthly_income
```

Emergency fund target:

```text
target_liquidity = survival_expenses * target_months + near_term_one_time_risks
```

Use 3 months as a bare minimum, 6 months as a normal resilience target, and 9 to 12 months when income is unstable, relocation risk is real, debt is high, dependents are involved, or local infrastructure risk is elevated.

## Scenario Rules

### 100 Percent Income Loss

Model income as zero for 3, 6, and 9 months. Compare accessible liquidity against survival burn for each horizon.

Report:

- How many months are covered.
- Which horizon fails first.
- Cash gap at 3, 6, and 9 months.
- Whether debt payments remain serviceable.

### 30 Percent Income Reduction

Set stressed income to 70 percent of baseline monthly income. Use baseline required expenses first, then survival expenses after cuts.

Flag a failure if required expenses plus debt minimums exceed stressed income.

### Urgent Relocation

Apply a one-time shock for travel, deposits, temporary housing, documents, pet or family logistics, equipment movement, and duplicate rent. If no estimate is provided, ask for one or use a broad placeholder and label it clearly.

Relocation stress should also include 1 to 2 months of duplicate expenses when plausible.

### 20 Percent Required Expense Increase

Increase required expenses by 20 percent. Keep reducible expenses separate so the user sees whether lifestyle cuts actually solve the problem.

### Currency Devaluation

Model the mismatch between income currency and expense currency.

If expenses are in a stronger or foreign currency and income is in a weaker currency, increase the affected expense share:

```text
stressed_expenses = local_expenses + fx_exposed_expenses * (1 + devaluation_rate)
```

If income is in the weakening currency and expenses are in the stronger currency, reduce real income or increase expenses equivalently. Do not double count both unless the user explicitly wants a combined shock.

### Frozen Bank Or Broker Access

Remove the largest single institution balance or the user-specified frozen balance from accessible liquidity. Do not assume brokerage assets are liquid if market access, withdrawal rails, compliance checks, or sanctions screening could block withdrawals.

Report whether essential spending can continue from other institutions for 30, 60, and 90 days.

### Medical Or Family Expense

Apply a one-time shock. Prioritize immediate cash availability and insurance deductibles. Do not recommend delaying essential medical care for financial optimization.

### Blackout Or Infrastructure Shock

Apply one-time equipment or logistics costs and recurring resilience costs: power bank, generator fuel, backup internet, water, transport, coworking, device repair, or temporary lodging. Treat work-enabling connectivity as a stabilizer, not luxury spending.

### Delayed Salary, Invoice, Or Grant

Set income to zero or reduced until the expected payment date. If the payment is uncertain, do not count it as available liquidity. Model a late-payment bridge separately from a permanent income-loss scenario.

## Risk Score Calibration

Start with runway:

- More than 12 months: 2.
- 6 to 12 months: 4.
- 3 to 6 months: 6.
- 1 to 3 months: 8.
- Less than 1 month: 10.

Adjust upward:

- Add 1 if one institution holds more than 50 percent of accessible liquidity.
- Add 1 if fixed-cost ratio exceeds 60 percent.
- Add 1 if income is unstable, delayed, grant-based, commission-based, or single-client.
- Add 1 if debt minimums exceed 15 percent of income.
- Add 1 if FX mismatch is material.
- Add 1 if blackout, relocation, legal, war-risk, or medical exposure is active.

Adjust downward only when there is redundant liquidity across institutions, multiple stable income sources, low fixed costs, and no high-interest debt. Cap final score between 1 and 10.

## Preventive Action Library

Match actions to the bottleneck:

- Runway too short: build cash buffer, pause new investing, redirect surplus, sell non-core low-friction assets.
- Expense base too rigid: renegotiate rent, reduce subscriptions, lower recurring commitments, refinance or restructure debt.
- Bank concentration: split cash across at least two institutions and payment rails.
- Broker concentration: keep survival liquidity outside brokerage accounts.
- FX mismatch: hold part of the emergency fund in the currency of expenses.
- Delayed income risk: maintain a payment-delay buffer and written invoice follow-up process.
- Relocation risk: pre-price the move, keep documents ready, reserve cash for deposits and travel.
- Medical risk: verify insurance coverage, deductibles, exclusions, and emergency cash access.
- Blackout risk: fund backup power, connectivity, water, and work-critical equipment before speculative investments.

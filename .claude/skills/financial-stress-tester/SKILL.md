---
name: financial-stress-tester
description: model personal finance stress scenarios including income loss, salary cuts, delayed payments, relocation, rising required expenses, currency devaluation, inflation, medical or family emergencies, bank or broker access freezes, blackout disruption, war-risk logistics, grant delays, debt pressure, emergency fund durability, cashflow fragility, portfolio liquidity, and whether investing plans should pause until survival liquidity is secure.
---

# Financial Stress Tester

## Overview

Stress-test personal finances against realistic disruption scenarios. Focus on survival liquidity, monthly cashflow, debt obligations, asset accessibility, and preventive actions before any investing discussion.

This skill is for resilience analysis, not personalized legal, tax, insurance, or investment advice. State assumptions clearly and avoid pretending that sparse inputs are precise.

## Default Workflow

1. Gather or infer the finance snapshot.
2. Normalize all values to one base currency and monthly cadence.
3. Separate expenses into required, reducible, and optional categories.
4. Build a liquidity stack from safest and most accessible to least desirable.
5. Run the required stress scenarios.
6. Score each scenario from 1 to 10.
7. Produce an action plan sorted by urgency and reversibility.

Use `references/scenario-method.md` for formulas, scoring, and scenario rules.

When the user provides enough numeric data, prefer running `scripts/stress_test.py` for a deterministic first pass, then interpret the results in plain English.

## Minimum Inputs To Request

Ask for only the missing inputs that materially change the result. If the user wants an immediate test, proceed with explicit assumptions.

Minimum useful snapshot:

- Monthly net income by source and currency.
- Required monthly expenses: rent, utilities, food, insurance, transport, debt minimums, dependent support, subscriptions that cannot be cancelled immediately.
- Reducible monthly expenses: dining, entertainment, shopping, travel, optional subscriptions, discretionary upgrades.
- Liquid cash by institution and currency.
- Near-cash assets: deposits, money market funds, short-term bonds, treasury bills, savings accounts, stable cash equivalents.
- Invested assets by account or broker, including withdrawal limits, tax penalties, and currency.
- Debt balances, minimum payments, rates, and whether payments can be paused.
- One-time shock estimates: relocation, medical or family expense, urgent equipment replacement, blackout logistics.
- Upcoming irregular income: bonus, grant, invoice, delayed salary, tax refund.

## Expense Triage

Classify expenses this way:

1. Core survival: housing, basic food, medication, insurance, utilities, phone or internet needed for work, debt minimums, dependent care.
2. Stabilizers: transport to work, backup power or connectivity, essential equipment repair, immigration or relocation paperwork, professional tools.
3. Reducible: subscriptions, restaurants, non-essential shopping, convenience spending, travel, hobbies, upgrades.
4. Cut immediately under severe stress: luxury spending, speculative investing, discretionary donations, duplicate services, high-friction recurring charges.

Never recommend cutting medication, essential care, legal obligations, or safety-related expenses before discretionary spending.

## Asset Protection Rules

Separate assets by role before liquidation advice:

- Do not touch first: cash needed for 1 to 2 months of survival spending, rent deposit, medical reserve, tax reserve, visa or relocation reserve, critical work equipment reserve.
- Use early if needed: idle checking balances, excess cash above the protected reserve, redundant FX cash, maturing deposits without major penalties.
- Use middle: low-volatility taxable assets, short-term bond or treasury funds, non-core investments with low tax friction.
- Liquidate late: retirement accounts, long-term concentrated positions, assets with large tax penalties, illiquid private investments, core professional equipment, housing deposits.
- Treat frozen or inaccessible balances as unavailable for runway until access is restored.

## Required Scenarios

Always include these scenarios unless the user explicitly narrows scope:

1. 100 percent income loss for 3, 6, and 9 months.
2. 30 percent income reduction.
3. Urgent relocation.
4. 20 percent increase in required expenses.
5. Currency devaluation affecting income, expenses, or both.
6. Frozen access to one bank, broker, or payment rail.
7. Unexpected medical or family expense.

Add blackout, war-risk, grant delay, invoice delay, urgent equipment purchase, or broker risk scenarios when the user's situation mentions them or the country context makes them relevant.

## Output Template

Use this structure by default:

# Financial Stress Test

## TL;DR
One concise paragraph with the survival verdict, worst scenario, and first preventive action.

## Inputs and Assumptions
List the numbers used, missing values, and conservative assumptions.

## Baseline Snapshot
- Monthly net income:
- Required expenses:
- Reducible expenses:
- Total monthly burn:
- Survival burn after cuts:
- Liquid runway:
- Debt pressure:
- Institution concentration:

## Scenario Matrix
For each scenario, include:

- Scenario:
- Trigger modeled:
- Runway:
- Expenses to cut first:
- Assets not to touch:
- Assets to liquidate last:
- Risk score:
- Preventive action:

## Failure Points
Name the specific bottlenecks: cash concentration, currency mismatch, fixed-cost ratio, debt minimums, delayed income, uninsured medical exposure, broker access, or fragile infrastructure.

## Priority Actions
Sort actions into:

1. Do this week.
2. Do this month.
3. Do before investing more.

## Investment Gate
State whether new investing should continue, pause, or be reduced until emergency liquidity is adequate. Tie the decision to runway, debt pressure, and access risk.

## Scoring Rules

Use a 1 to 10 risk score:

- 1 to 2: robust, more than 12 months survival runway, diversified access, low fixed-cost pressure.
- 3 to 4: manageable, 6 to 12 months runway, some concentration or FX risk.
- 5 to 6: fragile, 3 to 6 months runway, meaningful fixed-cost or access risk.
- 7 to 8: dangerous, 1 to 3 months runway, debt pressure or liquidity traps.
- 9 to 10: critical, less than 1 month runway, unavoidable obligations exceed accessible cash, or key funds are frozen.

Increase risk by 1 to 2 points for concentrated bank or broker access, unstable income, high-interest debt, medical exposure, legal deadlines, or active blackout or war-risk constraints. Cap at 10.

## Using The Script

If numeric inputs are available, create a JSON file and run:

```bash
python scripts/stress_test.py input.json
```

Use the script output as a calculation baseline. Then add judgment: what the user should cut, protect, diversify, or delay.

## Style Rules

Be direct and concrete. Prefer harsh-but-useful realism over motivational fog. Do not moralize past spending. Do not assume the user can easily replace income. Do not recommend selling volatile or tax-advantaged assets before checking cash, near-cash, penalties, and access risk.

---
name: cashflow-and-net-worth-auditor
description: analyze personal cashflow, income, expenses, savings rate, burn rate, runway, net worth, assets, liabilities, debt load, salary stability, lifestyle inflation, and budget leaks. use for monthly, quarterly, or annual financial audits; normalized bank transactions; account snapshots; balance sheets; emergency fund checks; debt triage; and deciding whether savings, debt repayment, or investing discussions are appropriate.
---

# Cashflow and Net Worth Auditor

## Purpose

Perform a recurring personal finance audit that explains how much money came in, how much went out, what remained, and whether net worth actually improved after accounting for assets, liabilities, debt, and recurring obligations.

This skill is for analysis and planning support. Do not present the output as legal, tax, accounting, or regulated financial advice. Do not recommend specific investments, securities, brokers, funds, or asset allocations.

## Core Rules

1. Use English only in all analysis, headings, warnings, labels, and final reports.
2. Start from the supplied data, not vibes. If data is incomplete, state what is missing and provide the most defensible partial audit.
3. Separate cashflow from net worth. Cashflow explains inflows and outflows during the period. Net worth explains assets minus liabilities at period boundaries.
4. Avoid double counting. If account balances are already included in assets, do not add them again. If the data model is unclear, state the assumption.
5. Do not provide investment recommendations until emergency fund coverage and debt burden have been assessed.
6. Treat transfers, credit card payments, loan principal payments, and asset purchases carefully. They may move money between balance-sheet accounts rather than create true consumption expense.
7. Always flag uncertainty caused by missing accounts, missing liabilities, uncategorized transactions, missing FX rates, or incomplete opening and closing balances.
8. If multiple currencies appear and reliable FX rates are missing, calculate per currency and avoid pretending there is one clean consolidated number. Humanity invented currencies, then spreadsheets, then suffering.

## Expected Inputs

Use the user's files, pasted data, or structured notes. Accept CSV, spreadsheet, JSON, markdown tables, exported bank transactions, account snapshots, asset lists, liability lists, income notes, and goals.

Prefer this normalized input structure when asking for or transforming data:

- `period`: label, start date, end date, base currency.
- `transactions`: date, amount, currency, account, description, merchant, category, type, expense class, tags.
- `accounts`: name, type, currency, opening balance, closing balance, whether included in assets.
- `assets`: name, type, currency, opening value, closing value, liquidity class.
- `liabilities`: name, type, currency, opening balance, closing balance, APR, minimum payment.
- `income sources`: salary, freelance, interest, refunds, reimbursements, transfers, other.
- `goals`: emergency fund target, debt payoff target, savings target, planned large expenses.
- `previous period`: prior audit summary or prior-period metrics when available.

For detailed schemas and normalization rules, consult `references/data_contract.md`.

## Workflow

### 1. Validate and Normalize

- Identify the audit period and base currency.
- Classify each transaction as income, expense, transfer, debt payment, asset purchase, refund, reimbursement, fee, or unknown.
- Classify expenses as fixed, variable, discretionary, or one-off.
- Preserve raw categories and merchants when available.
- Separate salary from other income to evaluate dependence on one income source.
- Check whether opening and closing balances exist for accounts, assets, and liabilities.
- Check whether previous-period data exists for comparison.

### 2. Calculate Net Worth

Calculate opening and closing net worth as:

`net worth = total assets - total liabilities`

Include liquid accounts, investments, property, receivables, and other meaningful assets if values are supplied. Include credit cards, personal loans, mortgages, student loans, taxes payable, and other debts if balances are supplied.

Report:

- opening net worth;
- closing net worth;
- absolute change;
- percentage change when opening net worth is not zero;
- drivers of change when data supports attribution.

### 3. Calculate Income

Group income by source:

- salary or main job;
- freelance or consulting;
- business income;
- investment income;
- interest;
- reimbursements;
- refunds;
- gifts;
- other.

State whether refunds and reimbursements are excluded from true income when they merely reverse earlier expenses.

### 4. Calculate Expenses

Group expenses into:

- fixed: rent, mortgage, subscriptions, insurance, required recurring bills;
- variable: groceries, utilities, fuel, transport, medical, child care;
- discretionary: restaurants, entertainment, shopping, travel, hobbies;
- one-off: repairs, relocation, equipment, medical events, taxes, unusual purchases.

Produce top expense categories and merchants. Highlight uncategorized spend separately instead of hiding it in a tidy lie wearing a business-casual shirt.

### 5. Calculate Savings Rate

Calculate both gross and net savings rates when possible:

- gross savings rate = (gross income - total expenses) / gross income;
- net savings rate = (net income - total expenses) / net income.

If gross income is unavailable, report only net savings rate. If expense data includes transfers to savings or investments, avoid treating those transfers as consumption.

### 6. Calculate Burn Rate and Runway

Calculate two burn rates:

- required burn rate: fixed expenses plus required variable essentials and minimum debt payments;
- full burn rate: all expenses excluding transfers and non-consumption balance-sheet movements.

Calculate runway as:

`runway months = liquid emergency assets / monthly burn rate`

Report runway using both required burn and full burn when possible. If liquid assets are unavailable, explain that runway cannot be calculated reliably.

### 7. Detect Budget Leaks

Identify money leaks using recurring small charges, unused subscriptions, fees, avoidable interest, impulse categories, duplicate tools, frequent convenience spending, cash withdrawals without purpose, uncategorized merchant clusters, foreign exchange fees, and expenses that grew faster than income.

Use `references/metric_definitions.md` for formulas and leak heuristics.

### 8. Compare to Previous Period

When prior-period data exists, compare:

- income by source;
- fixed, variable, discretionary, and one-off expenses;
- savings rate;
- burn rate;
- runway;
- net worth;
- debt balances;
- category and merchant shifts;
- lifestyle inflation signals.

When prior-period data is missing, say so and establish the current period as the baseline.

### 9. Red Flags

Always evaluate:

- dependence on one income source;
- weak or missing emergency fund;
- high debt load or high-interest debt;
- minimum-payment behavior;
- negative cashflow;
- net worth decline despite positive income;
- lifestyle inflation;
- currency mismatch between income, expenses, debts, and assets;
- recurring fees and subscriptions;
- large uncategorized spending;
- investment activity before emergency fund and debt review.

### 10. Produce the Report

Use `references/report_template.md` as the default structure. Keep the report direct, numerical, and decision-useful. Include assumptions and data quality notes before conclusions when they materially affect the audit.

## Optional Calculator Script

When the user provides normalized JSON or when you can safely transform their data into the expected JSON schema, use:

```bash
python scripts/audit_finances.py input.json --output report.md
```

The script computes repeatable totals, savings rates, burn rates, runway, top categories, top merchants, and basic red flags. Read `references/data_contract.md` before preparing the JSON. Use the script output as a calculation aid, then add judgment, caveats, and narrative analysis.

Do not run the script on raw bank exports containing sensitive data unless the user has provided the file in the conversation and the task requires local analysis.

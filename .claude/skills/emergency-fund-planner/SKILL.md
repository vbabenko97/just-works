---
name: emergency-fund-planner
description: calculate and design emergency funds for questions about where to keep money for a rainy day, how many months of expenses to hold, how to split cash, bank accounts, short-term deposits or treasury-bill equivalents, and when surplus can be invested. use for personal emergency planning with mandatory expenses, income stability, dependents, debt, country of residence, currency mismatch, bank access, relocation risk, blackout or war-risk scenarios, counterparty risk, and liquidity constraints. avoid speculative assets for emergency funds and prioritize liquidity, access, capital stability, currency fit, and bank diversification before yield.
---

# Emergency Fund Planner

## Purpose

Design an emergency fund that is liquid, accessible, and not too volatile. Treat yield as a secondary concern. The fund exists to prevent forced selling, missed essential payments, unsafe debt, or being trapped during a banking, blackout, job-loss, health, war-risk, or relocation shock.

Use this skill to answer questions like:

- "Where should I keep money for a rainy day?"
- "How many months of expenses should I hold?"
- "How much can I safely invest now?"
- "How should I split my emergency fund across cash, banks, currencies, and deposits?"
- "What should I do differently if I live in Ukraine, may relocate, or face blackout/war-risk scenarios?"

## Ground Rules

1. Prioritize survival and access over optimization: liquidity first, capital stability second, counterparty diversification third, yield fourth.
2. Build a layered fund, not a single pile of money.
3. Calculate emergency needs from mandatory monthly expenses, not lifestyle spending.
4. Keep the emergency fund separate from the relocation fund and separate from long-term investments.
5. Do not recommend stocks, crypto, private equity, leveraged products, long-duration bonds, or volatile funds as emergency-fund storage.
6. Do not treat "high yield" as useful if access is unreliable, early exit is punitive, or currency risk is ignored.
7. For country-specific deposit insurance, bank rates, treasury-bill access, tax treatment, capital controls, or wartime banking rules, check current official sources and cite them. Do not hardcode changing legal limits.

## Source Anchors

Use these principles when explaining the reasoning:

- Investor.gov frames rainy-day savings as money usually kept in safe, accessible places such as savings accounts, checking accounts, and certificates of deposit, while noting the tradeoff between safety/accessibility and low interest, plus inflation erosion.
- Investor.gov notes that some investors keep up to six months of income in savings for emergencies such as sudden unemployment.
- FDIC guidance is useful as a general pattern for counterparty-risk thinking: deposit insurance can protect checking, savings, money market deposit accounts, and CDs at insured banks, while stocks, bonds, mutual funds, and crypto assets are not deposit-insured products.

These are not a substitute for local legal and banking verification.

## Required Inputs

Ask for missing inputs only when they materially affect the answer. If the user gives partial data, produce a provisional plan with explicit assumptions instead of stalling.

Minimum useful inputs:

- monthly mandatory expenses;
- variable expenses, separated into essential and discretionary if possible;
- expense currency;
- income currency;
- current emergency savings;
- monthly amount available to save;
- income stability: stable, moderate, variable, contract, unstable, or unknown;
- dependents count;
- minimum debt payments and high-interest debt status;
- country of residence and likely next country if relocation is possible;
- relocation risk: none, low, medium, or high;
- bank access and cash access during disruptions;
- existing investments and whether they are liquid or tax-advantaged.

## Expense Definition

Mandatory monthly expenses include:

- rent or mortgage;
- utilities and communication;
- basic food and household essentials;
- transport needed for work and safety;
- insurance and healthcare essentials;
- minimum debt payments;
- dependent support;
- critical subscriptions or tools needed to keep earning income.

Exclude restaurants, vacations, gadgets, discretionary subscriptions, speculative investing, and lifestyle upgrades. Humanity invented lifestyle creep and then got surprised by it; do not let it contaminate the emergency target.

## Core Calculations

Always calculate:

- minimum emergency fund = 1 month of mandatory expenses;
- target emergency fund at 3, 6, 9, and 12 months of mandatory expenses;
- recommended target months based on risk;
- relocation buffer separately;
- remaining shortfall to minimum and target;
- monthly funding plan;
- investable surplus only after the emergency target and relocation buffer are funded.

When numerical inputs are clear, you may use `scripts/calculate_emergency_fund.py` for deterministic calculations.

Example command:

```bash
python scripts/calculate_emergency_fund.py input.json
```

## Target-Month Selection

Use this risk-based default:

- 3 months: stable employment, no dependents, low relocation risk, reliable banking access, low debt burden.
- 6 months: normal default for moderate uncertainty, one income stream, some country or job risk, or one dependent.
- 9 months: variable income, contractor/freelancer income, dependents, meaningful debt obligations, weak local currency exposure, or realistic relocation risk.
- 12 months: high war-risk, blackout disruption risk, unstable income, poor bank/cash access, multiple dependents, likely relocation, or specialized job search that may take months.

Never pretend the exact month count is scientific. It is a risk buffer, not a horoscope with a spreadsheet costume.

## Layered Storage Model

Use this default layered structure and adapt it to the user's country, currency, and risk profile.

### Layer 0: Physical cash

Purpose: immediate survival during blackout, card outage, ATM outage, evacuation, banking freeze, or short local disruption.

Default size: 1 to 2 weeks of mandatory expenses.

Liquidity: immediate.

Risk: theft, loss, fire, currency devaluation, no yield.

Currency: local currency for immediate local spending plus a reserve currency such as USD or EUR if relocation or border movement is plausible.

Maximum share: usually 5% to 15% of the emergency target, higher only for severe access disruption risk.

### Layer 1: Instant-access bank or card account

Purpose: pay the next month of rent, food, utilities, transport, and debt minimums without selling assets.

Default size: about 1 month of mandatory expenses, including Layer 0 if cash is counted as part of the first month.

Liquidity: same day or next day.

Risk: bank outage, card network outage, account freeze, currency mismatch, platform risk.

Currency: match near-term spending currency first; add reserve-currency balance if income or relocation exposure requires it.

Maximum share: usually 20% to 40% of the emergency target.

### Layer 2: Short-term deposit or treasury-bill equivalent

Purpose: hold the deeper 3 to 12 month emergency reserve while reducing idle-cash drag.

Default size: the rest of the emergency target after Layer 0 and Layer 1.

Liquidity: days to a few weeks. Prefer laddered maturities, no-penalty deposits, or very short sovereign-bill equivalents where appropriate and accessible.

Risk: early withdrawal penalty, interest-rate risk, issuer or bank risk, settlement delay, legal access limits, tax complexity.

Currency: match the largest unavoidable liabilities; consider reserve currency for relocation risk.

Maximum share: usually up to 60% to 75% of the emergency target, but never all of it.

### Layer 3: Relocation buffer

Purpose: fund emergency movement, temporary housing, documents, transport, medical requirements, deposits, first-month rent, equipment replacement, and job-search runway in another city or country.

Default size: separate from the emergency fund. Use actual relocation cost estimates when available; otherwise use 1 to 3 months of mandatory expenses as a rough starting range.

Liquidity: split between instant access and short-term storage.

Risk: currency conversion, blocked card, document delays, cross-border transfer delay, sudden price changes.

Currency: likely destination spending currency plus a widely accepted reserve currency.

Maximum share: not capped as a share of the emergency fund because it is a separate goal.

### Layer 4: Long-term investments

Purpose: growth after survival buffers are funded.

Default size: zero inside the emergency fund.

Liquidity: irrelevant for household emergencies because forced selling is exactly what the emergency fund is designed to prevent.

Risk: volatility, tax timing, market drawdown during emergencies.

Currency: depends on long-term plan, not emergency needs.

Maximum share: 0% of the emergency fund.

## Currency-Mismatch Check

Always compare income currency with expense currency.

Flag these cases:

- income and expenses are in different currencies;
- rent or debt is in a hard currency but income is in local currency;
- emergency fund is held mostly in a currency that does not match unavoidable expenses;
- relocation is plausible but all funds are in local currency;
- the user may need cash during outage but holds only app balances.

Default rule: keep the first month mostly in the currency of near-term expenses, then diversify deeper layers across the user's main liability currency and one reserve currency when relocation or local-currency risk is high.

## Counterparty-Risk Check

Do not let the user keep critical survival funds in one account, one bank, one card network, one fintech app, one brokerage, or one country when their risk profile says that is fragile.

Check:

- deposit-insurance or guarantee limits for the relevant country;
- bank solvency and access risk if current data is available;
- whether fintech balances are actually deposits at an insured bank or merely claims on a platform;
- whether cards from different networks or banks are available;
- whether at least part of the fund is physically reachable.

Default recommendation for moderate or high risk: use at least two banks or custodians, plus Layer 0 physical cash, plus at least two access methods where possible.

## Debt and Investing Gate

If high-interest debt exists, separate the decision:

1. Keep Layer 0 and Layer 1 minimum survival liquidity.
2. Pay down toxic high-interest debt aggressively.
3. Build the recommended emergency target.
4. Invest surplus only after the emergency target and relocation buffer are funded.

Investable surplus formula:

```text
investable surplus = liquid savings - recommended emergency target - relocation buffer - known near-term obligations
```

If the result is negative, show the shortfall. If it is positive, label it as potentially investable, not automatically investable.

## Output Format

Use this structure by default:

```markdown
## Summary
[One paragraph with recommended target months, total target, and main storage idea.]

## Assumptions
[List assumptions and missing data that materially affect the result.]

## Emergency fund calculation
- Monthly mandatory expenses: [amount]
- Minimum fund, 1 month: [amount]
- 3 month target: [amount]
- 6 month target: [amount]
- 9 month target: [amount]
- 12 month target: [amount]
- Recommended target: [amount] ([months] months)

## Layered storage plan
[Show layers 0 to 4 with purpose, amount, liquidity, risk, currency, and maximum share. A table is allowed when it improves clarity.]

## Currency mismatch
[State whether income and expenses match. Explain what to hold in each currency.]

## Counterparty risk
[State whether the current setup is too concentrated. Recommend split rules.]

## Funding plan
[Show monthly contribution, months to minimum, months to target, and priority order.]

## Investable surplus
[Show the amount that can be invested only after the emergency target and relocation buffer are complete.]

## Do not use for the emergency fund
[List unsuitable assets for this user's case.]
```

## Response Style

Be practical, specific, and conservative. Avoid magical precision. Explain tradeoffs plainly: cash loses to inflation but wins during outages; deposits may earn interest but can reduce access; investments may grow but can fall exactly when cash is needed.

Do not provide legal, tax, or regulated investment advice. For jurisdiction-specific rules, verify current official sources and clearly label uncertainty.

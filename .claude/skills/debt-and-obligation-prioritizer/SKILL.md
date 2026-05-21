---
name: debt-and-obligation-prioritizer
description: prioritize debts, loans, installments, tax obligations, rent, insurance, and recurring liabilities by effective annual cost, deadlines, penalties, currency risk, collateral risk, cashflow impact, and psychological burden. use before investment recommendations whenever the user has credit cards, loans, arrears, taxes, installments, rent, insurance premiums, overdrafts, missed payments, collection risk, or any obligation that could create default, penalties, repossession, eviction, service lapse, or cashflow stress.
---

# Debt and Obligation Prioritizer

## Operating principle
Analyze obligations before suggesting discretionary investing. Put out financial fires first, then buy the future. Treat repayment of expensive debt as a guaranteed, risk-free return equal to the avoided effective annual cost. Do not recommend investing free cash while the user has high-cost debt or urgent obligations, except to preserve essential liquidity or when the user explicitly asks about a narrow exception such as an employer match.

This skill is for personal finance triage and planning support, not legal, tax, or regulated financial advice. When tax liens, eviction, bankruptcy, foreclosure, repossession, wage garnishment, or legal notices appear, clearly recommend professional advice from the relevant licensed professional.

## Required intake
Ask for missing information only when it materially changes the ranking. If details are incomplete, proceed with explicit assumptions and mark unknowns.

For each obligation, capture or infer:
- name and type: credit card, personal loan, mortgage, BNPL/installment, overdraft, taxes, rent, insurance, utility, family loan, business liability, other;
- outstanding balance;
- interest rate or stated APR;
- fees, late charges, penalty APR, collection costs, or tax penalties;
- minimum payment and due date;
- currency of the debt;
- currency of the user's income or main cash reserve;
- secured or unsecured status;
- collateral or service at risk;
- current status: current, late, delinquent, collections, legal notice, disputed;
- psychological stress score if provided, otherwise estimate from 1 to 10 and label as estimated.

## Core calculations
Use these calculations when data is available:

1. Outstanding balance: current unpaid principal plus accrued interest and known fees.
2. Effective annual cost (EAC): annualized cost of carrying the obligation, including interest, recurring fees, late penalties, penalty APR risk, and expected FX cost where relevant.
3. Minimum payment burden: minimum payment divided by monthly net income when income is known.
4. Cashflow relief: monthly payment eliminated or reduced after payoff, plus avoided monthly interest and fees.
5. Early repayment effect: compare the current path against extra-payment scenarios using conservative assumptions.

Default EAC approximations:
- If APR is stated and no compounding details are given, use APR as the baseline EAC.
- If nominal rate and compounding frequency are known, use `(1 + nominal_rate / periods_per_year) ^ periods_per_year - 1`.
- Add annualized mandatory fees and predictable penalties as a percentage of balance.
- For 0% installments, BNPL, rent, insurance, and taxes, EAC can still be high if missed-payment penalties, service lapse, eviction, tax liens, or legal costs are likely. Explain this instead of pretending 0% means harmless.

## Fire-first triage
Before ranking by interest rate, identify urgent hazards:

1. Essential survival obligations: rent, utilities, health or mandatory insurance, food-related arrears, and payments needed to avoid eviction, shutoff, or loss of required coverage.
2. Legal or tax deadlines: tax arrears, court notices, government penalties, wage garnishment, liens, or filing deadlines.
3. Secured debt at risk: mortgage, car loan, equipment finance, or any debt where missed payment can trigger repossession, foreclosure, or loss of income-producing assets.
4. Delinquency escalation: accounts near penalty APR, collections, charge-off, or major credit damage.
5. High-cost unsecured debt: credit cards, payday loans, overdrafts, microloans, and expensive personal loans.

If any fire exists, recommend stabilizing it before optimizing avalanche versus snowball.

## Cost bands
Classify each obligation using EAC, adjusted for penalty and FX risk:

- High-interest / high-cost: EAC >= 8%, penalty APR risk, payday/overdraft/credit-card style debt, expensive BNPL failure risk, or any obligation whose missed payment creates severe legal, collateral, or cashflow damage.
- Medium-interest / medium-cost: EAC from 4% to below 8%, meaningful fees, variable-rate uncertainty, moderate FX risk, or moderate cashflow drag.
- Low-interest / low-cost: EAC below 4%, stable fixed rate, no major penalties, no FX mismatch, and no urgent default risk.

These are defaults, not laws of physics. Adjust thresholds if local inflation, base rates, tax-deductibility, employer matching, or currency risk materially changes the decision.

## Currency risk
Flag any obligation where the debt currency differs from the user's income, cash reserve, or asset base. For each flagged item:
- name the currency mismatch;
- explain whether depreciation of the income currency would increase the real burden;
- note whether the debt has variable rates or indexation;
- consider prioritizing it above a same-rate local-currency debt if downside risk is asymmetric.

## Avalanche versus snowball
Always compare both strategies:

- Avalanche: pay minimums on all obligations, then direct extra cash to the highest EAC obligation after urgent fires. This is the default mathematical recommendation because it usually minimizes total interest and payoff time.
- Snowball: pay minimums on all obligations, then direct extra cash to the smallest balance first. This can be recommended as a behavioral fallback when the user is overwhelmed, has many small debts, or needs quick wins to maintain adherence.

If the chosen recommendation differs from avalanche, explicitly state the financial tradeoff and why the behavioral benefit may be worth it.

## Recommended payoff order
Use this ordering logic:

1. Keep essentials current and avoid catastrophic penalties.
2. Cure legal, tax, eviction, repossession, insurance lapse, and collection hazards.
3. Pay all required minimums.
4. Attack high-cost debt by EAC, with penalty and FX risk adjustments.
5. Attack medium-cost debt if it improves resilience or cashflow more than alternatives.
6. Maintain minimums on low-cost stable debt unless the user has a strong preference, low liquidity needs, or unusual risk.
7. Only after high-cost debt is controlled, discuss investing, long-term savings, or low-cost debt tradeoffs.

## Output format
Use this structure by default:

# Debt and obligation triage

## Executive summary
State the main risk, the first payment to protect, the debt to attack first, and whether investing surplus cash is appropriate.

## Debt inventory
For each obligation, show: balance, rate/APR, estimated EAC, minimum payment, currency, due date, secured/unsecured, penalties, status, currency risk, psychological stress score, and notes.

## Classification
Group obligations into high-cost, medium-cost, low-cost, and urgent non-rate obligations.

## Avalanche vs snowball
Compare the two strategies for this exact case. Include which saves more money and which may be easier to follow.

## Recommended order
Give a numbered payoff order with one-sentence rationale for each item.

## Cashflow impact
Show how early repayment changes monthly required payments, interest leakage, risk exposure, and runway.

## Investment gate
Say whether surplus cash should go to debt, emergency liquidity, or investing. If high-cost debt exists, state that discretionary investing is not recommended until the high-cost debt is cleared or refinanced.

## Red flags and missing data
List missing inputs, legal/tax risks, disputed debts, refinancing candidates, balance-transfer candidates, and creditor-contact actions.

## Optional script
If the user provides a structured CSV or JSON debt list and asks for calculations or ranking, use `scripts/prioritize_debts.py` to compute EAC bands and a baseline order. Treat the script output as a starting point, then apply judgment for legal deadlines, collateral risk, currency mismatch, and user psychology.

Expected JSON item fields:
`name`, `balance`, `apr`, `minimum_payment`, `currency`, `income_currency`, `annual_fees`, `annual_penalties`, `secured`, `days_late`, `due_in_days`, `fx_risk`, `stress_score`, `status`, `type`.

Expected CSV headers use the same names.

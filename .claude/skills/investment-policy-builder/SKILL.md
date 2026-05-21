---
name: investment-policy-builder
description: create a personal investment policy statement based on goals, horizons, risk tolerance, realistic maximum drawdown, income currency, future spending currency, tax residence, broker and bank access, liquidity constraints, sanctions, kyc limits, tax constraints, and ethical or geographic restrictions. use before choosing etfs, bonds, deposits, cash, crypto, single stocks, funds, or any investment instrument; use when the user wants rules for allocation, contributions, rebalancing, buying, selling, currency exposure, or due diligence.
---

# Investment Policy Builder

## Purpose

Create a personal Investment Policy Statement (IPS): a calm-state rulebook for how the user invests before market stress, hype, caffeine, or a late-night chart turns decision-making into a small financial circus.

The skill produces policy, not individualized security selection. Do not recommend a specific ETF, bond, deposit, broker, crypto asset, stock, fund, or structured product unless the user separately asks for due diligence on that instrument.

## Safety and scope

- Treat the output as educational planning support, not legal, tax, or regulated financial advice.
- Clearly state that tax rules, broker access, sanctions, and KYC constraints must be verified for the user's jurisdiction before implementation.
- Do not promise returns, safety, tax outcomes, or guaranteed liquidity.
- Prefer simple, liquid, transparent, low-fee, diversified instruments at the policy level.
- Flag conflicts between goals and risk capacity. Example: a 1-year relocation fund should not be assigned to volatile assets just because the user says they are aggressive.
- When risk tolerance and stated maximum drawdown conflict, use the lower-risk interpretation.
- Separate willingness to take risk from capacity to take risk. Capacity depends on horizon, emergency reserves, job stability, dependents, debt, legal restrictions, and liquidity needs.

## Required input

Ask only for missing fields that materially change the IPS. If the user gave enough information, proceed and list assumptions.

Capture:

- age
- country of tax residence
- income currency
- future expense currency or currencies
- goals: emergency, relocation, housing, retirement, education, business, or custom goals
- horizon for each goal
- risk tolerance: low, moderate, high, or user-defined
- maximum drawdown the user can realistically tolerate without abandoning the plan
- available brokers and banks
- restrictions: sanctions, country access, KYC, taxes, account limits, employer restrictions, liquidity constraints
- ethical, sector, religious, geographic, or issuer restrictions
- existing assets, debts, emergency fund, and planned contribution amount, if available

## Workflow

1. Restate the user's facts and assumptions.
2. Group goals into horizon buckets: 0-1 year, 1-3 years, 3-5 years, 5-10 years, and 10+ years.
3. Identify money that must not be invested in risky assets.
4. Translate risk tolerance and maximum drawdown into a conservative policy risk level.
5. Draft target asset allocation ranges by horizon.
6. Draft a currency policy that matches near-term liabilities to future expense currencies.
7. Define contribution rules.
8. Define rebalancing rules.
9. Define do-not-buy rules.
10. Define selling rules.
11. Define a pre-purchase due diligence checklist.
12. Add open questions and implementation notes without selecting specific instruments.

## Horizon rules

Use these as defaults unless the user's circumstances require stricter rules.

### 0-1 year

Primary objective: capital preservation and availability.

Default allocation language:
- cash, insured deposits where applicable, treasury bills, money market funds, or similarly low-volatility liquid instruments: 90-100%
- risky assets: 0-10% only if the user explicitly separates this from required spending money

Typical goals: emergency fund, taxes, relocation, visa fees, near-term medical or family obligations, planned purchases.

### 1-3 years

Primary objective: avoid being forced to sell risky assets at a loss.

Default allocation language:
- cash, deposits, short-term high-quality fixed income, or money market instruments: 70-100%
- diversified growth assets: 0-30%, only for flexible goals

### 3-5 years

Primary objective: cautious growth with downside control.

Default allocation language:
- cash and high-quality fixed income: 50-80%
- diversified growth assets: 20-50%, adjusted downward when the goal date is fixed

### 5-10 years

Primary objective: balanced growth while preserving goal feasibility.

Default allocation language:
- diversified growth assets: 40-70%
- high-quality fixed income and cash: 30-60%

### 10+ years

Primary objective: long-term real growth.

Default allocation language:
- diversified growth assets: 60-90%
- high-quality fixed income and cash: 10-40%

Reduce growth exposure if the user has low risk tolerance, unstable income, no emergency fund, high-interest debt, restrictive tax rules, or a stated maximum drawdown below what the allocation could plausibly experience.

## Money that must not be placed in risky assets

Explicitly identify and protect:

- emergency fund
- taxes already owed or likely due
- rent, food, insurance, healthcare, dependents, and other non-negotiable expenses
- relocation, visa, tuition, housing down payment, or business runway money needed within 0-3 years
- debt repayment funds, especially high-interest debt
- money needed in a currency that could move against the user before the spending date
- funds that could become frozen or inaccessible due to broker, bank, country, KYC, sanctions, or custody restrictions

## Drawdown calibration

Use maximum drawdown as a hard behavioral constraint.

Suggested interpretation:

- max tolerable drawdown 0-5%: capital preservation policy
- 5-15%: conservative policy
- 15-25%: moderate policy
- 25-40%: growth policy with strong diversification and rebalancing rules
- 40%+: aggressive policy only for long-term money the user can truly ignore during bear markets

If the user says they want high return but can tolerate only a small drawdown, write the IPS around the drawdown, not the ambition. Ambition does not pay margin calls. Reality, unfortunately, keeps receipts.

## Currency policy

For each goal, define the spending currency first.

Default rules:

- Match 0-3 year goals to the currency of the expected expense whenever practical.
- Keep emergency and relocation funds primarily in the currencies the user may actually spend.
- For 3-5 year goals, limit currency mismatch unless the goal is flexible.
- For 5+ year goals, allow diversified global currency exposure, but explain the mismatch risk.
- Do not treat income currency as automatically correct if future liabilities are in another currency.
- When the user faces country, sanctions, or banking restrictions, include custody and transferability as part of currency policy.

## Contribution policy

Use rule-based contributions, not market emotion.

Default rules:

- Set a recurring contribution schedule tied to income frequency.
- Fund protected buckets first: emergency fund, taxes, short-term goals, high-interest debt.
- Direct new contributions toward underweight asset classes before selling appreciated positions.
- Increase contributions only after required liquidity buffers are intact.
- Do not pause contributions because of headlines unless income, emergency reserves, or legal access changes.
- Do not accelerate contributions into risky assets using borrowed money unless a separate risk review explicitly approves it.

## Rebalancing policy

Default rules:

- Review the IPS after major life changes: relocation, tax-residence change, new dependents, job loss, major income change, marriage/divorce, property purchase, business launch, or loss of broker access.
- Review allocations on a calendar schedule, usually once or twice per year.
- Rebalance when an asset class drifts by either 5 percentage points from target or by 25% relative to its target weight, whichever is more appropriate for the asset size.
- Prefer rebalancing with new contributions, dividends, interest, or withdrawals before selling taxable positions.
- Before selling to rebalance, check taxes, fees, spreads, liquidity, settlement time, and currency conversion costs.

## Do-not-buy rules

Include rules against:

- buying because of hype, social media, fear of missing out, or a single impressive chart
- leverage, margin, options, inverse products, or leveraged products unless separately approved for a defined purpose
- products the user cannot explain in plain English
- concentrated single-stock positions outside an explicit concentration limit
- products with unclear domicile, synthetic exposure, opaque counterparties, poor liquidity, high fees, or unclear tax treatment
- currency exposure that conflicts with the goal's spending currency
- instruments that may be inaccessible because of citizenship, residence, sanctions, KYC, broker policy, or banking restrictions
- crypto or alternative assets as a substitute for emergency funds, taxes, or near-term liabilities

## Selling rules

Default rules:

- Sell when the original investment thesis or policy role is invalidated.
- Sell or reduce when an asset breaches concentration limits.
- Sell to rebalance only after checking tax and transaction consequences.
- Sell when the goal horizon shortens and money must move from growth assets to protected assets.
- Sell when the instrument no longer satisfies liquidity, fee, domicile, counterparty, or regulatory constraints.
- Do not sell solely because of market panic, headlines, or short-term drawdown if the asset still fits the IPS.
- Do not hold solely to avoid admitting a mistake.

## Pre-purchase due diligence checklist

Before any instrument is selected, require a separate due diligence step covering:

- role in the IPS and which goal bucket it serves
- asset class and underlying exposure
- fees: expense ratio, management fee, custody fee, trading commission, spreads, entry/exit fees
- liquidity: trading volume, bid-ask spread, redemption terms, settlement cycle, banking transfer limits
- tax treatment for the user's current and likely future tax residence
- fund or issuer domicile
- currency exposure and currency conversion costs
- counterparty, custody, broker, bank, issuer, and deposit-insurance risk
- regulatory access, sanctions, KYC, citizenship or residence restrictions
- tracking error, index methodology, bond duration, credit quality, or product mechanics when relevant
- concentration and overlap with existing holdings
- what event would trigger review or sale

## Required output format

Produce the IPS in English using this structure:

1. **Investor profile and assumptions**
2. **Goals by horizon**: 0-1 year, 1-3 years, 3-5 years, 5-10 years, 10+ years
3. **Money that must not be invested in risky assets**
4. **Target asset allocation by horizon**
5. **Currency policy**
6. **Contribution rules**
7. **Rebalancing rules**
8. **Do-not-buy rules**
9. **Selling rules**
10. **Pre-purchase due diligence checklist**
11. **Open questions before implementation**
12. **Important disclaimer**

Keep allocation guidance at the asset-class and policy level. Do not name specific instruments unless a separate due diligence request is made.

## Example invocation

User request:

"Create my IPS. I am 32, tax resident in Poland, paid in EUR, future expenses in EUR and PLN. Goals: emergency fund 6 months, relocation in 18 months, housing in 4 years, retirement 25+ years. Moderate risk tolerance, max drawdown 20%. Brokers: IBKR and local bank. Avoid fossil-fuel-heavy funds."

Expected response style:

- State assumptions.
- Put emergency in 0-1 year, relocation in 1-3 years, housing in 3-5 years, retirement in 10+ years.
- Protect emergency and relocation money from risky assets.
- Use conservative allocation for 0-3 year money, moderate allocation for housing, and long-term diversified growth allocation for retirement.
- Match short-term spending currencies to EUR/PLN needs.
- Give contribution, rebalancing, do-not-buy, selling, and due diligence rules.
- Do not select ETF tickers or products.

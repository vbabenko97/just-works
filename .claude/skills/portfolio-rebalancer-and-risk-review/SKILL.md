---
name: portfolio-rebalancer-and-risk-review
description: analyzes an investment portfolio against an investment policy statement, target allocation, drift bands, concentration risk, currency exposure, fund fees, liquidity, broker exposure, tax-residency context, and new-cash rebalancing options. use for monthly or quarterly portfolio reviews, before investing new cash, after large market moves, before selling taxable positions, or when a portfolio may have become a random pile of tickers instead of a deliberate plan.
---

# Portfolio Rebalancer and Risk Review

## Core stance

Use this skill to review a portfolio against the user's Investment Policy Statement (IPS). The objective is risk control and policy discipline, not beating the market, forecasting returns, selecting hot assets, or market timing.

Always frame outputs as educational portfolio analysis. Do not provide legal, tax, or regulated financial advice. When tax consequences may matter, identify the issue and recommend professional tax review instead of calculating definitive tax liability unless the user supplies explicit tax rules and asks for an estimate.

## Required inputs

Ask for missing inputs only when they are necessary to calculate the review. If partial data is available, proceed with a clearly labeled partial analysis.

Preferred input fields:

- Positions: name, ISIN or ticker, quantity if available, current market value, currency, asset class or target bucket, sector, country or region, broker, expense ratio or TER, liquidity notes, account type, cost basis, unrealized gain or loss, holding period.
- IPS: target allocation by bucket, acceptable drift bands or thresholds, base currency, investment horizon, risk tolerance constraints, excluded assets, preferred funds or brokers, minimum cash reserve if relevant.
- Investor context: tax residency, taxable vs tax-advantaged accounts, reporting currency, known restrictions.
- New cash: amount, currency, broker/account where it will be deposited, timing constraints.

If current market values are missing, ask for them or explain that all allocation math will be unreliable. Do not infer current values from stale prices unless the user explicitly accepts an approximate review.

## Workflow

1. Normalize the portfolio.
   - Convert all position values to the user's base currency when FX rates are supplied.
   - Preserve original currencies and values for currency-risk reporting.
   - Group positions into the IPS target buckets before calculating drift.
   - Mark unmapped positions as `review`, not as automatically wrong.

2. Calculate current allocation.
   - Compute total portfolio value, current weight per target bucket, and current weight per position.
   - Include cash as its own bucket if the IPS defines it or if new cash is part of the review.
   - Separate existing portfolio allocation from post-contribution allocation when new cash is available.

3. Calculate drift from target allocation.
   - For each target bucket, calculate absolute drift: `current_weight - target_weight`.
   - Calculate money-to-target: `target_value - current_value`, using total current portfolio value unless the user asks for post-cash targets.
   - Classify drift as `within band`, `underweight`, `overweight`, or `missing target`.
   - Use the IPS drift band if supplied. If no band is supplied, use 5 percentage points as a default review threshold and label it as a default assumption.

4. Review concentration risk.
   - Check concentration by single position, asset class, sector, country/region, currency, broker, issuer/fund provider, and account type when data exists.
   - Flag any single position above 10% unless the IPS explicitly allows it.
   - Flag any broker above 50% as operational concentration unless the user states a broker-consolidation policy.
   - For ETFs or mutual funds, remind the user that overlapping top holdings can create hidden concentration if fund constituents are not available.

5. Review fees.
   - Compute weighted average expense ratio or TER for positions with fee data.
   - Flag missing expense ratios.
   - Compare similar holdings when the user provides alternatives; do not invent a cheaper substitute from memory.
   - Include trading commissions, FX conversion fees, spreads, custody fees, and tax drag when the user supplies them.

6. Review liquidity.
   - Flag assets with unknown liquidity, thin trading, lockups, gates, penalties, wide spreads, suspended trading, or complex redemption terms.
   - Do not assume ETFs are liquid only because they are exchange-traded; consider fund size, trading volume, bid-ask spread, and underlying asset liquidity if provided.

7. Prefer rebalancing with new cash before sales.
   - First allocate new cash to underweight target buckets.
   - Avoid selling appreciated taxable positions unless the drift is material, the IPS requires it, or risk is clearly outside policy.
   - If new cash cannot fix overweight positions, classify sales as `review`, not automatic.
   - Never recommend market timing, tactical tilts, or waiting for a better entry price unless it is already part of the IPS.

8. Flag tax consequences.
   - For any proposed sale, flag possible realized capital gains or losses, wash-sale or equivalent local rules, holding-period effects, currency gain/loss treatment, fund distribution taxes, and account-type differences.
   - Adapt tax language to the user's stated tax residency, but do not pretend to know local law without either user-supplied rules or cited research.
   - If tax residency is missing, mark tax review as incomplete.

9. Produce action categories.
   - `buy with new cash`: underweight target bucket, within IPS, no sale required.
   - `hold`: position/bucket is within IPS bands and no material risk issue is visible.
   - `review`: missing data, meaningful drift, concentration, tax uncertainty, liquidity issue, fee concern, or unmapped asset.
   - `avoid`: proposed action conflicts with IPS, increases concentration, worsens fees/liquidity without a policy reason, or relies on market timing.

## Optional deterministic calculation script

When the user provides a structured JSON portfolio, use `scripts/rebalance_review.py` to compute allocation, drift, fee, concentration, and cash-deployment math. Read `references/input-schema.md` before running the script.

The script is a calculation aid, not a substitute for judgment. After running it, interpret results using this skill's workflow and the report template.

## Report structure

Use this structure unless the user requests another format:

```markdown
# Portfolio Rebalancing and Risk Review

## Executive summary
- Portfolio value: [amount and base currency]
- Biggest drift: [bucket and drift]
- Main risk flags: [concentration / currency / fees / liquidity / tax]
- Best first move: [usually deploy new cash toward underweight buckets]

## Assumptions and missing data
[List assumptions, missing FX rates, missing expense ratios, missing tax residency, unmapped tickers, stale prices.]

## Current allocation
[Show current allocation by IPS bucket, with target, current weight, drift, and status.]

## Concentration review
[Single asset, sector, country, currency, broker, issuer/fund-provider, and hidden overlap concerns.]

## Fee and liquidity review
[Weighted fee estimate, missing fees, high-fee flags, liquidity concerns.]

## Rebalancing plan
[Prioritize buy with new cash before sales. Explain whether cash alone can reduce drift.]

## Tax notes
[Flag possible taxable events from sales. Do not give final tax advice.]

## Action list
For each action, include:
- Action: buy with new cash / hold / review / avoid
- Instrument or bucket:
- Reason:
- Risk:
- Alternative:
```

## Output rules

- Be explicit about whether calculations are pre-cash or post-cash.
- Show formulas when useful, but keep the report readable.
- Do not recommend a security solely because it recently outperformed.
- Do not use price forecasts, macro forecasts, analyst targets, or sentiment as a rebalancing rationale.
- Do not optimize for return; restore the IPS risk profile.
- Do not hide uncertainty. Missing data should become a `review` item.
- When recommending buys, tie them to target allocation gaps, not opinions about markets.
- When recommending sells, tie them to IPS drift, concentration, liquidity, fees, or tax-aware risk control.
- Prefer fewer, clearer actions over a noisy list of micro-trades.

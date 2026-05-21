---
name: bank-broker-due-diligence
description: check banks, brokers, investment platforms, fintechs, crypto-adjacent platforms, and financial products before opening an account, transferring money, buying securities, or relying on custody. use for license and jurisdiction checks, asset protection, deposit and securities protection, fee drag, tax documents, residency restrictions, sanctions/kyc risk, account blocking risk, reputational red flags, alternatives, and a final suitable / risky / avoid / needs human review verdict.
---

# Bank Broker Due Diligence

## Purpose

Use this skill to evaluate a bank, broker, investment platform, fintech account, or financial product before the user commits money or personal documents. Prioritize current, primary-source verification over marketing claims.

Never treat a polished app, referral bonus, influencer recommendation, or high advertised yield as evidence of safety. Humanity keeps trying this experiment. It keeps ending in paperwork.

## Required inputs

Ask for missing critical inputs when they materially affect the answer. If the user only provides partial information, proceed with explicit assumptions and mark unknowns.

Required or strongly preferred inputs:

- Institution or product name
- Legal entity name if known
- Claimed country of registration or licensing
- User country of tax residence and physical residence
- Product or service type: bank deposit, brokerage account, ETF, fund, CFD, crypto, savings product, robo-advisor, payment wallet, pension, structured note, etc.
- Expected amount and currency
- Intended use: savings, long-term investing, trading, salary receipt, emergency fund, custody, remittance, corporate account, etc.
- User constraints: citizenship, sanctions exposure, US person status, Ukrainian/Russian/Belarusian nexus, EU/UK/US tax reporting needs, preferred base currency, withdrawal needs

## Core workflow

### 1. Identify the exact counterparty

Determine the legal entity, not just the brand. Capture:

- Brand name
- Legal entity name
- Registration number
- Regulator reference number
- Operating country and customer-contracting entity
- Whether the user is onboarded by a local entity, offshore entity, appointed representative, introducing broker, tied agent, white-label partner, or omnibus structure
- Custodian, clearing broker, payment processor, and deposit-taking bank if different from the brand

If the legal entity cannot be identified, escalate the verdict at least to `risky` and usually to `avoid` for meaningful deposits or investment balances.

### 2. Verify license and permissions using primary sources

Use web search for current information unless the user explicitly prohibits browsing. Prefer official regulator registers, investor protection schemes, prospectuses, audited reports, terms, fee schedules, and tax-document pages.

Do not rely on:

- The platform's own footer alone
- Screenshots from support chats
- Influencer posts
- App-store descriptions
- Generic statements like "regulated in Europe"
- A license that covers a different activity than the one being offered

Check that the license covers the product. Example: an e-money license does not equal deposit insurance; a crypto AML registration does not equal investment-product authorization; a payment institution license does not equal permission to hold client securities.

For source selection and regulator lookup patterns, consult `references/source-map.md`.

### 3. Map asset protection

Separate protection by asset type:

- Bank deposits: deposit guarantee scheme, limit, eligible depositor rules, currency treatment, branch vs subsidiary status
- Brokerage cash: client money rules, segregation, qualified custodian, sweep bank, money market fund treatment
- Securities: nominee/beneficial ownership, segregation, central securities depository, clearing broker, securities investor compensation scheme
- Funds/ETFs: fund domicile, UCITS or non-UCITS status, depository/custodian, investor class, KIID/KID availability
- Derivatives/CFDs/margin: counterparty exposure, negative balance protection, leverage limits, liquidation rules
- Crypto or tokenized products: custody model, private-key control, insolvency treatment, whether the product is a regulated security, and whether any investor compensation scheme applies

Explicitly state what is not protected. This matters more than the brochure's soothing adjectives.

### 4. Build a full fee picture

Check all relevant fees and make them comparable:

- Deposit fee
- Withdrawal fee
- FX conversion fee and markup
- Custody or platform fee
- Trading commissions
- Fund TER or OCF
- Spread
- Inactivity fee
- Transfer-out fee
- Corporate action fee
- Tax-document fee
- Margin interest
- Card, cash, ATM, or account maintenance fees for banking products

When fees are percentage based, estimate annual and multi-year drag for the user's amount and holding period. If helpful, use `scripts/fee_drag.py` to compare fee scenarios.

### 5. Check tax reporting and documents

Verify whether the platform provides documents relevant to the user's residence and product:

- Annual activity statement
- Realized gains/losses report
- Dividend and withholding tax report
- Interest income report
- CRS/FATCA classification
- Form 1042-S, 1099, W-8BEN, W-8BEN-E, W-9, where relevant
- Local tax certificates or country-specific reports
- Export formats: CSV, PDF, XML, broker tax statement, transaction-level data

If tax documents are unavailable or incomplete, flag operational friction even if the product is otherwise legitimate.

### 6. Check residency, sanctions, and KYC risk

For the user's residence and citizenship context, verify:

- Whether residents of the user's country are accepted
- Whether onboarding is restricted for sanctioned regions or high-risk jurisdictions
- Whether the platform can close, freeze, limit, or liquidate accounts based on residence changes, document expiry, nationality, source-of-funds checks, or sanctions screening
- Whether deposits and withdrawals must come from same-name accounts
- Whether third-party transfers are prohibited
- Whether proof of address, tax ID, source of wealth, or employment documents are required
- Whether the platform has recent mass offboarding or account-freezing reports affecting similar users

Use current sources and mark anecdotal reports as anecdotal, not proof.

### 7. Screen red flags

Consult `references/red-flags.md` and score the case conservatively. Red flags include:

- No verifiable legal entity or license
- License mismatch
- Regulator warning or clone-firm warning
- Guaranteed high returns or unrealistic yield
- Pressure to deposit quickly
- Withdrawal complaints with consistent patterns
- Opaque fee schedule
- Unclear custody chain
- Offshore entity for retail users without clear protections
- Product complexity disproportionate to user goal
- No independent audited financials where expected
- Inconsistent company names, addresses, or regulator numbers
- Support pushing bank transfers or crypto deposits to unrelated entities

### 8. Compare alternatives

Provide at least two alternatives when possible, unless the user asks only for a narrow verification. Alternatives should match the user's country, currency, amount, and goal. Compare by:

- Regulatory quality
- Protection scheme
- Total fees
- Tax-document quality
- Product availability
- Account restriction risk
- Operational reliability

Do not recommend an alternative from memory when current availability, fees, or country restrictions matter. Verify current details.

### 9. Produce a verdict

Use exactly one final verdict label:

- `suitable`: no material unresolved red flags, license and protection match the intended use, fees are competitive, and residency/tax handling is acceptable
- `risky`: usable only with limits or mitigations; material uncertainties or operational risks exist
- `avoid`: major red flags, license mismatch, regulator warning, unclear custody, unacceptable restrictions, or withdrawal/account-freezing risk outweighs benefits
- `needs human review`: legal, tax, sanctions, cross-border, large-sum, corporate, estate, pension, or complex-derivative issues require a qualified professional

Never guarantee safety. State residual risks and suggested exposure limits where relevant.

## Default output format

Use this structure unless the user requests another format:

```markdown
# Due diligence: [institution/product]

## TL;DR
[One paragraph with verdict, main reasons, and maximum prudent next step.]

## Assumptions and missing information
[List assumptions and missing inputs.]

## Entity and license check
- Brand:
- Legal entity:
- Jurisdiction:
- Regulator:
- Register status:
- Permissions relevant to this product:
- Source confidence:

## Protection of funds and securities
[Explain deposit, cash, securities, fund, derivative, or crypto protection separately.]

## Fees and cost drag
[Summarize fees. Include fee-drag estimates when useful.]

## Tax documents and reporting
[Assess availability and gaps.]

## Residency, KYC, sanctions, and account-blocking risk
[Assess user-country fit and operational failure modes.]

## Red flags
[Separate confirmed red flags from unresolved questions.]

## Alternatives
[Compare at least two verified alternatives when possible.]

## Verdict
**[suitable / risky / avoid / needs human review]**

[Explain the verdict in plain language.]
```

## Evidence rules

- Cite sources for every material claim about regulation, fees, protection limits, country availability, tax documents, warnings, sanctions, or reputation.
- Prefer regulator pages, official registers, scheme pages, fee schedules, terms, prospectuses, annual reports, and official help pages.
- Use dated language: "as of [date]" for fees, availability, restrictions, and register status.
- If sources conflict, prioritize regulator and legal documents over company marketing.
- If evidence is stale, unavailable, or region-specific, state uncertainty instead of inventing confidence. Financial due diligence is not fan fiction.

## Human-review triggers

Escalate to `needs human review` when any of these apply:

- Expected amount is large relative to the user's net worth or emergency fund
- Corporate, trust, estate, pension, or grant funds are involved
- The user has a sanctioned-country nexus or complex residence/citizenship situation
- The product is a derivative, structured product, private placement, high-yield note, leveraged product, or crypto custody/staking product
- The platform refuses to provide legal entity, custodian, or fee details
- Tax reporting depends on uncertain treaty treatment, PFIC rules, PRIIPs/KID restrictions, CRS/FATCA status, or local capital-control rules
- The user needs legal, tax, or investment advice rather than due-diligence research


# Calculation notes

Use these notes only when the user asks for detailed math or when a structured debt file is provided.

## Effective annual cost

Effective annual cost estimates the annualized cost of keeping an obligation unpaid. Start with stated APR, then add annualized recurring fees, predictable late fees, penalty APR effects, and material currency-risk adjustments when they can be reasonably estimated.

If compounding is specified:

`EAC = (1 + nominal_rate / periods_per_year) ^ periods_per_year - 1`

If the debt has no interest but harsh missed-payment consequences, do not label it low risk automatically. Rent, tax, insurance, utility, and BNPL obligations can become high-priority because of discontinuous penalties rather than ordinary interest.

## Cashflow relief

Cashflow relief from payoff includes:

- the minimum payment no longer required;
- interest and fees avoided;
- avoided penalty escalation;
- reduced currency exposure when debt currency differs from income currency;
- reduced mental load when the user gives a high stress score.

## Strategy preference

Use avalanche as the mathematical baseline. Use snowball only when adherence risk is high enough that a cheaper plan is less useful because the user is unlikely to follow it.

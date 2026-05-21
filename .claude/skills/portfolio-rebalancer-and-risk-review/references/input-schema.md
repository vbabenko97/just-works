# Input schema for portfolio rebalancing reviews

Use this schema when the user provides structured JSON for deterministic calculations with `scripts/rebalance_review.py`.

## Minimal example

```json
{
  "base_currency": "USD",
  "new_cash": {"amount": 5000, "currency": "USD"},
  "fx_rates_to_base": {"USD": 1.0, "EUR": 1.08},
  "targets": [
    {"bucket": "global equity", "target_weight": 0.70, "rebalance_band": 0.05},
    {"bucket": "bonds", "target_weight": 0.20, "rebalance_band": 0.05},
    {"bucket": "cash", "target_weight": 0.10, "rebalance_band": 0.03}
  ],
  "positions": [
    {
      "name": "example global equity etf",
      "ticker": "EXAMPLE",
      "isin": "IE00EXAMPLE00",
      "value": 42000,
      "currency": "USD",
      "bucket": "global equity",
      "asset_class": "equity",
      "sector": "broad market",
      "country": "global",
      "broker": "example broker",
      "issuer": "example issuer",
      "expense_ratio": 0.002,
      "liquidity": "high",
      "account_type": "taxable",
      "unrealized_gain": 12000,
      "holding_period_days": 900
    }
  ]
}
```

## Field notes

- `target_weight` and `expense_ratio` may be decimals (`0.70`) or percentages (`70`). The script normalizes values greater than 1 as percentages.
- `fx_rates_to_base` should map each currency to one unit of that currency in base currency. If a currency is missing, the script keeps the nominal value and marks the conversion as missing.
- `bucket` should match the IPS target bucket. If missing, the script uses `asset_class`; if both are missing, the position is classified as `unmapped`.
- `rebalance_band` is optional per target. If omitted, the script uses a default absolute drift band of 0.05.
- `new_cash` is optional. If supplied, the script proposes cash-only allocation toward underweight buckets.

## Data quality checklist

Before trusting the output, check that:

- Position market values are current and in the stated currency.
- FX rates are supplied for every non-base currency.
- Targets sum to approximately 100%.
- Expense ratios are annual percentages or decimals, not basis points unless converted.
- Tax lots, cost basis, and holding period are present before evaluating sales.
- ETF/fund holdings overlap is not ignored when concentration matters.

# Forecasting and time-ordered prediction

Read this when the model predicts a future value or event: demand, churn by a date, default within a window, or any label that matures after the prediction.

## Fix the time contract first

Write these down in order:

`forecast origin → horizon → feature cutoff → label availability → training window → evaluation windows → gap`

- **Forecast origin**: when forecasts are produced, for example every Monday at 06:00.
- **Horizon**: how far ahead each forecast looks. When it spans several steps, report errors per horizon step.
- **Feature cutoff**: the latest information usable at the origin. Inputs known in advance (calendar, holidays, planned prices or promotions) differ from inputs observed only afterwards (actual weather, actual sales). For the latter, use the forecast or the value as it was known at the origin.
- **Label availability**: when the target becomes known. A 6-month default label for a loan disbursed in August is unknown until February.
- **Gap**: time excluded between the last training label and the evaluation period, so that no training label depends on the evaluation period.

The owner sets the origin and horizon from the operational decision. Without them, the split and the metric are undefined and the readiness verdict stays blocked.

## Backtesting

Evaluate over several origins rolling forward through time, with an expanding or sliding training window, rather than on one split. At each origin, training rows are those whose label was observable by the origin, and evaluation rows are forecasts made after it. Keep the most recent period as the final test when a final estimate is needed. Random or shuffled K-fold lets the model train on the future; it does not fit time-ordered prediction.

With many series (stores, products), split by time, not by series. Add series-disjoint evaluation only when the model must forecast series that did not exist in training, such as new stores, and report those as a separate slice.

## Time-specific leakage checks

- Lags and rolling windows are shifted so that each window ends at the origin, not at the target time.
- Aggregates (customer totals, store averages) use data up to the origin only.
- Joins against tables that hold current state (current price, current status) are replaced by as-of joins.
- For horizons beyond one step, target-derived features such as recent sales stop at the origin.
- Values corrected later in the source system are used in the form they had at the origin.

## Baselines

Naive (last observed value), seasonal naive (value from the same season in the previous cycle), and the historical mean or median for the matching season and group. A model that does not beat seasonal naive on the backtest is not ready.

Sources: [Forecasting: Principles and Practice, 5.10 Time series cross-validation](https://otexts.com/fpp3/tscv.html); [5.2 Some simple forecasting methods](https://otexts.com/fpp3/simple-methods.html).

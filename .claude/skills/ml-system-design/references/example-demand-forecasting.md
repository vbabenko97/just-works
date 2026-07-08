> Source: [ML-SystemDesign/MLSystemDesign](https://github.com/ML-SystemDesign/MLSystemDesign), MIT License. Distilled and rewritten, not verbatim.

# Worked Example: Retail Demand Forecasting
Forecast daily per-SKU-per-store demand for a large grocery retail chain to narrow the gap between
delivered and sold units while maintaining a defined service-level agreement on out-of-stock incidents.
Maturity: production

## I. Problem Definition

Supermegaretail operates thousands of stores across multiple countries selling groceries, household
essentials, and perishables. The core tension: overstock wastes margin (especially for perishable items),
while out-of-stock drives customers to competitors and obscures true demand — the more damaging failure.
Combined overstock and out-of-stock losses were estimated at $800M/year. Operational context: one-year
manufacturer deals (adjustable 90 days ahead within the first nine months), 47 distribution centers, a
two-day delivery cadence between centers and stores, and no in-store warehouses. Three forecast horizons
are needed: weekly (store ordering), monthly (center planning), and annual (manufacturer contracts).
Stakeholders: logistics, procurement, and operations departments. Key risks: ML monitoring infrastructure
does not yet exist; model failures need checks and fallbacks. A hybrid rollout targeting the highest-gap
categories first limits exposure while leaving well-forecast categories untouched.

## II. Metrics and Losses

After reviewing *Evaluating Predictive Count Data Distributions in Retail Sales Forecasting*: MAPE and
sMAPE are rejected as undefined or unstable when actuals are zero; MAE-based metrics optimize the median,
which is biased for asymmetric low-volume count distributions; MSE is too sensitive to outliers in
intermittent demand. Selected metric: quantile metrics at quantiles 1.5, 25, 50, 75, 95, and 99 — both
unweighted and weighted by SKU price — reported as point estimates with 95% confidence intervals. The
loss function directly matches the metric: six separate models trained using the corresponding quantile
(pinball) loss, making the loss-to-metric link exact. Secondary experiment: Tweedie loss for zero-inflated
count distributions (compound Poisson-Gamma). Business KPIs tracked via A/B tests: revenue (expected up),
stock level (expected down or flat), and margin (expected up).

## III. Dataset

Atomic training object: (date, product, store); label: units sold. No manual labeling needed — labels
are read directly from transaction aggregates. Internal sources: transaction history (sales count, revenue,
discounts, transaction IDs), stock history (daily inventory and expirations), product and store metadata,
and the promo calendar. External purchased: weather forecasts, customer foot-traffic from telecom
providers, and global market indicators. External manually gathered: competitor prices refreshed daily
from a subset of competitor stores (~25% of SKU coverage, with gaps). Over three years of history already
collected. Known quality issues: missing and duplicate values in transactions, stock, and promo data;
competitor price coverage is partial. ETL pipeline: aggregate transactions daily, append to partition
table, optionally rewrite the last 2–3 days to correct corruptions, join all sources by (date, product,
store), then compute features.

## IV. Validation Schema

Data constraints driving the design: daily arrival with up to 48h delay, 15% assortment turnover per
month, and strong weekly and annual seasonality. Inference mirrors production: train on the last 2 years
and predict the next 4 weeks. A 3-day gap between training and validation sets simulates data delay and
determines which features are actually available at prediction time. Outer loop: rolling cross-validation
with K=5 folds, 28-day validation window, 7-day step, and 3-day gap. Inner loop: 3-fold rolling CV inside
each outer training set, same 2-year window, used only for hyperparameter tuning; skipped when no tuning
is required. Update cadence: weekly rolling split updates to capture local trend changes; a separate
quarterly golden holdout set tracks long-term model improvement.

## V. Baseline Solution

Constant baseline: actual sales for the same item exactly one week prior — same weekday, tolerates the
48h data delay, accounts for weekly seasonality. Advanced constant baseline: historical quantiles at all
six target quantiles using a one-year rolling window, providing a per-quantile performance floor. Linear
model baseline: linear regression with quantile loss using lagged sales values and rolling min/max/mean/
std/quantile aggregations over 7, 14, 30, 60, 90, and 180-day windows. Time-series baseline: ARIMA/SARIMA
for explicit seasonality modeling, or Prophet as a robust alternative that handles outliers, missing values,
and trend shifts with minimal preprocessing. Feature baseline: adds product attributes (brand, category
hierarchy), store geo features, temporal features (day of week, holidays), and interaction features such
as penetration ratio (SKU/category sales) and days-since-last-purchase.

## VI. Error Analysis

Convergence analysis on gradient boosting: verify the loss decreases and the model beats baseline metrics
across a rough tree-count grid (500–1000–2000–3000–5000), then fix the tree count for subsequent feature
experiments. Model-complexity curves guide selection of optimal lag count and rolling window granularity.
Dataset-size curves identify whether 2 years of history is necessary or whether downsampling to 20/10/5%
is acceptable. The granularity decision (day-level vs week-level training objects) materially changes
system throughput and product scope; requires product manager alignment before implementation. Residual
analysis: a small positive bias (overprediction) is preferred since overstock cost is lower than out-of-
stock cost. A skew toward negative residuals is a deployment red flag. Validate per-quantile model
assumptions explicitly — e.g., 95% of residuals should be positive for the 95th-quantile model. Check
elasticity using elasticity curves; use isotonic regression post-processing as a fast fix if elasticity
is not captured. Per-rollout structured reports cover short-history items, high/low-price items, holiday
and promo days, and items with near-zero or extreme residuals.

## VII. Training Pipeline

Tools: Python, Spark for distributed feature computation, PyTorch for deep learning experiments, MLflow
for experiment tracking and model versioning, Docker for environment reproducibility, and AWS SageMaker
or Google Cloud AI Platform for cloud-scale training. Preprocessing: missing-value and duplicate handling,
feature engineering (lag/rolling aggregations, temporal features, promo and external-data joins), numeric
normalization, and temporal train-test splits with explicit leakage prevention. Model types in scope:
statistical baselines (moving average, exponential smoothing, ARIMA), tree-based ML (gradient boosting,
random forest), and deep learning (LSTM, Transformer) when warranted. Hyperparameter tuning via grid
search or Bayesian optimization. MLflow tracks parameters, feature engineering choices, evaluation
metrics, and serialized model artifacts. CI/CD integration automates scheduled retraining and deploys
updated models with minimal manual intervention.

## VIII. Features

Selection criteria (in priority order): prediction quality, interpretability (black-box solutions are not
trusted early in the project), computation time, and pipeline stability. A feature requiring more than 6
hours to compute is excluded regardless of metric gain. Feature hypothesis list: competitor price delta
(absolute and relative), promo and discount calendar, SKU price (regular and discounted), penetration
ratio (SKU sales / category sales at levels 1–3), brand and category attributes, price elasticity
coefficient, rolling sales statistics (sum/min/max/mean/std/quantile over 7/14/30/60/90/180-day windows),
same-SKU sales one year prior, weather forecast, store foot-traffic, store-level total sales volume, and
macroeconomic indicators. Feature importance via SHAP, LIME, shuffle importance, and built-in methods
(linear coefficients, gradient boosting split counts). RFE used for automated selection in early phases.
Feature quality tests run pre- and post-training: range/outlier checks, pairwise correlation below
threshold, nonzero coefficient or split count, and compute time under 6h. Centralized feature store
refreshed daily at (SKU, store, day) granularity with versioning and dependency tracking.

## IX. Measuring and Reporting

Offline experiment: a unified single model outperforms per-category models, especially for small
categories where per-category models lacked sufficient training data. Improvement is consistent across
seasons and key geographies. Expected revenue uplift in the pilot group: 0.3–0.7%. A/B test design:
split by distribution center (each center serves a cluster of stores); representative store subsets
assigned to groups A and B. Primary metric: average check value (strong proxy for revenue assuming
stable check volume). Hypothesis: revenue increases by at least 0.3%. Control metrics: daily check
count, model update frequency, offline quantile metrics, and WAPE. Statistical test: Welch's t-test,
5% significance level, 10% type II error rate. Duration: one month, extended from two weeks to cover
a full replenishment cycle. Report includes: 95% confidence intervals for all metrics, time-series
plots for both groups, absolute counts, methodology appendix, and next-step recommendation.

## X. Integration

Three-tier fallback: primary = main model on key features (activated when no drift is detected in that
subset); secondary = SARIMA or Prophet (less feature-dependent, activated on feature drift); tertiary =
last week's actuals adjusted for known upcoming events and holidays. HTTP API: GET endpoint with SKU,
entity, period, and version parameters, returning JSON predictions per (SKU, entity, period). Separate
release tracks for infrastructure (software-driven, less frequent, backward-compatibility testing
required) and model (data-driven, more frequent, validated in shadow mode before promotion). Feedback
and manual override available to store managers and category managers via admin UI. No green-blue
deployment required given internal-only batch consumers. Non-engineering integration requirements
include admin panels, company-level dashboards, override UI, and a standard CI/scheduler.

## XI. Monitoring

All predictions logged with input features and timestamps to ClickHouse (column-oriented DBMS).
Infrastructure metrics (RPS, error rate, p90/p99/p999 latency) collected via Kafka and visualized in
Prometheus + Grafana (30-day retention). ML monitoring via Evidently AI covering Data Quality, Data
Stability, Data Drift, and Target Drift. Data quality alarms: missing values beyond 3σ of historical
baseline for important features (4σ for others), schema compliance, feature range checks (e.g., sales
>= 0), and a pairwise correlation delta alarm when any feature pair deviates by more than 0.15. Model
quality: all six quantile metrics (weighted and unweighted) plus RMSE and MAE monitored daily after
the 15-minute label delay; thresholds set from the first 3 months of production data. Alarms for
negative predictions and for new maximum values more than 50% above the previously seen maximum.
Prediction drift monitored via Population Stability Index > 0.2 and Wasserstein distance > 0.1 (growth
multiplier applied when comparing across calendar years). Business KPIs tracked through A/B test
rotation.

## XII. Serving and Inference

Primary requirement is batch throughput: forecasts run daily, weekly, and monthly across all SKU-store
combinations. Sensitive inventory and sales data must remain within secured infrastructure. Serving
architecture: Docker containers orchestrated by AWS Batch on EC2, with dynamic resource allocation and
job queuing for large workloads. Jobs are triggered on schedule — read inputs from S3, run inference,
write predictions back to S3. An optional Flask API layer supports on-demand inference requests. All
processing occurs within secured AWS infrastructure with credential-based authentication. Auto-scaling
groups size to workload; spot instances used where job flexibility allows to reduce cost. No specialized
hardware required at this stage — horizontal parallelism via AWS Batch is sufficient for batch
throughput. Serving-level monitoring: job success rate, duration, and failure rate; rows processed per
job; server CPU/memory/disk utilization; prediction accuracy vs actual demand; and data validation
check pass/fail alerts.

> Source: [ML-SystemDesign/MLSystemDesign](https://github.com/ML-SystemDesign/MLSystemDesign), MIT License. Distilled and rewritten, not verbatim.

# ML Design Doc Template — 12 Sections

Section names are verbatim from the source template. For each section: what it must answer, what authors commonly omit, and how deep to go per maturity level (POC vs production).

## I. Problem Definition

Must answer: what problem, for whom, why now. Origin of the problem, stakeholders and their current workflow, why existing (non-ML or legacy) solutions fall short, business impact and cost of the status quo, prior attempts and their lessons, known risks, cost of a wrong prediction, and required safeguards.
Commonly omitted: cost of mistakes; what happens when the model is wrong and who absorbs the damage.
POC: origin, stakeholders, expected benefit, mistake cost. Production: add prior work, infrastructure needs, failure modes, safeguards.

## II. Metrics and Losses

Must answer: how success is measured and what the model optimizes. Business KPIs, model metrics (offline), the loss function, and the explicit link between loss → model metric → business KPI. Name the trade-offs (precision vs recall, latency vs accuracy).
Commonly omitted: the loss-to-business-metric link; a metric the business actually tracks.
POC: one business KPI, one model metric, chosen loss. Production: full metric hierarchy with trade-off rationale and measurement framework.

## III. Dataset

Must answer: what data exists and how it becomes training data. Sources (internal/external), labeling methodology and its QA and cost, available metadata, historical depth (seasonality coverage, retention, schema drift), known quality issues and mitigations, and the ETL pipeline with refresh cadence.
Commonly omitted: labeling cost; schema consistency over history; data freshness at inference time.
POC: sources, labels, volume, known issues. Production: add metadata usage, retention policy, full ETL design, cleaning process.

## IV. Validation Schema

Must answer: how offline evaluation mirrors reality. Validation requirements, leakage prevention, temporal constraints, inference horizon, inner/outer loop design (cross-validation strategy, time-series handling), and re-validation frequency.
Commonly omitted: temporal leakage (future information in features); mismatch between validation split and inference-time conditions.
POC: split strategy and leakage statement. Production: add inner/outer loops, update triggers, drift-driven re-validation.

## V. Baseline Solution

Must answer: what the model must beat. A constant/heuristic baseline with its measured performance, candidate model baselines with trade-offs, and an initial feature baseline.
Commonly omitted: the constant baseline — teams jump to models without a floor number.
POC: constant baseline plus one simple model. Production: add model comparison table and feature-importance-based baseline.

## VI. Error Analysis

Must answer: how errors will be found and understood. Learning-curve analysis (over/underfitting), residual analysis (error distribution, outliers), and best/worst/corner-case analysis with identified failure modes.
Commonly omitted: corner cases; a defined process for turning error findings into improvements.
POC: residual overview and top failure modes. Production: full learning-curve, residual, and case analysis with an improvement loop.

## VII. Training Pipeline

Must answer: how a model gets trained reproducibly. Architecture and tools, preprocessing and feature engineering steps, hyperparameter handling, hardware needs, and experiment tracking (logging, metrics, model versioning).
Commonly omitted: reproducibility measures (seeds, data snapshots, environment pinning).
POC: tools and a minimal tracking setup. Production: add versioning, resource plan, full reproducibility guarantees.

## VIII. Features

Must answer: which features, and how they stay healthy. Selection criteria and importance measurement, the feature list with transformations and dependencies, computational constraints, and feature tests (quality checks, drift detection).
Commonly omitted: feature tests; dependencies that break when an upstream table changes.
POC: initial feature list with sources. Production: add selection methodology, tests, drift monitoring, update plan.

## IX. Measuring and Reporting

Must answer: how results are proven and communicated. Success metrics and tracking, A/B testing strategy (traffic allocation, success criteria), and reporting to stakeholders.
Commonly omitted: pre-registered A/B success criteria; who receives reports and how often.
POC: offline results reporting only; A/B Testing subsection = "Deferred until production." Production: full A/B design and reporting plan.

## X. Integration

Must answer: how the model enters the product safely. Fallback strategies and recovery, API design with SLAs, release cycle with rollback, and operational concerns (monitoring hooks, alerting, incident response).
Commonly omitted: fallback behavior when the model is unavailable or degraded.
POC: API sketch and a fallback statement. Production: full SLA, release/rollback procedure, incident response.

## XI. Monitoring

Must answer: how you know it still works next month. System health metrics and alert thresholds, data quality and schema validation, model quality (data/concept drift, retraining triggers), and business-metric correlation post-deployment.
Commonly omitted: retraining triggers; linking model drift to business KPI movement.
POC: basic health and quality checks. Production: all four monitoring layers with thresholds and triggers.

## XII. Serving and Inference

Must answer: how predictions reach consumers within constraints. Latency/throughput/scalability/cost requirements, serving architecture (deployment mode, scaling, security), optimization trade-offs, and serving-level monitoring.
Commonly omitted: cost per prediction; degradation response when load exceeds capacity.
POC: requirements and a minimal architecture; Optimization subsection = "Deferred until production." Production: full architecture, optimization analysis, degradation playbook.

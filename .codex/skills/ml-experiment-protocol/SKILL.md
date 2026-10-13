---
name: ml-experiment-protocol
description: Use when comparing, tuning, or selecting predictive models, or when judging whether a model result supports a claim. Covers baselines, hypotheses, search budgets and stopping rules, fair comparison, final-test discipline, variability, slices, calibration and thresholds, error analysis, ablations, and the decision to keep the simpler model or adopt a complex one, for tabular, forecasting, vision, and NLP or deep-learning experiments. Not for ML system design documents, design reviews, product stage-gate decisions, or descriptive analysis of business data.
---

# ML experiment protocol

Choose and evaluate models so that the result holds up. Library-specific code belongs to stack skills such as scikit-learn, which implement this protocol and cannot change it.

## Prerequisites

Experiments need a problem contract, a split, and a leakage verdict, as produced by the ml-problem-and-data-audit skill. Reuse valid existing evidence. When the user asks for a later stage and prerequisites are missing, first complete the ones that stage depends on: at minimum the target, the decision time, the primary metric, and a split that matches deployment. Until they are established, do not train or tune models, even under an exploratory label; limit the work to inspecting the data and sketching the protocol or code.

Before the first material run, set up run records in the format of the ml-provenance-and-handoff skill (`runs/<run-id>/run.json` unless the project has its own location), and record every material run, including failed ones. A run is material when its result can inform a decision or appear in a report.

## Workflow

1. **Plan.** Fill [assets/experiment-plan.md](assets/experiment-plan.md) before results arrive: the question, baselines, hypotheses, search space, budget, selection rule, stopping criteria, and variability method.
2. **Baselines first.** Run a naive baseline (prior or majority class, mean or median, last value, seasonal naive, or the current business rule) and a simple model (a regularized linear or logistic model, a small tree model, or the simplest standard architecture). When a complex model does not beat them, revisit the data, target, and features before tuning further.
3. **Controlled experiments.** Make one interpretable change per manual experiment, or run a declared search. Compare candidates on identical data, split, metric, and preprocessing policy, with a comparable tuning budget. Record any difference in conditions in [assets/baseline-comparison.md](assets/baseline-comparison.md).
4. **Tuning.** Tune only on training and validation data or inner cross-validation. Stop when the budget is spent, when gains fall below the minimum useful lift or within observed variability, or when the protocol becomes contaminated. Keep every trial's result.
5. **Variability.** Name the sources (data sampling, groups, forecast origins, training randomness) and choose a matching method from [references/variability.md](references/variability.md). No fixed seed count or interval method fits every task.
6. **Freeze, then evaluate once.** Freeze the candidate: configuration, preprocessing, threshold, and calibration. Evaluate it on the final test once and log that access. Report in [assets/evaluation-report.md](assets/evaluation-report.md): primary and guardrail metrics against the baseline, variability with its method, important slices, and, when probabilities or a threshold drive decisions, calibration and threshold behavior ([references/thresholds-and-calibration.md](references/thresholds-and-calibration.md)).
7. **Error analysis.** Inspect actual errors on out-of-fold or validation predictions and record them in [assets/error-analysis.md](assets/error-analysis.md): high-cost failures, systematic slices, label problems, and cases where the baseline and candidate disagree. Run ablations when the claim is that a specific component helps.
8. **Decide.** Fill [assets/candidate-decision.md](assets/candidate-decision.md). Adopt the more complex candidate only when its lift exceeds both the minimum useful lift and the observed variability, its guardrails and slices hold, and the gain justifies its latency, compute, and maintenance cost. Otherwise keep the simpler model.

## Final-test discipline

The final test must not influence features, model family, hyperparameters, thresholds, calibration, or stopping. Once a test result has influenced any of these, every later result on that set is exploratory, and the report says so. Reshuffling or relabeling the same data does not create an untouched test; a reliable estimate then needs data that did not inform development, such as a later period or newly collected data. Decline requests to tune against the final test and offer validation-based tuning instead.

## Reporting

- A reproducible result that shows no improvement is a valid outcome; report it as one.
- Reproduce the decisive comparison when the authorized compute budget allows; otherwise record it as skipped, with the reason.
- Report the variability you observed and the checks you skipped. Never present an unexecuted check as executed.
- Record any protocol change made after seeing results; evidence gathered after the change is exploratory.

## Proportionality

Match the effort to the question. An exploratory signal check needs a valid split, a naive baseline, a simple model, and run records. By default it lives in one script or notebook, with one run record per run and a short report; add structure only when the existing project already needs it. Tracking servers, model registries, serving, and monitoring are added only when production is an explicit requirement.

## Outputs

| Output | Template |
|---|---|
| Experiment plan | [assets/experiment-plan.md](assets/experiment-plan.md) |
| Baseline comparison | [assets/baseline-comparison.md](assets/baseline-comparison.md) |
| Evaluation report | [assets/evaluation-report.md](assets/evaluation-report.md) |
| Error analysis | [assets/error-analysis.md](assets/error-analysis.md) |
| Candidate decision | [assets/candidate-decision.md](assets/candidate-decision.md) |

Use the project's existing locations when it has them. A brief request can carry the same sections in the reply instead of files. Sources and authorship: [SOURCES.md](SOURCES.md).

# Sources and authorship

Package: `scikit-learn` · Version 1.0.0 · Sources reviewed 2026-10-13 against scikit-learn 1.9.1

## Authorship

Written for this repository in October 2026 from the official scikit-learn documentation below. The guidance, code patterns, and evaluation cases are original. A private research brief, which is not distributed, identified [K-Dense-AI's scikit-learn skill](https://github.com/K-Dense-AI/scientific-agent-skills/blob/main/skills/scikit-learn/SKILL.md) as a related resource; no text from it is included.

## Sources

| Source | URL | Used for |
|---|---|---|
| Common pitfalls and recommended practices | https://scikit-learn.org/stable/common_pitfalls.html | Leakage through preprocessing and feature selection; Pipeline; controlling randomness |
| Cross-validation | https://scikit-learn.org/stable/modules/cross_validation.html | Grouped, stratified, predefined, and time-series splitters; `cross_val_predict` limits |
| `TimeSeriesSplit` | https://scikit-learn.org/stable/modules/generated/sklearn.model_selection.TimeSeriesSplit.html | `test_size` and `gap` |
| `StratifiedGroupKFold` | https://scikit-learn.org/stable/modules/generated/sklearn.model_selection.StratifiedGroupKFold.html | Stratified grouped folds |
| Nested versus non-nested cross-validation | https://scikit-learn.org/stable/auto_examples/model_selection/plot_nested_cross_validation_iris.html | Optimistic `best_score_`; nested estimates |
| Metadata routing | https://scikit-learn.org/stable/metadata_routing.html | Routing `groups` to inner splitters |
| Dummy estimators | https://scikit-learn.org/stable/modules/model_evaluation.html#dummy-estimators | Baselines |
| Tuning the decision threshold | https://scikit-learn.org/stable/modules/classification_threshold.html | `TunedThresholdClassifierCV`, `FixedThresholdClassifier` |
| Probability calibration | https://scikit-learn.org/stable/modules/calibration.html | `CalibratedClassifierCV`, `FrozenEstimator`, calibration checks |
| `TargetEncoder` | https://scikit-learn.org/stable/modules/generated/sklearn.preprocessing.TargetEncoder.html | Cross fitting in `fit_transform` |

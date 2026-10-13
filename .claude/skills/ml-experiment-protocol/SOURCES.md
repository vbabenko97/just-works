# Sources and authorship

Package: `ml-experiment-protocol` · Version 1.0.0 · Sources reviewed 2026-10-13

## Authorship

Written for this repository in October 2026. The workflow, templates, and evaluation cases are original. The design draws on a private research brief, which is not distributed, and on the primary sources below. The brief identified [Emily2040/data-science-agent-skills](https://github.com/Emily2040/data-science-agent-skills) as a related design; it could not confirm that repository's license, so no text from it is included.

## Sources

| Source | URL | Used for |
|---|---|---|
| Google: Rules of Machine Learning, rule 4 | https://developers.google.com/machine-learning/guides/rules-of-ml | A simple first model as the baseline for later models |
| Google Machine Learning Crash Course: Dividing the original dataset | https://developers.google.com/machine-learning/crash-course/overfitting/dividing-datasets | Test sets wearing out with repeated use |
| scikit-learn: Nested versus non-nested cross-validation | https://scikit-learn.org/stable/auto_examples/model_selection/plot_nested_cross_validation_iris.html | Optimistic bias of scores used for selection |
| scikit-learn: Statistical comparison of models using grid search | https://scikit-learn.org/stable/auto_examples/model_selection/plot_grid_search_stats.html | Correlated fold scores; corrected resampled t-test |
| scikit-learn: Dummy estimators | https://scikit-learn.org/stable/modules/model_evaluation.html#dummy-estimators | Naive baselines |
| scikit-learn: Tuning the decision threshold | https://scikit-learn.org/stable/modules/classification_threshold.html | Threshold selection apart from the evaluation data |
| scikit-learn: Probability calibration | https://scikit-learn.org/stable/modules/calibration.html | Disjoint calibration data; calibration checks |
| Agent Skills specification | https://agentskills.io/specification | Package layout |

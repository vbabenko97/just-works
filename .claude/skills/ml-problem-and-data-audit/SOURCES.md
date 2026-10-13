# Sources and authorship

Package: `ml-problem-and-data-audit` · Version 1.0.0 · Sources reviewed 2026-10-13

## Authorship

Written for this repository in October 2026. The workflow, templates, and evaluation cases are original. The design draws on a private research brief, which is not distributed, and on the primary sources below. The brief identified [Emily2040/data-science-agent-skills](https://github.com/Emily2040/data-science-agent-skills) as a related design; it could not confirm that repository's license, so no text from it is included.

## Sources

| Source | URL | Used for |
|---|---|---|
| scikit-learn: Common pitfalls and recommended practices | https://scikit-learn.org/stable/common_pitfalls.html | Splitting before preprocessing; fitting transformations on training data only |
| scikit-learn: Cross-validation | https://scikit-learn.org/stable/modules/cross_validation.html | Grouped and time-ordered splitting |
| Google Machine Learning Crash Course: Dividing the original dataset | https://developers.google.com/machine-learning/crash-course/overfitting/dividing-datasets | Duplicates between training and evaluation data; test sets wearing out |
| Forecasting: Principles and Practice (3rd edition), 5.10 Time series cross-validation | https://otexts.com/fpp3/tscv.html | Rolling forecast origins |
| Forecasting: Principles and Practice (3rd edition), 5.2 Some simple forecasting methods | https://otexts.com/fpp3/simple-methods.html | Naive and seasonal naive baselines |
| Agent Skills specification | https://agentskills.io/specification | Package layout |

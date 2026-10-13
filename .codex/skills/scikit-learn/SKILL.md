---
name: scikit-learn
description: Use when writing or reviewing scikit-learn code for preprocessing, cross-validation, model comparison, hyperparameter search, threshold tuning, or probability calibration. Implements an accepted evaluation protocol with Pipeline and ColumnTransformer, group- and time-aware cross-validation, dummy baselines, explicit scoring, and budgeted search, and flags preprocessing fitted outside training folds. Does not decide the split, metric, or final-test policy; it follows them.
---

# scikit-learn

Implement the accepted evaluation protocol correctly in scikit-learn. Written against the scikit-learn 1.9.1 documentation.

## Authority

This skill does not set the split, the metric, or the final-test policy. When a request conflicts with the accepted protocol, for example "just use train_test_split" on grouped data, keep the protocol and explain why. When no protocol exists yet, establish the target, decision time, split, and metric first (the ml-problem-and-data-audit skill). Until then, limit the work to inspecting data and drafting code; do not run training whose results could inform a decision or appear in a report, whatever label the work carries.

## Rules

- **Fit learned preprocessing inside a `Pipeline`**: imputation, scaling, encoding, target encoding, feature selection, dimensionality reduction, and text vectorizers. Use `ColumnTransformer` for per-column preprocessing. Do not fit anything on the data used to evaluate the model. Code that fits transformations on the full dataset before splitting produces optimistic scores, and those scores are not comparable with corrected ones. A model without learned preprocessing, such as a tree model on raw features, needs no `Pipeline`; fitting it inside the folds is enough.
- **Build the splitter from the accepted split:**

  | Accepted split | Splitter |
  |---|---|
  | Independent rows | `KFold` or `StratifiedKFold` with `shuffle=True` and an integer `random_state` |
  | Groups | `GroupKFold`, `StratifiedGroupKFold`, `GroupShuffleSplit`, or `LeaveOneGroupOut`, with `groups=` |
  | One evenly spaced series | `TimeSeriesSplit(n_splits=..., test_size=..., gap=...)` on rows sorted by time |
  | Panel data, forecast origins, label maturity | An explicit list of `(train_idx, test_idx)` pairs built from the origins |
  | Persisted assignments | `PredefinedSplit(test_fold)` or a list of index pairs loaded from the assignments file |

  `train_test_split` cannot account for groups, so it does not fit grouped data.
- **Materialize folds once** with `folds = list(cv.split(X, y, groups))` and pass `cv=folds` to every comparison, so every candidate sees identical folds.
- **Include a dummy baseline** in every comparison: `DummyClassifier(strategy="prior")` or `"most_frequent"`, `DummyRegressor(strategy="mean")` or `"median"`. For forecasting, compute naive and seasonal-naive forecasts directly.
- **Name the scoring** (`scoring="average_precision"`, a dict of metrics, or `make_scorer`). The estimator's default `score` is rarely the metric in the problem contract.
- **Search within a budget**: `RandomizedSearchCV(n_iter=...)` or a small `GridSearchCV`, over the whole pipeline (parameter names such as `model__C`), with the accepted folds. Keep `cv_results_` with the run record. `best_score_` is optimistic for the selected configuration; nested cross-validation or a later untouched evaluation gives an unbiased estimate.
- **Pass groups to every splitter that needs them.** `search.fit(X, y, groups=groups)` reaches the search's splitter. In nested cross-validation, enable metadata routing so that groups reach the inner splitter as well; see the patterns reference.
- **Thresholds and calibration on development data only, as part of the candidate**: wrap the tuned pipeline in `CalibratedClassifierCV` (cross-validated, or `FrozenEstimator` with a calibration split disjoint from the evaluation data) and that in `TunedThresholdClassifierCV` with a scorer that encodes the decision costs. Inside these nested fits, pass splitter objects rather than precomputed index folds, and route groups with metadata routing.
- **`cross_val_predict` gives out-of-fold predictions** for error analysis and reliability curves. It is not an estimate of generalization error.
- **`TargetEncoder`**: keep it inside the pipeline or use `fit_transform` on training data, which cross-fits internally. `fit(X, y).transform(X)` on the same rows leaks the target.
- **Randomness**: pass integer `random_state` values to splitters. For reproducible estimators, pass integers, or one `np.random.RandomState` created at the top of the program, rather than setting the global NumPy seed.
- **Final test once, on the complete candidate**: evaluate the selected estimator with its calibration and threshold, fitted on all development rows, never a component such as `search.best_estimator_` alone. Score the reserved rows once and record the access.

`HistGradientBoostingClassifier` and `HistGradientBoostingRegressor` handle missing values natively and accept pandas `category` columns with `categorical_features="from_dtype"`, so they often need little preprocessing.

## Patterns

[references/patterns.md](references/patterns.md) holds code for each rule: grouped comparison with baselines, persisted folds, origin-based time folds, budgeted search, nested grouped search with metadata routing, the complete candidate with calibration and a cost-based threshold, its out-of-fold predictions, and its single final-test evaluation.

Sources and authorship: [SOURCES.md](SOURCES.md).

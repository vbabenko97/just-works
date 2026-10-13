# scikit-learn patterns

Written against scikit-learn 1.9.1. The snippets build on each other and share these names: `X_dev`, `y_dev`, and `groups_dev` hold the development rows; `X_test` and `y_test` hold the final test, used once; `numeric` and `categorical` list the feature columns. Adapt the splitter and metric to the accepted protocol.

## Grouped comparison with baselines

```python
from sklearn.compose import ColumnTransformer
from sklearn.dummy import DummyClassifier
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import StratifiedGroupKFold, cross_validate
from sklearn.pipeline import Pipeline, make_pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

preprocess = ColumnTransformer([
    ("num", make_pipeline(SimpleImputer(strategy="median"), StandardScaler()), numeric),
    ("cat", OneHotEncoder(handle_unknown="ignore"), categorical),
])
candidates = {
    "dummy_prior": DummyClassifier(strategy="prior"),
    "logistic": Pipeline([("preprocess", preprocess), ("model", LogisticRegression(max_iter=1000))]),
    # Categorical columns must have the pandas "category" dtype.
    "hist_gb": HistGradientBoostingClassifier(categorical_features="from_dtype", random_state=0),
}
cv = StratifiedGroupKFold(n_splits=5, shuffle=True, random_state=0)
folds = list(cv.split(X_dev, y_dev, groups=groups_dev))  # identical folds for every candidate
scoring = {"average_precision": "average_precision", "neg_log_loss": "neg_log_loss"}
results = {
    name: cross_validate(model, X_dev, y_dev, cv=folds, scoring=scoring)
    for name, model in candidates.items()
}
paired_difference = (
    results["hist_gb"]["test_average_precision"] - results["logistic"]["test_average_precision"]
)
```

Judge a candidate by the paired per-fold differences, not by the two means alone.

## Persisted folds

```python
from sklearn.model_selection import PredefinedSplit

# `assignments` comes from the assignments file named in the split configuration, with one row
# per development row; align it to X_dev by row ID first. Fold -1 means "always in training".
persisted_cv = PredefinedSplit(test_fold=assignments.loc[X_dev.index, "fold"].to_numpy())
```

## Folds from forecast origins

```python
import numpy as np


def origin_folds(label_time, prediction_time, origins, test_window):
    """Train on rows whose label was observable at the origin; test on predictions made after it."""
    for origin in origins:
        train = np.flatnonzero(label_time <= origin)
        test = np.flatnonzero((prediction_time > origin) & (prediction_time <= origin + test_window))
        yield train, test


time_folds = list(origin_folds(label_time, prediction_time, origins, test_window))
```

Each test row's features must be computed as of that row's own prediction time. For a single, evenly spaced series sorted by time, `TimeSeriesSplit(n_splits=5, test_size=horizon, gap=gap)` gives the same structure.

## Budgeted search

```python
import numpy as np
from sklearn.model_selection import RandomizedSearchCV

search = RandomizedSearchCV(
    candidates["logistic"],
    {"model__C": np.logspace(-3, 2, 50)},
    n_iter=20,
    cv=folds,
    scoring="average_precision",
    random_state=0,
)
search.fit(X_dev, y_dev)
trials = search.cv_results_  # store every trial with the run record, not only the best
```

## Nested grouped search

```python
import sklearn
from sklearn.model_selection import GridSearchCV, GroupKFold, cross_validate

with sklearn.config_context(enable_metadata_routing=True):
    inner_search = GridSearchCV(
        candidates["logistic"],
        {"model__C": [0.01, 0.1, 1.0, 10.0]},
        cv=GroupKFold(n_splits=4),
        scoring="average_precision",
    )
    nested = cross_validate(
        inner_search,
        X_dev,
        y_dev,
        cv=GroupKFold(n_splits=5),
        params={"groups": groups_dev},  # routed to the outer and the inner splitter
        scoring="average_precision",
    )
```

The outer scores estimate the whole tuning procedure. Without metadata routing, `cross_validate(..., groups=groups_dev)` gives groups to the outer splitter only: an inner group splitter then has no groups and fails, and an inner splitter that ignores groups mixes them silently.

## The complete candidate: tuned pipeline, calibration, and threshold

```python
import sklearn
from sklearn.base import clone
from sklearn.calibration import CalibratedClassifierCV
from sklearn.metrics import confusion_matrix, make_scorer
from sklearn.model_selection import StratifiedGroupKFold, TunedThresholdClassifierCV


def negative_cost(y_true, y_pred, fp_cost, fn_cost):
    tn, fp, fn, tp = confusion_matrix(y_true, y_pred, labels=[0, 1]).ravel()
    return -(fp * fp_cost + fn * fn_cost)


cost_scorer = make_scorer(negative_cost, fp_cost=15, fn_cost=900)
candidate = TunedThresholdClassifierCV(
    CalibratedClassifierCV(
        clone(search.best_estimator_), method="sigmoid", cv=StratifiedGroupKFold(n_splits=3)
    ),
    scoring=cost_scorer,
    cv=StratifiedGroupKFold(n_splits=5),
)
with sklearn.config_context(enable_metadata_routing=True):
    candidate.fit(X_dev, y_dev, groups=groups_dev)  # groups reach both splitters
chosen_threshold = candidate.best_threshold_
```

The candidate is everything that makes decisions: the tuned pipeline, its calibration, and its threshold. Calibration and threshold selection each run their own grouped cross-validation inside the development rows. They take splitter objects rather than the `folds` index list, because indices computed on all development rows do not apply inside a nested fit. After choosing the threshold, `TunedThresholdClassifierCV` refits the calibrated pipeline on all development rows. Drop a wrapper only when decisions do not use it, for example calibration when only the ranking matters.

To calibrate a model that is already fitted, wrap it as `CalibratedClassifierCV(FrozenEstimator(model))` (from `sklearn.frozen`) and fit it on rows disjoint from both the model's training rows and the evaluation rows.

## Out-of-fold predictions of the candidate

```python
from sklearn.calibration import calibration_curve
from sklearn.model_selection import cross_val_predict

oof_cv = StratifiedGroupKFold(n_splits=5)
with sklearn.config_context(enable_metadata_routing=True):
    oof_decision = cross_val_predict(
        candidate, X_dev, y_dev, cv=oof_cv, params={"groups": groups_dev}
    )
    oof_proba = cross_val_predict(
        candidate, X_dev, y_dev, cv=oof_cv, params={"groups": groups_dev}, method="predict_proba"
    )[:, 1]
fraction_positive, mean_predicted = calibration_curve(y_dev, oof_proba, n_bins=10)
```

Use out-of-fold decisions and probabilities for error analysis and reliability curves, not as the generalization estimate.

## Final test, once

```python
from sklearn.metrics import average_precision_score, brier_score_loss

test_proba = candidate.predict_proba(X_test)[:, 1]  # calibrated probabilities
final_results = {
    "total_cost": -cost_scorer(candidate, X_test, y_test),  # decisions at the tuned threshold
    "average_precision": average_precision_score(y_test, test_proba),
    "brier_score": brier_score_loss(y_test, test_proba),
}
```

Evaluate the fitted candidate itself. Scoring `search.best_estimator_` would evaluate a model without the calibration and threshold that make the decisions. Record this evaluation in the run record and in the split configuration's final-test access log.

# Thresholds and calibration

Read this when a decision depends on a threshold over model scores, or when people or systems downstream read scores as probabilities.

## Thresholds are model parameters

Choose the threshold on development data, never on the final test, and choose it from the decision rather than a default metric:

- **Costs**: minimize expected cost using the error costs from the problem contract, for example a missed fraud at EUR 900 against a false alert at EUR 15.
- **Capacity**: when reviewers can handle k cases per period, choose the threshold that yields about k alerts at the expected volume, and report precision and recall at that operating point.
- **Constraint**: a required recall or maximum false-positive rate.

Select the threshold on out-of-fold or validation predictions, freeze it, then evaluate once on untouched data. An F1 score computed at the threshold that maximizes it on the same evaluation set is optimistic.

## Calibration

Ranking quality (for example AUC) and calibration (whether a predicted 0.2 means a 20% rate) are different properties. Check calibration whenever probabilities are consumed.

- Fit the calibrator on data disjoint from the evaluation data: cross-validated calibration within development data, or a separate calibration split.
- Check calibration with a reliability curve and proper scoring rules such as the Brier score and log loss. A lower Brier score alone does not show better calibration, because it mixes calibration with discrimination.
- Sigmoid calibration suits small calibration sets. Isotonic calibration needs more data (roughly a thousand samples or more) and can overfit.
- A change in class prevalence between training and deployment shifts calibration; recheck it on recent data.

Calibration fitted on the final test makes every probability-based number on that set optimistic and turns the set into development data.

Sources: [scikit-learn, Tuning the decision threshold](https://scikit-learn.org/stable/modules/classification_threshold.html); [scikit-learn, Probability calibration](https://scikit-learn.org/stable/modules/calibration.html).

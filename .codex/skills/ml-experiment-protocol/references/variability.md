# Variability

A difference between two models counts as evidence only when it is large compared with how much the metric moves under resampling and retraining. Choose the method from the sampling unit and the dependence structure, and report it with the result.

## Choose the method

| Structure | Method |
|---|---|
| Independent rows, cross-validation | Per-fold scores on identical folds. Analyze the paired per-fold differences between models rather than two separate means. Repeating cross-validation with different shuffles shows sensitivity to the split. Fold scores are correlated because training sets overlap, so naive standard errors are too small; a corrected resampled t-test (Nadeau and Bengio) is one option. |
| Grouped data | Group-level folds, or bootstrap resampling of whole groups. |
| Time series | Per-origin errors from the backtest, compared origin by origin. Resample blocks of time, never individual rows. |
| Single holdout set | Bootstrap the evaluation units (rows, or groups when the data is grouped) for an interval. For a model comparison, use a paired bootstrap of the difference on the same resamples. |
| Stochastic training (neural networks, some ensembles) | Repeat each configuration over several seeds that vary initialization and data order, with the split held fixed, and compare the distributions. |

## Report

State the estimate, the spread, the method, and the number of units (folds, groups, origins, or seeds). Compare the difference with both the observed variability and the minimum useful lift from the problem contract. A difference inside the variability means no difference was detected, which favors the simpler model.

When compute limits the number of repetitions, say how many were run and that the estimate is rough.

Source: [scikit-learn, Statistical comparison of models using grid search](https://scikit-learn.org/stable/auto_examples/model_selection/plot_grid_search_stats.html).

# Leakage audit

Decision time: <from the problem contract>
Split: <split configuration path and assignments hash>

## Feature availability

| Feature | Source and timestamp | Available at decision time? | Evidence | Verdict: keep / fix / drop / unknown |
|---|---|---|---|---|

An unknown verdict on a material feature blocks modeling until it is resolved.

## Checks

| Check | Result | Evidence |
|---|---|---|
| Target proxies and post-outcome fields | | |
| Aggregates and windows end before decision time | | |
| Joins use as-of values, not current snapshots | | |
| Entity overlap across splits matches the evaluated population (none when it represents unseen entities) | | |
| No established duplicate of the same item (same ID, source record, or content) on both sides of a split | | |
| Learned preprocessing is fitted only inside training folds | | |
| Final test has not informed feature, model, parameter, threshold, or stopping decisions | | |
| Unexpectedly strong results investigated | | |

## Verdict

<no material leakage / leakage fixed: list / blocking leakage: list>

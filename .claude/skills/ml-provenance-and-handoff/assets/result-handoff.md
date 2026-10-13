# Result: <short title>

Claim: <one sentence: what was achieved, on which evaluation data, compared with which baseline>
Status: validated | exploratory | not reproducible | no improvement over baseline
Intended use: <population, decision, inputs>
Not supported: <uses outside the evaluated conditions>

## Evidence chain

| Item | Value |
|---|---|
| Decisive run | <run ID and path to run.json> |
| Baseline run | <run ID> |
| Code | <commit SHA; clean, or dirty with diff and source snapshot paths> |
| Data | <identity method and value> |
| Split | <assignments hash; final-test status> |
| Environment | <lock file or package list; hardware> |
| Configuration and seeds | <path> |
| Artifacts | <model, predictions, logs, each with sha256> |

## Reproduce

```bash
<exact commands: check out the recorded revision, apply the saved tracked-file diff when present, restore the untracked source snapshot, and run the result; credentials replaced by variable names>
```

Reproduction status: reproduced (<observed difference>) | not reproduced (<reason>) | skipped (<reason>)

## Assumptions

- <assumption and its effect on the claim>

## Limitations and known failure modes

- <limitation>

## Checks not run

| Check | Reason |
|---|---|

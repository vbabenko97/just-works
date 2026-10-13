# Experiment plan

Question: <what the experiments must decide>
Readiness: <path to the readiness verdict, or the prerequisites completed for this stage>
Evaluation protocol: <split configuration and assignments hash; primary metric; guardrails>
Final test policy: <reserved rows; evaluated once on the frozen candidate; access log location>
Run records: <directory and format>

## Baselines

| Name | Kind: naive / domain rule / simple model | Why it is relevant |
|---|---|---|

## Hypotheses

| ID | Change: one interpretable factor or a declared search | Expected effect | Decision it informs |
|---|---|---|---|

## Search

- Search space: <parameters and ranges>
- Budget: <trials, wall-clock time, compute>. Compared candidates get the same budget class, or the difference is recorded.
- Selection rule, fixed before results: <for example, best mean score, or the simplest candidate within observed variability of the best>
- Stop when: the budget is spent; gains fall below the minimum useful lift; gains sit within observed variability; added complexity is not justified; or the protocol becomes contaminated.

## Variability

- Sources: <data sampling, groups, forecast origins, training randomness>
- Method: <paired fold differences, group-level resampling, per-origin errors, repeated seeds>

# Problem contract

Status: draft | accepted | blocked
Last updated: <date>

| Field | Value | Source: owner statement, document, or labeled assumption |
|---|---|---|
| Decision or use | <action the prediction informs> | |
| Prediction unit | <one prediction per customer, encounter, image, store-day, ...> | |
| Target | <exact definition, how the label is recorded, and when it becomes known> | |
| Decision time | <moment the prediction is made> | |
| Information available at decision time | <sources and their cutoffs> | |
| Horizon and label delay | <how far ahead the prediction looks; delay before the label is observable> | |
| Deployment population | <who or what will be scored; known differences from historical data> | |
| Primary metric | <metric and why it reflects the decision> | |
| Guardrail metrics | <metrics that must not get worse> | |
| Error costs | <cost of false positives and false negatives, or the regression analogue> | |
| Minimum useful lift | <smallest improvement over the current approach worth adopting> | |
| Constraints | <latency, compute, interpretability, regulation> | |

## Assumptions

- A1: <assumption>. Affects: <field>. Confirm by: <question for the owner>.

## Open questions that block modeling

- Q1: <question>. Blocks: <field>.

## Claims outside this contract

<If the request implies a causal claim ("X causes churn"), state that a predictive model does not establish it.>

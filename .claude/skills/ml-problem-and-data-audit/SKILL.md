---
name: ml-problem-and-data-audit
description: Use before training, tuning, or evaluating a predictive model on a new or changed problem or dataset, and when a model result looks too good to be true. Fixes the problem contract (prediction unit, target, decision time, horizon, metric, error costs) and audits data quality, joins, duplicates, split validity, and leakage, ending in a readiness verdict. Covers tabular, forecasting, vision, and text data. Not for ML system design documents, design reviews, product stage-gate decisions, or descriptive analysis of business data.
---

# ML problem and data audit

Decide whether modeling can begin, and record the evidence for that decision. This skill does not train models; the ml-experiment-protocol skill takes over once the verdict allows it.

## Start from existing evidence

Look for earlier problem contracts, data reports, split files, and audits in the project before writing new ones. Reuse what is still valid for the current data and question, and complete only the missing or stale parts that the requested stage depends on. Use the project's existing artifact locations; the templates in `assets/` are defaults. For a quick question, the same sections may appear in the reply instead of files, ending with the verdict.

## 1. Problem contract

Fill [assets/problem-contract.md](assets/problem-contract.md). The contract fixes what the evaluation has to imitate:

- the prediction unit, the target definition, and when the label becomes known;
- the decision time and the information available at that moment;
- the horizon and label delay for forecasts and delayed outcomes;
- the deployment population;
- the primary metric, guardrail metrics, error costs, and minimum useful lift.

Take these from the user, the repository, or documents. Ask the owner when the target meaning, decision time, horizon, error costs, or deployment population is unknown and would change the split, the features, or the metric. A low-impact, reversible gap may be filled with an assumption that the contract labels as such. Do not substitute an assumed forecast horizon or decision time for the owner's answer: they define the whole evaluation. You may sketch the evaluation for candidate horizons, but the verdict stays blocked until one is chosen.

## 2. Data audit

Fill [assets/data-report.md](assets/data-report.md). Record the dataset identity (file hash or snapshot ID) first. Then check row and entity counts, schema and impossible values, missingness, the target's definition and distribution, timestamps and label maturity, rows with identical values, repeated entities, near-duplicates wherever items can repeat (images, documents, merged sources), and the cardinality and time semantics of every join. Each anomaly ends as fixed, accepted with a reason, or blocking.

Identical values do not prove that two rows record the same observation. Treat rows as duplicates only when identity or provenance shows it: the same ID, the same source record, or the same item by content hash or a reviewed near-duplicate match. Otherwise keep the unit of independence the owner stated, and report the identical rows as a finding.

Quality checks may scan all rows. Feature ideas and modeling choices come from the training portion only.

## 3. Split design

Choose the split from how the data was generated and how the model will be used:

- Random or stratified splits only when observations are independent and the deployment population resembles the historical data.
- Group-disjoint splits when one entity produces several rows and the model will score unseen entities. When deployment also scores known entities (repeat customers), the deployment population decides what the evaluation represents; report new and known entities as separate slices.
- Chronological splits whenever the model predicts the future. Forecasts need origins, a horizon, and a label-maturity rule.
- Both constraints together when both apply.

Reserve a final test when a reliable final estimate is needed. Record the split in [assets/split-config.json](assets/split-config.json) and persist the assignments (IDs per split or fold) or a deterministic procedure with its seed, plus a hash of the assignments. Verify that no forbidden overlap exists: entities the evaluation must treat as unseen, established duplicates of the same item, or training labels from after the evaluation period begins. Entity overlap is forbidden only when the evaluation represents unseen entities; a chronological evaluation of known entities overlaps by design. Each evaluation on the final test adds an entry (date, run ID, purpose) to `final_test.access_log`.

## 4. Leakage audit

Fill [assets/leakage-audit.md](assets/leakage-audit.md). For every feature, answer: would this value be available at decision time, with this exact meaning? Look for:

- target proxies and post-outcome fields;
- totals and "latest", "last", or "current" columns extracted after decision time;
- windows and aggregates that include the decision time or later;
- joins against current snapshots instead of as-of values;
- entity overlap that the evaluated population forbids, and established duplicates on both sides of a split;
- learned preprocessing (imputation, scaling, encoding, feature selection, vocabularies, dimensionality reduction) fitted outside training folds;
- final-test results that have influenced any decision.

An unexpectedly strong result is a reason to audit before reporting it. An evaluation already contaminated by leakage or test reuse is exploratory, and relabeling or reshuffling the same data does not restore an untouched test.

## 5. Readiness verdict

Finish with [assets/readiness.md](assets/readiness.md): **ready**, **ready with recorded risks**, or **blocked**. Each blocker states why it invalidates modeling or evaluation and what resolves it: an owner's answer, a data fix, or new data.

The verdict is blocked when any of these holds:

- the target, the decision time, or a required forecast horizon is undefined;
- the primary metric is undefined;
- the split is missing or unverified for the requested evaluation;
- a material feature is unavailable at decision time, or its availability is unknown;
- forbidden entity, duplicate, or time overlap exists between splits, as defined in step 3;
- learned preprocessing was fitted on evaluation data and the evaluation of record depends on it;
- the primary metric does not reflect the decision and its error costs.

A blocked verdict stops training and evaluation for the requested stage, and calling the work exploratory does not lift it. Until the blockers are resolved, work is limited to inspecting the data, running quality checks, and sketching the protocol or code.

Do not invent blockers either. When observations are independent and the contract is complete, say so and hand over to the experiment protocol.

## Conditional references

| Situation | Read |
|---|---|
| Forecasting, delayed labels, or any time-ordered prediction | [references/forecasting.md](references/forecasting.md) |
| Repeated entities: patients, customers, devices, sites, stores | [references/grouped-data.md](references/grouped-data.md) |
| Images, video frames, documents, text chunks, or merged sources | [references/duplicates.md](references/duplicates.md) |

## Outputs

| Output | Template |
|---|---|
| Problem contract | [assets/problem-contract.md](assets/problem-contract.md) |
| Data report | [assets/data-report.md](assets/data-report.md) |
| Split configuration and persisted assignments | [assets/split-config.json](assets/split-config.json) |
| Leakage audit | [assets/leakage-audit.md](assets/leakage-audit.md) |
| Readiness verdict | [assets/readiness.md](assets/readiness.md) |

Sources and authorship: [SOURCES.md](SOURCES.md).

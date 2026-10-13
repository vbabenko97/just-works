# Data report

Dataset identity: <path or table; snapshot or as-of time; sha256 or snapshot ID>
Extraction: <query or command that produced the data>
Audit code: <path and revision> · Audited on: <date>

## Shape

- Rows: <n>. Prediction units: <n>. Groups: <n per grouping column>.
- Time coverage: <first and last decision time; last date with a mature label>.

## Schema and validity

| Column | Type | Missing % | Invalid or impossible values | Notes |
|---|---|---|---|---|

## Target

- Matches the problem contract: <yes / no; how checked>
- Distribution: <class balance or summary statistics; over time when relevant>
- Label quality: <known noise, delay, censoring, or relabeling>

## Duplicates and repeated entities

- Rows with identical values: <n; whether IDs or provenance show they record the same observation>
- Rows per entity: <distribution for each grouping column>
- Near-duplicates: <method, threshold, n found> (images, documents, overlapping sources)

## Joins

| Join | Keys | Expected cardinality | Rows before / after | Time semantics: as-of value or current snapshot |
|---|---|---|---|---|

## Anomalies

| ID | Finding | Evidence | Disposition: fixed / accepted (reason) / blocking |
|---|---|---|---|

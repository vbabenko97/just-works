---
name: ml-system-design-review
description: Apply when reviewing, critiquing, scoring, or checking an ML system design document against a quality checklist. Walks a 14-group checklist, reports severity-graded findings (blocker / major / minor) with section references and concrete fixes, and ends with a ready / needs work / incomplete verdict. Critique only — pairs with ml-system-design for authoring or rewriting.
---

# ML System Design Review

Critique an ML system design document against a 14-group checklist distilled from the companion repo of Manning's *Machine Learning System Design*. Critique only: do not rewrite the document unless the user asks. For authoring a new doc, use `ml-system-design` (this skill's author pair).

## Workflow

### 1. Intake

- Accept a file path or pasted document text. If neither is provided, ask for one.
- Determine the doc's maturity level (POC vs production) from its header or content. If unstated, ask the user before evaluating — the incomplete verdict depends on it.

### 2. Evaluate

Walk `references/checklist.md` group by group. Use its mapping table to locate which doc sections each group evaluates. Three groups are cross-cutting: System Architecture and Implementation Plan draw on multiple sections; Documentation evaluates the doc itself (organization, diagrams, glossary).

### 3. Report

One finding per failed line item:

`[blocker|major|minor] <doc section> — <what is missing or weak> — Fix: <concrete action>`

- **blocker** — absence sinks the project: no business metric, leakage-prone validation, no fallback strategy, no baseline.
- **major** — significant gap; the project survives but degraded: missing drift monitoring, unspecified labeling QA, no rollback plan.
- **minor** — polish and completeness: missing glossary, thin reporting cadence, unlabeled diagram.

### 4. Verdict

- **ready** — no blockers, at most a few majors.
- **needs work** — blockers present or majors widespread, but all required sections exist.
- **incomplete** — whole required sections absent for the doc's maturity level. For POC docs, A/B Testing and Serving Optimization subsections are not required ("Deferred until production" is acceptable).

## References

- `references/checklist.md` — the 14 checklist groups with line items and the group-to-section mapping table.

# Phase 3: Validate

## Purpose

Independently re-derive the findings and check for the traps that routinely mislead executives. This is the phase that separates honest analysis from analyst overconfidence. A finding that can't survive a second derivation by a different path shouldn't be shipped.

## Input

- `findings.json` from Phase 2
- Data and exploration scripts

## Output (deliverable for this phase)

`validation.md` in the workspace, with one section per finding:

- Original claim
- Re-derivation result (matches / doesn't match / caveat)
- Bias checks (Simpson's Paradox, survivorship, selection, etc.)
- Confidence grade: High / Medium / Low
- Any caveats to include in the final story

Plus an updated `findings.json` where each finding has a `validation` field.

## Philosophy

The validation phase uses a different voice in your head. When you're exploring, you're trying to find patterns. When you're validating, you're trying to break them. If your exploration was "look for Simpson's Paradox", then your validation should be "try to make the finding disappear".

Write validation scripts **independently** — don't just re-run the exploration code. Use different aggregations, different sanity checks, different reference points. The point is to triangulate, not duplicate.

## Validation process

### 3.1 — Arithmetic re-derivation

For each key number in the findings, derive it a second way:

- If the original used `groupby(...).sum()`, re-derive from a pivot table or SQL-style query
- If the original computed a percentage, verify both the numerator and denominator independently
- If the original used a rolling average, also compute the point-in-time values and check consistency
- Reconcile subtotals: do the parts sum to the whole?

Any finding whose numbers don't match the re-derivation must be flagged with a caveat or demoted.

### 3.2 — Simpson's Paradox check

**Run this for every aggregate finding.** A positive aggregate can hide negative subgroup trends, and vice versa. It's the single most common way analysts embarrass themselves.

**Procedure:**
1. Identify the aggregation (e.g., "average conversion rate moved from X to Y")
2. Decompose by each meaningful dimension (segment, time, channel)
3. Check: does the direction of the change hold in each subgroup?
4. If some subgroups move opposite to the aggregate, the headline number is misleading

**If you find Simpson's Paradox:**
- Do not present the aggregate as the headline
- Reframe the finding around the subgroup reality
- Document why the aggregate is misleading

This check alone prevents more bad analyses than any other single discipline.

### 3.3 — Bias checks

Work through this checklist. Mark each as checked/not applicable/found-issue:

- **Survivorship bias** — Are dropped entities (churned customers, closed stores, deprecated products) excluded in a way that distorts the picture?
- **Selection bias** — Is the sample non-representative of the population you're drawing conclusions about?
- **Lookahead bias** — Does any calculation use information that wasn't available at the time?
- **Composition shift** — Did the mix of segments change over the period, such that "apples-to-apples" comparisons require normalization?
- **Metric definition drift** — Was the metric defined or measured the same way across the whole period?
- **Base rate neglect** — Are you comparing rates against a sensible denominator?

### 3.4 — Confidence grading

Assign each finding a grade:

- **High**: Numbers reconcile, no bias issues found, effect size is large relative to noise, multiple angles confirm
- **Medium**: Numbers reconcile but with caveats (small sample, short time window, one angle only)
- **Low**: Re-derivation has discrepancies, or a bias is plausible, or the effect is small relative to noise

If most findings are High, you're probably not looking hard enough.

### 3.5 — Recommendation rankability

If the analysis leads to recommendations, each one must be rankable by confidence and impact. Any recommendation that ends up neither confident nor impactful should be cut. An unranked recommendation list is a sign the analysis wasn't decisive.

## Gate (must clear before Phase 4)

- [ ] Every finding in `findings.json` has a validation section
- [ ] Simpson's Paradox check was performed on all aggregates
- [ ] Bias checklist was worked through (not just read)
- [ ] Each finding has a confidence grade
- [ ] Findings with unresolved issues are explicitly demoted or dropped

## Common pitfalls

- **Skipping validation because "I already checked".** No you didn't. Run it again with a different approach.
- **Re-running the same script.** This doesn't validate; it confirms the same bug twice.
- **Grading everything "High".** If your grades don't vary, you're not being honest.
- **Hiding caveats.** The moment you hide a caveat, the analysis becomes a marketing pitch instead of an analysis. Put them in the deliverable.

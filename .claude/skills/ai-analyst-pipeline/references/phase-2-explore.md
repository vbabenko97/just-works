# Phase 2: Explore

## Purpose

Investigate the data across six angles: profile, descriptive segmentation, time-over-time patterns, root cause drill-down, opportunity sizing, and (where relevant) experiment design. The goal is to build a mosaic of findings that collectively answer the framed question.

## Input

- `framing.md` from Phase 1
- Data files

## Output (deliverable for this phase)

A running `findings.json` in the workspace with each finding as an entry:

```json
{
  "findings": [
    {
      "id": "F1",
      "claim": "Maui visitor arrivals grew 7% YoY while other islands declined 3%",
      "type": "segmentation",
      "evidence": "Computed from data/monthly_tourism.csv, groupby island_name",
      "supporting_numbers": {"maui_yoy": 0.07, "others_yoy": -0.03},
      "hypothesis_tested": "H2",
      "confidence": "high",
      "script": "notebooks/01_segmentation.py"
    }
  ]
}
```

Every entry points to a reproducible script. If you can't regenerate the number, it's not a finding.

## Six exploration angles

Work through these roughly in order, but adapt to what the data supports. Not every analysis makes sense for every dataset — skip what isn't relevant.

### 2.1 Data profile

Goal: know the data before interpreting it.

- Row counts, date ranges, segment cardinality
- Missing value patterns (by column, by time, by segment)
- Outliers and their likely causes (genuine extremes vs. data errors)
- Obvious quality issues that might distort findings

Output: short `profile.md` summary. If quality is bad enough to compromise analysis, flag it to the user before proceeding.

### 2.2 Descriptive segmentation

Goal: find where the variance lives.

For the key metric, break it down by each plausible dimension and measure:
- Which segments contribute most to the total
- Which segments have diverged from the average
- Concentration: is the change driven by a few segments or broadly distributed?

Save each breakdown as a CSV in `notebooks/` so you can recompute later.

### 2.3 Time-over-time (trend detection)

Goal: characterize how the metric moves over time.

- Plot the metric over the full available time window
- Identify structural breaks (where does the slope change?)
- Separate seasonal patterns from trend changes (YoY comparison, or seasonal decomposition)
- Flag anomalies: specific dates or periods that don't fit the pattern

### 2.4 Root cause drill-down

This is the highest-value phase. Most analyses stop at segmentation; real insight comes from drilling further.

**Iterative decomposition process:**

1. Take the segment with the largest or most interesting movement (from 2.2)
2. Break it down by the next most plausible dimension
3. Check whether the movement concentrates in a sub-segment
4. If yes, drill again — keep going until the explanation is specific enough to act on
5. If no, try a different dimension or go one level up

The source methodology drills up to **seven layers deep**. The stopping condition is: "could a decision-maker take specific action based on this?" If you can't name a specific lever, drill further.

**Example chain:**
- Overall: tourism flat
- → By island: Maui +7%, Oahu -5%
- → Oahu by accommodation type: hotels -8%, vacation rentals +2%
- → Hotel segment by price tier: luxury -12%, mid-market -3%
- → Luxury by origin market: Japan -18%, US mainland -4%
- → (Actionable: target Japanese visitor recovery at luxury Oahu hotels)

### 2.5 Opportunity sizing

For each notable finding, estimate the business impact:

- If the pattern continues, what does the metric look like in 3/6/12 months?
- What would correcting the pattern be worth (revenue, cost, user impact)?
- Do a sensitivity analysis: what if the assumptions shift ±20%?

Do not ship findings without an attempt at quantification. "Unit economics are bad in Segment X" is less actionable than "fixing Segment X unit economics recovers ~$2M ARR at base case, ~$1M-$3M range."

### 2.6 Experiment design (optional)

If the right follow-up is a test, sketch the experiment:

- Treatment / control definition
- Primary and guardrail metrics
- Minimum detectable effect and required sample size
- Duration given traffic

Only do this when the decision actually requires an experiment. Don't manufacture one.

## Parallelization

Steps 2.1 through 2.5 can be partly parallelized. A reasonable sequence for a solo execution:

- **First**: 2.1 (profile) and 2.3 (trend) — both give context
- **Then**: 2.2 (segmentation)
- **Then**: 2.4 (root cause), iterating on the most interesting finding from 2.2
- **Finally**: 2.5 (sizing) for each root-cause finding

## Gate (must clear before Phase 3)

- [ ] `findings.json` contains at least 3 distinct findings
- [ ] Each finding points to a reproducible script
- [ ] At least one finding is the result of root-cause drill-down (not just surface segmentation)
- [ ] Hypotheses from Phase 1 are each marked as supported / refuted / inconclusive

## Common pitfalls

- **Stopping at first segmentation.** "X is down in Segment A" is a starting point, not a finding. Drill further.
- **Collecting charts without claims.** Every finding should be a claim about the business, not "here's a chart".
- **Ignoring anomalies.** If something looks weird, either explain it or flag it. Don't paper over.
- **Conflating correlation with cause.** Root-cause drill-down isolates; it doesn't prove causation. Be careful with language.
# Phase 6: Deliver

## Purpose

Assemble the storyboard, charts, and recommendations into the final deliverable format the user requested. Four output formats are supported; pick the one(s) the user asked for.

## Input

- `storyboard.md` (narrative spine)
- `charts/` (PNG files, one per beat)
- `validation.md` (for appendix and caveats)
- `findings.json` (for traceability)

## Output (deliverable for this phase)

Whichever format(s) the user chose:

1. **Markdown report** → `report.md`
2. **Marp slide deck** → `deck.md`
3. **Jupyter notebook** → `analysis.ipynb`
4. **Raw findings JSON + charts** → `findings.json` with enriched structure, plus `charts/` PNGs

If the user picked multiple, build the markdown report first (it's the reference artifact), then derive the others from it.

## Format 1: Markdown report

**Structure:**

```markdown
# [Headline message from Phase 4]

*Prepared for [audience] • [date]*

## Executive summary

[2-3 paragraph overview: the question, the key finding, the top recommendation.]

## Context

[Beats from the Context section of the storyboard. Each beat is a short paragraph
with the corresponding chart embedded inline.]

![Chart 1 action title](charts/01_aggregate_tourism.png)

[Commentary under the chart that elaborates on what it shows and transitions to the next.]

## What's happening

[Beats from the Tension section. Same structure.]

## Root cause and recommendations

[Beats from the Resolution section.]

### Recommendations

| # | Recommendation | Owner | Success metric | Confidence | Follow-up |
|---|---|---|---|---|---|
| 1 | ... | ... | ... | High | 2026-05-15 |

## Appendix

### Methodology
[How the analysis was done; pointer to notebooks/ directory.]

### Validation summary
[Summary from validation.md — Simpson's Paradox checks, bias checks, confidence grading.]

### Caveats
[Anything the audience should know about limits of the analysis.]
```

**Tips:**
- Embed PNGs with relative paths (`charts/...`) so the report is portable
- Keep commentary under each chart short — the chart title does heavy lifting
- Appendix is for the skeptical reader; it should hold up on its own

## Format 2: Marp slide deck

Marp is a markdown-based slide framework. Each slide is separated by `---`.

**Structure:**

```markdown
---
marp: true
theme: default
paginate: true
---

# [Headline message]
Prepared for [audience] • [date]

---

## [Beat 1 action title]

![bg right:55%](charts/01_aggregate_tourism.png)

- Key point 1
- Key point 2

<!-- Speaker note: elaborate on why this matters -->

---

## [Beat 2 action title]
...
```

**Marp-specific tips:**
- Use `![bg right:55%](...)` to put the chart on one side and bullets on the other
- One beat = one slide (usually). If a beat is complex, split it, but don't stuff two beats on one slide
- Speaker notes (HTML comments after a slide) let you elaborate without cluttering the slide
- Target 10-20 slides for a typical executive analysis. The source methodology's Hawaii example landed at 20.

**To render:**

```bash
# Marp CLI (install once): npm install -g @marp-team/marp-cli
marp deck.md -o deck.pdf
# or for HTML: marp deck.md -o deck.html
# or for PowerPoint: marp deck.md -o deck.pptx
```

Don't render the deck to PDF/PPTX unless the user asks — ship the `.md` and let them pick.

## Format 3: Jupyter notebook

Best when stakeholders want to re-run the analysis or tweak it.

**Structure:**

- Cell 1 (markdown): Title + headline message
- Cell 2 (markdown): Executive summary
- Cell 3 (code): Imports and data loading, clearly commented
- For each beat:
  - Markdown cell: beat title + commentary (mirrors the markdown report)
  - Code cell: the minimal code to produce the chart inline
  - Chart renders inline via `plt.show()`
- Final markdown cell: recommendations table
- Final code cells (optional): validation checks re-run so reviewers can see them pass

**Tips:**
- Use `%matplotlib inline` at the top
- Keep each code cell small — one chart per cell, not a mega-cell
- Include the data quality checks from Phase 2.1 as code cells with output, so reviewers see the basis
- At the end, include a "How to reproduce" cell that explains where the inputs are and how to run

## Format 4: Raw findings JSON + charts

For downstream consumption (another agent, a dashboard, an archiving system).

**Enriched `findings.json` structure:**

```json
{
  "metadata": {
    "analysis_name": "...",
    "prepared_for": "...",
    "date": "2026-04-17",
    "data_sources": ["data/monthly_tourism.csv"],
    "headline": "..."
  },
  "findings": [
    {
      "id": "F1",
      "claim": "...",
      "confidence": "high",
      "validation": {
        "rederived": true,
        "simpsons_paradox_checked": true,
        "bias_checks": ["survivorship: n/a", "selection: ok"]
      },
      "evidence": {},
      "chart": "charts/01_aggregate_tourism.png",
      "script": "chart_scripts/01_aggregate_tourism.py"
    }
  ],
  "recommendations": [
    {
      "id": "R1",
      "action": "...",
      "owner": "...",
      "success_metric": "...",
      "confidence": "high",
      "follow_up_date": "2026-05-15",
      "supports_findings": ["F2", "F4"]
    }
  ],
  "narrative": {
    "arc": "CTR",
    "beats": [
      {"section": "context", "title": "...", "findings": ["F1"], "chart": "charts/01_aggregate_tourism.png"}
    ]
  },
  "caveats": ["..."],
  "appendix": {
    "methodology_doc": "methodology.md",
    "validation_doc": "validation.md"
  }
}
```

**Tips:**
- Keep charts as separate PNG files in `charts/` — referenced by relative path
- Make the JSON self-describing (include a metadata block)
- Numbers should be typed (not strings), dates as ISO 8601 strings

## Process

### 6.1 — Build the markdown report first

Even if the user didn't ask for markdown, build this first. It forces the narrative to be complete in prose form, which makes the other formats straightforward to derive.

### 6.2 — Derive the other formats

For each additional format the user asked for:
- Marp: take the markdown report and split it into slides at beat boundaries
- Notebook: convert each section into markdown+code cell pairs, inlining charts
- JSON: extract structured data from the narrative and findings

### 6.3 — Final delivery summary

Give the user a short handoff:

- List of files produced with paths
- One-sentence reminder of the headline
- Top 3 recommendations summarized
- Where to look for the reproducible scripts

## Gate (analysis complete)

- [ ] Requested deliverable format(s) produced
- [ ] Every chart referenced in the deliverable exists in `charts/`
- [ ] Appendix/methodology section allows reproduction
- [ ] Final summary given to user with file locations and headline

## Common pitfalls

- **Skipping the appendix.** Without it, skeptical reviewers can't check your work and will discount the findings.
- **Over-designing slides.** Marp has enough defaults. Don't fight the tool adding custom CSS unless the user asked.
- **Mismatched headline across formats.** Keep the headline word-for-word identical in the report, deck, and notebook. It's the anchor.
- **Losing caveats between formats.** When deriving Marp/notebook from the markdown report, don't drop the caveats section. Executives need to know limits.

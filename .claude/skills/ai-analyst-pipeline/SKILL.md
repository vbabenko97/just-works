---
name: ai-analyst-pipeline
description: Run a disciplined six-phase data analysis pipeline (Frame → Explore → Validate → Story → Charts → Deliver) on tabular data (CSV/Excel) to produce executive-quality analysis with validated findings, data-driven narrative, and polished visualizations. Use this skill whenever the user has raw data and a business question — e.g. "analyze this sales data", "what happened to our metrics", "dig into this CSV", "build me an executive summary from this spreadsheet", "why did revenue drop", "root cause this trend", "put together a deck from this data" — even when they don't explicitly ask for a "pipeline" or "analysis". This skill is the right choice whenever the user expects interpretation and recommendations, not just charts or summary statistics.
---

# AI Analyst Pipeline

## Purpose

Transform raw tabular data plus a business question into an executive-ready deliverable through six explicit phases. The goal is **analytical judgment, not just execution** — surface real root causes, validate findings against common traps, and tell a coherent data-driven story.

## Why this exists

Ad-hoc analysis tends to jump straight from "here's a spreadsheet" to "here's a chart" — skipping the work that separates a good analyst from a query runner. This pipeline enforces the discipline: frame the question precisely, explore multiple angles in parallel, independently validate key numbers, structure a narrative before choosing visuals, and only then deliver. Every phase has a clear gate; downstream work doesn't start until upstream findings are sound.

## When to use this skill

- User provides CSV/Excel data and asks for analysis, interpretation, or recommendations
- User asks "why" about a metric or trend (root cause territory)
- User needs to prepare an analysis for stakeholders (exec summary, report, deck)
- User mentions building or refining a data-driven story
- User wants to size an opportunity, design an experiment, or validate a finding

## When NOT to use this skill

- Pure one-shot queries ("how many rows?", "sum this column") — just answer directly
- ETL / data cleaning without analytical intent
- Pure chart-only requests when the user explicitly doesn't want interpretation
- Data engineering tasks (pipelines, schemas, migrations)

## Pipeline overview

The pipeline has six phases. Each phase has deliverables that feed the next. Do not skip phases or run them out of order — the value comes from the discipline.

| Phase | Name | Input | Output | Reference |
|---|---|---|---|---|
| 1 | Frame | Vague question + data files | Structured analytical question + hypotheses | `references/phase-1-frame.md` |
| 2 | Explore | Framed question + data | Findings across profile, trends, drivers, root cause | `references/phase-2-explore.md` |
| 3 | Validate | Findings | Re-derived numbers, bias checks, confidence grades | `references/phase-3-validate.md` |
| 4 | Story | Validated findings | Storyboard with CTR arc | `references/phase-4-story.md` |
| 5 | Charts | Storyboard + data | Designed visualizations | `references/phase-5-charts.md` |
| 6 | Deliver | Storyboard + charts | Final deliverable in chosen format | `references/phase-6-deliver.md` |

Read each phase reference file when you enter that phase. The SKILL.md body covers orchestration only; details live in the references.

## Orchestration

### Step 1 — Confirm scope upfront

Before running the pipeline, confirm three things with the user (ask in one message, not separately):

1. **The business question** — what decision will the output support? If the user gave a vague prompt ("analyze this"), propose 2-3 specific framings and let them pick.
2. **The output format** — markdown report, Marp deck, Jupyter notebook, or raw JSON + charts. If unclear, default to markdown report.
3. **The audience** — executives, analysts, a specific team? This shapes tone, depth, and chart complexity.

Do not silently guess these. The pipeline's value depends on getting them right.

### Step 2 — Establish the workspace

Create a working directory for the analysis (e.g., `analysis-<topic>/`) with this structure:

```
analysis-<topic>/
├── data/              # Copies/references to input files
├── notebooks/         # Exploratory Python scripts (save what you run)
├── charts/            # Generated chart PNGs
├── findings.json      # Running log of validated findings
└── <deliverable>      # Final output (report.md, deck.md, analysis.ipynb, etc.)
```

Write each intermediate artifact to disk. The analysis should be reproducible and auditable.

### Step 3 — Run the phases

Work through the six phases in order. At each phase:

1. Read the corresponding reference file (`references/phase-N-*.md`)
2. Produce the phase's deliverable
3. Explicitly note what you're carrying forward to the next phase
4. Do not proceed if the phase's gate (explicit in each reference) hasn't been cleared

### Step 4 — Report briefly between phases

Give the user a one-sentence update when entering each phase, plus the key finding or decision from the previous phase. This keeps them oriented without flooding them with output. Example: *"Phase 2 → Explore. Top signal from Phase 1: the revenue dip is likely segmented (hypothesis H2), not seasonal. Starting with segmentation analysis."*

Don't dump raw tool output on the user. They care about interpretation and decisions, not every `df.describe()` you ran.

## Non-negotiable rules

These rules exist because skipping them is the most common way analysis goes wrong. They are drawn from the analytical traps surfaced in the source methodology — each has a reason, not just a mandate.

1. **No recommendation without validation.** Every quantitative claim presented in the final deliverable must have been independently re-derived in Phase 3. If a number can't survive a second derivation by a different approach, it doesn't ship.

2. **Check Simpson's Paradox when aggregating.** Whenever you compute an aggregate across segments (averages across groups, totals across time periods, etc.), confirm the direction holds within each segment. A flat aggregate often hides opposite trends in subgroups — this is the single most common way analysts mislead executives.

3. **Root-cause before recommending.** Don't recommend actions based on surface patterns. Drill down until you've isolated the specific segment, time window, or mechanism driving the pattern. The source methodology recommends iterating up to seven layers deep — stop when the explanation is specific enough to act on.

4. **Narrative before charts.** Design the story arc (Phase 4) before choosing visualizations (Phase 5). Charts serve the story; building charts first tends to produce decks where each slide is a chart, not an argument.

5. **Action titles, not descriptive titles.** Chart titles state what the data means for the business, not what the data is. "Maui tourism up 7% while other islands declined" beats "Monthly tourism by island". This is so important it warrants a rule — executive audiences skim titles.

6. **Confidence grades on every recommendation.** Tag each recommendation as High / Medium / Low confidence based on how much the data supports it. If everything is "High", you're not being honest with yourself.

## Output format selection

The user picks one (or more) of four formats. Each has its own reference section in `references/phase-6-deliver.md`:

- **Markdown report** — single `.md` with embedded PNG charts. Best default; easy to share, version-control, and iterate on.
- **Marp slide deck** — `.md` with Marp directives that renders to slides. Best for live executive presentations.
- **Jupyter notebook** — `.ipynb` with code + commentary + inline charts. Best when stakeholders want to re-run or modify.
- **Raw JSON + charts** — structured findings for downstream consumption. Best when feeding another system.

If the user asks for multiple formats, build the markdown report first as the source of truth, then derive the others from it.

## Quality bar

Before handing off the final deliverable, self-check against this list:

- [ ] Business question clearly stated upfront
- [ ] Key findings each have a supporting chart and a validated number
- [ ] Simpson's Paradox check explicitly performed and documented
- [ ] Root cause drilled at least 3 layers (segment → sub-segment → mechanism)
- [ ] Narrative flows as Context → Tension → Resolution
- [ ] Chart titles are action-oriented, not descriptive
- [ ] Recommendations have owners, success metrics, and confidence grades
- [ ] Deliverable is reproducible from the files in the workspace

If any box is unchecked, say so and propose how to close the gap.

# Phase 5: Charts

## Purpose

Design visualizations that serve the narrative beats from Phase 4. Every chart should earn its place: if removing it doesn't break the story, it's not pulling its weight. This phase uses the "Storytelling with Data" discipline (Cole Nussbaumer Knaflic) — the underlying idea is that charts communicate arguments, not data.

## Input

- `storyboard.md` from Phase 4
- Validated findings and their source data/scripts

## Output (deliverable for this phase)

- One PNG per beat (or small-multiple group) saved to `charts/`
- A naming convention like `01_aggregate_tourism.png`, `02_island_divergence.png`, tied to the beat number
- A `chart_scripts/` directory with the Python script that generates each chart (reproducibility)

## Design checklist (apply to every chart)

Before a chart is "done", it must pass this checklist. These aren't style preferences — each item directly affects whether the audience gets the point.

### Action titles, not descriptive titles

The title of every chart states **what the data means**, not **what the data is**.

- Descriptive (weak): "Monthly Revenue by Region"
- Action (strong): "West region revenue stalled while East grew 15%"

The title is often the only part of a chart an executive reads. Make it carry the argument. If you can't write an action title for a chart, the chart probably doesn't have a point.

### Direct labeling over legends

When there are 5 or fewer series, label them directly on the chart rather than with a legend. The eye shouldn't have to jump between legend and data.

### Color hierarchy: gray first, emphasis color for the story

- Default everything to gray
- Use one bold color (or one per key series) to call out what the story is about
- If you use a rainbow of colors, you've told the audience "everything matters equally" — which is almost never true

The emphasis color should match the point of the chart. If the story is about Maui, Maui is colored; all other islands are gray.

### Declutter

Remove everything that doesn't carry the argument:
- Drop gridlines unless reading exact values is essential
- Drop the chart border
- Drop axis titles if the data labels make them redundant
- Drop decimal places beyond what's meaningful
- Drop legend entries that aren't referenced

### Annotations to guide the eye

For any non-trivial chart, add:
- A callout arrow or text annotation on the key data point
- Labels on the first/last points of lines
- A horizontal line or shaded region for thresholds/targets when relevant

### Scale honestly

- Bar charts start at zero. No exceptions. A bar chart starting at 50 makes a 5% change look like a 50% change.
- Line charts can start above zero if the variation matters and zero-start would obscure it, but annotate the y-axis clearly.
- Avoid dual y-axes. They almost always mislead. Use small multiples or indexed values instead.

### Size and layout

- Chart aspect ratio: trend lines wider than tall; bar charts can be taller than wide if many categories
- Font sizes readable at final rendering size (don't make a chart legible in Jupyter but illegible in a deck)
- White space around the chart — don't pack right up to the edges

### Small multiples over overcomplicated single charts

When comparing the same metric across many entities, use small multiples (grid of small charts with shared axes) rather than overlaying many series. The source methodology's key example — Maui vs. other islands — is clearer as small multiples than as a six-series line chart.

## Collision detection

When you have multiple data labels on a chart (e.g., first and last point labels for 8 lines), check for visual collisions:

- Do any labels overlap?
- Are any labels cut off at the edge?
- If labels would collide, shift them or use a callout line

This is one of the most common sources of low-quality charts. Generate the PNG, then visually check.

## Chart types by purpose

Pick based on what the beat argues, not by default habit:

| Argument | Chart type |
|---|---|
| Level of a metric over time | Line chart |
| Composition of a whole, once | Stacked bar or waterfall |
| Composition over time | Stacked area (sparingly) or small-multiples bar |
| Comparison across categories | Horizontal bar (ordered) |
| Distribution of a population | Histogram or box plot |
| Correlation between two variables | Scatter (add trend line if relevant) |
| Divergence between groups | Small multiples of line charts |
| Root-cause drill-down | Waterfall or decomposition tree |

Default to simpler chart types. If a standard chart is hard to make readable, the story is probably too complex for one chart — split it into beats.

## Process

### 5.1 — For each beat, design the chart

Write out the chart design before generating it:
- What data subset (dataframe + filters)
- What chart type
- What's the action title
- What's the emphasis color and on what series
- What annotations

### 5.2 — Generate and iterate

Use `matplotlib` (or `plotly` if interactive is needed for the Jupyter output). Save PNG to `charts/` with the beat-numbered filename.

After generating, open the PNG and visually inspect:
- Does the title carry the argument?
- Does the emphasis direct the eye to the right place?
- Are there collisions, clipped labels, or illegible text?
- Would someone skimming the deck get the point from this chart alone?

If no to any — iterate.

### 5.3 — Visual design critic pass

Once all charts are drafted, do a holistic review across the set:
- Consistent style? (fonts, colors, aspect ratios)
- Does the color emphasis strategy make sense across charts? (One chart says "Maui is highlighted blue"; if another chart uses blue to highlight something different, the audience gets confused.)
- Is there a chart that's redundant with another?

## Gate (must clear before Phase 6)

- [ ] Each beat in the storyboard has a chart (unless the beat is deliberately chart-less, like a recommendation table)
- [ ] Every chart has an action title
- [ ] Every chart uses the gray-plus-emphasis color strategy
- [ ] No visual collisions, clipped labels, or illegible text
- [ ] Chart style is consistent across the set
- [ ] Each chart has a reproducible script in `chart_scripts/`

## Common pitfalls

- **Descriptive titles.** The single most common issue. "Monthly Tourism" is not a title; it's a caption.
- **Too many colors.** If the chart has six distinct colors, the audience has no idea where to look.
- **Dual y-axes.** Misleading. Use small multiples or indexed values.
- **Bar chart y-axis not starting at zero.** This is not a style preference; it's a correctness issue.
- **Making the chart look nice before the argument is clear.** Form follows function. Design the message first, then the aesthetics.

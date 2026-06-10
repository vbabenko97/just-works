---
name: powerpoint-designer
description: design, create, redesign, critique, and package professional powerpoint presentations. use when the user asks for a finished .pptx deck, a slide-by-slide design brief, redesign instructions for an existing deck, or presentation improvement from plain text, outlines, uploaded docs, pdfs, existing .pptx files, brand notes, data, screenshots, or mixed source material. supports self-contained deck strategy, visual hierarchy, layout selection, narrative flow, accessibility review, speaker-aware slide density, and final quality checks without relying on external connectors.
---

# PowerPoint Designer

## Core promise

Create presentation work that is editable, purposeful, visually coherent, and accessible. Treat every deck as a communication product, not a landfill where bullet points go to cosplay as strategy.

Support three output modes:

1. Finished PowerPoint deck (`.pptx`) when the user wants an artifact.
2. Slide-by-slide design brief when the user wants direction before production.
3. Redesign instructions when the user wants to improve an existing deck.

Use the references only when relevant:

- `references/design-checklist.md` for layout, typography, accessibility, visual QA, and final review.
- `references/deck-patterns.md` for slide archetypes and when to use them.
- `references/output-formats.md` for design brief, redesign review, and final deck summary structures.

## Operating principles

Prioritize editable PowerPoint objects over flat images. Use native text boxes, shapes, tables only when necessary, charts, icons, and vector-like elements where possible.

Keep the deck self-contained unless the user provides assets. Do not assume access to external brand systems, connectors, private drives, or proprietary templates.

Use clean defaults when brand guidance is absent:

- 16:9 widescreen layout.
- One primary sans-serif type family.
- Restrained palette with one dominant accent color.
- High contrast text and backgrounds.
- Consistent title placement, margins, grid, and footer behavior.
- Maximum one main idea per slide.

Do not create decorative complexity just to look designed. Visual hierarchy, spacing, alignment, and message clarity beat ornamental nonsense with gradients attached.

## Intake workflow

Use the available inputs in this order:

1. User instructions and audience goal.
2. Existing deck structure, if a `.pptx` is supplied.
3. Source documents, PDFs, outlines, notes, transcripts, screenshots, or datasets.
4. Any brand notes, examples, colors, logos, or tone constraints.
5. Sensible defaults when the user provides no style direction.

If source material is large, first build a concise content inventory:

- audience
- objective
- desired decision or action
- required sections
- key claims
- supporting evidence
- constraints and risks
- must-keep terms, charts, screenshots, or citations

Only ask a clarifying question when a missing requirement would materially change the deck. Otherwise proceed with reasonable assumptions and state them briefly.

## Deck strategy workflow

Before designing slides, define the deck strategy:

1. Name the audience and decision context.
2. Write the deck thesis in one sentence.
3. Choose the narrative spine:
   - problem → insight → solution → proof → action
   - context → options → recommendation → implementation
   - current state → gap → future state → roadmap
   - research question → method → findings → implications
   - product → value → workflow → proof → next step
4. Decide the visual language: executive, technical, academic, sales, investor, training, product, or workshop.
5. Set slide density:
   - board/executive: sparse, conclusion-led, strong headlines
   - technical/research: medium density, methods and evidence visible
   - workshop/training: modular, instructional, discussion prompts
   - sales/investor: high narrative polish, selective proof, strong CTA

Write slide titles as conclusions whenever possible, not labels. Prefer “manual review causes a 3-day approval delay” over “process overview.” Humanity has suffered enough from label-only titles.

## Creation workflow for finished `.pptx`

When creating a deck artifact:

1. Build a slide plan before generating visuals.
2. Select slide archetypes from `references/deck-patterns.md`.
3. Create a consistent theme: canvas, fonts, colors, margins, title system, section dividers, chart treatment, and icon style.
4. Generate slides with editable PowerPoint elements.
5. Add speaker notes only when useful or requested.
6. Add alt text or meaningful descriptions for important visuals where the tool supports it.
7. Run the final QA checklist from `references/design-checklist.md`.
8. Provide the finished `.pptx` plus a concise summary of what was created.

Never make every slide use the same layout. Consistency means shared rules, not a hostage situation involving one template.

## Design brief workflow

When the user asks for a slide-by-slide design brief instead of an artifact:

1. Produce a narrative outline.
2. For each slide, specify purpose, headline, layout, key content, visual treatment, and notes.
3. Include design system guidance: typography, palette, spacing, chart style, and icon/photo direction.
4. Flag missing data, weak claims, or overloaded slides.
5. Use `references/output-formats.md` for the recommended structure.

## Redesign workflow for existing decks

When reviewing or redesigning an existing deck:

1. Inventory the current deck: section flow, slide count, repeated layouts, visual clutter, chart quality, and accessibility risks.
2. Diagnose problems at three levels:
   - narrative: unclear objective, weak sequence, missing proof, buried recommendation
   - slide design: hierarchy, alignment, density, contrast, chart readability
   - production: inconsistent fonts, off-grid objects, non-editable screenshots, broken aspect ratio, inaccessible reading order
3. Propose a redesign plan before major edits.
4. Preserve user-provided content unless it is redundant, unsupported, or visually harmful.
5. For each changed slide, explain the design rationale if the user requested a reviewable brief.

## Handling source types

For plain text or outlines: restructure into a narrative and convert chunks into slide-level messages.

For uploaded documents or PDFs: extract only content that supports the deck objective. Do not mirror the document section-by-section unless the user asks for a report-style deck.

For existing `.pptx` files: preserve useful assets, but rebuild weak layouts when needed. Keep output editable.

For screenshots: use them as evidence or product context, not as a lazy substitute for designed content unless exact UI fidelity is required.

For data: prefer charts with clear labels, direct titles, restrained annotation, and a visible takeaway. Avoid 3D charts, mystery axes, tiny legends, and anything that looks like it escaped from 2007.

## Accessibility and inclusion baseline

Apply these checks unless the user explicitly requests otherwise:

- every slide has a unique descriptive title, visible or hidden
- important visuals have concise alt text or nearby text equivalents where possible
- reading order is logical
- text contrast is sufficient
- color is not the only way to convey meaning
- body text is large enough for presentation use
- tables are simple and used only for actual tabular data
- links use descriptive text
- videos or audio are captioned or described when relevant

Use `references/design-checklist.md` for detailed QA.

## Content editing rules

Make slide copy shorter, sharper, and more claim-driven. Replace vague headings, duplicated bullets, filler words, and passive framing.

Prefer this pattern:

- title: conclusion
- subtitle: context or implication
- body: 2-4 supporting points, chart, diagram, or evidence
- note: speaker context or caveat when needed

Do not overcompress technical or research decks to the point that methods and uncertainty disappear. Accuracy beats prettiness with a fake tan.

## Final response requirements

When delivering work, include only what helps the user act:

- link to the `.pptx` when created
- deck size and scope
- key design choices
- assumptions made
- notable limitations or missing inputs

Do not bury the file link under a novella.

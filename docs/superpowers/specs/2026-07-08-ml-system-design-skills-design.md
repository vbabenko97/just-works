# ML System Design Skills — Design Spec

**Date:** 2026-07-08
**Status:** Approved
**Source material:** [ML-SystemDesign/MLSystemDesign](https://github.com/ML-SystemDesign/MLSystemDesign) (MIT) — companion repo to Manning's *Machine Learning System Design* (Babushkin/Kravchenko)

## Goal

Turn the ML System Design methodology (12-section design-doc template + 14-group review checklist + worked examples) into two paired Claude Code / Codex skills in this repo:

1. `ml-system-design` — author an ML system design document
2. `ml-system-design-review` — critique a design document against the checklist

## Non-goals

- No implementation of any actual ML system
- No reviewer subagent (skills only)
- No verbatim copying of source content — all reference material is distilled/rewritten with attribution
- No runtime fetching from GitHub — skills are self-contained

## Deliverables

Four skill directories (two skills × two providers):

```
.claude/skills/ml-system-design/
  SKILL.md                          # triage → draft → gap-interview workflow
  references/
    template.md                     # distilled 12-section template with per-section guidance
    example-demand-forecasting.md   # condensed classic-ML worked example
    example-rag-system.md           # condensed LLM/RAG worked example
.claude/skills/ml-system-design-review/
  SKILL.md                          # doc in → checklist findings out
  references/
    checklist.md                    # distilled 14-group review checklist
.codex/skills/ml-system-design/          # mirror of the .claude skill
.codex/skills/ml-system-design-review/   # mirror of the .claude skill
```

Structure follows the existing `ai-analyst-pipeline` convention (SKILL.md + references/). Each reference file carries an attribution line: source repo, MIT license.

## Skill 1: ml-system-design (authoring)

**Trigger (description):** applies when the user wants to design an ML system, write an ML system design document, or plan an ML project before implementation. Must not trigger on generic ML coding tasks.

**Workflow:**

1. **Triage** — one batched question set (AskUserQuestion on Claude; plain questions on Codex):
   - Problem domain and business goal
   - Data situation (sources, labels, volume, freshness)
   - Scale/latency constraints
   - Deployment context
   - Project maturity: POC vs production — this decides section depth. A POC doc skips A/B testing and serving optimization sections rather than padding them; a production doc completes all 12 sections.
2. **Draft** — generate the full document from `references/template.md`. Every fact the model invents (not supplied by the user) is marked inline as `[ASSUMPTION: ...]`.
3. **Gap interview** — list only load-bearing assumptions (those affecting metrics, architecture, or cost) and ask the user to confirm or correct them in batches. Minor assumptions stay flagged in the doc.
4. **Finalize** — write the doc to the user's chosen path (ask; suggest `docs/ml-design/<name>.md` as default), then suggest running `ml-system-design-review`.

**Template sections (12, from source `basic_ml_design_doc.md`):** Problem Definition; Metrics and Losses; Dataset; Validation Schema; Baseline Solution; Error Analysis; Training Pipeline; Features; Measuring and Reporting; Integration; Monitoring; Serving and Inference. `references/template.md` distills each section into: what it must answer, common omissions, and depth guidance per maturity level.

**Worked examples:** two condensed references calibrate tone and depth — one classic tabular ML (retail demand forecasting), one LLM/RAG (chat with document versions). Condensed means: keep section structure and representative content, target roughly 150-250 lines each.

## Skill 2: ml-system-design-review (review)

**Trigger (description):** applies when the user wants to review, critique, score, or check an ML system design document. Non-overlapping with the authoring skill's trigger.

**Workflow:**

1. **Input** — accept a file path or pasted document text.
2. **Evaluate** — walk `references/checklist.md` group by group against the doc.
3. **Report** — findings formatted as: severity (blocker / major / minor) + doc section reference + what is missing or weak + concrete fix.
4. **Verdict** — one of: ready / needs work / incomplete (incomplete = whole required sections absent for the doc's maturity level).

Critique only — the skill does not rewrite the document unless the user asks. Cross-references `ml-system-design` for authoring (pairing pattern: `ticket-writing` ↔ `clickup-tickets`).

**Checklist groups (14, from source `design_doc_checklist.md`):** Problem Definition; Metrics and Losses; Data Considerations; Validation Schemas; Baseline Solutions; Error Analysis; Training Pipeline; Feature Engineering; System Architecture; Integration; Documentation; Evaluation Strategy; Implementation Plan; Maintenance and Operations.

## Provider mirroring

`.codex/skills/` copies match the `.claude/skills/` versions. Before writing the mirrors, diff an existing mirrored pair (e.g., `python-coding`) to confirm whether Codex SKILL.md format differs (frontmatter fields, tool references); adjust AskUserQuestion references to plain-question phrasing if the Codex versions do so.

## Verification criteria

- All 4 SKILL.md files have valid frontmatter (name + description)
- `plugin-dev:skill-reviewer` agent passes on both `.claude` skills
- Dry-run authoring: a toy prompt produces a doc containing `[ASSUMPTION:` markers and maturity-scaled sections
- Dry-run review: running the review skill on that doc (or a condensed example) produces severity-graded findings and a verdict
- README skills list updated to mention both skills
- Mirror parity: `.codex` copies match `.claude` copies modulo any provider-format differences found in the diff step

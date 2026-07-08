# ML System Design Skills — Design Spec

**Date:** 2026-07-08
**Status:** Approved (revised after agent review)
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
    checklist.md                    # distilled 14-group checklist + template mapping table
.codex/skills/ml-system-design/          # mirror of the .claude skill
.codex/skills/ml-system-design-review/   # mirror of the .claude skill
```

Structure follows the existing `ai-analyst-pipeline` convention (SKILL.md + references/).

**Attribution:** every reference file opens with this exact first line:
`> Source: [ML-SystemDesign/MLSystemDesign](https://github.com/ML-SystemDesign/MLSystemDesign), MIT License. Distilled and rewritten, not verbatim.`

## Skill 1: ml-system-design (authoring)

**Trigger (description):** applies when the user wants to design an ML system, write an ML system design document, or plan an ML project before implementation. The description must require explicit ML domain language ("ML system", "model", "training pipeline", "ML design doc") so it wins routing over the general `doc-coauthoring` skill. SKILL.md includes a "When NOT to use" clause: generic docs/specs → `doc-coauthoring`; generic ML coding → language skills.

**Workflow:**

1. **Triage** — one batched question set (AskUserQuestion on Claude; plain questions on Codex):
   - Problem domain and business goal
   - Data situation (sources, labels, volume, freshness)
   - Scale/latency constraints
   - Deployment context
   - Project maturity: POC vs production — this decides section depth. A POC doc skips A/B testing and serving optimization sections rather than padding them; a production doc completes all 12 sections. The chosen maturity level is stated in the doc header.
2. **Draft** — generate the full document from `references/template.md`. Every fact the model invents (not supplied by the user) is marked inline as `[ASSUMPTION: ...]`.
3. **Gap interview** — surface load-bearing assumptions (those affecting metrics, architecture, or cost) in a single batched message for confirm/correct. Iterate with another batch only if answers create new load-bearing gaps; typically one round.
4. **Finalize** — for each confirmed or corrected assumption, remove the `[ASSUMPTION: ...]` tag and update the text with the confirmed value; unresolved minor assumptions remain tagged. Write the doc to the user's chosen path (ask; suggest `docs/ml-design/<name>.md` as default), then suggest running `ml-system-design-review`.

**Template sections (12, names verbatim from source `basic_ml_design_doc.md`):** Problem Definition; Metrics and Losses; Dataset; Validation Schema; Baseline Solution; Error Analysis; Training Pipeline; Features; Measuring and Reporting; Integration; Monitoring; Serving and Inference. `references/template.md` distills each section into: what it must answer, common omissions, and depth guidance per maturity level.

**Worked examples:** two condensed references calibrate tone and depth — one classic tabular ML (retail demand forecasting), one LLM/RAG (chat with document versions). Condensed means: keep section structure and representative content, target roughly 150-250 lines of readable prose (wrap around 100 chars).

## Skill 2: ml-system-design-review (review)

**Trigger (description):** applies when the user wants to review, critique, score, or check an ML system design document. Non-overlapping with the authoring skill's trigger.

**Workflow:**

1. **Input** — accept a file path or pasted document text. If neither is provided, ask for one. Determine the doc's maturity level (POC vs production) from its header or content; if unstated, ask the user before evaluating — the incompleteness verdict depends on it.
2. **Evaluate** — walk `references/checklist.md` group by group against the doc, using its mapping table (below).
3. **Report** — findings formatted as: severity (blocker / major / minor) + doc section reference + what is missing or weak + concrete fix.
4. **Verdict** — one of: ready / needs work / incomplete (incomplete = whole required sections absent for the doc's maturity level).

Critique only — the skill does not rewrite the document unless the user asks. The two skills form a complementary author/reviewer pair; each SKILL.md mentions the other by name.

**Checklist groups (14, names verbatim from source `design_doc_checklist.md`):** Problem Definition; Metrics and Losses; Data Considerations; Validation Schemas; Baseline Solutions; Error Analysis; Training Pipeline; Feature Engineering; System Architecture; Integration; Documentation; Evaluation Strategy; Implementation Plan; Maintenance and Operations.

**Checklist ↔ template mapping:** group and section names intentionally differ (both kept verbatim from source); `references/checklist.md` includes an explicit mapping table so the review walks cleanly:

| Checklist group | Template section(s) |
|---|---|
| Problem Definition | Problem Definition |
| Metrics and Losses | Metrics and Losses |
| Data Considerations | Dataset |
| Validation Schemas | Validation Schema |
| Baseline Solutions | Baseline Solution |
| Error Analysis | Error Analysis |
| Training Pipeline | Training Pipeline |
| Feature Engineering | Features |
| System Architecture | Serving and Inference + Integration (cross-cutting) |
| Integration | Integration |
| Documentation | the doc itself (organization, diagrams, glossary) |
| Evaluation Strategy | Measuring and Reporting |
| Implementation Plan | cross-cutting (timeline/resources; flag as gap if absent in a production doc) |
| Maintenance and Operations | Monitoring |

## Provider mirroring

Existing mirrored pairs (e.g., `python-coding`) are byte-for-byte identical between `.claude/skills/` and `.codex/skills/` — write the Codex copies as direct copies of the Claude copies. Both skills are mirrored because methodology skills with no provider-specific tooling follow the same pattern as the mirrored coding/prompting skills. The AskUserQuestion mention in triage stays as-is ("AskUserQuestion on Claude; plain questions on Codex" is already provider-conditional).

## Verification criteria

- All 4 SKILL.md files have valid frontmatter (`name` + `description`); manual check that frontmatter parses as YAML
- `plugin-dev:skill-reviewer` (agent from the installed plugin-dev plugin, not a repo agent) passes on both `.claude` skills; if the plugin is unavailable, fall back to the manual frontmatter + description-trigger check
- Dry-run authoring: a toy prompt produces a doc containing `[ASSUMPTION:` markers and maturity-scaled sections
- Dry-run review: running the review skill on that doc (or a condensed example) produces severity-graded findings and a verdict
- README: add both skill names to the **Skills** paragraph in README.md (the sentence-style category list), as a new "ML system design" mention matching adjacent entry style
- Mirror parity: `.codex` copies are byte-identical to `.claude` copies

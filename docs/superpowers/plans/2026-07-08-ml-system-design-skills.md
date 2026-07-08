# ML System Design Skills Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add two paired skills — `ml-system-design` (author an ML design doc) and `ml-system-design-review` (critique one against a checklist) — to `.claude/skills/` and mirror them byte-identically to `.codex/skills/`.

**Architecture:** Pure-markdown skills following the `ai-analyst-pipeline` convention (SKILL.md + references/). Methodology distilled from the MIT-licensed ML-SystemDesign/MLSystemDesign repo: a 12-section template, a 14-group checklist with an explicit mapping table, and two condensed worked examples. No code, no runtime fetching.

**Tech Stack:** Markdown with YAML frontmatter. Validation via shell (grep/diff/wc). Spec: `docs/superpowers/specs/2026-07-08-ml-system-design-skills-design.md`.

## Global Constraints

- Frontmatter contains exactly `name` and `description` (convention: `.claude/skills/ticket-writing/SKILL.md`).
- Every `references/*.md` file opens with this exact first line:
  `> Source: [ML-SystemDesign/MLSystemDesign](https://github.com/ML-SystemDesign/MLSystemDesign), MIT License. Distilled and rewritten, not verbatim.`
- Template section names and checklist group names are kept verbatim from the source repo (they intentionally differ; the mapping table reconciles them).
- `.codex/skills/` copies must be byte-identical to `.claude/skills/` copies.
- No emojis anywhere. Repo root: `/Users/vitaliibabenko/babenko-dev/just-works`.
- Commit after each task with the message given in the task.

---

### Task 1: Authoring skill — SKILL.md + references/template.md

**Files:**
- Create: `.claude/skills/ml-system-design/SKILL.md`
- Create: `.claude/skills/ml-system-design/references/template.md`

**Interfaces:**
- Produces: skill name `ml-system-design`; reference path `references/template.md` (consumed by SKILL.md workflow text); the 12 verbatim section names listed below (consumed by Task 2 examples and Task 3 mapping table).

- [ ] **Step 1: Create SKILL.md with this exact content**

````markdown
---
name: ml-system-design
description: Apply when designing an ML system, writing an ML system design document, or planning an ML project before implementation — requests mentioning an ML system, model, training pipeline, or ML design doc. Guides triage, drafting with assumption markers, a gap interview, and a finalized 12-section design document. Not for generic docs or specs (use doc-coauthoring) and not for reviewing an existing design doc (use ml-system-design-review).
---

# ML System Design

Author an ML system design document from a 12-section template distilled from the companion repo of Manning's *Machine Learning System Design* (Babushkin/Kravchenko).

## When NOT to use

- Generic documentation, proposals, or specs with no ML component — use `doc-coauthoring`.
- Writing ML code without a design phase — use the language coding skills.
- Reviewing or scoring an existing design doc — use `ml-system-design-review` (this skill's reviewer pair).

## Workflow

### 1. Triage

Ask one batched question set (AskUserQuestion on Claude; plain numbered questions on Codex):

1. Problem domain and business goal — what decision or process does the model improve?
2. Data situation — sources, labels, volume, freshness.
3. Scale and latency constraints — requests/day, acceptable latency, budget limits.
4. Deployment context — batch / online / edge; cloud / on-prem.
5. Project maturity — POC or production.

Maturity decides depth. State the chosen maturity in the doc header.

- **Production:** complete all 12 sections at full depth.
- **POC:** keep all 12 section headers; abbreviate throughout; replace the "A/B Testing" subsection (Measuring and Reporting) and the "Optimization" subsection (Serving and Inference) with the single line "Deferred until production."

### 2. Draft

Generate the full document from `references/template.md`. Mark every fact not supplied by the user inline as `[ASSUMPTION: what was assumed]`. Calibrate tone and depth against the closer worked example: `references/example-demand-forecasting.md` (classic tabular ML) or `references/example-rag-system.md` (LLM/RAG).

### 3. Gap interview

Collect load-bearing assumptions — those affecting metrics, architecture, or cost — into a single batched confirm/correct message. Iterate with another batch only if the answers create new load-bearing gaps; typically one round. Minor assumptions are not raised.

### 4. Finalize

- For each confirmed or corrected assumption: remove the `[ASSUMPTION: ...]` tag and update the text with the confirmed value.
- Unresolved minor assumptions stay tagged in the doc.
- Ask for the output path; suggest `docs/ml-design/<name>.md` as the default.
- Suggest running `ml-system-design-review` on the finished doc.

## References

- `references/template.md` — the 12 sections: what each must answer, common omissions, depth by maturity.
- `references/example-demand-forecasting.md` — condensed classic-ML worked example.
- `references/example-rag-system.md` — condensed LLM/RAG worked example.
````

- [ ] **Step 2: Create references/template.md with this exact content**

````markdown
> Source: [ML-SystemDesign/MLSystemDesign](https://github.com/ML-SystemDesign/MLSystemDesign), MIT License. Distilled and rewritten, not verbatim.

# ML Design Doc Template — 12 Sections

Section names are verbatim from the source template. For each section: what it must answer, what authors commonly omit, and how deep to go per maturity level (POC vs production).

## I. Problem Definition

Must answer: what problem, for whom, why now. Origin of the problem, stakeholders and their current workflow, why existing (non-ML or legacy) solutions fall short, business impact and cost of the status quo, prior attempts and their lessons, known risks, cost of a wrong prediction, and required safeguards.
Commonly omitted: cost of mistakes; what happens when the model is wrong and who absorbs the damage.
POC: origin, stakeholders, expected benefit, mistake cost. Production: add prior work, infrastructure needs, failure modes, safeguards.

## II. Metrics and Losses

Must answer: how success is measured and what the model optimizes. Business KPIs, model metrics (offline), the loss function, and the explicit link between loss → model metric → business KPI. Name the trade-offs (precision vs recall, latency vs accuracy).
Commonly omitted: the loss-to-business-metric link; a metric the business actually tracks.
POC: one business KPI, one model metric, chosen loss. Production: full metric hierarchy with trade-off rationale and measurement framework.

## III. Dataset

Must answer: what data exists and how it becomes training data. Sources (internal/external), labeling methodology and its QA and cost, available metadata, historical depth (seasonality coverage, retention, schema drift), known quality issues and mitigations, and the ETL pipeline with refresh cadence.
Commonly omitted: labeling cost; schema consistency over history; data freshness at inference time.
POC: sources, labels, volume, known issues. Production: add metadata usage, retention policy, full ETL design, cleaning process.

## IV. Validation Schema

Must answer: how offline evaluation mirrors reality. Validation requirements, leakage prevention, temporal constraints, inference horizon, inner/outer loop design (cross-validation strategy, time-series handling), and re-validation frequency.
Commonly omitted: temporal leakage (future information in features); mismatch between validation split and inference-time conditions.
POC: split strategy and leakage statement. Production: add inner/outer loops, update triggers, drift-driven re-validation.

## V. Baseline Solution

Must answer: what the model must beat. A constant/heuristic baseline with its measured performance, candidate model baselines with trade-offs, and an initial feature baseline.
Commonly omitted: the constant baseline — teams jump to models without a floor number.
POC: constant baseline plus one simple model. Production: add model comparison table and feature-importance-based baseline.

## VI. Error Analysis

Must answer: how errors will be found and understood. Learning-curve analysis (over/underfitting), residual analysis (error distribution, outliers), and best/worst/corner-case analysis with identified failure modes.
Commonly omitted: corner cases; a defined process for turning error findings into improvements.
POC: residual overview and top failure modes. Production: full learning-curve, residual, and case analysis with an improvement loop.

## VII. Training Pipeline

Must answer: how a model gets trained reproducibly. Architecture and tools, preprocessing and feature engineering steps, hyperparameter handling, hardware needs, and experiment tracking (logging, metrics, model versioning).
Commonly omitted: reproducibility measures (seeds, data snapshots, environment pinning).
POC: tools and a minimal tracking setup. Production: add versioning, resource plan, full reproducibility guarantees.

## VIII. Features

Must answer: which features, and how they stay healthy. Selection criteria and importance measurement, the feature list with transformations and dependencies, computational constraints, and feature tests (quality checks, drift detection).
Commonly omitted: feature tests; dependencies that break when an upstream table changes.
POC: initial feature list with sources. Production: add selection methodology, tests, drift monitoring, update plan.

## IX. Measuring and Reporting

Must answer: how results are proven and communicated. Success metrics and tracking, A/B testing strategy (traffic allocation, success criteria), and reporting to stakeholders.
Commonly omitted: pre-registered A/B success criteria; who receives reports and how often.
POC: offline results reporting only; A/B Testing subsection = "Deferred until production." Production: full A/B design and reporting plan.

## X. Integration

Must answer: how the model enters the product safely. Fallback strategies and recovery, API design with SLAs, release cycle with rollback, and operational concerns (monitoring hooks, alerting, incident response).
Commonly omitted: fallback behavior when the model is unavailable or degraded.
POC: API sketch and a fallback statement. Production: full SLA, release/rollback procedure, incident response.

## XI. Monitoring

Must answer: how you know it still works next month. System health metrics and alert thresholds, data quality and schema validation, model quality (data/concept drift, retraining triggers), and business-metric correlation post-deployment.
Commonly omitted: retraining triggers; linking model drift to business KPI movement.
POC: basic health and quality checks. Production: all four monitoring layers with thresholds and triggers.

## XII. Serving and Inference

Must answer: how predictions reach consumers within constraints. Latency/throughput/scalability/cost requirements, serving architecture (deployment mode, scaling, security), optimization trade-offs, and serving-level monitoring.
Commonly omitted: cost per prediction; degradation response when load exceeds capacity.
POC: requirements and a minimal architecture; Optimization subsection = "Deferred until production." Production: full architecture, optimization analysis, degradation playbook.
````

- [ ] **Step 3: Validate both files**

Run:
```bash
cd /Users/vitaliibabenko/babenko-dev/just-works
head -1 .claude/skills/ml-system-design/SKILL.md | grep -qx -- '---' && \
grep -q '^name: ml-system-design$' .claude/skills/ml-system-design/SKILL.md && \
grep -q '^description: Apply when designing an ML system' .claude/skills/ml-system-design/SKILL.md && \
head -1 .claude/skills/ml-system-design/references/template.md | grep -q '^> Source: \[ML-SystemDesign/MLSystemDesign\]' && \
[ "$(grep -c '^## ' .claude/skills/ml-system-design/references/template.md)" -eq 12 ] && echo PASS
```
Expected: `PASS`

- [ ] **Step 4: Commit**

```bash
git add .claude/skills/ml-system-design/SKILL.md .claude/skills/ml-system-design/references/template.md
git commit -m "feat(skills): add ml-system-design authoring skill with 12-section template"
```

---

### Task 2: Condensed worked examples (2 reference files)

**Files:**
- Create: `.claude/skills/ml-system-design/references/example-demand-forecasting.md`
- Create: `.claude/skills/ml-system-design/references/example-rag-system.md`

**Interfaces:**
- Consumes: the 12 verbatim section names from Task 1's template.md.
- Produces: the two reference paths named in Task 1's SKILL.md References list.

This task condenses two pinned source documents. It is content generation with fixed inputs and mechanical acceptance checks — not free composition.

- [ ] **Step 1: Fetch the two source documents**

Run:
```bash
cd /Users/vitaliibabenko/babenko-dev/just-works
curl -sf https://raw.githubusercontent.com/ML-SystemDesign/MLSystemDesign/main/Design_Doc_Examples/Examples/EN/Retail_Demand_Forecasting_Design.md -o /tmp/src_forecast.md
curl -sf "https://raw.githubusercontent.com/ML-SystemDesign/MLSystemDesign/main/Design_Doc_Examples/Mock/EN/RAG_Chat_With_Doc_Versions/RAG_Chat_With_Doc_Versions_Design.md" -o /tmp/src_rag.md
wc -l /tmp/src_forecast.md /tmp/src_rag.md
```
Expected: both files download; nonzero line counts printed. If curl fails, retry once; if it still fails, stop and report — do not invent example content.

- [ ] **Step 2: Write example-demand-forecasting.md**

Read `/tmp/src_forecast.md` and produce `.claude/skills/ml-system-design/references/example-demand-forecasting.md` under these rules:

- First line: the exact attribution line from Global Constraints.
- Second block: a 3-line header — title (`# Worked Example: Retail Demand Forecasting`), one-line problem summary, `Maturity: production`.
- Then all 12 template section headers from Task 1 (`## I. Problem Definition` … `## XII. Serving and Inference`), in order.
- Under each header: condense the source's corresponding content to 8-20 lines of readable prose (wrap around 100 chars). Preserve concrete decisions verbatim in spirit: chosen metrics and losses, validation scheme, baseline choices, named model types, monitoring signals. Drop long narrative, repeated justifications, and tables longer than 5 rows (summarize them in a sentence).
- Where the source has no matching content for a section, write one line: `Source doc does not cover this section; a complete doc would.` — do not invent content.
- Total length 150-250 lines.

- [ ] **Step 3: Write example-rag-system.md**

Same rules as Step 2 applied to `/tmp/src_rag.md`, title `# Worked Example: RAG Chat With Document Versions`, one-line problem summary, `Maturity: POC`. Where the source references its PNG diagrams, replace with one sentence describing what the diagram shows.

- [ ] **Step 4: Validate both files**

Run:
```bash
cd /Users/vitaliibabenko/babenko-dev/just-works
for f in .claude/skills/ml-system-design/references/example-demand-forecasting.md .claude/skills/ml-system-design/references/example-rag-system.md; do
  head -1 "$f" | grep -q '^> Source: \[ML-SystemDesign/MLSystemDesign\]' || { echo "FAIL attribution $f"; exit 1; }
  [ "$(grep -c '^## ' "$f")" -eq 12 ] || { echo "FAIL sections $f"; exit 1; }
  n=$(wc -l < "$f"); [ "$n" -ge 150 ] && [ "$n" -le 250 ] || { echo "FAIL length $f ($n)"; exit 1; }
done; echo PASS
```
Expected: `PASS`

- [ ] **Step 5: Commit**

```bash
git add .claude/skills/ml-system-design/references/example-demand-forecasting.md .claude/skills/ml-system-design/references/example-rag-system.md
git commit -m "feat(skills): add condensed worked examples to ml-system-design"
```

---

### Task 3: Review skill — SKILL.md + references/checklist.md

**Files:**
- Create: `.claude/skills/ml-system-design-review/SKILL.md`
- Create: `.claude/skills/ml-system-design-review/references/checklist.md`

**Interfaces:**
- Consumes: skill name `ml-system-design` (cross-reference); the 12 template section names (mapping table).
- Produces: skill name `ml-system-design-review` (cross-referenced by Task 1's SKILL.md, already written there).

- [ ] **Step 1: Create SKILL.md with this exact content**

````markdown
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
````

- [ ] **Step 2: Create references/checklist.md with this exact content**

````markdown
> Source: [ML-SystemDesign/MLSystemDesign](https://github.com/ML-SystemDesign/MLSystemDesign), MIT License. Distilled and rewritten, not verbatim.

# ML Design Doc Review Checklist — 14 Groups

Group names are verbatim from the source checklist; template section names are verbatim from the source template. They intentionally differ — use this mapping table to locate what each group evaluates.

| Checklist group | Template section(s) evaluated |
|---|---|
| Problem Definition | I. Problem Definition |
| Metrics and Losses | II. Metrics and Losses |
| Data Considerations | III. Dataset |
| Validation Schemas | IV. Validation Schema |
| Baseline Solutions | V. Baseline Solution |
| Error Analysis | VI. Error Analysis |
| Training Pipeline | VII. Training Pipeline |
| Feature Engineering | VIII. Features |
| System Architecture | XII. Serving and Inference + X. Integration (cross-cutting) |
| Integration | X. Integration |
| Documentation | the doc itself: organization, diagrams, glossary, version history |
| Evaluation Strategy | IX. Measuring and Reporting |
| Implementation Plan | cross-cutting: timeline and resources anywhere in the doc; blocker-level gap if absent in a production doc |
| Maintenance and Operations | XI. Monitoring |

## 1. Problem Definition

- Clear problem statement with measurable objectives
- Scope, constraints, and stakeholders identified
- Business justification and cost of the status quo
- Existing solutions analyzed; risks assessed; success criteria defined

## 2. Metrics and Losses

- Business metrics and model metrics defined
- Loss function justified and linked to business goals
- Trade-offs named; measurement framework in place

## 3. Data Considerations

- Sources identified; quality and freshness assessed
- Labeling process planned with QA and cost
- ETL pipeline designed; data quality checks defined
- Privacy/security measures; versioning; storage requirements; metadata usage

## 4. Validation Schemas

- Requirements defined; schema designed
- Data leakage prevented; temporal aspects handled
- Cross-validation strategy set; update frequency planned

## 5. Baseline Solutions

- Constant baseline defined with a measured floor
- Model and feature baselines selected; comparison methodology planned
- Minimum acceptable performance stated; improvement metrics defined

## 6. Error Analysis

- Learning-curve and residual analysis planned
- Edge cases identified; failure modes monitored
- Error tracking designed; improvement process defined

## 7. Training Pipeline

- Architecture designed; tools selected
- Preprocessing planned; experiment tracking and model versioning set up
- Resources allocated; process documented; monitoring configured

## 8. Feature Engineering

- Selection criteria defined; initial features listed
- Feature tests and monitoring planned
- Dependencies documented; computational constraints considered; update plan exists

## 9. System Architecture

- Infrastructure requirements and scalability considered
- Latency defined; security measures specified
- Integration points and deployment strategy documented

## 10. Integration

- API interfaces designed; SLAs defined
- Release cycle and fallback strategies planned
- Operational procedures, monitoring/alerts, incident response, deployment docs in place

## 11. Documentation

- Clear organization and technical detail
- Diagrams present and labeled; references included
- Terminology glossary; version history; maintenance and update guidelines

## 12. Evaluation Strategy

- Success metrics defined; A/B testing methodology specified
- Performance benchmarks set; monitoring approach and alert thresholds defined

## 13. Implementation Plan

- Realistic timeline; resources specified
- Dependencies identified; risks assessed with mitigations

## 14. Maintenance and Operations

- Monitoring configured; update procedures defined
- Backup strategies; incident response planned
- Data drift planning; resource scaling strategy
````

- [ ] **Step 3: Validate both files**

Run:
```bash
cd /Users/vitaliibabenko/babenko-dev/just-works
head -1 .claude/skills/ml-system-design-review/SKILL.md | grep -qx -- '---' && \
grep -q '^name: ml-system-design-review$' .claude/skills/ml-system-design-review/SKILL.md && \
head -1 .claude/skills/ml-system-design-review/references/checklist.md | grep -q '^> Source: \[ML-SystemDesign/MLSystemDesign\]' && \
[ "$(grep -c '^## ' .claude/skills/ml-system-design-review/references/checklist.md)" -eq 14 ] && \
grep -q '| Maintenance and Operations | XI. Monitoring |' .claude/skills/ml-system-design-review/references/checklist.md && echo PASS
```
Expected: `PASS`

- [ ] **Step 4: Commit**

```bash
git add .claude/skills/ml-system-design-review
git commit -m "feat(skills): add ml-system-design-review skill with 14-group checklist"
```

---

### Task 4: Codex mirrors

**Files:**
- Create: `.codex/skills/ml-system-design/` (copy of `.claude/skills/ml-system-design/`)
- Create: `.codex/skills/ml-system-design-review/` (copy of `.claude/skills/ml-system-design-review/`)

**Interfaces:**
- Consumes: the four Claude-side files from Tasks 1-3, finalized.

- [ ] **Step 1: Copy both skill directories**

```bash
cd /Users/vitaliibabenko/babenko-dev/just-works
cp -R .claude/skills/ml-system-design .codex/skills/ml-system-design
cp -R .claude/skills/ml-system-design-review .codex/skills/ml-system-design-review
```

- [ ] **Step 2: Verify byte-identical**

```bash
cd /Users/vitaliibabenko/babenko-dev/just-works
diff -r .claude/skills/ml-system-design .codex/skills/ml-system-design && \
diff -r .claude/skills/ml-system-design-review .codex/skills/ml-system-design-review && echo PASS
```
Expected: `PASS` (no diff output above it)

- [ ] **Step 3: Commit**

```bash
git add .codex/skills/ml-system-design .codex/skills/ml-system-design-review
git commit -m "feat(skills): mirror ml-system-design skills to codex"
```

---

### Task 5: README update

**Files:**
- Modify: `README.md:22` (the `**Skills**` paragraph)

**Interfaces:**
- Consumes: both skill names.

- [ ] **Step 1: Edit the Skills paragraph**

Current line 22 begins:
```
**Skills** — coding standards (Python, TypeScript, React, Tailwind, shadcn/ui, Swift, C#, Dart/Flutter), architecture patterns (DDD, feature-driven), model-specific prompt engineering (Claude Opus 4.8 & Fable 5, GPT-5.5, Gemini 3), and behavioral modes (`minimal-coding` for least-code solutions).
```

Insert a new category after "architecture patterns (DDD, feature-driven)," so the line reads:
```
**Skills** — coding standards (Python, TypeScript, React, Tailwind, shadcn/ui, Swift, C#, Dart/Flutter), architecture patterns (DDD, feature-driven), ML system design (`ml-system-design` authoring + `ml-system-design-review` checklist critique), model-specific prompt engineering (Claude Opus 4.8 & Fable 5, GPT-5.5, Gemini 3), and behavioral modes (`minimal-coding` for least-code solutions).
```
Keep the trailing sentence of the paragraph unchanged.

- [ ] **Step 2: Validate**

```bash
cd /Users/vitaliibabenko/babenko-dev/just-works
grep -q 'ML system design (`ml-system-design` authoring + `ml-system-design-review` checklist critique)' README.md && echo PASS
```
Expected: `PASS`

- [ ] **Step 3: Commit**

```bash
git add README.md
git commit -m "docs(readme): list ml-system-design skills"
```

---

### Task 6: Verification pass (skill review + dry-runs)

**Files:**
- Possibly modify: any of the eight skill files, if findings require fixes (then re-run Task 4 Step 1-2 to re-sync mirrors and amend).

**Interfaces:**
- Consumes: everything from Tasks 1-5.

This task is executed by the orchestrator session (not a fresh subagent) because it dispatches agents.

- [ ] **Step 1: Run plugin-dev:skill-reviewer on both skills**

Dispatch the `plugin-dev:skill-reviewer` agent (from the installed plugin-dev plugin) once per skill, pointing it at `.claude/skills/ml-system-design/` and `.claude/skills/ml-system-design-review/`. If the plugin is unavailable, fall back to the manual check: frontmatter has `name` + `description`; description states trigger conditions and non-triggers; body references only files that exist.

- [ ] **Step 2: Dry-run authoring (simulated)**

Dispatch a general-purpose subagent with: "Read /Users/vitaliibabenko/babenko-dev/just-works/.claude/skills/ml-system-design/SKILL.md and follow its workflow to draft a design doc. Toy triage answers: domain = churn prediction for a telecom, business goal = reduce voluntary churn; data = 24 months of CRM + billing, labels from cancellation records; scale = 2M customers scored weekly, batch; deployment = cloud batch job; maturity = POC. Skip the gap interview (no user available) — leave all assumption markers in. Output the doc as text."
Check the output: contains `[ASSUMPTION:` at least once; contains all 12 section headers; A/B Testing and Optimization subsections say "Deferred until production."

- [ ] **Step 3: Dry-run review (simulated)**

Dispatch a general-purpose subagent with: "Read /Users/vitaliibabenko/babenko-dev/just-works/.claude/skills/ml-system-design-review/SKILL.md and its references/checklist.md, then review the attached doc following the workflow. Maturity: POC." Attach the Step 2 output doc.
Check the output: findings use the `[blocker|major|minor]` format; a verdict line (ready / needs work / incomplete) is present.

- [ ] **Step 4: Fix findings, re-sync mirrors, commit**

If Steps 1-3 produced fixes: apply them to the `.claude` copies, re-run Task 4 Steps 1-2 (`cp -R` + `diff -r`), then:
```bash
git add .claude/skills/ml-system-design .claude/skills/ml-system-design-review .codex/skills/ml-system-design .codex/skills/ml-system-design-review
git commit -m "fix(skills): apply review findings to ml-system-design skills"
```
If no fixes: no commit; record "verification clean" in the task report.

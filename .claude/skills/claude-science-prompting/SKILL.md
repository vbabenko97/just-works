---
name: claude-science-prompting
description: Create, audit, migrate, and evaluate prompts for Claude Science and Claude-based scientific research workflows. Use when a user needs a ready-to-paste research prompt, scientific brief, system/user prompt split, source and tool plan, reproducibility and provenance requirements, reviewer-agent instructions, or evaluation cases for literature review, data analysis, computational pipelines, experimental design, figures, manuscripts, or multi-agent research across biology, biomedicine, genomics, proteomics, structural biology, chemistry, and other scientific domains.
---

# Claude Science Prompting

## Purpose

Turn a scientific goal into the smallest prompt that reliably produces an evidence-grounded, reproducible, reviewable result in Claude Science. Treat prompt design as research design: define the question, evidence standard, methods, tools, uncertainty, validation, and deliverable before polishing wording.

Do not duplicate capabilities Claude Science already provides. Direct its coordinating agent, specialist agents, connectors, compute, artifacts, and reviewer toward clear acceptance criteria instead of demanding that every capability be used on every task.

## Workflow

1. Classify the request:
   - **Create**: turn a research goal or rough notes into a ready-to-paste prompt.
   - **Audit**: identify scientific, evidentiary, tool-use, reproducibility, or prompt-design defects.
   - **Migrate**: adapt a generic Claude, legacy-model, or human SOP prompt for Claude Science.
   - **Evaluate**: build representative test cases and a grading rubric.
   - **Configure**: recommend app/API structure, model settings, tools, connectors, compute, or approval boundaries.

2. Extract the research contract:
   - Research question, decision, or hypothesis.
   - Population, system, intervention, comparator, endpoints, timeframe, and exclusions when relevant.
   - Available documents, datasets, code, prior results, and trusted internal methods.
   - Required evidence quality and acceptable source types.
   - Analysis methods, statistical expectations, and important assumptions.
   - Available connectors, scientific databases, skills, packages, local files, SSH/HPC, or on-demand compute.
   - Privacy, ethics, biosafety, clinical, licensing, cost, and approval boundaries.
   - Required artifacts, audience, format, and publication standard.
   - Measurable success criteria and stopping conditions.

3. Resolve missing details:
   - Ask only when a missing fact materially changes safety, data access, scientific validity, or the requested deliverable.
   - Otherwise use conservative defaults, state assumptions, and proceed.
   - Never invent unavailable measurements, sample characteristics, citations, identifiers, or tool access.

4. Select prompt depth:
   - **Compact**: a bounded factual or literature question with no substantial computation.
   - **Standard**: multi-source synthesis, moderate data analysis, or a defined scientific decision. Use this by default.
   - **Full workflow**: long-horizon research, large datasets, specialist agents, external compute, publication artifacts, or high-stakes evidence review.

5. Compose only the sections that affect behavior:
   - Objective and scope.
   - Materials and data.
   - Success criteria.
   - Research and analysis workflow.
   - Source and citation policy.
   - Tool, connector, subagent, and compute policy.
   - Reproducibility and provenance requirements.
   - Uncertainty, limitations, safety, and approval boundaries.
   - Reviewer checks.
   - Output contract and stopping rules.

6. Validate the prompt against the checklist below, then return the requested artifact.

## Claude Science Optimization

Use Claude Science's capabilities deliberately:

- Let the generalist agent coordinate the workflow and use specialist agents when tasks can run in parallel, need isolated context, or require distinct expertise.
- Keep simple, sequential, or tightly stateful work with the coordinating agent rather than spawning decorative committees of robots.
- Name relevant connectors, databases, packages, skills, or compute resources when known. Do not instruct Claude to use every available tool.
- For long research tasks, maintain an evidence ledger, hypothesis tracker, decision log, or analysis state so claims and choices remain inspectable.
- Ask Claude Science to preserve the exact code, environment, package versions, random seeds, input versions, and transformations behind numerical results and figures.
- Use the reviewer to check citation fidelity, calculations, units, statistical claims, data-to-code lineage, and figure-to-code consistency.
- Ask before accessing new paid or restricted resources, submitting costly jobs, writing to shared systems, exposing sensitive data, or taking hard-to-reverse actions.
- Use forks or parallel approaches only when comparing methods or hypotheses would materially improve the answer.
- For long-context prompts, place source material and metadata before the final task, use descriptive XML tags, and put the decisive query and output requirements near the end.

## Scientific Integrity Rules

Preserve or add these controls when relevant:

- Distinguish observations, reported findings, calculations, inferences, hypotheses, and recommendations.
- Prefer primary literature, original datasets, authoritative databases, and official methods. Use secondary sources for orientation, not as silent substitutes for primary evidence.
- Label preprints, retractions, corrections, non-peer-reviewed sources, model predictions, and conflicting evidence.
- Require citations for material factual claims and verify identifiers such as DOI, PMID, accession number, gene/protein identifier, trial identifier, or database record when available.
- Never fabricate a citation or silently replace missing data with synthetic values. If simulation or imputation is appropriate, label it and justify it.
- Require checks for units, denominators, multiple testing, data leakage, confounding, batch effects, sensitivity to assumptions, and other method-specific failure modes.
- Require independent validation or expert review before clinical, regulatory, safety-critical, or consequential experimental decisions.
- Respect consent, privacy, controlled-access data, IRB/IACUC requirements, biosafety rules, licensing, and lab authorization.
- State uncertainty and limitations in calibrated language. Do not manufacture precise confidence values without a defensible method.

Load [references/scientific-rigor.md](references/scientific-rigor.md) for detailed source routing, provenance, computation, statistics, figures, manuscripts, and domain-specific checks.

## Prompt Design Rules

- Be clear, direct, and specific about the desired result.
- Explain the purpose behind unusual constraints when that helps the model generalize.
- Use descriptive XML tags when instructions, materials, examples, and variable inputs are mixed.
- Use examples only to resolve a demonstrated ambiguity in format, classification, or judgment. Prefer three to five diverse examples for production tasks that genuinely need few-shot steering.
- Ask for concise rationale, evidence, and verification, not hidden chain-of-thought.
- Prefer positive instructions describing the desired behavior over sprawling prohibition lists.
- Avoid generic ceremony such as “be a world-class scientist,” “never hallucinate,” “think step by step,” “use every tool,” “double-check everything,” or “do not stop until perfect.” Replace it with testable requirements.
- Avoid prescribing an exhaustive sequence when Claude Science can plan effectively from outcome, constraints, and acceptance criteria.
- Do not hardcode a model name, tool version, database release, or API parameter unless compatibility requires it and the value has been verified.

## Review Checklist

Before returning a prompt, verify that it:

1. States a bounded scientific objective and the decision or artifact it must support.
2. Defines what evidence is acceptable and how claims must be cited or traced.
3. Specifies methods and assumptions enough to detect invalid analysis without micromanaging routine work.
4. Routes tools, connectors, subagents, and compute by need, with approval boundaries for costly, sensitive, external, or irreversible actions.
5. Requires reproducible code, environments, data lineage, and figure provenance when computation is involved.
6. Separates evidence from inference and requires uncertainty, conflicts, negative findings, and limitations.
7. Gives the reviewer concrete checks rather than a vague command to “review carefully.”
8. Defines output structure, required artifacts, acceptance criteria, and stop/report behavior for missing data or failed tools.
9. Contains no contradictory instructions, invented capabilities, or legacy prompt theater.
10. Is no longer than needed for the scientific risk and workflow complexity.

When a prompt is saved to a file and code execution is available, run:

```bash
python scripts/check_prompt.py path/to/prompt.txt --strict
```

Treat the script as a structural lint, not proof of scientific correctness.

## Output Patterns

### Create

Return:

1. **Recommended prompt**: ready to paste into Claude Science.
2. **Research contract**: objective, scope, evidence bar, deliverable, and success criteria in compact form.
3. **Source, tool, and compute map**: only resources relevant to the task, including approval boundaries.
4. **Reviewer and reproducibility plan**: concrete checks and provenance requirements.
5. **Evaluation cases**: three to seven representative cases covering the main failure modes.
6. **Assumptions**: only unresolved assumptions that materially affect behavior.
7. **API split**: system prompt, user prompt, tool guidance, and runtime suggestion only when requested or clearly useful.

For compact requests, combine items 2–6 into short implementation notes rather than repeating the prompt.

### Audit

Return findings in severity order. For each finding, quote or identify the exact instruction, explain the scientific or operational failure mode, and give the smallest correction. Provide a fully rewritten prompt when the user requests a usable replacement.

### Migrate

Return:

1. **Verdict**: the main mismatch with Claude Science.
2. **Migrated prompt**: ready to paste, preserving necessary variables and domain rules.
3. **Material changes**: only consequential removals, additions, or semantic changes.
4. **Evaluation plan**: representative cases and acceptance thresholds for production prompts.

### Evaluate

Compare prompt variants on representative scientific tasks. Measure objective fidelity, required-field completeness, evidence traceability, citation correctness, methodological validity, reproducibility, uncertainty calibration, reviewer defect detection, tool routing, approval compliance, latency, cost, and unnecessary calls.

Do not claim that a prompt is better merely because it is longer, shorter, more agentic, or more elaborate. Require non-inferior scientific quality on critical cases and a meaningful improvement in reliability or efficiency.

Load [references/audit-evaluation.md](references/audit-evaluation.md) for the full rubric, test-case patterns, and grader templates.

## Templates and Current Guidance

- Load [references/prompt-blueprints.md](references/prompt-blueprints.md) for compact, standard, full-workflow, API-split, and domain examples.
- Load [references/anthropic-guidance.md](references/anthropic-guidance.md) before making current claims about Claude Science, Claude models, thinking settings, tools, research mode, connectors, or skills.
- When web access is available and current product behavior or model configuration matters, verify live official Anthropic documentation. Claude Science is a beta product and the model roster, capabilities, and API parameters can change faster than researchers can agree on a normalization method.

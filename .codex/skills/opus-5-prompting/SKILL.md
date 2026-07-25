---
name: opus-5-prompting
description: Create, migrate, audit, debug, and evaluate prompts and agent instructions for Claude Opus 5. Use when a user needs an Opus 5 system prompt, tool-using agent prompt, coding or research prompt, migration from an earlier Claude model, API runtime guidance for effort or thinking, control of verbosity or progress narration, subagent delegation rules, or diagnosis of over-verification, scope expansion, tool misuse, excessive cost, or thinking-disabled output artifacts.
---

# Claude Opus 5 Prompting

## Purpose

Produce a prompt and runtime configuration that exploit Claude Opus 5's strengths without carrying forward scaffolding that now causes verbosity, unnecessary verification, scope expansion, excess delegation, or wasted reasoning tokens.

Treat migration as an evaluation-driven retuning pass, not a model-ID replacement.

## Workflow

1. Classify the request:
   - **Create**: turn a goal, specification, or rough prompt into an Opus 5 prompt.
   - **Migrate**: adapt a prompt or agent harness from another Claude model.
   - **Audit**: identify contradictions, legacy scaffolding, missing boundaries, or likely failure modes.
   - **Debug**: diagnose a concrete behavior such as excessive narration, overthinking, tool underuse, over-delegation, or incomplete output.
   - **Configure**: recommend model parameters, tool exposure, context strategy, and fallback handling.
   - **Evaluate**: define representative cases, metrics, and an effort sweep.

2. Extract the behavioral contract before rewriting:
   - Required user-visible outcome.
   - Context and source material the model actually needs.
   - Correctness, evidence, safety, and domain constraints.
   - Scope boundaries and authorization for reads, writes, destructive actions, or external effects.
   - Available tools and the conditions for using them.
   - Required output format, length, and downstream compatibility.
   - Success criteria and representative failure cases.

3. Resolve minor gaps with conservative assumptions or visible placeholders. Ask a question only when different answers would materially change the prompt or runtime design.

4. Remove legacy instructions that duplicate or fight Opus 5 behavior:
   - Generic commands to be brilliant, meticulous, extremely thorough, or to think step by step.
   - Repeated self-check, double-check, verifier, or final-validation instructions.
   - Mandatory verifier subagents for ordinary work.
   - Blanket instructions to use every tool or delegate whenever possible.
   - Contradictory demands such as "exhaustive" and "minimal output."
   - Long refusal-avoidance phrasing, fake certainty, or requests to expose hidden reasoning.
   - Prescriptive reasoning recipes when the required outcome and constraints are sufficient.
   - Old prompt-side workarounds for vision, coding, or tool use that have not been revalidated.

5. Add only controls that materially steer Opus 5:
   - Explicit response length or concision, because effort does not reliably control visible verbosity.
   - A progress-update cadence for agentic work.
   - A written-deliverable length rule when the model writes files or reports.
   - A narrow scope boundary when the task should not expand.
   - Explicit action language when implementation is intended rather than advice.
   - Delegation criteria and spawn caps when the harness supports subagents.
   - Permission and stopping boundaries for consequential actions.
   - Exact schemas, citations, evidence rules, or compatibility constraints.
   - A brief correction policy when user-facing correction narration is distracting.

6. Build the smallest prompt that expresses the contract. Use this order when useful:

```text
Role or objective
[One sentence only when it changes expertise, perspective, or tone.]

Task
[The concrete outcome to produce or action to complete.]

Context
[Only the facts, inputs, and environment needed for the task.]

Requirements
[Correctness, evidence, scope, permissions, and domain constraints.]

Tools and execution
[Relevant tools, when to use them, progress cadence, delegation limits, and stopping rules.]

Output
[Task-specific structure, length, schema, or artifact requirements.]
```

Do not force headings into simple prompts. Prefer direct prose when it is clearer.

7. Validate the candidate:
   - Every instruction must affect correctness, evidence, safety, authorization, scope, cost, or output compatibility.
   - Remove duplicate priorities and hidden contradictions.
   - Preserve complete deliverables; do not optimize tokens by omitting requested work.
   - Distinguish prompt changes from API or harness changes.
   - Do not claim the rewrite is better without an evaluation; label untested changes as recommendations.

## Opus 5 runtime defaults

Load [references/anthropic-opus-5-guidance.md](references/anthropic-opus-5-guidance.md) before making current API claims or migration recommendations. Verify live official Anthropic documentation when web access is available because model features, beta headers, pricing, and availability can change.

Apply these starting points unless the workload indicates otherwise:

- Use `claude-opus-5` as the Claude API model ID after verifying current availability.
- Keep adaptive thinking enabled. It is on by default.
- Start at `high` effort, then test `medium` and `low` for routine workloads.
- Use `xhigh` for demanding long-horizon coding or agentic work when evaluations justify the added cost.
- Reserve `max` for capability-critical tasks and compare it against `xhigh`; do not use it by reflex.
- At `xhigh` or `max`, start with `max_tokens` of at least 64k and tune against actual workloads.
- Prefer thinking enabled at lower effort over thinking disabled. If thinking must be disabled, keep effort at `high` or below and add the output-artifact mitigation from the reference.
- Omit non-default `temperature`, `top_p`, and `top_k`; supported Opus 5 requests reject them.
- Do not use assistant-message prefills. Use system instructions or structured output instead.
- Re-run token, latency, and cost measurements rather than inheriting settings from another Claude model.

## Opus 5-specific prompt controls

### Response length

Use a direct length rule rather than lowering effort:

```text
Keep the response focused and proportionate to the question. Lead with the result. Preserve required evidence, caveats, and next steps; remove filler, repeated summaries, and generic background.
```

For strict limits, specify an approximate word count, section count, or maximum number of findings.

### Agentic progress updates

State the desired cadence positively:

```text
Before the first tool call, give one sentence describing the approach. During execution, update the user only after a material finding, blocker, or change of direction. At completion, lead with the outcome and place supporting detail after it.
```

Remove this block for silent or machine-to-machine agents.

### Written artifacts

```text
Match document length to the task. Cover the substance without filler sections, repeated conclusions, or boilerplate.
```

Add concrete page, word, slide, or section limits when downstream review depends on them.

### Scope control

```text
Complete the requested task at the intended scope. Make routine judgment calls yourself. Ask only when materially different interpretations would produce different work. Mention a better approach briefly, but do not silently widen, narrow, or replace the requested task. Stop before actions clearly outside the request.
```

### Delegation control

```text
Delegate only genuinely independent, substantial tracks of work. Do not spawn subagents for tasks you can finish in a few tool calls, and do not use subagents merely to verify your own work. Prefer one capable subagent to several overlapping ones and keep the spawn count low.
```

Use deterministic spawn limits when the harness can enforce them.

### Corrections

```text
Call out a correction only when it changes the user's code, conclusion, or decision. State it briefly and continue. Fix inconsequential slips silently.
```

## Migration rules

When migrating from Claude Opus 4.8 or earlier:

1. Change the model ID only after inventorying prompt and request behavior.
2. Revisit `max_tokens` because thinking is on by default and shares the output limit with visible text.
3. Remove manual extended-thinking budgets and non-default sampling parameters where present.
4. Remove assistant prefills.
5. Audit requests that disable thinking; `xhigh` or `max` with thinking disabled is invalid.
6. Run a fresh effort sweep instead of preserving an inherited effort setting without evidence.
7. Retune response length, progress narration, and written-artifact length explicitly.
8. Remove redundant verification, self-correction, and verifier-subagent instructions.
9. Constrain scope and delegation where the old prompt relied on weaker model initiative.
10. Revalidate tool availability and harness features. Do not assume every tool supported by another Claude model is available on Opus 5.
11. Rebaseline token counts, cost, latency, refusal handling, and fallback behavior.

## Output patterns

### Create

Return:

1. **Recommended prompt**: ready to paste.
2. **Runtime settings**: only settings relevant to the task.
3. **Assumptions**: only unresolved assumptions that materially affect behavior.
4. **Evaluation cases**: include for production prompts.

### Migrate

Return:

1. **Verdict**: the main migration risks or prompt defects.
2. **Migrated prompt**: ready to paste with placeholders preserved.
3. **Runtime/config changes**: separate from prompt text.
4. **Removed legacy scaffolding**: only consequential deletions.
5. **Evaluation plan**: representative cases and acceptance thresholds.

### Audit or debug

Report findings in severity order. For each finding, identify the exact instruction or configuration, explain the Opus 5 failure mode, and give the smallest corrective change. Provide a complete replacement prompt when the user needs a usable artifact.

### Configure

Return the recommended model ID, effort, thinking setting, `max_tokens`, tool exposure, progress behavior, delegation cap, and any beta-dependent feature separately. Explain each non-default choice in one sentence.

### Evaluate

Compare the baseline and candidate on representative tasks. Measure task success, required-field completeness, factual or evidence correctness, tool-route correctness, scope compliance, unnecessary tool calls, subagent count, repeated verification, visible verbosity, input/output tokens, latency, and cost.

Adopt the candidate only when critical-case quality is non-inferior and any efficiency gain is meaningful. Do not average away failures in safety, permissions, evidence, or required output fields.

## Reference patterns

Load [references/prompt-patterns.md](references/prompt-patterns.md) when the user needs reusable templates, before/after migrations, a debugging matrix, or an evaluation checklist.

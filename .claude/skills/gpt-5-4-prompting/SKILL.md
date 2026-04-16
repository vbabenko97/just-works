---
name: gpt-5-4-prompting
description: Apply when creating or editing prompts targeting GPT-5.4. Covers output contracts, follow-through defaults, task-update steering, tool persistence, dependency-aware execution, verification loops, citation-grounded research, long-session compaction, coding-agent patterns, and migration from GPT-5.2, GPT-5.3-Codex, GPT-4.1, or GPT-4o.
---

# GPT-5.4 Prompt Writing Guidelines

## When to Use

- Creating or editing system prompts targeting GPT-5.4
- Writing prompts for long-running or tool-using assistants and agents
- Structuring prompts for large multi-document or long-session workflows
- Designing research, review, and synthesis prompts with citation requirements
- Writing prompts for coding agents, terminal agents, and frontend tasks
- Defining strict output contracts for JSON, SQL, XML, Markdown, or schema-bound extraction
- Migrating prompts from GPT-5.2, GPT-5.3-Codex, GPT-4.1, or GPT-4o

## Overview

GPT-5.4 works especially well for long-running tasks, tool use, evidence-rich synthesis, and reliable multi-step execution. It performs best when prompts define:

- the exact output contract,
- when to proceed vs ask permission,
- what tools are expected,
- how verification works,
- and what counts as "done".

Treat prompt blocks as targeted controls, not decoration. Start with the smallest prompt that passes evals, then add blocks only when they fix a measured failure mode.

<context>
Design prompts around these GPT-5.4 tendencies:

- Stronger long-horizon execution and follow-through
- Better tone and personality adherence over long answers
- Better long-context and multi-document synthesis
- Better batched / parallel tool use when dependencies are explicit
- Better results when completion criteria, citation rules, and verification are spelled out

Still prompt explicitly for:
- low-context tool routing,
- prerequisite / dependency handling,
- high-impact or irreversible actions,
- research workflows that need disciplined evidence collection,
- and exact output packaging.
</context>

## Core Output and Control Patterns

### Output contracts

Use an explicit output contract to control both structure and token efficiency.

```txt
<output_contract>
- Return only the requested sections, in the requested order.
- If the prompt defines working notes, analysis, or a preamble, do not treat them as extra deliverables.
- Apply length limits only to the section they belong to.
- If a specific format is required (JSON, Markdown, SQL, XML), output only that format.
</output_contract>
````

### Verbosity controls

GPT-5.4 responds well to hard output constraints. Use explicit ranges instead of vague instructions like "be concise".

```txt
<verbosity_controls>
- Prefer concise, information-dense writing.
- Do not repeat or paraphrase the user's request unless needed for correctness.
- Keep updates short.
- Do not over-compress the answer so much that evidence, reasoning, or completion checks are lost.
</verbosity_controls>
```

Example clamp:

```txt
<output_verbosity_spec>
- Default: 1 short overview paragraph, then up to 5 bullets.
- Simple factual questions: 1-3 sentences.
- Multi-step tasks: short overview, then sections for What changed, Where, Risks, and Next step.
- Avoid long narrative filler.
</output_verbosity_spec>
```

## Follow-Through and Mid-Conversation Steering

### Default follow-through policy

Define when the model should continue without asking and when it must pause.

```txt
<default_follow_through_policy>
- If user intent is clear and the next step is reversible and low-risk, continue without asking.
- Ask permission only when the next step is:
  - irreversible,
  - externally state-changing,
  - or blocked on sensitive / choice-dependent information that would materially change the result.
</default_follow_through_policy>
```

### Task updates

For mid-conversation changes, use narrow overrides with explicit scope.

```txt
<task_update>
For the next response only:
- Do not complete the task.
- Produce only a plan.
- Keep it to 5 bullets.

All previous instructions still apply unless this update conflicts with them.
</task_update>
```

If the task itself changes, say so directly and redefine what is allowed for that turn.

## Tool Use and Execution Discipline

### Tool persistence

GPT-5.4 does better when prompts make it clear that the task is not complete just because the first plausible answer appears.

```txt
<tool_persistence_rules>
- Use tools whenever they materially improve correctness, completeness, or grounding.
- Do not stop early if another tool call is likely to improve the answer.
- Continue until the task is complete and verification passes.
- If a tool result is empty or partial, retry with a different strategy before concluding failure.
</tool_persistence_rules>
```

### Dependency checks

```txt
<dependency_checks>
- Before taking an action, check whether lookup, retrieval, or prerequisite discovery is required.
- Do not skip prerequisite steps just because the intended final action seems obvious.
- If a later step depends on an earlier result, resolve that dependency first.
</dependency_checks>
```

### Parallel tool calling

Use selective parallelism only for truly independent work.

```txt
<parallel_tool_calling>
- Parallelize independent retrieval or lookup steps when it reduces latency.
- Do not parallelize steps that have prerequisites or where one result determines the next action.
- After parallel retrieval, pause to synthesize before making additional calls.
- Prefer parallel evidence gathering, not speculative or redundant tool use.
</parallel_tool_calling>
```

### Completeness and empty-result recovery

```txt
<completeness_contract>
- Treat the task as incomplete until every requested item is covered or explicitly marked [blocked].
- Maintain an internal checklist of required deliverables.
- For batches, lists, or paginated results, estimate expected scope when possible and confirm coverage before finalizing.
- If something is blocked, say exactly what is missing.
</completeness_contract>
```

```txt
<empty_result_recovery>
- If a search or lookup is empty, partial, or suspiciously narrow, do not conclude failure immediately.
- Retry with 1-2 fallback strategies such as broader terms, alternate wording, prerequisite lookup, or a different source/tool.
- Only then report that no results were found, and include what was tried.
</empty_result_recovery>
```

### Verification loop

```txt
<verification_loop>
Before finalizing:
- Check correctness against every stated requirement.
- Check grounding against provided context or tool outputs.
- Check formatting against the requested schema or style.
- Check safety and irreversibility before taking any external action.
</verification_loop>
```

### Missing-context gating

```txt
<missing_context_gating>
- If required context is missing, do not guess.
- Prefer retrieval or lookup tools when the missing context can be fetched.
- Ask a minimal clarifying question only when the missing detail cannot be retrieved.
- If you must proceed, label assumptions explicitly and choose a reversible action.
</missing_context_gating>
```

## Grounding, Citations, and Research

### Citation and grounding rules

Lock both the allowed evidence boundary and the citation format.

```txt
<citation_rules>
- Cite only sources retrieved in the current workflow.
- Never invent citations, URLs, IDs, page numbers, or quote spans.
- Use exactly the citation format required by the host environment.
- Attach citations to the claims they support, not only at the end.
</citation_rules>
```

```txt
<grounding_rules>
- Base claims only on provided context or tool outputs.
- If sources conflict, state the conflict explicitly and attribute each side.
- If the context is insufficient, narrow the answer or say the claim cannot be supported.
- If a statement is an inference, label it as an inference.
</grounding_rules>
```

### Research mode

For research, review, or synthesis tasks, explicitly force a multi-pass process.

```txt
<research_mode>
- Work in 3 passes:
  1. Plan: identify 3-6 sub-questions.
  2. Retrieve: search each sub-question and follow 1-2 second-order leads.
  3. Synthesize: resolve contradictions and produce the final answer with citations.
- Stop only when further searching is unlikely to change the conclusion.
</research_mode>
```

### Strict structured outputs

For parse-sensitive outputs, make the output boundary explicit.

```txt
<structured_output_contract>
- Output only the requested format.
- Do not add prose or markdown fences unless requested.
- Validate bracket and delimiter balance before finishing.
- Do not invent fields or tables.
- If required schema information is missing, ask for it or return an explicit error object.
</structured_output_contract>
```

## Long Context and Long Sessions

GPT-5.4 handles large context well, but prompt for grounding anyway when working over large codebases, long threads, or many documents.

```txt
<long_context_handling>
- For large multi-document inputs:
  - identify the relevant sections first,
  - restate the operative constraints before answering,
  - anchor claims to specific sections, documents, or retrieved evidence,
  - and quote or paraphrase exact details when the answer depends on dates, thresholds, clauses, or numbers.
- Prefer synthesis across sources over isolated per-document summaries.
</long_context_handling>
```

If you use compaction in long-running sessions:

```txt
<compaction_rules>
- Compact after major milestones, not every turn.
- Treat compacted items as opaque state.
- Keep prompts functionally identical after compaction.
- Do not change the system prompt between compacted sessions unless you are intentionally changing behavior.
</compaction_rules>
```

## Coding, UI, and Terminal Agents

### Coding persistence

```txt
<autonomy_and_persistence>
- Persist until the task is handled end-to-end within the current turn when feasible.
- Do not stop at analysis if implementation and lightweight verification are expected.
- Carry the work through implementation, verification, and concise outcome reporting unless the user explicitly redirects the task.
</autonomy_and_persistence>
```

### Frontend / design scope

GPT-5.4 can overbuild UI unless constrained. Preserve existing product and design-system patterns.

```txt
<design_and_scope_constraints>
- Implement exactly what was requested.
- Do not add features, pages, components, or styling flourishes that were not asked for.
- Preserve the established design system, structure, and visual language.
- Avoid generic, overbuilt layouts when a simpler composition satisfies the task.
- If ambiguous, choose the simplest valid interpretation.
</design_and_scope_constraints>
```

### Terminal hygiene

```txt
<terminal_tool_hygiene>
- Run shell commands only through the terminal tool.
- Do not pretend to execute tools inside bash.
- If an edit or patch tool exists, use it directly instead of simulating it in shell.
- After changes, run a lightweight verification step before declaring success.
</terminal_tool_hygiene>
```

## Agentic Steerability and User Updates

GPT-5.4 works well with sparse, outcome-based progress updates.

```txt
<user_updates_spec>
- Send short user-facing progress updates while working.
- Use 1-2 sentences per update.
- Put updates in the commentary channel, not the final answer channel.
- Give an initial update before substantial work begins.
- Keep updates outcome-focused, not tool-by-tool narration.
- Provide updates roughly every 30 seconds on long tasks.
</user_updates_spec>
```

For long-running or tool-heavy Responses API flows, preserve assistant `phase` metadata if your runtime uses it. Commentary / intermediate messages should remain distinguishable from the final answer.

## Reasoning Effort

Treat `reasoning_effort` as a last-mile tuning knob, not your first fix.

### Recommended defaults

* `none`: best for fast, cost-sensitive, execution-heavy tasks
* `low`: use when a little extra thinking helps with complex instructions
* `medium` or `high`: reserve for research-heavy or ambiguity-heavy tasks
* `xhigh`: use only when evals show clear benefit on long, reasoning-heavy work

In many cases, better prompts recover more quality than simply increasing reasoning effort. Before raising effort, first add:

* `<completeness_contract>`
* `<verification_loop>`
* `<tool_persistence_rules>`

If the model still stops at the first plausible answer, add:

```txt
<dig_deeper_nudge>
- Do not stop at the first plausible answer.
- Look for second-order issues, edge cases, and missing constraints.
- For accuracy-critical tasks, perform at least one verification step.
</dig_deeper_nudge>
```

## Migration Guide

Migrate one variable at a time:

1. Switch the model first.
2. Pin the starting `reasoning_effort`.
3. Run evals before prompt edits.
4. Add prompt blocks only where failures appear.
5. Re-run evals after each change.

### Suggested starting points

* From GPT-5.2: keep the same reasoning effort first, then tune
* From GPT-5.3-Codex: keep the same reasoning effort, especially for coding workflows
* From GPT-4.1 or GPT-4o: start with `none`
* For research-heavy assistants: start with `medium` or `high` and add explicit research + citation blocks
* For long-horizon agents: add tool persistence and completeness accounting before increasing effort

## Small-Model Guidance

### GPT-5.4-mini

`gpt-5.4-mini` is more literal and less likely to infer missing steps. For mini prompts:

* Put critical rules first
* Specify exact execution order
* Separate action instructions from reporting instructions
* Define ambiguity behavior explicitly
* Specify packaging directly: length, section order, citations, whether follow-up questions are allowed

### GPT-5.4-nano

Use `gpt-5.4-nano` only for narrow, tightly bounded tasks.

* Prefer closed outputs such as labels, enums, short JSON, or fixed templates
* Avoid multi-step orchestration unless the workflow is extremely constrained
* Route ambiguous or planning-heavy work to a stronger model instead of over-prompting nano

Good default structure for smaller models:

1. Task
2. Critical rule
3. Exact step order
4. Edge-case / clarification behavior
5. Output format
6. One correct example

## Web Research

For web-enabled research agents, start from the GPT-5.2 research block and tighten it with citation gating, empty-result recovery, and explicit finalization.

```txt
<web_search_rules>
- Prefer research over unsupported assumptions when facts may be uncertain.
- Cover the full query, including likely second-order implications.
- Use retrieved evidence only, with citations attached to supported claims.
- Resolve contradictions explicitly.
- Do not stop when additional searching is still likely to change the answer.
- Keep the final answer clear, direct, and well-structured.
</web_search_rules>
```

## Anti-Patterns

* Using vague output instructions instead of an explicit output contract
* Raising reasoning effort before fixing completion, grounding, or verification failures
* Stopping after the first plausible answer when more retrieval would materially improve the result
* Skipping prerequisite lookups because the end state seems obvious
* Inventing citations, URLs, IDs, or exact evidence details
* Treating empty search results as proof that nothing exists
* Allowing compacted sessions to resume under a changed system prompt
* Letting frontend tasks drift into generic or overbuilt UI
* Using small models for ambiguous orchestration-heavy tasks and then trying to rescue them with louder wording

## Quality Checklist

* [ ] Output contract is explicit
* [ ] Verbosity and section order are defined
* [ ] Follow-through policy is defined
* [ ] Tool persistence and dependency handling are specified
* [ ] Verification loop is present for important workflows
* [ ] Citation and grounding rules are explicit for research tasks
* [ ] Large-context grounding is specified for multi-document inputs
* [ ] Compaction rules are defined for long sessions
* [ ] Reasoning effort is chosen by task shape, not habit
* [ ] Migration was tested one change at a time with evals

## Reference

* Official GPT-5.4 Prompt Guidance: [https://developers.openai.com/api/docs/guides/prompt-guidance](https://developers.openai.com/api/docs/guides/prompt-guidance)
* Latest GPT-5.4 Model Guide: [https://developers.openai.com/api/docs/guides/latest-model](https://developers.openai.com/api/docs/guides/latest-model)
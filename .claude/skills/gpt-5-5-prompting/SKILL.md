---
name: gpt-5-5-prompting
description: use when creating, rewriting, auditing, or migrating prompts for openai gpt-5.5 models, especially api prompts, system/developer instructions, agent prompts, tool-heavy responses api workflows, customer-facing assistants, retrieval/citation workflows, coding or frontend agents, and migrations from gpt-5.4, gpt-5.3, gpt-5.2, gpt-5.1, gpt-5, gpt-4.1, gpt-4o, claude, gemini, or older prompt stacks. covers outcome-first prompting, reasoning_effort tuning, text.verbosity, personality and collaboration style, preambles, phase handling, assistant-item replay, retrieval budgets, grounding, validation rules, stopping conditions, and prompt review checklists.
---

# GPT-5.5 Prompting

## Core stance

Optimize GPT-5.5 prompts for outcomes, not choreography. Define the target result, success criteria, constraints, evidence rules, output shape, and stop conditions. Let the model choose an efficient path unless the process itself is a true requirement.

Use this skill to produce prompts that are shorter, sharper, and easier to evaluate than legacy prompt piles. Human civilization has apparently decided to solve ambiguity by adding twelve conflicting MUSTs. Do not help it continue.

## Default workflow

1. Identify the prompt type: assistant, agent, coding agent, research workflow, retrieval workflow, customer support, creative drafting, extraction, classification, or structured transform.
2. Extract the required outcome, user-visible success criteria, side effects, available tools, grounding sources, output contract, and stop rules.
3. Remove legacy process-heavy instructions unless they are true invariants.
4. Add decision rules for ambiguity, tool use, retrieval, validation, and when to ask the user.
5. Tune `reasoning_effort` and `text.verbosity` only after the prompt contract is clear.
6. Return either a complete rewritten prompt or a prompt review with prioritized fixes, depending on the user request.

## Prompt structure for complex GPT-5.5 prompts

Use this skeleton as the default. Keep each section short and add detail only when it changes behavior.

```text
Role: [1-2 sentences defining the assistant's function and operating context]

# Personality
[brief tone and collaboration style, if user-facing]

# Goal
[user-visible outcome]

# Success criteria
[what must be true before the final answer]

# Constraints
[safety, business, policy, source, tool, privacy, and side-effect limits]

# Tools and evidence
[which sources/tools to use, when to use them, and what evidence is enough]

# Output
[format, sections, length, citation style, and verbosity]

# Stop rules
[when to retry, fallback, abstain, ask, or stop]
```

For small prompts, collapse this into one concise paragraph plus an output contract.

## Outcome-first rewriting rules

Prefer instructions like:

```text
Resolve the user's request end to end.
Success means:
- the core decision is made from available evidence
- required side effects are completed before the final answer
- unsupported claims are removed or labeled as assumptions
- blockers are named precisely
```

Avoid instructions that force unnecessary internal process, for example fixed step sequences that are not required for correctness.

Use `always`, `never`, `must`, and `only` only for true invariants: safety boundaries, required fields, hard business rules, irreversible side effects, or required validation. For judgment calls, write decision rules.

## Reasoning effort guidance

Treat `reasoning_effort` as a last-mile tuning knob, not a substitute for a good prompt.

- Start with `none` for fast execution-heavy tasks: field extraction, support triage, short transforms, simple routing, and obvious formatting.
- Use `low` when a latency-sensitive task has complex instructions or a modest interpretation burden.
- Use `medium` for multi-document synthesis, ambiguous requirements, planning, research, code review, or tasks needing careful tradeoffs.
- Use `high` when correctness is worth latency/cost: complex agents, difficult debugging, strategy, legal/policy-like analysis, or high-stakes synthesis.
- Avoid `xhigh` as a default. Use it only when evals show clear benefit for long, agentic, reasoning-heavy tasks.

Before increasing effort, first improve the prompt with clearer success criteria, retrieval rules, validation loops, and stop conditions.

## Verbosity and formatting

Use `text.verbosity` and explicit output guidance together.

- `low`: terse answers, labels, routing, status, compact support replies, short JSON, or UI-constrained surfaces.
- `medium`: default for most explanations, reviews, and professional answers.
- `high`: detailed analysis, technical migration notes, architecture rationale, research synthesis, or long-form documentation.

Default to plain readable formatting. Add headers, bullets, tables, or numbered lists only when they improve scanning or the product UI needs stable structure. Preserve a user's requested length, structure, and genre for rewriting tasks.

## Personality and collaboration style

For user-facing assistants, separate:

- Personality: sound, tone, warmth, formality, humor, empathy, polish.
- Collaboration style: how the assistant works, when it asks, when it assumes, how proactive it is, how it handles uncertainty, and when it checks work.

Keep both short. Do not use personality instructions to paper over vague goals or missing tool rules. Apparently charm is not a database schema.

## Preambles, phases, and tool-heavy workflows

For multi-step or tool-heavy tasks in streaming products, instruct the model to emit a short preamble before tool calls. The preamble should acknowledge the request and state the first step in one or two sentences.

For Responses API workflows that replay assistant items manually:

- Preserve assistant-item `phase` values exactly.
- Use `phase: "commentary"` for intermediate user-visible updates.
- Use `phase: "final_answer"` for completed answers.
- Do not add phase metadata to user messages.

If the integration uses `previous_response_id`, prefer relying on preserved assistant state rather than manually reconstructing it.

## Grounding and retrieval budgets

For factual answers, prompts must say what requires support, what counts as enough evidence, and what to do when evidence is missing.

Default retrieval budget:

```text
Start with one broad retrieval call using short, discriminative keywords. Search again only when the top results do not answer the core question, a required fact is missing, the user asked for exhaustive coverage, a specific artifact must be read, or the final answer would otherwise contain an important unsupported claim.
```

Do not search again merely to improve phrasing, add ornamental citations, or support generic wording that can be made less specific.

When evidence is absent, do not convert absence into a factual negative. Say what was searched, what was missing, and what conclusion is or is not supported.

## Creative drafting guardrails

For slides, launch copy, summaries, leadership blurbs, outbound copy, and narrative framing, distinguish source-backed facts from creative wording.

Use sourced or provided facts for concrete customer, metric, roadmap, date, capability, product, and competitive claims. If support is weak, write a useful generic version with placeholders or labeled assumptions instead of inventing details. Humanity has generated enough confident nonsense already.

## Validation and self-check rules

When validation is possible, prompt the model to check the work with the most relevant available method:

- Coding: targeted tests, type checks, lint, build, or a smoke test.
- Visual artifacts: render and inspect for clipping, spacing, layout, missing content, and consistency.
- Plans: map requirements to resources, APIs, files, data flow, validation, failure behavior, privacy/security, and material open questions.
- Research: verify citations support the exact claims made.

If validation cannot be run, require a concise explanation and the next best check.

## Migration checklist

When migrating a legacy prompt to GPT-5.5:

1. Switch model first and preserve current behavior as much as possible.
2. Keep or map existing reasoning and verbosity settings before changing the prompt.
3. Remove obsolete process scaffolding and duplicated instructions.
4. Replace vague or conflicting instructions with explicit success criteria and decision rules.
5. Add grounding, retrieval, tool, phase, and validation rules only when relevant.
6. Run evals or representative test prompts.
7. Change one thing at a time after the baseline migration.

See `references/migration-checklist.md` for a fuller checklist and `references/prompt-review-rubric.md` for review scoring.

## Output patterns

### If asked to rewrite a prompt

Return:

1. A short note on the major changes.
2. The complete rewritten prompt in a code block.
3. A compact rationale with the highest-impact changes.
4. Suggested starting settings for `reasoning_effort` and `text.verbosity`.

### If asked to audit a prompt

Return findings ordered by severity:

- Critical behavior risks
- Conflicts or ambiguity
- Over-specified process
- Missing success criteria or stop rules
- Missing evidence/tool/validation rules
- Suggested rewritten sections

### If asked to create a new prompt from a product/task description

Return a complete prompt and call out assumptions. Avoid asking for clarification unless a missing detail materially changes behavior or risk.

## Reference files

Consult these references only when useful for the current task:

- `references/prompt-patterns.md`: reusable GPT-5.5 prompt blocks and templates.
- `references/migration-checklist.md`: migration steps from older prompts and other model families.
- `references/prompt-review-rubric.md`: scoring rubric for prompt audits.

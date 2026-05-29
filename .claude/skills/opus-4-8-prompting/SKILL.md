---
name: opus-4-8-prompting
description: use when creating, editing, migrating, auditing, or testing prompts for claude opus 4.8, especially prompts involving effort tuning, adaptive thinking, long-horizon agentic coding, tool-use calibration, mid-conversation system messages, prompt caching, response length, tone, code review harnesses, frontend/design defaults, subagent guidance, migration from opus 4.7 or earlier, or removal of stale sampling, budget_tokens, or prefill assumptions.
---

# Opus 4.8 Prompting

## Overview

Use this skill to write, revise, migrate, or audit prompts for Claude Opus 4.8. Optimize for the model's actual 4.8 behavior instead of carrying forward stale assumptions from Opus 4.7, Opus 4.6, or older Claude prompts.

Default to preserving the user's intent and product behavior. Make prompts clearer, more explicit, easier to evaluate, and better aligned with the current Messages API.

## Quick Workflow

1. Identify the task type: new prompt, prompt rewrite, API migration, eval harness tuning, agent prompt, coding prompt, research prompt, code review prompt, frontend/design prompt, or output-format prompt.
2. Preserve any working behavior from the existing prompt unless it conflicts with Opus 4.8 API constraints or current model behavior.
3. Decide whether the answer should include only prompt text, an API config snippet, a migration checklist, or all three.
4. Remove obsolete controls such as non-default `temperature`, `top_p`, `top_k`, manual `budget_tokens`, and last-turn assistant prefills when targeting Opus 4.8.
5. Use `effort` and `thinking: {"type": "adaptive"}` as the main model-side controls for intelligence, latency, and token spend.
6. Make scope explicit. Do not rely on the model to infer that an instruction applies to every file, section, document, tool, source, or output item.
7. When tool use, subagent use, frontend aesthetics, progress updates, or action-taking behavior matters, specify concrete trigger conditions and examples.
8. End prompt rewrites with a compact rationale or migration notes only when useful to the user.

## Opus 4.8 Baseline

### Model and API defaults

Use the model string:

```text
claude-opus-4-8
```

When migrating from Opus 4.7, the model name change is usually enough for code that already follows Opus 4.7 constraints. For prompts or clients from Opus 4.6 or older, also apply the 4.7-era breaking changes before assuming the prompt is ready.

Key assumptions for Opus 4.8:

- It is strong on complex reasoning, long-horizon agentic coding, high-autonomy work, knowledge work, vision, and memory tasks.
- It generally performs well on prompts already tuned for Opus 4.7.
- The default `effort` is `high` across the API and Claude Code.
- Use `xhigh` explicitly for coding, high-autonomy, and long-running agentic work.
- Adaptive thinking is the only supported thinking mode on Opus 4.8. Thinking is off unless the request explicitly sets `thinking: {"type": "adaptive"}`.
- Do not use manual `thinking: {"type": "enabled", "budget_tokens": N}`. Opus 4.8 rejects it.
- Do not set `temperature`, `top_p`, or `top_k` to non-default values. Opus 4.8 rejects non-default sampling parameters.
- The 1M context window is default on the Claude API, Amazon Bedrock, and Vertex AI. Microsoft Foundry may have a smaller launch context window, so do not hard-code 1M as universal across all surfaces.
- Opus 4.8 supports 128k max output tokens.
- Mid-conversation system messages can update instructions after user turns while preserving earlier prompt cache hits. Use the top-level `system` field for instructions that apply from the start.
- Refusal responses can include `stop_details`; prompt and client guidance should not assume only the `refusal` stop reason exists.
- Fast mode may be available as `speed: "fast"` for API workloads that prioritize throughput and accept premium pricing.
- The minimum cacheable prompt length is lower than on Opus 4.7, so prompts around 1,024 tokens can be cacheable on Opus 4.8.

### Recommended API shape

```python
client.messages.create(
    model="claude-opus-4-8",
    max_tokens=64000,
    thinking={"type": "adaptive"},
    output_config={"effort": "high"},  # use "xhigh" for coding or agentic work
    messages=[{"role": "user", "content": "..."}],
)
```

For simple, latency-sensitive tasks, omit `thinking` and use lower effort only if quality tradeoffs are acceptable.

## Behavior to Design Around

### Literal instruction following

Opus 4.8 is precise and literal, especially at lower effort levels. If the model should apply an instruction broadly, write the scope explicitly.

```text
Weak: Format the examples consistently.
Better: Format every example in this prompt using the same schema, including edge cases and failure cases.
```

### Verbosity calibration

Opus 4.8 calibrates response length to task complexity. If a product requires a stable answer length or style, specify it and include a positive example.

```text
Provide concise, focused responses. Skip non-essential context, keep examples minimal, and use at most two short paragraphs unless the user asks for deeper analysis.
```

Avoid vague instructions like "be less verbose" unless paired with a target style.

### Effort before prompt contortions

Use `effort` as the first control lever for reasoning depth and token spend.

- `low`: short, narrow, latency-sensitive tasks where under-thinking is acceptable.
- `medium`: cost-sensitive tasks with moderate complexity.
- `high`: default for intelligence-sensitive work.
- `xhigh`: best default for coding, autonomous agents, and long-horizon tool work.
- `max`: reserve for the hardest workloads; validate cost and overthinking behavior.

If a prompt under-thinks, raise effort before adding elaborate reasoning instructions. If it over-thinks, lower effort before adding long anti-overthinking rules.

### Adaptive thinking

Use adaptive thinking for complex, multi-step, agentic, coding, or research tasks.

```text
Use adaptive thinking for requests that require multi-step reasoning, code investigation, tool-result reflection, or cross-source synthesis. For simple lookups or short transformations, respond directly.
```

Do not ask the model to reveal hidden chain of thought. Ask for concise rationale, assumptions, checks, or verification results in the final answer instead.

### Tool use

Opus 4.8 has improved required-tool triggering compared with Opus 4.7, but tool behavior still benefits from explicit trigger conditions. Avoid aggressive blanket rules that force tools when they do not improve the result.

```text
Use web search when the answer depends on current, external, niche, or independently verifiable facts. Use file tools when the user references uploaded files, project files, code, logs, datasets, or documents. Do not guess file contents or external facts that can be checked with an available tool.
```

Use higher effort if the model is skipping needed tools in agentic search or coding workflows.

### Progress updates

Opus 4.8 can produce more useful progress updates in long agentic traces. Remove old scaffolding such as "after every 3 tool calls, summarize progress" unless your product has a measured need for it.

When updates are required, specify content and length:

```text
During long-running work, send brief user-facing updates only when you have a meaningful finding, a change in plan, or a partial result. Keep each update to one or two sentences and avoid low-level tool logs.
```

### Tone and style

Opus 4.8 tends toward direct, opinionated prose with less validation-forward language and sparing emoji. If a warmer or more supportive voice is required, prompt for it directly.

```text
Use a warm, collaborative tone. Acknowledge the user's framing briefly, then give the answer directly. Avoid cheerleading, excessive reassurance, and emoji unless the user uses them first.
```

### Subagents

Opus 4.8 may spawn fewer subagents by default. Specify when delegation is useful.

```xml
<subagent_guidance>
Do not spawn a subagent for work you can complete directly in a single response.
Spawn subagents when independent workstreams can run in parallel, such as auditing multiple modules, researching unrelated source categories, or comparing several implementation strategies.
Keep work direct and sequential when shared context is important or when the task is limited to one file, one question, or one small edit.
</subagent_guidance>
```

### Long context

For long-context prompts, put documents and large inputs before the task instructions and final query. Wrap documents in structured tags with source metadata.

```xml
<documents>
  <document index="1">
    <source>...</source>
    <document_content>...</document_content>
  </document>
</documents>

<task>
Use the documents above to answer the query. Quote the most relevant evidence first, then synthesize the answer.
</task>
```

For long-running agents, encourage state tracking in durable notes, structured JSON, or git when available.

## Prompt Patterns

### Default-to-action agent prompt

Use this when the product should implement requested changes rather than merely advising.

```xml
<default_to_action>
By default, implement requested changes rather than only suggesting them. If the user's intent is unclear, infer the most useful likely action and proceed using available tools to discover missing details. Do not guess facts that can be checked. Ask before actions that are destructive, hard to reverse, visible to others, or affect shared systems.
</default_to_action>
```

### Conservative advisory prompt

Use this when the product should avoid edits unless explicitly requested.

```xml
<do_not_act_before_instructions>
Do not modify files, send messages, change external systems, or execute irreversible actions unless the user clearly asks for implementation. When intent is ambiguous, provide analysis, recommendations, or a proposed plan instead.
</do_not_act_before_instructions>
```

### Code review coverage prompt

Use this when Opus 4.8 appears too conservative because the harness tells it to report only high-severity findings.

```text
Your goal in this pass is coverage. Report every issue you find, including issues you are uncertain about or consider low severity. Do not filter findings by importance or confidence at this stage. For each finding, include confidence, estimated severity, concrete evidence, and the smallest reproduction or reasoning path. A separate verification step may rank or remove findings later.
```

If the product needs one-pass filtering, use concrete bars instead of vague words:

```text
Report any bug that could cause incorrect behavior, a failing test, data loss, security exposure, misleading output, or user-visible breakage. Omit only pure naming, formatting, or style nits.
```

### Anti-overengineering coding prompt

```xml
<scope_constraints>
Avoid over-engineering. Only make changes that are directly requested or clearly necessary for the task.
Do not add unrelated features, speculative abstractions, broad refactors, helper layers, or future-proofing.
Do not add comments, docstrings, type annotations, or defensive branches to code you did not materially change.
Validate at system boundaries, but do not add fallbacks for impossible states or hypothetical failures.
Use standard tools and idioms. Do not hard-code values or solve only for tests.
If tests are wrong or the request is infeasible, say so instead of working around it.
</scope_constraints>
```

### Frontend and design prompt

Opus 4.8 has strong visual priors. Generic instructions like "make it modern" or "avoid AI slop" are not enough. Provide a concrete direction or ask the model to propose options before building.

```xml
<frontend_aesthetics>
Before implementation, propose four distinct visual directions tailored to the brief. For each direction, include background hex, accent hex, typeface direction, layout density, motion style, and one-line rationale. Ask the user to choose one, then implement only that direction.
</frontend_aesthetics>
```

For direct implementation, specify palette, typography, spacing, density, radius, shadows, motion, and target product category.

```xml
<frontend_aesthetics>
Design a dense healthcare analytics dashboard, not an editorial landing page. Use a cool neutral palette, compact spacing, sans-serif typography, restrained motion, accessible contrast, square cards with minimal radius, and strong information hierarchy. Avoid cream backgrounds, decorative serif display type, terracotta accents, portfolio styling, and generic purple gradients.
</frontend_aesthetics>
```

### Research prompt

```text
Search in a structured way. Define success criteria before collecting sources. Track competing hypotheses and confidence as evidence arrives. Verify important claims across independent sources. Prefer primary or authoritative sources when available. Distinguish sourced facts, inference, uncertainty, and unresolved gaps in the final answer.
```

### Formatting prompt

Use positive format instructions and match the prompt style to the desired output.

```text
Write the response as smoothly flowing prose paragraphs. Use headings only where they improve navigation. Avoid bullets unless presenting truly discrete items, rankings, checklists, or steps requested by the user.
```

For math in plain-text targets:

```text
Format math in plain text only. Do not use LaTeX, MathJax, or markup such as \( \), $, or \frac{}{}. Write expressions with standard characters like /, *, and ^.
```

## Migration from Opus 4.7

Use this checklist when adapting an existing Opus 4.7 prompt or client:

- [ ] Change model references from `claude-opus-4-7` to `claude-opus-4-8`.
- [ ] Re-baseline evals before rewriting the prompt heavily, since 4.8 should work well on many 4.7 prompts.
- [ ] Keep `temperature`, `top_p`, and `top_k` unset unless default behavior is intended.
- [ ] Use `thinking: {"type": "adaptive"}` only when thinking is desired.
- [ ] Use `output_config: {"effort": "high"}` or omit effort for the default; use `xhigh` for coding or high-autonomy agents.
- [ ] Re-baseline cost and latency, because effort levels are recalibrated relative to 4.7.
- [ ] Remove any context-window beta header that exists only to unlock 1M context on older models, except where a provider-specific surface still requires different handling.
- [ ] Consider mid-conversation system messages for long-running conversations that update instructions after earlier turns.
- [ ] Update refusal handling to inspect `stop_details` where relevant.
- [ ] Re-test prompt caching assumptions, especially for prompts near 1,024 tokens.
- [ ] Re-test tool triggers. 4.8 improves required-tool triggering, so old aggressive forcing language may be unnecessary.
- [ ] Re-test progress-update scaffolding and remove mechanical update rules unless they improve measured UX.

## Migration from Opus 4.6 or Older

Apply all relevant older-model migrations before applying 4.8 tuning:

- Replace manual extended thinking budgets with adaptive thinking plus effort.
- Remove non-default sampling parameters.
- Remove last-turn assistant prefills.
- Re-test token counting, max output settings, and compaction thresholds.
- Replace brittle verbosity or formatting hacks with positive examples and explicit output contracts.
- Replace blanket tool-use mandates with trigger-based tool instructions.
- Replace vague autonomy language with explicit action, safety, and reversibility rules.

## Output When Rewriting Prompts

When the user asks for a prompt rewrite, return the rewritten prompt first. Use fenced code blocks when the prompt is intended to be copied.

After the prompt, include a short "Notes" section only when it adds value. Keep notes focused on meaningful changes, such as effort choice, adaptive thinking, removed stale API controls, tool trigger changes, or migration risks.

When the user asks for an audit, organize findings by impact:

1. API-breaking or invalid settings.
2. Behavior regressions likely on Opus 4.8.
3. Quality improvements.
4. Optional eval suggestions.

Do not bury an invalid API parameter under style advice. Apparently humans enjoy debugging 400 errors at 2 a.m., but the skill should not help them create more.

## Anti-Patterns

Avoid these when targeting Claude Opus 4.8:

- Assuming thinking is on by default.
- Using `budget_tokens` with Opus 4.8.
- Setting non-default `temperature`, `top_p`, or `top_k`.
- Relying on last-turn assistant prefills.
- Prompting around under-thinking before trying a higher effort level.
- Adding excessive chain-of-thought demands instead of using adaptive thinking, effort, and final-answer verification.
- Using vague scope such as "do this consistently" without saying where it applies.
- Forcing tools for every task instead of defining when tools improve accuracy.
- Keeping mechanical progress-update scaffolding without evidence it helps.
- Giving generic frontend instructions that leave the model's default visual style intact.
- Asking for only high-severity code review findings when the goal is bug recall.
- Treating a migration as complete without re-running evals against representative prompts.

## References

- Official prompting best practices: https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices
- What's new in Claude Opus 4.8: https://platform.claude.com/docs/en/about-claude/models/whats-new-claude-4-8
- Migration guide: https://platform.claude.com/docs/en/about-claude/models/migration-guide
- Effort: https://platform.claude.com/docs/en/build-with-claude/effort
- Adaptive thinking: https://platform.claude.com/docs/en/build-with-claude/adaptive-thinking

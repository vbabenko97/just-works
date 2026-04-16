---
name: opus-4-7-prompting
description: use when creating or editing prompts targeting claude opus 4.7. covers effort tuning, adaptive thinking enablement, task budgets, response-length calibration, literal instruction following, tool-use calibration, progress updates, tone and style shifts, subagent guidance, design and frontend defaults, api breaking changes, and migration from opus 4.6 or older claude models. especially useful for prompt rewrites that need to preserve behavior while removing obsolete 4.6 assumptions such as budget_tokens thinking config, sampling parameters, assistant prefills, fixed-verbosity scaffolding, or overly vague scope instructions.
---

# Opus 4.7 Prompting

## Overview

Claude Opus 4.7 is Anthropic's most capable generally available model. It works well on many Opus 4.6 prompts without major rewrites, but it is more literal about instructions, calibrates verbosity by perceived task complexity, uses fewer tools by default, spawns fewer subagents by default, and exposes new API constraints that matter during migration.

Use this skill to write or revise prompts so they match Opus 4.7's actual behavior instead of carrying forward stale assumptions from Opus 4.6.

<context>
Key characteristics to design around:

- **Literal instruction following**: state scope explicitly; the model will not silently generalize from one example or one item to all others.
- **Verbosity calibration**: short for simple tasks, much longer for open-ended analysis unless you steer style and length.
- **Effort matters more**: `effort` is now a stronger lever than before, with new `xhigh` for coding and agentic work.
- **Thinking is explicit**: thinking is off by default on Opus 4.7; enable it with `thinking: {"type": "adaptive"}`.
- **Fewer tool calls by default**: Opus 4.7 reasons more and uses tools less than Opus 4.6 unless you raise effort or instruct tool usage clearly.
- **Better built-in progress updates**: long agent traces already produce better interim updates, so forced status scaffolding is often unnecessary.
- **Fewer subagents by default**: subagent use is steerable and should be specified for fan-out work.
- **Stronger visual/design priors**: UI, slide, and frontend prompts may inherit a default editorial aesthetic unless you specify concrete visual direction.
</context>

## General Principles

### Be clear and direct

Opus 4.7 responds best to explicit instructions. If you want behavior that goes beyond the literal request, ask for it directly.

```text
Good: "Read the files directly related to this bug, identify the root cause,
implement the fix, run the relevant tests, and summarize the change."

Avoid: "Fix this."
```

### Add context that explains why

Rules land better when the model understands the reason behind them.

```xml
<task>
Respond in plain text paragraphs.

<context>
The output will be read aloud by a text-to-speech system.
Markdown punctuation would be spoken literally and reduce comprehension.
</context>
</task>
```

### Use examples carefully

Examples are strong behavioral anchors. Every example should demonstrate the exact pattern you want repeated.

### State scope explicitly

Opus 4.7 is more literal than Opus 4.6, especially at lower effort. If an instruction should apply broadly, say so.

```text
Weak: "Format the heading in title case."
Better: "Format every heading in the document in title case, not just the first one."
```

### Prefer positive instructions over negations

Tell the model what to do, not only what to avoid.

```text
Better: "Write the response as short prose paragraphs with no bullets."
Worse: "Do not use bullets."
```

## Thinking and Effort

### Use effort as the primary control lever

For Opus 4.7, `effort` is the main knob for trading off intelligence, speed, and token use.

- `xhigh`: best default for coding and agentic workflows
- `high`: minimum default for most intelligence-sensitive tasks
- `medium`: cost-sensitive workloads with moderate complexity
- `low`: short, scoped, latency-sensitive tasks
- `max`: use selectively for especially demanding tasks; it can increase token usage and sometimes overthink

On Opus 4.7, `low` and `medium` are stricter than on Opus 4.6. At those levels, the model is more likely to do exactly what was asked and nothing extra.

### Adaptive thinking must be enabled explicitly

Do not assume Opus 4.7 thinks by default. It does not.

```python
# Opus 4.7
thinking = {"type": "adaptive"}
output_config = {"effort": "high"}
```

If you omit `thinking`, the request runs without thinking.

### Steer thinking only after tuning effort

Raise `effort` before adding elaborate anti-underthinking instructions. Lower `effort` before adding elaborate anti-overthinking instructions.

```text
If this task requires multi-step reasoning, think carefully through the problem
before responding. Otherwise, respond directly.
```

```text
Thinking adds latency and should only be used when it will meaningfully improve
answer quality, typically for problems that require multi-step reasoning. When in
doubt, respond directly.
```

### Give enough output room at high effort

If you run Opus 4.7 with `xhigh` or `max` effort in agentic workflows, give it a large output budget so it has room to think, use tools, and complete the task.

```text
Start around 64k max output tokens for demanding agentic or coding traces, then tune.
```

## Response Length and Communication Style

### Control verbosity explicitly when it matters

Opus 4.7 calibrates answer length to perceived task complexity. If your product depends on a consistent style or length, specify it.

```text
Provide concise, focused responses. Skip non-essential context, and keep examples minimal.
```

Positive examples of the desired level of concision work better than vague complaints about being too verbose.

### Re-baseline tone and voice

Compared with Opus 4.6, Opus 4.7 is more direct and opinionated, with less validation-forward phrasing and fewer emoji. If you need a warmer voice, say so.

```text
Use a warm, collaborative tone. Acknowledge the user's framing before answering.
```

### Progress-update scaffolding is often unnecessary

Opus 4.7 already produces better user-facing progress updates during long agentic traces. Remove rules like "after every 3 tool calls, summarize progress" unless you have a measured reason to keep them.

If you need specific update behavior, describe the cadence, length, and content directly and provide a short example.

## Tool Use and Action Steering

### Be explicit about when tools should be used

Opus 4.7 tends to use tools less often than Opus 4.6 and to reason more before calling them. If tool usage matters, define the trigger conditions clearly.

```text
Use web search when the answer depends on recent, external, or verifiable facts.
Use local file tools when the user refers to specific files, directories, or code.
```

### Increase effort before overcomplicating tool instructions

If the model is underusing tools in search or coding workflows, first try `high` or `xhigh` effort. Those settings produce substantially more tool use.

### Steer action vs recommendation behavior directly

```xml
<default_to_action>
By default, implement changes rather than only suggesting them. If the user's
intent is unclear, infer the most useful likely action and proceed, using tools
to discover missing details instead of guessing.
</default_to_action>
```

```xml
<do_not_act_before_instructions>
Do not jump into implementation or file changes unless clearly instructed.
Default to research, explanation, and recommendations when the request is ambiguous.
</do_not_act_before_instructions>
```

### Use parallel tool guidance only when needed

Opus 4.7 already does parallel tool use well. Add explicit parallelization guidance only if you need to maximize or constrain it.

```xml
<use_parallel_tool_calls>
If multiple tool calls are independent, make them in parallel. If any call depends
on the result of another, do them sequentially and do not guess missing parameters.
</use_parallel_tool_calls>
```

## Subagents and Long-Horizon Work

### Subagents are no longer as eager by default

Opus 4.7 spawns fewer subagents than Opus 4.6. If a workflow benefits from fan-out, specify when to delegate.

```xml
<subagent_guidance>
Do not spawn a subagent for work you can complete directly in a single response.
Spawn multiple subagents in the same turn when fanning out across independent
items, files, or research branches.
</subagent_guidance>
```

### Keep long tasks milestone-based

For long-horizon work, structure prompts around verifiable milestones rather than one giant instruction. This improves tracking and makes agent traces easier to inspect.

## Output Structure and Formatting

### Use XML tags where they add clarity

Use XML tags to separate inputs, constraints, and desired output when the prompt is complex. Do not add tags mechanically when plain structure is already clear.

Recommended tags:
- `<context>`
- `<task>`
- `<instructions>`
- `<requirements>`
- `<constraint>`
- `<example>` / `<examples>`
- `<input>` / `<output>`
- `<format>` / `<output_format>`

### Match the prompt style to the output style

If you want structured output, prompt structurally. If you want prose, prompt in prose.

```text
Instead of: "Do not use markdown."
Use: "Write the answer as smoothly flowing prose paragraphs."
```

### LaTeX is still the default for math

If the rendering target does not support LaTeX, opt out explicitly.

```text
Format your response in plain text only. Do not use LaTeX, MathJax, or markup
notation such as \( \), $, or \frac{}{}. Write math using standard text
characters such as /, *, and ^.
```

## Agentic Safety and Scope Control

### Distinguish reversible from irreversible actions

```xml
<action_safety>
Consider the reversibility and potential impact of your actions. You may take
local, reversible actions such as reading files, editing local files, or running
tests. Ask the user before taking actions that are destructive, hard to reverse,
affect shared systems, or are visible to other people.
</action_safety>
```

Ask for confirmation before:
- deleting files, branches, or data
- force pushing, hard resets, or migrations
- sending messages, posting comments, or modifying shared infrastructure

### Prevent over-engineering and eagerness

```xml
<scope_constraints>
Avoid over-engineering. Only make changes that are directly requested or clearly
necessary. Keep solutions simple and focused:
- Don't add features, refactor unrelated code, or make speculative improvements.
- Don't add docstrings, comments, or type annotations to code you did not change.
- Don't add defensive handling for impossible or purely hypothetical cases.
- Don't create helpers, utilities, or abstractions for one-off work.
</scope_constraints>
```

### Reduce temporary file sprawl when desired

```text
If you create any temporary new files, scripts, or helper files for iteration,
clean them up by removing them at the end of the task.
```

### Prevent test-chasing and hard-coding

```text
Write a high-quality, general-purpose solution using the standard tools available.
Do not hard-code values or solve only for the test cases. Implement the actual
logic that solves the problem generally. If tests are wrong, say so instead of
working around them.
```

### Minimize hallucinations by forcing investigation

```xml
<investigate_before_answering>
Never speculate about code you have not opened. If the user references a specific
file, read it before answering. Investigate relevant files before making claims
about the codebase.
</investigate_before_answering>
```

## Frontend, Slides, and Visual Outputs

### Override the default house style with concrete specs

Opus 4.7 has a stronger built-in editorial aesthetic than Opus 4.6, especially for frontends, slide decks, and visual documents. If you want a different look, specify concrete visual direction rather than generic instructions like "make it minimal".

Include explicit choices such as:
- palette
- typography
- layout density
- corner radius and shadows
- motion style
- interaction patterns
- target product context

```xml
<frontend_aesthetics>
Design a dense enterprise dashboard for a fintech product. Use a cool neutral
palette, sans-serif typography, compact spacing, restrained motion, and strong
information hierarchy. Avoid editorial or portfolio styling.
</frontend_aesthetics>
```

## API Migration Notes for Opus 4.7

### Breaking changes

1. Update the model name:

```text
claude-opus-4-6 -> claude-opus-4-7
```

2. Replace extended-thinking budgets:

```python
# before
thinking = {"type": "enabled", "budget_tokens": 32000}

# after
thinking = {"type": "adaptive"}
output_config = {"effort": "high"}
```

3. Remove non-default sampling parameters. On Opus 4.7, setting `temperature`, `top_p`, or `top_k` to non-default values returns a 400 error.

4. Remove assistant-message prefills on the last assistant turn.

### Silent but important behavior changes

1. Thinking content is omitted by default. If your UI streams reasoning text, opt in explicitly:

```python
thinking = {
    "type": "adaptive",
    "display": "summarized",
}
```

2. Token counting changed. Re-test client-side token estimates, `max_tokens`, and compaction thresholds.

3. `task_budget` is new and optional. Use it when you want the model to self-scope a full agentic loop to an advisory token budget. Do not use it by default for open-ended quality-first tasks.

## Prompt Migration Checklist

- [ ] rename the model string to `claude-opus-4-7`
- [ ] replace `thinking: {type: "enabled", budget_tokens: n}` with `thinking: {type: "adaptive"}` plus `effort`
- [ ] explicitly enable thinking if needed; it is off by default otherwise
- [ ] remove non-default `temperature`, `top_p`, and `top_k`
- [ ] remove assistant prefills on the last assistant turn
- [ ] if your ui shows reasoning, set `thinking.display` to `"summarized"`
- [ ] re-benchmark `max_tokens`, token estimation, and compaction thresholds because tokenization changed
- [ ] test `xhigh` for coding and agentic workflows; use at least `high` for intelligence-sensitive tasks
- [ ] remove forced progress-update scaffolding unless you have a measured reason to keep it
- [ ] rewrite any vague instructions so their scope is explicit
- [ ] re-baseline tone prompts if you need a warmer or more conversational voice
- [ ] add concrete visual specs for frontend, slide, or design-heavy prompts
- [ ] re-test tool usage patterns; Opus 4.7 uses fewer tools by default than Opus 4.6
- [ ] consider `task_budget` only for token-scoped agentic loops, not as a default setting

## Anti-Patterns

- **Assuming thinking is on by default**: on Opus 4.7 it is not.
- **Treating effort as a minor detail**: on Opus 4.7 it is a primary behavior lever.
- **Vague scope**: the model will not silently generalize instructions for you.
- **Complaining about verbosity without showing the target style**: give a positive verbosity example instead.
- **Expecting old tool behavior**: Opus 4.7 tends to reason more and call tools less unless prompted or run at higher effort.
- **Forcing synthetic progress updates**: remove scaffolding first and re-baseline.
- **Generic visual instructions**: weak style prompts often leave the default house style intact.
- **Keeping stale API params**: `budget_tokens`, assistant prefills, and non-default sampling parameters should be removed or replaced.
- **Prompting around under-thinking before changing effort**: try the effort lever first.
- **Overloading prompts with unnecessary tags and rules**: use only the structure that adds real clarity.

## Reference

- official prompting best practices: https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices/
- what's new in claude opus 4.7: https://platform.claude.com/docs/en/about-claude/models/whats-new-claude-4-7
- migration guide: https://platform.claude.com/docs/en/about-claude/models/migration-guide

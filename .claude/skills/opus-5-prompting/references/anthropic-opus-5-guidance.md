# Official Claude Opus 5 guidance

Source of truth: Anthropic Claude Platform documentation.

Retrieved: 2026-07-25

Treat this file as a compact snapshot. Verify the live official documentation before making production claims about model availability, parameters, beta headers, pricing, tool support, or limits.

## Primary sources

- Prompting Claude Opus 5: https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-opus-5
- What's new in Claude Opus 5: https://platform.claude.com/docs/en/about-claude/models/whats-new-opus-5
- Migration guide: https://platform.claude.com/docs/en/about-claude/models/migration-guide
- Prompting best practices: https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices
- Effort: https://platform.claude.com/docs/en/build-with-claude/effort
- Steering thinking: https://platform.claude.com/docs/en/build-with-claude/thinking-steering-and-cost

## Model and limits

- Claude API model ID: `claude-opus-5`.
- Intended use: complex agentic coding and enterprise work.
- Context window: 1 million tokens by default and as the maximum.
- Maximum output: 128k tokens.
- Prompt cache minimum: 512 tokens.
- Thinking: adaptive thinking is on by default.
- `max_tokens` is a hard limit shared by thinking and visible response output.

## Effort

Supported levels are `low`, `medium`, `high`, `xhigh`, and `max`.

- `high` is the API default.
- `low` and `medium` are strong candidates for routine or cost-sensitive work.
- `xhigh` targets demanding long-running coding and agentic workloads.
- `max` targets capability-critical work and may overthink simpler tasks.
- At `xhigh` or `max`, Anthropic recommends a large `max_tokens`; 64k is a documented starting point.
- Effort affects thinking, tool calls, function arguments, and visible text token spend, but it does not reliably control visible response length.

Run a workload-specific effort sweep. Do not inherit an effort setting unchanged from another model.

## Thinking behavior

- Omitting the `thinking` field enables adaptive thinking.
- `thinking: {type: "adaptive"}` is equivalent to the default.
- Thinking can be disabled only at `high`, `medium`, or `low` effort.
- Combining disabled thinking with `xhigh` or `max` returns a 400 error.
- Prefer thinking enabled at lower effort over disabling it; Anthropic reports better quality at similar cost for most tasks.

With thinking disabled, two visible-output artifacts may occur:

1. A tool call may appear as plain text instead of a structured tool-use block.
2. Internal XML-like tags may leak into visible output.

Where thinking must be disabled, use this mitigation:

```text
You may briefly announce a tool call. When no available tool can perform the request, report that limitation rather than fabricating an action. Keep internal control tags out of user-visible text.
```

Do not instruct the model not to think or not to reason; such wording can worsen tag leakage.

## Prompting behavior changes

Compared with Claude Opus 4.8, Opus 5 commonly needs explicit tuning for:

- Longer default user-facing responses.
- More frequent narration during agentic work.
- Longer written artifacts.
- More autonomous scope expansion.
- More eager subagent delegation.
- Built-in self-verification and self-correction.

Consequences:

- Control visible length with direct length instructions, not effort alone.
- Specify progress-update cadence.
- Calibrate document length separately from conversational verbosity.
- Remove carried-over verification and double-check instructions.
- Constrain narrow task scope explicitly.
- Define when subagents are warranted and cap spawning.
- Limit correction narration to errors that matter to the user.

## Capability-oriented guidance

- Give the complete task specification up front for difficult coding and agentic work.
- Ask code review to report all real findings, then filter severity in a separate pass. A conservative first-pass instruction can suppress valid findings.
- Revalidate prompt-side workarounds for vision, charts, documents, diagrams, UI replication, spreadsheets, and slides; stronger model capability may make them unnecessary.
- Prefer iterative tool use for visual verification over merely increasing thinking effort.
- Use explicit implementation language when action is intended; vague requests for suggestions may produce advice rather than edits.

## API migration constraints

- Non-default `temperature`, `top_p`, or `top_k` values return a 400 error. Omit them.
- Manual extended thinking with `budget_tokens` is unsupported.
- Assistant-message prefill is unsupported. Use system instructions or structured output.
- Mid-conversation system messages are supported subject to placement rules.
- Mid-conversation tool changes are beta and require the current documented beta header.
- Server-side fallback is beta and requires the current documented beta header.
- Web search is documented as available, but web fetch is not available on Opus 5.
- Priority Tier is not supported on Opus 5.
- Refusals can return HTTP 200 with `stop_reason: "refusal"`; inspect `stop_details` and handle fallbacks deliberately.

## Long-context prompting

For large inputs:

- Place long documents and source material before the task query.
- Put the actual question and instructions near the end.
- Separate documents and metadata with clear XML tags when ambiguity is likely.
- Ask for evidence extraction before synthesis when grounded analysis matters.
- Do not fill the context window merely because it exists; remove stale or irrelevant history.

## General prompt construction

- Be direct and specific about the outcome.
- Explain context or motivation only when it helps the model choose correctly.
- Use 3 to 5 diverse examples when format or edge-case consistency is hard to achieve with instructions alone.
- Use XML tags when a prompt mixes instructions, context, examples, and variable input.
- Prefer positive instructions describing the desired output.
- Match prompt structure to desired output style when format steering is difficult.

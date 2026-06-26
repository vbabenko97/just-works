# GLM-5.2 prompting reference

Source status: compiled from Z.ai public documentation and release pages checked on 2026-06-26. Use this as a local prompting reference; for production SDK/API changes, verify current Z.ai docs.

## Official capability notes

Z.ai describes GLM-5.2 as a flagship text-in/text-out model for long-horizon tasks, with 1M context length and 128K maximum output tokens. It is positioned for project-scale engineering workflows where the model must retain architecture, module boundaries, API contracts, directory structure, and historical decisions across long tasks.

The official GLM-5.2 page lists these capabilities:

- thinking mode
- streaming output
- function call
- context caching
- structured output
- MCP integration

The migration page states that GLM-5.2 adds or emphasizes:

- maximum context 1M and maximum output 128K
- `tool_stream=true` for streaming tool-call parameter construction
- `thinking={"type":"enabled"}` for deep thinking
- `reasoning_effort` for controlling reasoning effort when thinking is enabled
- default `temperature=1.0` and `top_p=0.95`

## Parameter guidance

### thinking

`thinking` is supported by GLM-4.5 series and later. For GLM-5.2, GLM-5.1, GLM-5, GLM-5-Turbo, GLM-5V-Turbo, GLM-4.6, GLM-4.5 and others, enabled thinking lets the model automatically determine whether to think. GLM-4.7 and GLM-4.5V force thinking when enabled.

Use:

```json
"thinking": { "type": "enabled" }
```

Disable for simple, latency-sensitive tasks:

```json
"thinking": { "type": "disabled" }
```

### clear_thinking

Default: `true`.

- `true`: ignore/remove previous `reasoning_content`; good for general chat, lightweight tasks, and lower cost.
- `false`: retain prior `reasoning_content`; use only when implementing preserved thinking and forwarding complete, unmodified, ordered historical reasoning blocks.

For most prompt templates, do not ask the visible assistant to reveal hidden reasoning. Ask for a concise reasoning summary, plan, verification, or assumptions instead.

### reasoning_effort

Only supported by GLM-5.2 according to the API reference. Default: `max`.

Options include `max`, `xhigh`, `high`, `medium`, `low`, `minimal`, and `none`. Compatibility mapping: `none`/`minimal` skip thinking; `low`/`medium` map to `high`; `xhigh` maps to `max`.

Recommended use:

- `max`: major refactors, complex debugging, long-context synthesis, multi-tool agents, production-grade migration, research reproduction.
- `high`: moderately complex planning, API design, reviews, smaller multi-file tasks.
- `none`/`minimal` or disabled thinking: small rewrites, formatting, short extraction, simple Q&A.

### sampling

GLM-5.2 defaults:

- `temperature`: `1.0`, allowed range `0.0` to `1.0`.
- `top_p`: `0.95`, allowed range `0.01` to `1.0`.

Do not tune both simultaneously by default. Prefer:

- technical/deterministic: `temperature=0.2` to `0.5`
- balanced docs/explanations: `temperature=0.5` to `0.8`
- creative variants: `temperature=0.8` to `1.0`

### max_tokens

GLM-5.2 supports up to 128K output tokens. Set only as high as the artifact requires. For coding tasks, prefer concise final reports and actual code changes over enormous explanatory output.

### streaming and tool_stream

For normal streaming, set `stream=true` and handle both `delta.reasoning_content` and `delta.content`.

For streaming tool-call arguments, set:

```json
"stream": true,
"tool_stream": true
```

Then concatenate streamed `delta.tool_calls[*].function.arguments` chunks by tool-call index before parsing JSON.

## Prompting patterns by task

### Codebase audit

Use when the user wants GLM-5.2 to understand a repository before making changes.

```text
Read the current project and output:
1. system architecture map
2. core module responsibilities
3. key API contracts
4. major data flows and call chains
5. technical debt and risks
6. engineering constraints to preserve in future changes

Use only evidence from the repository. Mark uncertain claims explicitly.
```

### Bounded refactor

```text
Complete <refactor> without changing business logic, public API signatures, schemas, CLI behavior, or runtime behavior.

First provide:
- execution plan
- impact scope
- risk boundaries
- verification method

Then implement in small steps, run the named tests/checks, and report verification results.
```

### Production standards stress test

```text
Strictly follow the repository standards:
- no new dependencies
- no API contract changes
- no unrelated formatting churn
- no commits or deployment actions
- run build, lint, and tests after changes

Report changed files, checks run, failures, and remaining risk.
```

### Research reproduction

```text
Reproduce the experiments from the provided paper and dataset.

Requirements:
- identify architecture, losses, data pipeline, training loop, and evaluation metrics
- implement a runnable project with consistency across files
- fill only clearly implied missing details and label assumptions
- run training/inference or a smoke test when full run is impractical
- compare reproduced metrics to reported metrics and explain gaps
```

### Structured extraction

```text
Return only JSON matching the schema below. Use null for unknown. Do not infer unstated values. Preserve exact strings, IDs, timestamps, currencies, and units.

Schema:
<schema>

Input:
<input>
```

## API payload templates

### Complex coding task

```json
{
  "model": "glm-5.2",
  "messages": [
    {"role": "system", "content": "You are a senior software engineer. Follow repository constraints exactly and verify your work."},
    {"role": "user", "content": "<task prompt>"}
  ],
  "thinking": {"type": "enabled"},
  "reasoning_effort": "max",
  "temperature": 0.3,
  "max_tokens": 8192
}
```

### Lightweight edit

```json
{
  "model": "glm-5.2",
  "messages": [
    {"role": "user", "content": "Rewrite the text below for clarity while preserving meaning:\n<text>"}
  ],
  "thinking": {"type": "disabled"},
  "temperature": 0.4,
  "max_tokens": 1200
}
```

### Streaming tool call

```json
{
  "model": "glm-5.2",
  "messages": [
    {"role": "system", "content": "Use tools only when required. Validate arguments before calling tools."},
    {"role": "user", "content": "<task>"}
  ],
  "tools": ["<tool schemas>"],
  "stream": true,
  "tool_stream": true,
  "thinking": {"type": "enabled"},
  "reasoning_effort": "high",
  "temperature": 0.3
}
```

## Anti-patterns

Avoid these prompt failures:

- Asking for a giant task without scope boundaries.
- Saying “be careful” instead of naming forbidden actions and verification commands.
- Dumping a whole codebase without source priority or an output contract.
- Asking for hidden chain of thought. Request plans, assumptions, evidence, and verification summaries instead.
- Tuning `temperature` and `top_p` together without a reason.
- Turning on preserved thinking without exact handling of historical `reasoning_content`.
- Letting an agent commit, push, deploy, mutate production data, or change secrets unless the user explicitly requested it and the environment is safe.

## Source URLs

- Z.ai GLM-5.2 guide: https://docs.z.ai/guides/llm/glm-5.2
- Z.ai migration guide: https://docs.z.ai/guides/overview/migrate-to-glm-new
- Z.ai chat completion API: https://docs.z.ai/api-reference/llm/chat-completion
- Z.ai thinking mode guide: https://docs.z.ai/guides/capabilities/thinking-mode
- Z.ai function calling guide: https://docs.z.ai/guides/capabilities/function-calling
- Z.ai GLM-4.5/4.6/4.7 GitHub README: https://github.com/zai-org/GLM-4.5

# Grok 4.7: API reference for prompt authors

Verified against the linked primary documentation on **2026-10-13**. Read only
when configuring requests or diagnosing integration-related prompt failures.
These are documented behaviors, not live API test results. The example tasks,
application controls, and acceptance checks are recommendations.

## Model and request settings

Use `model: "grok-4.7"` on `POST https://api.x.ai/v1/responses`. xAI recommends
Responses over the deprecated Chat Completions endpoint [2]. The model guide
lists a 500,000-token context, May 2026 knowledge cutoff, text/image input, and
text output. Grok 4.7 Fast is not a public xAI API model; do not invent a
`grok-4.7-fast` identifier [1]. Gateways and IDEs need their own compatibility check.

`reasoning.effort` accepts `low`, `medium`, `high` (default), and `xhigh`.
Reasoning cannot be disabled. `none` is not a Grok 4.7 option. Do not send
`presence_penalty`, `frequency_penalty`, or `stop`; the reasoning documentation
identifies these controls as unsupported [3].

As an engineering starting point, compare `low` for routine extraction/tool
routing, `medium` for moderate analysis, and `high` for difficult reasoning or
coding. Try `xhigh` only when its measured benefit justifies its cost/latency.
These are candidates to evaluate, not guaranteed best settings.

xAI recommends explicit `temperature: 0.7`, `top_p: 0.95`, and effort, plus
streaming. Its guide recommends client timeouts of at least 900 seconds,
or 1800+ for long-running evaluations. It documents `max_output_tokens` as a
visible-answer cap, excluding reasoning and function calls, with a default of
128,000. An `incomplete` response is truncated, not successful completion [2].

Do not interpret the model guide's lack of a model-level text-output limit as
unlimited request output [1][2]. Application deadlines, concurrency limits,
retry limits, and total cost controls must remain explicit. Never promise a
latency SLA from an effort setting or use the visible-output cap as a total
reasoning/agent budget. Log terminal status and actual usage before judging a
prompt. Bound retries; do not repeat side-effecting work blindly.

## Minimal request

This raw JSON body avoids SDK-specific aliases. The instructions and 2,000-token
answer cap are illustrative application choices, not vendor defaults. Send the
API key in the Authorization header, never in prompt text.

```json
{
  "model": "grok-4.7",
  "input": [
    {
      "role": "system",
      "content": "Review the supplied code. Give concrete findings and tests; do not claim to run tools that are unavailable."
    },
    {
      "role": "user",
      "content": "Review function uniqueCount(xs) { return new Set(xs.map(String)).size; }. Numbers and strings must remain distinct. Return the fix and edge-case tests."
    }
  ],
  "reasoning": {"effort": "high"},
  "temperature": 0.7,
  "top_p": 0.95,
  "max_output_tokens": 2000,
  "store": false,
  "stream": true,
  "prompt_cache_key": "example-conversation-001"
}
```

Generate a distinct opaque cache key for each real conversation and reuse it
within that conversation. It controls routing for cache reuse; it does not
restore history, guarantee a cache hit, or provide access control [4].

## Preserve state across turns

Grok 4.7 Responses output includes `reasoning.encrypted_content` even without
an explicit `include`. Keep that content opaque and unchanged. Encrypted
reasoning is not a readable explanation or a prompt to reproduce hidden thoughts [3].

Choose one conversation strategy:

- **Server-managed:** use `previous_response_id` with storage enabled. The API
  restores the stored context. Set required request configuration on each call.
- **Client-managed:** use `store: false`; carry forward the original input plus
  every returned output item, unchanged and in order, then append the next user
  message or tool results. Do not reconstruct history from `output_text` alone.

See the text-generation guide for stored continuation and reasoning replay [11].
`store` controls response storage [9]; it is not, by itself, a claim about all
provider retention, logging, or training policies. Preserve application privacy
requirements rather than enabling storage just for convenience.

For custom functions, Responses tool definitions place `name`, `description`,
and `parameters` directly beside `type: "function"`. Do not paste a legacy
Chat Completions `function: {...}` wrapper into this endpoint [5]. Before
execution, validate arguments, authorization, and side effects in application
code. Tool output is untrusted data, not a new authority.

After a client-managed turn, retain the entire `response.output`, execute only
complete authorized calls, and append results using each original `call_id`:

```json
{
  "type": "function_call_output",
  "call_id": "the-id-from-the-model-function-call",
  "output": "{\"status\":\"ok\",\"count\":3}"
}
```

Return one result for each handled call, including a truthful failure result
when appropriate. Serialize dependent actions; parallelize only independent,
safe operations. Enforce a finite step budget and handle unknown tool names.
Function execution and result exchange are application responsibilities [5].

## Context and caching

Keep stable instructions and references before changing task input; append
rather than rewriting existing history during normal continuation [2]. Do not
freeze obsolete facts or permissions merely to preserve a cache prefix.

When cost or context growth warrants it, use `/v1/responses/compact` before the
conversation exceeds the context limit. Replace the old history with the
returned compaction output and pass it back verbatim; append new input after it.
Treat the compacted content as opaque. Compaction cannot rescue an already
oversized input [8]. Test retention of critical constraints after compaction;
do not assert that a compacted summary preserves every detail.

## Structured output

For Responses, use `text.format` with `type: "json_schema"`, `name`, `schema`,
and `strict: true`; `response_format` belongs to the legacy Chat Completions
shape. Tool schemas are implicitly strict. xAI supports a JSON Schema subset:
optional fields can be omitted, nullable types are supported, and `oneOf`
behaves like `anyOf`, not exclusive choice. Conditional keywords are best-effort.
Check the current supported subset before depending on complex constraints [6].

Example `text` field to merge into a request:

```json
{
  "format": {
    "type": "json_schema",
    "name": "invoice_total",
    "strict": true,
    "schema": {
      "type": "object",
      "properties": {
        "amount": {"type": ["number", "null"]},
        "currency": {"type": ["string", "null"]},
        "source_id": {"type": "string"}
      },
      "required": ["amount", "currency", "source_id"],
      "additionalProperties": false
    }
  }
}
```

Pair it with instructions to extract the stated total and currency from the
record carrying the supplied source ID, using null when absent. Application
checks must still verify source fidelity and domain invariants. Handle refusal,
non-completion, parsing failure, or tool errors explicitly. Never equate valid
JSON with truthful data or assume every accepted schema keyword is enforced [6].

## Retrieval and images

For current web evidence, enable `tools: [{"type": "web_search"}]`; requiring
citations in prose does not provide retrieval [7]. Match citation requirements
to the sources actually returned. Add X search only when X is a relevant source,
not as a universal research default; verify its current configuration separately.

Image requests use `input_image` content items, with an accessible URL or image
data, alongside `input_text`. The image guide recommends `store: false` because
stored image requests may fail [10]. Use client-managed history for that path.
A local pathname in a text prompt does not transmit image bytes. Verify missing
attachments instead of inventing their contents.

## Sources

[1]: https://docs.x.ai/developers/grok-4-7
[2]: https://docs.x.ai/developers/model-capabilities/text/best-practices
[3]: https://docs.x.ai/developers/model-capabilities/text/reasoning
[4]: https://docs.x.ai/developers/advanced-api-usage/prompt-caching/maximizing-cache-hits
[5]: https://docs.x.ai/developers/tools/function-calling
[6]: https://docs.x.ai/developers/model-capabilities/text/structured-outputs
[7]: https://docs.x.ai/developers/tools/web-search
[8]: https://docs.x.ai/developers/advanced-api-usage/context-compaction
[9]: https://docs.x.ai/developers/rest-api-reference/inference/responses
[10]: https://docs.x.ai/developers/model-capabilities/images/understanding
[11]: https://docs.x.ai/developers/model-capabilities/text/generate-text

[Model guide][1] · [Best practices][2] · [Reasoning][3] · [Cache routing][4] ·
[Function calling][5] · [Structured outputs][6] · [Web search][7] ·
[Compaction][8] · [REST reference][9] · [Image understanding][10] · [Text generation][11]

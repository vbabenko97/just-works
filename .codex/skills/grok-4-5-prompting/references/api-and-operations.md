# API and operations guidance

## Preferred request shape

Use the Responses API unless the surrounding system requires Chat Completions.

```python
import os
from openai import OpenAI

client = OpenAI(
    api_key=os.environ["XAI_API_KEY"],
    base_url="https://api.x.ai/v1",
)

response = client.responses.create(
    model="grok-4.5",
    reasoning={"effort": "medium"},
    input=[
        {"role": "system", "content": "[stable system instructions]"},
        {"role": "user", "content": "[task and changing data]"},
    ],
    extra_body={"prompt_cache_key": "stable-conversation-or-workload-id"},
)

print(response.output_text)
```

Keep the API key in an environment variable. Confirm current SDK parameter support before copying provider-specific fields into production code.

## Place controls in the right layer

| Concern | Put it in |
|---|---|
| Task, context, constraints, output meaning | Prompt |
| Reasoning depth | `reasoning.effort` |
| Current information | Web or X Search tool |
| Exact calculations / data analysis | Code execution tool |
| Machine-readable shape | Structured output schema |
| External actions | Function definitions and application loop |
| Cache routing | `prompt_cache_key` or `x-grok-conv-id` |
| Long-history reduction | Context Compaction API |

## Tool selection

- `web_search`: changing public facts and browsing webpages. Restrict domains when authoritative sources are known.
- `x_search`: X posts, threads, first-party handles, or social discourse. Restrict handles and dates when possible.
- `code_interpreter`: calculations, simulations, data analysis, or executable verification.
- custom functions: private systems and side effects controlled by the caller.
- collections search: uploaded knowledge bases and proprietary document retrieval.

Do not enable every tool by default. Each unnecessary tool expands the action space and can add latency or irrelevant evidence.

## Function-calling design

- Use distinct verb-first names.
- Describe when the tool should and should not be used.
- Define narrow JSON schemas with required fields, enums, ranges, and descriptions.
- Return structured errors that distinguish retryable from permanent failures.
- Process all parallel calls before continuing when calls are independent.
- Make side effects idempotent where possible.
- Bound retries and define the final stop condition in application logic.

## Structured outputs

Use strict JSON Schema for parsers, workflows, or persistent records. Define nullability and `additionalProperties`. Include evidence fields when traceability matters.

Keep the prompt about extraction or reasoning semantics; keep syntax guarantees in the schema.

## Prompt caching

For reliable cache reuse:

1. Set `prompt_cache_key` for Responses or `x-grok-conv-id` for Chat Completions.
2. Keep the identifier stable for the same conversation or workload.
3. Never edit, remove, or reorder earlier messages in an active cached conversation.
4. Front-load static system instructions, examples, and reference material.
5. Append changing user turns and tool results.
6. Monitor cached-token usage; zero cache hits indicate routing or prefix instability.
7. Treat cache hits as an optimization, not a correctness dependency.

## Context compaction

Use compaction when a valid conversation still fits the context window but repeated history is raising cost, latency, or distraction.

- Preserve the returned compaction item verbatim.
- Append new turns after it.
- Do not parse, edit, merge, or reorder encrypted content.
- Compact before exceeding the context window; it cannot rescue an already over-limit request.
- Re-compaction is acceptable as the conversation grows again.

## Stateful responses and privacy

The Responses API may store request/response state to support continuation. xAI documents a 30-day storage period for stored responses. Review application privacy requirements and use the documented no-store/local-history pattern when server-side retention is inappropriate, especially for images or sensitive data.

## Compatibility guard

Provider documentation and SDKs evolve. When producing code:

- verify current official docs;
- distinguish xAI-native SDK fields from OpenAI-compatible client extensions;
- avoid undocumented parameters;
- report untested examples as untested rather than implying execution.

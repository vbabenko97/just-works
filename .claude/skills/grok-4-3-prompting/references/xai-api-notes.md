# xAI API Notes for Grok 4.3

Use this reference only when the user asks for API migration, SDK snippets, tool schemas, structured outputs, or deployment-oriented prompt changes.

## Model facts

- Model name: `grok-4.3`
- Common aliases include `grok-4.3-latest` and `grok-latest`. Prefer the pinned model name for reproducibility.
- Modalities: text and image input, text output.
- Context window: 1,000,000 tokens.
- Capabilities: configurable reasoning, function calling, structured outputs.
- Reasoning levels: `none`, `low`, `medium`, `high`.

## Recommended endpoint style

Prefer the Responses API for new text applications, especially when using stateful conversations, server-side tools, structured outputs, or web search.

```python
from openai import OpenAI
import httpx
import os

client = OpenAI(
    api_key=os.environ["XAI_API_KEY"],
    base_url="https://api.x.ai/v1",
    timeout=httpx.Timeout(3600.0),
)

response = client.responses.create(
    model="grok-4.3",
    reasoning={"effort": "medium"},
    input=[
        {"role": "system", "content": "You are a precise technical assistant."},
        {"role": "user", "content": "Summarize the release note and list migration risks."},
    ],
)
```

## Reasoning

- If unspecified, reasoning defaults to `low`.
- `none` disables reasoning and uses no thinking tokens.
- Use `medium` for complex data analysis and long-context reasoning.
- Use `high` for difficult logic, math, proofs, and tasks where errors are expensive.
- Some parameters cannot be used with reasoning models, including `presencePenalty`, `frequencyPenalty`, and `stop`.
- Encrypted reasoning can be returned by including `reasoning.encrypted_content` and passed back for continuity.

## Stateful storage

The Responses API stores request/response state by default for 30 days. Set `store: false` if the application should not store request/response state on xAI servers.

```python
response = client.responses.create(
    model="grok-4.3",
    store=False,
    input="Classify this ticket as billing, bug, feature, or other: ...",
)
```

## Web search

Use server-side `web_search` for current or external facts. Web Search is available on the Responses API. The older Live Search behavior on Chat Completions is deprecated.

```python
response = client.responses.create(
    model="grok-4.3",
    input="What changed in the latest xAI release notes? Cite sources.",
    tools=[{"type": "web_search"}],
)
```

Useful search filters:

```python
tools=[{
    "type": "web_search",
    "filters": {"allowed_domains": ["docs.x.ai"]},
}]
```

Do not claim current facts unless a search tool or another current source is available.

## Function calling

Define tools with specific names, clear descriptions, and narrow JSON schemas. The model returns the function call, the developer executes it, and the result is sent back using the returned call ID and previous response ID.

```python
tools = [{
    "type": "function",
    "name": "get_temperature",
    "description": "Get current temperature for a city.",
    "parameters": {
        "type": "object",
        "properties": {
            "location": {"type": "string", "description": "City name"},
            "unit": {"type": "string", "enum": ["celsius", "fahrenheit"], "default": "fahrenheit"}
        },
        "required": ["location"]
    },
}]

response = client.responses.create(
    model="grok-4.3",
    input=[{"role": "user", "content": "What is the temperature in San Francisco?"}],
    tools=tools,
)
```

## Structured outputs

Use `response_format` with `json_schema` for exact machine-readable outputs. Use `json_object` only when any valid JSON is sufficient.

Schema notes:

- Supported schema types include `string`, `number`, `integer`, `boolean`, `null`, `enum`, `const`, `array`, `object`, `anyOf`, `oneOf`, single-subschema `allOf`, and non-circular `$ref` / `$defs`.
- `additionalProperties` defaults to `false`; explicitly set it to `true` when extra keys are allowed.
- Optional fields are fields not listed in `required`.
- Nullable fields should use a type array such as `["string", "null"]` or an `anyOf` branch with `null`.
- Enforced string formats include `date`, `time`, `date-time`, `email`, `uuid`, `ipv4`, `ipv6`, and `uri`.
- Avoid unsupported regex features: lookahead, lookbehind, backreferences, word boundaries, Unicode property escapes, inline modifiers, and conditional expressions.

## Migration notes

As of the May 15, 2026 retirement, several older slugs redirect to `grok-4.3`. Explicitly choose `grok-4.3` and the desired reasoning effort instead of relying on redirects.

Redirect behavior to remember:

- Old reasoning model slugs redirect to `grok-4.3` with `low` reasoning effort.
- Old non-reasoning model slugs redirect to `grok-4.3` with `none` reasoning effort.
- `grok-3` redirects to `grok-4.3` with `none` reasoning effort.

Prompt migration checklist:

- Replace old model strings with `grok-4.3`.
- Add explicit `reasoning.effort`.
- Add search/tool policy for current facts.
- Re-test structured output schemas.
- Re-benchmark requests above 200K context tokens because higher context pricing applies.
- Re-test tone and verbosity, especially prompts tuned around older Grok behavior.

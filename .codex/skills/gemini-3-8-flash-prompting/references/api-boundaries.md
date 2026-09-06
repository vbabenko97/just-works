# API boundaries: configuration is not prompt text

Read the model profile first. IDs below resolve in `sources.json`.
Do not run the example requests automatically: they are inert JSON files, not clients.

## Choose a surface before producing code

Google recommends Interactions for new projects; generateContent remains supported.
These are distinct request/response shapes. Interactions keeps parameters such as
`system_instruction`, `tools`, and `generation_config` scoped to each request:
re-send the necessary controls on continuation turns. [S05]

Keep an existing generateContent integration unless migration is requested.
For exact code, verify that surface's current reference and installed SDK version.
Never paste an Interactions payload into generateContent or translate fields by
changing capitalization alone. Do not invent a minimum SDK version from memory.

## Request body examples

`examples/draft-request.json`, `examples/extraction-request.json`, and
`examples/research-request.json` use the Interactions API. All are single-turn,
set `store` to false, and contain only synthetic input. They are examples of
request bodies, not executable calls or proof of API acceptance.

Use `generation_config.thinking_level` for this surface. See S04 for its allowed
values. A prose request for a detailed answer is not equivalent to changing the
thinking setting. Unsupported fields are listed once in the model profile.

## Structured output

Interactions uses `response_format` with `type: "text"`,
`mime_type: "application/json"`, and a `schema`. Google documents a subset of
JSON Schema. [S06]

Specify required fields, nullability, enums, and evidence fields deliberately.
Parse the result and validate both its shape and its factual contents. A valid
JSON object can still contain a wrong date or an unsupported entity. Handle an
empty, blocked, or incomplete response rather than pretending extraction succeeded.
Choose any output cap from the expected workload; a cap can truncate the result.

## State, privacy, and signatures

Interactions stores interactions by default. `store: false` opts out of that
stored interaction resource and prevents using that turn as server-side history
via `previous_interaction_id`. It does not mean on-device inference or a general
zero-retention guarantee. Do not silently enable stored history for private data.
Batch, explicit caching, and automatic Python function calling are among the
surface differences listed in the current overview. [S05]

For permitted stateful continuation, use `previous_interaction_id`.
For client-managed history, preserve thought blocks and applicable tool signatures
unchanged; do not replace signed history with a text summary. In generateContent,
signatures attach to parts, while Interactions represents thoughts as steps.
Thought summaries are not the full private reasoning trace. [S04]

## Function calls are requests for the host to execute

In Interactions, return a `function_result` with the corresponding `name`,
`call_id` from the function-call step, and properly typed result blocks. [S07]

Validate arguments, permissions, and scope before executing. Limit retries and
the total number of tool calls in host code. Report actual failure results,
not fabricated successes. Never execute arbitrary model-supplied code merely
because it appeared in a function argument. Keep instructions separate from
untrusted tool payloads.

For generateContent compatibility, the 3.8 migration checklist also calls for
`name` and `call_id` on function responses and removing model-turn prefills. [S02]

## Grounding

Declare the supported search tool in the request when it is needed and authorized.
Interactions uses `tools: [{"type": "google_search"}]`. Preserve returned source
metadata/citations in the final application rather than manufacturing URLs. [S08]

No tools are installed or enabled by this skill. Never imply that attaching a
local prompting skill switches ChatGPT to Gemini or supplies Google credentials.

# Gemini 3.7 Flash model contract

Source of truth: [Google's Gemini 3.7 Flash developer guide](https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/guides/gemini-3-7-flash) and [model page](https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/gemini/3-7-flash).

| Property | Contract |
| --- | --- |
| Model ID and launch | `gemini-3.7-flash`, GA |
| Input / output | Text, image, audio, and video input; text output |
| Context / output limit | 1,048,576 context tokens; 65,536 maximum output tokens |
| Thinking | `LOW`, `MEDIUM`, `HIGH`; `MEDIUM` is default. `MINIMAL` returns a validation error. |
| Supported capabilities | Structured output, function calling, code execution, computer use (Preview), and Search/Maps grounding (when configured in the selected platform and harness). |

## Migration and request rules

- Replace `thinking_budget` with `thinking_level`.
- Remove `temperature`, `top_k`, and `top_p`: they are deprecated and ignored.
- Remove `frequency_penalty`, `presence_penalty`, and `candidate_count`: they produce API errors.
- A `FunctionResponse` must match the preceding `FunctionCall` exactly by ID, name, and execution count. Treat every tool call as an accounting record; do not merge, omit, duplicate, or rename it.
- History cannot end in a `model` role turn. Prefilled model responses are unsupported. Empty turns are invalid or are dropped, so remove them before sending a request.

## Capability choice

Use structured output to enforce the final response shape. Use function calling for actions that external code executes. Use code execution for bounded computation, Preview computer use for controlled UI interaction, and Search/Maps grounding only when current web or geographic data is necessary. The model supports a capability; the application still needs to expose, authorize, and validate it.

Do not treat the model contract as an agent contract: retries, sandboxing, repository access, tool permissions, checkpoints, and verification are harness responsibilities.

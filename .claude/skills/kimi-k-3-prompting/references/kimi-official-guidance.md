# Kimi official guidance

Checked 2026-07-17. Treat runtime limits as a dated snapshot and verify the linked Kimi API Platform pages before production use.

## Source scope

Kimi's public **Best Practices for Prompts** page is model-agnostic rather than an exclusively K3-authored prompting guide. Combine its prompting principles with the K3 model, thinking-effort, and tool-calling pages below. Do not attribute derived recommendations in this skill to Kimi as direct claims.

Official sources:

- [Best Practices for Prompts](https://platform.kimi.ai/docs/guide/prompt-best-practice)
- [Kimi K3](https://platform.kimi.ai/docs/guide/kimi-k3-quickstart)
- [Thinking Effort](https://platform.kimi.ai/docs/guide/use-thinking-effort)
- [Thinking Mode](https://platform.kimi.ai/docs/guide/use-kimi-k2-thinking-model)
- [Kimi K3 API Tool Calling Best Practices](https://platform.kimi.ai/docs/guide/kimi-k3-tool-calling-best-practice)
- [Use Kimi API for Tool Calls](https://platform.kimi.ai/docs/guide/use-kimi-api-to-complete-tool-calls)

## Prompt practices stated by Kimi

Kimi recommends:

1. Write clear instructions because unspecified needs force the model to guess.
2. Include important details and context to improve relevance.
3. Assign a role when it helps produce a more accurate response.
4. Use delimiters such as XML tags, headings, or triple quotes to distinguish input parts.
5. Define the task's steps explicitly for multi-stage work.
6. Provide examples when they communicate desired behavior or style more efficiently than prose rules.
7. Specify desired output length, favoring paragraphs, sentences, or bullet counts over exact word counts.
8. Ground answers in supplied reference text and define what to say when the answer is absent.
9. Classify requests so only the relevant branch of a large instruction set applies.
10. Summarize or filter prior conversation in long-running applications.
11. Chunk long documents and recursively combine partial summaries; carry forward earlier summaries when later sections depend on them.

## K3 runtime facts stated by Kimi

As of the check date:

- The model identifier is `kimi-k3` and its context window is 1M tokens.
- K3 always reasons. The top-level `reasoning_effort` field currently accepts only `"max"`, which is also the default. Do not send the K2.x `thinking` parameter.
- K3 may return reasoning separately in `reasoning_content`.
- Multi-turn conversations and tool loops must pass the complete prior assistant message back unchanged, including `reasoning_content` and `tool_calls`.
- Strict structured output uses `response_format` with `json_schema` and `strict: true`; parse final `message.content`, not `reasoning_content`.
- Partial Mode continues from a final assistant message marked `partial: true`.
- Automatic context caching requires no cache identifier. Preserve a stable long prefix to make cache hits possible.
- The documented sampling values are fixed: `temperature=1.0`, `top_p=0.95`, `n=1`, `presence_penalty=0`, and `frequency_penalty=0`. Kimi instructs clients to omit them.
- The documented `max_completion_tokens` default is 131,072 and its upper bound is 1,048,576. Diagnose output truncation at the request layer before changing prompt wording.

## Tool-calling practices stated by Kimi

For agents with dozens or hundreds of tools, Kimi recommends:

1. Declare a backend-implemented `search_tools` function plus only a few universally useful tools at conversation start.
2. Tell the model which tool domains or catalog tags it can search.
3. Set `tool_choice: "required"` when first-turn retrieval must occur, then switch to `"auto"`.
4. Inject complete matching tool definitions on demand through a `system` message with a `tools` field.
5. Keep dynamically injected declarations in later request history if the tools should remain available.
6. Preserve the complete assistant message, execute every returned call, and append a result with the matching `tool_call_id` for each one.
7. Decide reasoning effort before the conversation starts. The current K3 setting is only `"max"`; future levels may change latency, cost, and cache behavior.

## Derived working rules

The following are this skill's synthesis, not direct Kimi quotations:

- Use a role to encode relevant expertise, audience, or decision perspective; avoid decorative prestige language.
- Treat the 1M context window as capacity rather than a target. Relevant, well-separated context remains easier to govern and evaluate.
- Replace requests for hidden chain-of-thought with observable checks, evidence, calculations, or verification criteria.
- Diagnose message-state loss, invalid request fields, tool visibility, schema enforcement, and truncation before repeatedly expanding the prompt.
- Keep stable policy and tool rules in the system layer, changing task data in later messages to support clarity and prefix caching.
- Treat strict JSON Schema as a structural constraint, not a grounding or business-policy mechanism.
- Treat `tool_choice: "required"` as “call at least one visible tool.” Restrict the visible set or validate the result when one specific operation is mandatory.
- Scope evidence-absence statements to what was actually searched; top-k retrieval cannot establish absence from an entire corpus.

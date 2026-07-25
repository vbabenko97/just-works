# Grok 4.5 model profile

## Verified capabilities

Use these facts when choosing prompt and API structure:

- Model identifier: `grok-4.5`; aliases include `grok-4.5-latest` and `grok-build-latest`.
- Primary positioning: coding, agentic tasks, engineering, and knowledge work.
- Knowledge cutoff: February 1, 2026.
- Context window: 500,000 tokens. Higher-context pricing begins above the documented 200K threshold.
- Input modalities: text and images. Documented image formats are JPEG and PNG, with a maximum image size of 20 MiB per image.
- Reasoning is always active. Supported effort levels are `low`, `medium`, and `high`; default is `high`.
- `presencePenalty`, `frequencyPenalty`, and `stop` are incompatible with reasoning-model requests.
- Supported APIs include Responses and Chat Completions. xAI documents Responses as the preferred API for text generation.
- Supported capabilities include function calling, structured outputs, web search, X Search, code execution, and collections search.
- Structured outputs can enforce supported JSON Schema shapes.
- Parallel function calling is enabled by default.
- Prompt caching is automatic for matching prefixes, but sticky routing through `prompt_cache_key` or `x-grok-conv-id` is recommended.
- Context compaction can replace long histories with an opaque item that must be passed back unchanged.

## Prompting implications

These are engineering inferences, not verbatim xAI prompting rules:

1. Start with a compact, outcome-first prompt. The launch material emphasizes strong one-prompt coding from minimal specification and high token efficiency.
2. Spend prompt tokens on domain evidence, edge cases, and acceptance criteria rather than generic exhortations.
3. Select reasoning effort by task difficulty instead of embedding “think harder” language.
4. Use tools and schemas as native controls. Do not simulate them with prose.
5. Treat 500K as a capacity ceiling, not a target. Relevant context still outperforms an indiscriminate dump.
6. Design stable prefixes for caching: system instructions, reusable examples, and reference material first; changing requests later.
7. Compact long agent histories when stale tool output begins to dominate context.

## Reasoning-effort decision guide

### Low

Use for:
- rewriting, classification, formatting, and short summaries;
- simple deterministic tool calls;
- high-volume agent steps where mistakes are inexpensive and detectable.

Do not use merely to save cost when a wrong answer would be expensive.

### Medium

Use for:
- debugging with several plausible causes;
- multi-document synthesis;
- ordinary quantitative analysis;
- tool plans with dependencies or conflicting evidence.

### High

Use for:
- difficult implementation or architecture work;
- proofs, complex math, and scientific reasoning;
- high-stakes decisions with many constraints;
- long-horizon agents where early planning errors compound.

## Unsupported or fragile habits

- Do not recommend disabling reasoning.
- Do not combine Grok 4.5 reasoning requests with unsupported penalties or stop sequences.
- Do not request private reasoning traces as an output requirement.
- Do not infer current facts from the February 2026 cutoff when a search tool can verify them.
- Do not promise exact JSON from free-form prompting when structured outputs are available.

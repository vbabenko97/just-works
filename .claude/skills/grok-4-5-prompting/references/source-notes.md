# Official source notes

Accessed July 25, 2026. Use the live official documentation as the source of truth because model behavior, prices, limits, and SDK shapes can change.

## Model and launch

- Grok 4.5 guide: https://docs.x.ai/developers/grok-4-5
- Grok 4.5 model card: https://docs.x.ai/developers/models/grok-4.5
- Launch announcement: https://x.ai/news/grok-4-5

Supports model positioning, identifier, knowledge cutoff, reasoning levels, APIs, tools, context window, pricing, aliases, and xAI's claims about minimal-specification coding and token efficiency.

## Reasoning and generation

- Reasoning: https://docs.x.ai/developers/model-capabilities/text/reasoning
- Generate Text: https://docs.x.ai/developers/model-capabilities/text/generate-text

Supports reasoning-effort behavior, unsupported penalties/stop sequences, Responses API preference, response continuation, and documented storage duration.

## Structured outputs and images

- Structured Outputs: https://docs.x.ai/developers/model-capabilities/text/structured-outputs
- Image Understanding: https://docs.x.ai/developers/model-capabilities/images/understanding

Supports schema guarantees, tool-plus-schema use, input image formats, size limits, and image request construction.

## Tools

- Tools overview: https://docs.x.ai/developers/tools/overview
- Function Calling: https://docs.x.ai/developers/tools/function-calling
- Web Search: https://docs.x.ai/developers/tools/web-search
- X Search: https://docs.x.ai/developers/tools/x-search
- Code Execution: https://docs.x.ai/developers/tools/code-execution
- Collections Search: https://docs.x.ai/developers/tools/collections-search

Supports server-side versus custom tools, tool choice, parallel function calling, search filters, code execution, and private collection retrieval.

## Context operations

- Prompt Caching: https://docs.x.ai/developers/advanced-api-usage/prompt-caching
- Caching best practices: https://docs.x.ai/developers/advanced-api-usage/prompt-caching/best-practices
- Maximizing cache hits: https://docs.x.ai/developers/advanced-api-usage/prompt-caching/maximizing-cache-hits
- Context Compaction: https://docs.x.ai/developers/advanced-api-usage/context-compaction

Supports stable-prefix caching, sticky routing keys, append-only history, cached-token monitoring, and opaque context compaction behavior.

## Evidence boundary

xAI had not published a standalone Grok 4.5 prompt-engineering guide in the official sources reviewed for this build. The skill's prompt architecture and migration advice are therefore practical inferences from official model capabilities, launch examples, and general prompt-engineering principles. Do not present those inferences as direct xAI quotations or mandates.

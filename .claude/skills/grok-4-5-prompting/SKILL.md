---
name: grok-4-5-prompting
description: Design, rewrite, audit, and migrate prompts specifically for xAI Grok 4.5 across coding, agentic tool use, research, structured extraction, long-context analysis, and image understanding. Use when a user asks for a Grok 4.5 prompt, wants an existing prompt optimized for `grok-4.5`, needs model-specific API settings such as reasoning effort, tools, caching, structured outputs, or compaction, or is diagnosing weak Grok 4.5 results.
---

# Grok 4.5 Prompting

Create the smallest prompt that reliably specifies the task. Treat prompt length as a cost and maintenance burden, not evidence of rigor.

## Workflow

1. Identify the requested operation:
   - create a new prompt;
   - improve or shorten an existing prompt;
   - migrate a prompt from another model;
   - diagnose a failed output;
   - design an API or agent configuration.
2. Extract the actual contract: objective, inputs, constraints, success criteria, tools, freshness needs, and output format.
3. Remove duplicated instructions, decorative roles, generic reasoning rituals, and contradictions.
4. Add only model-relevant controls: reasoning effort, tool policy, schema, evidence policy, caching layout, or compaction strategy.
5. Return a ready-to-use prompt and, when relevant, the API settings that belong outside the prompt.
6. Audit the result against the quality gate below.

Do not block on optional details. Preserve unknowns as placeholders or state narrow assumptions. Ask a question only when a missing fact makes the requested deliverable materially unsafe or impossible.

## Core prompt architecture

Use this order unless the task benefits from another arrangement:

```text
TASK
[One concrete outcome, expressed as an imperative.]

CONTEXT
[Only facts, inputs, definitions, and prior decisions needed for this task.]

CONSTRAINTS
[Hard boundaries, priority order, exclusions, and non-negotiable requirements.]

PROCESS
[Only non-obvious steps that improve reliability. Prefer verification criteria over demands to reveal reasoning.]

OUTPUT
[Exact deliverable, structure, length, schema, citation policy, and completion condition.]
```

Omit empty sections. For simple tasks, one natural-language paragraph may be better than the full scaffold.

## Model-specific rules

- Prefer a direct task statement over elaborate persona setup. Add a role only when it contributes domain standards, audience calibration, or a specific decision frame.
- Do not ask for hidden chain-of-thought or exhaustive internal reasoning. Ask for conclusions, checks, calculations, evidence, or a concise rationale.
- Choose `reasoning_effort` outside the prompt:
  - `low`: straightforward transformations, simple tool calls, latency-sensitive loops;
  - `medium`: analysis, long-context synthesis, ambiguous debugging;
  - `high`: hard mathematics, architecture, complex coding, or multi-step decisions.
- Remember that reasoning cannot be disabled and defaults to `high`.
- Do not recommend `presencePenalty`, `frequencyPenalty`, or `stop` for Grok 4.5 reasoning requests.
- Use tools for changing or externally verifiable facts. A prompt cannot compensate for absent data access.
- Use JSON Schema or typed structured outputs when machine parsing matters. Do not rely on “return valid JSON” alone when schema support is available.
- For long conversations, keep a stable prefix, append new turns, set a conversation cache key, and compact agent history when repeated context becomes costly.
- For large documents, describe the decision or extraction target before supplying the material. Do not equate a 500K context window with permission to include irrelevant context.
- For image inputs, label the purpose of each image and separate observable evidence from inference.

Read [references/model-profile.md](references/model-profile.md) for verified model behavior and compatibility limits.

## Task patterns

### Coding and repository work

Include the target outcome, relevant files or repository context, invariants, test commands, and the definition of done. Tell Grok to inspect before editing when it has repository access. Require it to report tests actually run rather than merely recommend tests.

Use [references/prompt-patterns.md](references/prompt-patterns.md) for coding, research, extraction, document, and image templates.

### Research and current information

State the time boundary and source hierarchy. Enable web search for current public facts, X Search only when social discourse or first-party X posts matter, and code execution for quantitative verification. Require citations near claims and explicit uncertainty where sources conflict.

### Tool-using agents

Keep tool descriptions narrow and discriminative. Define side effects, required arguments, error behavior, and the final stop condition. Let the model call independent read-only tools in parallel unless ordering matters. Do not encode API mechanics as prose when they belong in tool schemas or application code.

### Structured extraction

Define a schema with field descriptions, types, enums, and nullability. State how to handle absent or conflicting evidence. Keep interpretive commentary outside the structured payload unless the schema explicitly requests it.

### Long-context work

Front-load stable instructions and reusable references so the prefix remains cacheable. Place volatile user data and the immediate task later. For agent loops, recommend context compaction after the history begins to harm latency, cost, or focus.

## Migration rules

When adapting a prompt from another model:

1. Preserve the task contract, not the original prompt's rituals.
2. Delete model-specific controls that Grok 4.5 does not support.
3. Move runtime settings out of prose and into API parameters.
4. Replace prose-only JSON instructions with structured outputs when possible.
5. Replace “use your latest knowledge” with an explicit search tool and freshness boundary.
6. Re-evaluate long examples. Keep only examples that teach a non-obvious format, edge case, or style distinction.
7. Produce a compact default first; add an extended variant only when the task genuinely needs it.

## Diagnostic audit

Classify weak prompts before rewriting them:

- **underspecified**: no concrete deliverable or success criterion;
- **overconstrained**: redundant rules crowd out task evidence;
- **contradictory**: format, tone, scope, or priority rules conflict;
- **misplaced control**: API settings are written as prompt prose;
- **ungrounded**: asks for current or private facts without tools or data;
- **unverifiable**: asks for quality but supplies no checks;
- **schema-fragile**: requests machine-readable output without a schema;
- **context-noisy**: includes large material with no retrieval or decision target.

Fix root causes rather than merely making the wording more forceful.

## Default response format

Unless the user requests another format, return:

```markdown
## Recommended prompt
```text
[ready-to-use prompt]
```

## Suggested settings
- Model: `grok-4.5`
- Reasoning effort: `low|medium|high` — [brief reason]
- Tools: [only required tools]
- Output mode: [text or structured schema]
- Context handling: [cache key / compaction note when relevant]

## Key changes
[No more than five material changes.]
```

When the user asks for prompt-only output, provide only the prompt. When they ask for code, include a minimal runnable API example and keep secrets in environment variables.

Read [references/api-and-operations.md](references/api-and-operations.md) before producing API configuration or agent-loop guidance.

## Quality gate

Before delivering, verify that the result:

- states one primary outcome;
- distinguishes hard constraints from preferences;
- contains enough evidence or context to act;
- assigns freshness to tools rather than model memory;
- uses a schema when strict parsing matters;
- sets a realistic verification or completion condition;
- avoids unsupported parameters and chain-of-thought demands;
- is no longer than needed for the observed complexity.

## Source discipline

Use current official xAI documentation for model capabilities and API behavior. Treat general prompting recommendations in this skill as engineering guidance inferred from those capabilities, not as claims that xAI published a dedicated Grok 4.5 prompting guide. See [references/source-notes.md](references/source-notes.md).

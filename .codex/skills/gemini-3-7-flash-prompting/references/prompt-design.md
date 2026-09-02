# Prompt design

Gemini 3.7 Flash performs best with direct instructions and native thinking. Keep the prompt compact, make the source of truth explicit, and put the concrete task after its context.

## Required instruction fields

| Field | What to state |
| --- | --- |
| Objective | Desired outcome and user value. |
| Source of truth | Files, documents, APIs, or observations that control when they conflict. |
| Context | Relevant repository state, inputs, and constraints. |
| Scope | In-scope files/systems and explicit exclusions. |
| Constraints | Compatibility, safety, style, and time/cost limits. |
| Acceptance criteria | Observable conditions that make the work acceptable. |
| Tools and approval | Read vs write permissions, prohibited tools, and which side effects need approval. |
| Verification | Tests, checks, manual scenarios, and evidence to return. |
| Output format | Exact response structure, length, and any schema supplied by the API. |
| Failure behavior | What to do when context is missing, a tool fails, or criteria cannot be met. |

## Structure

Put stable identity, constraints, and output requirements first. Put supplied documents, code, and examples next. Put the specific task last. Choose either XML tags or Markdown headings for structural sections; do not mix them in one prompt. Use API structured-output schemas rather than duplicating a schema in prose.

Do not ask for hidden reasoning or phrases such as “think step by step.” Ask instead for a brief plan when useful, explicit decisions, concise evidence, and a final result. This preserves inspectability without demanding chain-of-thought.

## Thinking-level router

| Situation | Level | Prompt posture |
| --- | --- | --- |
| Fast extraction, classification, routine edits | `LOW` | Give explicit constraints and a narrow output. |
| Normal coding, review, standard tool workflows | `MEDIUM` | Default; request a short plan only if it adds value. |
| Ambiguous diagnosis, architecture, migration, multi-step trade-offs | `HIGH` | Ask for assumptions, alternatives, decision, and verification evidence. |

`MINIMAL` is invalid for this model. Do not use `thinking_budget`. Do not depend on sampling controls: remove `temperature`, `top_k`, `top_p`, `frequency_penalty`, `presence_penalty`, and `candidate_count` from migrated requests.

## Tool behavior

State which tools can read, which can write, and when approval is mandatory. For failed reads, try a scoped fallback and report unavailable evidence. For failed writes or destructive actions, stop and report the exact blocker. In multi-turn function calling, return one matching function response per invocation with its original ID, name, and execution count.

Official reference: [Gemini 3.7 Flash developer guide](https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/guides/gemini-3-7-flash).

---
name: gemini-3-7-flash-prompting
description: Use when designing, migrating, reviewing, or evaluating prompts and coding-agent instructions that target GA Gemini 3.7 Flash.
---

# Gemini 3.7 Flash Prompting

Use this skill for prompts, system instructions, and agent harnesses targeting `gemini-3.7-flash`.

Start with the model contract: [model-contract.md](references/model-contract.md). Then shape the prompt with [prompt-design.md](references/prompt-design.md), select or adapt a complete template from [templates.md](references/templates.md), and use [comparison-and-evaluation.md](references/comparison-and-evaluation.md) for model-versus-agent decisions.

## Workflow

1. State the objective, source of truth, scope, constraints, acceptance criteria, tool/approval boundaries, verification, output format, and failure behavior.
2. Put stable instructions first; put supplied context before the specific task. Keep one structural delimiter style per prompt.
3. Choose `thinking_level`: `LOW` for routine extraction or fast loops, `MEDIUM` for normal coding and tool work, `HIGH` for ambiguous planning, migration, or multi-step diagnosis. Do not use `MINIMAL`.
4. Let native reasoning work. Ask for a concise plan, decisions, and evidence—not hidden or step-by-step chain-of-thought.
5. If using tools, define clear read/write boundaries and preserve the exact function-call identifiers and count in responses.
6. Validate the prompt or instruction with `scripts/lint_gemini_prompt.py`, then evaluate representative tasks end to end.

## Guardrails

- Use model ID `gemini-3.7-flash`; it is GA and accepts text, image, audio, and video input with text output.
- Replace `thinking_budget` with `thinking_level` (`LOW`, `MEDIUM`, `HIGH`; default `MEDIUM`).
- Remove `temperature`, `top_k`, and `top_p` because the backend ignores them. Remove `frequency_penalty`, `presence_penalty`, and `candidate_count` because they error.
- Do not prefill model responses or end chat history with a model turn. Empty history turns are invalid or dropped.
- Use structured output for final data shape and function calling for actions. Search/Maps grounding, code execution, and computer use (Preview) are available when the harness exposes them.

## Resources

- [Google: Gemini 3.7 Flash developer guide](https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/guides/gemini-3-7-flash)
- [Google: model capabilities](https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/gemini/3-7-flash)
- [OpenAI: Codex](https://developers.openai.com/codex/)
- [OpenAI: model comparison](https://developers.openai.com/api/docs/models/compare)

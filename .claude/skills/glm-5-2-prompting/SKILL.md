---
name: glm-5-2-prompting
description: create, audit, and refine prompts for z.ai glm-5.2 and related glm coding-agent workflows. use when the user asks for glm-5.2 prompts, prompt templates, system prompts, coding-agent instructions, migration from earlier glm models, long-context/codebase prompting, tool/function-calling prompts, structured-output prompts, api payload suggestions, or parameter recommendations for thinking, reasoning_effort, temperature, top_p, max_tokens, streaming, and tool_stream.
---

# GLM-5.2 Prompting

Use this skill to produce practical prompts and API payload guidance for Z.ai GLM-5.2. Optimize for long-horizon coding, project-scale context, strict engineering constraints, tool/function calling, and structured outputs.

## Core workflow

1. Classify the request as one of these modes:
   - `coding-agent`: implementation, refactor, debugging, tests, migration, repository audit.
   - `long-context-analysis`: codebase, docs, paper, spec, logs, or multi-file reasoning.
   - `tool-agent`: function calling, MCP, web/search/tool orchestration, streaming tool calls.
   - `structured-output`: JSON, schemas, extraction, eval output, deterministic reporting.
   - `general-writing`: product copy, docs, explanations, role-play, lightweight rewriting.
2. Ask only for missing inputs that materially affect the prompt. Prefer making reasonable assumptions over blocking.
3. Produce either a ready-to-paste prompt, an API-ready message/payload block, or a prompt audit with a rewritten version.
4. Include parameter recommendations when they affect model behavior.
5. For complex engineering prompts, include verification and stop conditions, because models do not deserve unchecked agency any more than interns with production credentials do.

## GLM-5.2 defaults and model-specific rules

Use these defaults unless the user or deployment wrapper says otherwise:

- Model: `glm-5.2`.
- Use `thinking: {"type": "enabled"}` for complex coding, architecture, debugging, planning, long-context analysis, or tool-heavy tasks.
- Use `reasoning_effort: "max"` for high-stakes, long-horizon, multi-file, or agentic tasks. Use `"high"` for medium-complexity work where latency/cost matters. Use disabled thinking or `none`/`minimal` only for trivial rewrite/fact/formatting turns.
- Do not tune both `temperature` and `top_p` unless the user explicitly asks. Prefer `temperature` as the main creativity/stability knob.
- For deterministic technical output, use lower temperature such as `0.2` to `0.5`. For exploration, product ideation, or writing variants, use `0.8` to `1.0`.
- Set `max_tokens` deliberately. GLM-5.2 supports very large outputs, but most prompts should request concise artifacts plus appendices rather than asking the model to fill the universe with markdown sediment.
- For streaming tool calls, include `stream: true` and `tool_stream: true`, and instruct the caller to concatenate streamed tool arguments by tool-call index.
- Preserve `reasoning_content` only when the runtime intentionally supports preserved thinking. If enabled, it must be forwarded exactly, unmodified and in order. Otherwise keep `clear_thinking: true` or omit historical reasoning.

See `references/glm-5-2-reference.md` for source-backed capability notes and parameter details.

## Prompt structure for GLM-5.2

Prefer this structure for non-trivial tasks:

```text
Role: <specific expert role, not ornamental cosplay>
Goal: <single outcome>
Context: <relevant repo/product/domain facts>
Inputs: <files, snippets, API contracts, constraints>
Hard constraints:
- <what must not change>
- <security/privacy/performance constraints>
- <scope boundaries>
Process:
1. Inspect and summarize the current state.
2. Produce a plan with impact scope and risks.
3. Execute in bounded steps.
4. Verify with named commands/checks.
5. Report changed files, verification results, remaining risks.
Output format: <exact sections or JSON schema>
Stop conditions: <when to stop and ask, or when to report partial completion>
```

Keep the prompt direct. GLM-5.2 benefits from explicit engineering constraints, evaluation criteria, tool boundaries, and verification commands more than decorative motivational fluff.

## Coding-agent prompt pattern

For coding or refactor prompts, include:

- repository boundaries: allowed files/directories, forbidden files, generated files policy.
- invariants: public APIs, database migrations, runtime behavior, compatibility, dependencies.
- execution rules: inspect before editing, make minimal coherent changes, preserve style, avoid broad rewrites.
- verification: exact lint/test/build commands, fallback verification if tools are unavailable.
- reporting: changed files, rationale, tests run, risks, follow-ups.

Template:

```text
You are a senior software engineer working inside this repository.

Task: <specific change>.

Scope:
- Allowed: <paths/components>.
- Forbidden: <paths/components/actions>.
- Preserve: <APIs, behavior, schemas, CLI args, public contracts>.

Repository rules:
- Follow existing style and architecture.
- Do not add dependencies unless explicitly required.
- Do not commit, push, deploy, or alter secrets.
- Keep the diff minimal and reviewable.

Execution:
1. Inspect the relevant code and summarize the current design.
2. Write a short implementation plan with risks.
3. Apply the change.
4. Run: <commands>.
5. If a command cannot run, explain why and perform the closest static check.

Final response:
- Summary
- Changed files
- Verification results
- Risks or gaps
```

Recommended parameters: `thinking.enabled`, `reasoning_effort=max`, `temperature=0.2-0.5`, `max_tokens` sized to task.

## Long-context prompt pattern

For codebase, docs, papers, or logs, tell the model how to use the context instead of merely dumping it into the token pit and praying.

```text
Read all provided context before answering. Build a compact working map first:
- main entities/components
- dependencies and call chains
- contradictions or stale sections
- source confidence

Then answer the user request using only supported evidence. If evidence is missing, mark it as unknown instead of guessing.

Prioritize:
1. current source files / latest docs
2. tests and execution traces
3. historical notes
4. comments and guesses

Output:
- Answer-first conclusion
- Evidence map
- Detailed reasoning summary
- Risks / unresolved questions
```

Recommended parameters: `thinking.enabled`, `reasoning_effort=max` for hard tasks, `temperature=0.2-0.4`.

## Tool/function-calling prompt pattern

Define tools with narrow descriptions and precise schemas. In the prompt, separate the user's goal from tool-use policy.

```text
Goal: <what the user wants done>.

Tool policy:
- Use tools only when they provide required fresh, private, computational, or external state.
- Do not call write/action tools until prerequisites are satisfied.
- Validate tool arguments before calling.
- After each tool result, interpret the result before deciding the next action.
- If tool output conflicts with prior assumptions, trust the tool output and explain the correction.

Final answer:
- State what was done or found.
- Cite or summarize tool evidence.
- Include unresolved gaps if any.
```

For streaming tool calls, recommend `stream=true` plus `tool_stream=true`, and remind implementers to concatenate partial `function.arguments` chunks by tool-call index.

## Structured-output prompt pattern

Use schema-first prompting. Do not bury the schema after paragraphs of vibes.

```text
Return only valid JSON matching this schema:
<schema>

Rules:
- No markdown fences.
- Use null for unknown values.
- Do not invent missing fields.
- Preserve exact IDs, names, timestamps, and units from the input.
- Validate the JSON mentally before responding.

Input:
<content>
```

Recommended parameters: thinking disabled or enabled depending on extraction complexity; lower temperature; explicitly request no prose around JSON.

## Prompt audit checklist

When auditing a GLM-5.2 prompt, score it against:

- Goal clarity: one concrete outcome, not six loosely related hopes.
- Context quality: includes only relevant context, with source priority when context is large.
- Constraints: explicit non-negotiables, forbidden actions, and scope boundaries.
- Verification: concrete tests/checks and reporting requirements.
- Tool policy: clear when tools may or must be used.
- Output contract: exact sections, schema, or artifact expectations.
- Parameter fit: thinking, reasoning_effort, sampling, streaming, and max_tokens align with task complexity.

Return a concise diagnosis, then a rewritten prompt.

## Reference loading

Load `references/glm-5-2-reference.md` when the task involves API parameters, migration from earlier GLM versions, thinking/preserved-thinking behavior, streaming tool calls, or source-backed claims about GLM-5.2.

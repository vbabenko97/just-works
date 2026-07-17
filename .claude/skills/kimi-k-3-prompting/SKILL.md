---
name: kimi-k-3-prompting
description: Create, migrate, audit, debug, and evaluate prompts and agent instructions for Moonshot AI's Kimi K3. Use when a user needs to write or optimize a K3 system or user prompt, port a prompt from GPT, Claude, or Kimi K2.x, design grounded or long-context workflows, improve K3 tool selection and tool schemas, configure K3 reasoning or structured output, or diagnose instruction-following, hallucination, verbosity, context, tool-call, and multi-turn failures.
---

# Kimi K3 Prompting

## Purpose

Turn the user's goal into explicit, testable Kimi K3 instructions. Apply Kimi's official prompt practices—clear instructions, relevant detail, meaningful roles, delimiters, explicit task stages, examples, output-length guidance, reference grounding, and decomposition—without adding ornamental prompt ceremony.

Treat prompt wording, runtime configuration, tool orchestration, and conversation-state handling as separate control surfaces. Fix the surface that causes the observed failure.

## Workflow

1. Classify the request:
   - **Create**: turn a goal or rough notes into a ready-to-use K3 prompt.
   - **Migrate**: port an existing prompt from another model or Kimi K2.x.
   - **Audit**: find ambiguity, contradictions, missing context, weak grounding, or fragile output rules.
   - **Debug**: distinguish prompt failures from API, tool, context, or harness failures.
   - **Configure**: recommend K3 request fields, message handling, tools, or structured output.
   - **Evaluate**: define representative cases and acceptance criteria.

2. Extract the behavioral contract before rewriting:
   - Required outcome and intended audience.
   - Inputs, trusted references, and relevant context.
   - Domain role or viewpoint only when it changes the answer.
   - Required operations and genuinely sequential stages.
   - Correctness, evidence, safety, permission, and refusal boundaries.
   - Output structure and useful length units.
   - Tool availability, selection rules, and stopping conditions.
   - Success criteria and behavior when evidence is missing.

3. Build the prompt in this order when useful:

```text
Objective
[State the result to produce.]

Context
[Provide only facts needed for this task.]

Instructions
[State requirements; number stages only when order matters.]

Reference material
<reference>
[Place untrusted or source text inside a clear delimiter.]
</reference>

Output
[Specify the required structure and length in sections, paragraphs, sentences, or bullets.]

Fallback
[State what to do when evidence, inputs, or tool results are insufficient.]
```

Do not force every heading into a simple request. Use a direct sentence when it fully specifies the task.

4. Apply Kimi's prompt practices deliberately:
   - Include concrete details that change relevance or correctness.
   - Assign a role when expertise, audience, or evaluation perspective matters; omit decorative status claims.
   - Separate instructions, examples, and source text with XML tags, headings, or triple quotes.
   - Spell out ordered steps for multi-stage transformations; specify outcomes rather than narrating trivial reasoning.
   - Add a small number of examples when style, labeling, or edge-case behavior is difficult to express as rules.
   - Prefer structural length targets such as “three bullets” or “two paragraphs” over exact word counts.
   - For grounded answers, require use of the supplied reference and define an explicit not-found response.
   - Route large scenario-specific instruction sets by first classifying the request instead of activating every rule on every turn.

5. Handle long context intentionally:
   - Treat K3's 1M-token window as capacity, not permission to include irrelevant material.
   - Keep a reusable long prefix stable when automatic prefix caching matters; append changing questions after it.
   - Summarize or filter stale conversation history while preserving requirements, decisions, unresolved questions, and source provenance.
   - Chunk long documents and recursively combine partial summaries when a single-pass answer would dilute coverage.
   - Include earlier-section summaries when later interpretation depends on them.
   - Claim that evidence is absent from the full corpus only after exhaustive coverage. For top-k retrieval, say that evidence is absent from the retrieved excerpts.

6. Separate prompt fixes from K3 runtime fixes:
   - Configure K3 thinking through the top-level `reasoning_effort` field, not K2.x `thinking` fields or prompt phrases such as “enable thinking.”
   - Treat the currently supported value, `reasoning_effort: "max"`, as time-sensitive and verify official documentation before making production recommendations.
   - Use `reasoning_effort` to control supported inference effort, never as a substitute for task policy, ambiguity handling, grounding, or fallback instructions.
   - Preserve the complete assistant message in multi-turn and tool-call loops, including `reasoning_content` and `tool_calls`; retaining only `content` is a harness defect, not a prompt defect.
   - Use strict JSON Schema through `response_format` for parser-bound output instead of relying only on “return valid JSON” in prose. Keep field meaning, evidence rules, and business policy in the behavioral contract because schema enforcement constrains structure, not truth.
   - Use Partial Mode when continuation from an exact prefix is required rather than coercing a prefix with repeated prompt instructions.
   - Omit fixed sampling fields such as `temperature` and `top_p`; do not propose tuning controls that K3 ignores or rejects.

7. Design tool use at the schema and orchestration layers:
   - Give each tool a precise action, use condition, input schema, required fields, and concise parameter descriptions.
   - Keep a small set of core tools visible. For large inventories, expose a `search_tools`-style retrieval tool and load matching definitions on demand.
   - Advertise searchable tool domains in the system prompt so the model knows when retrieval is available.
   - Use `tool_choice: "required"` when a turn must retrieve or act before answering; return to `"auto"` only after the required operation succeeds.
   - Remember that `"required"` forces at least one visible tool call, not a particular correct call. During a mandatory phase, expose only the permitted tool or narrow read-only set, or enforce the expected successful result in application code.
   - Distinguish catalog lookup from evidence retrieval. A successful `search_tools` call does not satisfy a requirement to read private or current data.
   - Return one matching tool result for every `tool_call_id`, then continue until the model produces a final answer or a bounded stopping rule fires.
   - Do not hide authorization, destructive-action, retry, or failure-reporting boundaries inside verbose tool descriptions; state them explicitly in the agent contract.

8. Validate the result:
   - Ensure every instruction has one clear interpretation.
   - Remove contradictions, duplicated requirements, and examples that conflict with rules.
   - Confirm source text cannot be mistaken for instructions.
   - Confirm the fallback behavior prevents unsupported invention.
   - Confirm exact schemas live in API constraints when possible.
   - Confirm task semantics remain in the prompt or application policy rather than being incorrectly delegated to `reasoning_effort`, `response_format`, or `tool_choice`.
   - Confirm the prompt does not attempt to repair missing message state, unavailable tools, invalid parameters, or truncation.
   - Label untested improvements as recommendations, not proven gains.

## Migration rules

### From GPT or Claude

Preserve the behavioral contract, variables, schemas, permissions, evidence rules, and product-specific voice. Rebuild model-specific rituals only when a K3 evaluation demonstrates that they help. Convert hidden-reasoning requests into observable requirements such as checks, evidence, intermediate artifacts, or final-answer verification.

### From Kimi K2.x

Replace K2.x thinking configuration with K3's top-level `reasoning_effort`. Review message serialization because K3 requires the full assistant message to be returned in subsequent requests. Re-test sampling, maximum-output, structured-output, and tool-loading assumptions against current K3 documentation.

### From a monolithic system prompt

Keep global identity, product policy, permissions, and stable tool rules in the system message. Move task data and changing requirements into user messages. Route scenario-specific instructions after classification or load them only when relevant.

## Output patterns

### Create

Return:

1. **Recommended prompt**: ready to paste.
2. **Assumptions**: only unresolved assumptions that materially affect behavior.
3. **Runtime note**: only when K3 request fields, tools, or message handling matter.

### Migrate

Return:

1. **Verdict**: the main compatibility or quality issue.
2. **K3 prompt**: ready to paste, with placeholders preserved.
3. **Material changes**: only consequential additions, removals, and semantic changes.
4. **Runtime migration**: request and harness changes that cannot be solved in prompt text.
5. **Evaluation plan**: include for production prompts or disputed improvements.

### Audit or debug

Order findings by impact. For each finding, identify the exact clause or runtime behavior, explain the likely failure mode, classify it as prompt/runtime/tool/context, and give the smallest correction. Provide a full replacement only when requested or when piecemeal edits would leave contradictions.

### Evaluate

Compare baseline and candidate on representative normal, ambiguous, adversarial, missing-evidence, long-context, and tool-failure cases. Measure:

- Task success and required-field completeness.
- Grounding, factual accuracy, and abstention quality.
- Instruction and permission compliance.
- Tool selection, argument validity, and unnecessary calls.
- Schema validity and downstream parse success.
- Long-context retrieval and cross-section consistency.
- Input, reasoning, and output tokens; latency; and cost.

Prefer the simplest prompt that meets the same quality bar. Do not call a shorter prompt better if it loses required behavior.

## References

Read [references/kimi-official-guidance.md](references/kimi-official-guidance.md) before making claims about official Kimi guidance or current K3 API behavior. Verify the linked official pages when web access is available because K3 launched recently and supported fields can change.

Read [references/prompt-patterns.md](references/prompt-patterns.md) when the user needs reusable templates, migration examples, tool definitions, or an evaluation checklist.

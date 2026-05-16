---
name: grok-4-3-prompting
description: use when creating, reviewing, migrating, or debugging prompts for xai grok 4.3. covers prompt structure, reasoning_effort selection, non-reasoning mode, tool-use steering, web/x search grounding, structured outputs, json schema constraints, function calling, long-context handling, multimodal inputs, api migration from grok 3/grok 4/grok 4 fast/grok code fast, and response style calibration for grok 4.3.
---

# Grok 4.3 Prompting

## Overview

Use this skill to write, revise, or migrate prompts so they fit Grok 4.3 rather than older Grok 3, Grok 4, Grok 4 Fast, or Grok Code Fast assumptions. Prefer concise, explicit instructions, controlled reasoning effort, clear tool-use triggers, and schema-backed outputs when reliability matters.

<context>
Grok 4.3 is a text and image model with a 1,000,000-token context window, configurable reasoning, function calling, structured outputs, and server-side tools such as web search. Design prompts around those capabilities instead of relying on vague "be smart" instructions, because apparently humans still keep trying that and calling it engineering.
</context>

For API-specific details, read `references/xai-api-notes.md` when the user asks about code snippets, SDK parameters, structured outputs, tool schemas, migration, pricing-sensitive behavior, or endpoint choice.

## Core Prompting Principles

### State the operating mode explicitly

Grok 4.3 can run with no reasoning or with low, medium, or high reasoning. Tell the model the task type and the desired depth instead of hiding intent in vibes.

```text
For this task, use careful reasoning because correctness matters more than latency.
Verify assumptions, use tools for current facts, and return only the final answer.
```

```text
This is a latency-sensitive classification task. Use direct pattern matching, avoid extra analysis, and return only the requested label.
```

### Use positive, scoped instructions

Prefer direct commands over negation-only rules.

```text
Better: Return a compact JSON object matching the provided schema.
Worse: Do not be verbose, do not add commentary, do not break JSON.
```

If an instruction applies globally, say so.

```text
Apply these formatting rules to every item in the output, not only to the first example.
```

### Give domain context before constraints

Put the task, audience, and business or technical reason before detailed rules. Grok 4.3 tends to do better when constraints are attached to a purpose.

```xml
<context>
The output will be consumed by an automated triage pipeline. Stable field names and valid JSON matter more than fluent prose.
</context>

<task>
Classify the ticket and extract the required fields.
</task>
```

### Keep examples small and exact

Examples are behavioral anchors. Include only examples that demonstrate the pattern you want repeated. Avoid examples with shortcuts, missing edge cases, or formatting you do not want copied.

## Reasoning Effort Selection

Use `reasoning_effort` as the first lever for quality, latency, and cost tradeoffs.

- `none`: use for routing, extraction, formatting, short classification, and near-instant responses.
- `low`: default for general chat, light agentic workflows, simple tool calling, and normal coding edits.
- `medium`: use for long-context synthesis, data analysis, multi-document reasoning, and nontrivial debugging.
- `high`: use for math, proofs, difficult planning, architecture review, root-cause analysis, and tasks where errors are expensive.

Do not add elaborate "think harder" prose before selecting the right effort. First set the effort, then add task-specific verification steps.

```python
response = client.responses.create(
    model="grok-4.3",
    reasoning={"effort": "high"},
    input=[
        {"role": "system", "content": "You are a careful technical reviewer."},
        {"role": "user", "content": "Find the root cause and propose the smallest safe fix."},
    ],
)
```

When using reasoning, request final-answer discipline:

```text
Think through the problem internally. Do not reveal hidden reasoning. Present the final conclusion, key evidence, and any uncertainty.
```

## Non-Reasoning Mode

Use non-reasoning mode when determinism, latency, or cost matters more than deep inference.

```python
response = client.responses.create(
    model="grok-4.3",
    reasoning={"effort": "none"},
    input="Return exactly one category: billing, bug, feature, or other. Ticket: ...",
)
```

Pair non-reasoning mode with tight output constraints, a small set of labels, or a JSON schema. Do not ask for open-ended strategy while disabling reasoning, unless disappointing output is the goal and we are all pretending to be surprised.

## Tool Use and Grounding

### Define tool triggers in the prompt

Grok 4.3 has strong agentic tool calling, but do not assume it will infer every tool policy from tool names. Specify when tools are mandatory, optional, or forbidden.

```xml
<tool_policy>
Use web_search for current facts, prices, schedules, regulations, release notes, or claims that may have changed.
Use internal retrieval for user-provided files or private knowledge bases.
Do not use tools for arithmetic, style rewriting, or stable background knowledge unless verification is required.
</tool_policy>
```

### Ground current or external claims

Grok has no realtime knowledge unless search tools are enabled. For prompts that need freshness, explicitly require search and citations.

```text
Use web_search before answering. Cite the sources that support release dates, API behavior, pricing, and deprecation status. If the sources disagree, say so.
```

### Make tool schemas strict and narrow

Give each function a specific name, a practical description, and a minimal JSON schema. Avoid large catch-all tools like `do_everything`, humanity's favorite way to make debugging theatrical.

```json
{
  "type": "function",
  "name": "lookup_customer_plan",
  "description": "Return the current subscription plan and billing status for one customer account.",
  "parameters": {
    "type": "object",
    "properties": {
      "customer_id": {"type": "string", "description": "Internal customer account ID."}
    },
    "required": ["customer_id"]
  }
}
```

After a function call, return compact, factual tool results and ask Grok to separate tool evidence from inference.

## Structured Outputs

Use structured outputs whenever the consumer is code, a workflow, a database, an evaluation harness, or a diff-sensitive process.

Prefer `response_format.type = "json_schema"` for exact structure. Use `json_object` only when valid JSON is enough and schema conformance is not required.

```text
Return JSON that matches the schema exactly. Do not include markdown fences, comments, or extra keys.
If a value is unknown, use null rather than inventing it.
```

When writing schemas for Grok 4.3:

- Explicitly set `additionalProperties` when extra keys are allowed. Otherwise assume extra keys are not allowed.
- Mark nullable fields with a type array such as `["string", "null"]` or an `anyOf` branch containing `null`.
- Keep enums small and unambiguous.
- Avoid advanced regex features such as lookahead, lookbehind, backreferences, word boundaries, or Unicode property escapes.
- Validate client-side when strict conformance matters beyond the supported schema subset.

## Long Context and File-Heavy Prompts

Grok 4.3 has a large context window, but dumping everything into the prompt is still not a strategy. It is a landfill with invoices.

For long-context work:

1. Put the objective and success criteria before the documents.
2. Label each source with stable IDs.
3. Tell the model which sources are authoritative if conflicts appear.
4. Require source-grounded claims and quote or cite only the minimal necessary evidence.
5. Ask for an uncertainty section when evidence is missing or conflicting.

```xml
<objective>
Identify the three policy changes that affect onboarding workflows.
</objective>

<source_priority>
1. signed contracts
2. current handbook
3. Slack summaries
</source_priority>

<output_requirements>
For each finding, include the source ID and the exact section title. If no source supports a claim, omit it.
</output_requirements>
```

## Multimodal Inputs

Grok 4.3 supports text and image inputs. For image-heavy prompts, specify the visual task precisely.

```text
Analyze the screenshot for UI defects. Focus on layout, truncation, contrast, and missing states. Ignore product strategy unless visible UI evidence supports it.
```

When order matters, label each image and state how to compare them.

```text
Image A is the current production screen. Image B is the redesign. Compare only visible UI behavior and return regressions first.
```

## Coding and Agentic Workflows

For coding tasks, combine explicit scope, investigation requirements, tool policy, and verification commands.

```xml
<task>
Fix the failing checkout tax calculation test.
</task>

<instructions>
Open the relevant files before making claims.
Make the smallest change that fixes the root cause.
Do not refactor unrelated code.
Run the specific failing test first, then the nearest broader test suite.
Summarize changed files and remaining risks.
</instructions>
```

Use `medium` or `high` reasoning for root-cause debugging, architecture changes, or multi-file edits. Use `low` for small isolated patches. Use `none` only for mechanical code formatting or extraction.

## Style and Verbosity Calibration

Grok 4.3 is strong at instruction following, so make output style measurable:

```text
Write a concise engineering review: one-paragraph summary, then up to five bullets. Each bullet must include impact and recommended action.
```

For warmer or more skeptical tone, specify the behavior, not a personality costume.

```text
Use a direct, evidence-first tone. Challenge unsupported assumptions politely and give the strongest counterargument before the recommendation.
```

For executive outputs:

```text
Lead with the decision. Put caveats after the recommendation. Avoid implementation details unless they change the decision.
```

## API Migration Checklist

When migrating prompts or API calls from older Grok models to Grok 4.3:

- [ ] Set the model to `grok-4.3` unless the user explicitly wants an alias.
- [ ] Choose `reasoning.effort`: `none`, `low`, `medium`, or `high`.
- [ ] Re-test latency and cost, especially for requests above 200K context tokens.
- [ ] Replace old search integrations with Responses API `web_search` when using server-side web search.
- [ ] Use structured outputs or function schemas for machine-consumed results.
- [ ] Remove unsupported reasoning-model parameters such as `presencePenalty`, `frequencyPenalty`, and `stop` when applicable.
- [ ] Re-test prompts that relied on older Grok model tone, reasoning defaults, or deprecated model slugs.
- [ ] Add explicit current-facts tool policy because the base model does not know realtime events without tools.

## Prompt Review Checklist

Before finalizing a Grok 4.3 prompt, check:

- [ ] The task, audience, and success criteria are explicit.
- [ ] Reasoning effort matches task difficulty and latency/cost requirements.
- [ ] Tool-use triggers are defined for current facts, private data, code, and files.
- [ ] Output format is constrained with examples or schema when needed.
- [ ] Long-context inputs have source IDs, priority rules, and evidence requirements.
- [ ] The prompt uses positive instructions and avoids vague style demands.
- [ ] The prompt asks for uncertainty instead of hallucinated completeness.

## Anti-Patterns

- Assuming Grok 4.3 has realtime knowledge without web or X search.
- Using `none` reasoning for complex analysis, then blaming the model for acting like it was told to sprint through fog.
- Relying on deprecated model slugs instead of explicitly selecting `grok-4.3` and reasoning effort.
- Using free-form prose where a schema is required downstream.
- Providing huge context without source labels or conflict-resolution rules.
- Defining broad, ambiguous tools with loose parameters.
- Writing prompts that say "be concise" but then ask for twelve sections, three examples, and a small opera.

## Reference URLs

- xAI Grok 4.3 model docs: https://docs.x.ai/developers/models/grok-4.3
- xAI reasoning docs: https://docs.x.ai/developers/model-capabilities/text/reasoning
- xAI structured outputs docs: https://docs.x.ai/developers/model-capabilities/text/structured-outputs
- xAI function calling docs: https://docs.x.ai/developers/tools/function-calling
- xAI web search docs: https://docs.x.ai/developers/tools/web-search
- xAI migration docs: https://docs.x.ai/developers/migration/models

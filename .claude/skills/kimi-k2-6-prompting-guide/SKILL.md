---
name: kimi-k2-6-prompting-guide
description: Use this skill to create, review, and improve prompts for Moonshot AI Kimi K2.6, especially for long-horizon coding, agentic workflows, tool use, multimodal analysis, long-context document work, and prompt-to-production tasks.
version: 1.0.0
last_updated: 2026-05-16
---

# Kimi K2.6 Prompting Guide Skill

## Purpose

This skill turns vague user requests into high-performing Kimi K2.6 prompts. It is optimized for K2.6's strengths: long-context reasoning, long-horizon coding, multimodal input, software engineering tasks, and agentic workflows with tools.

Use it when the user asks for:

- a Kimi K2.6 prompt
- prompt engineering advice for Kimi/K2.6
- an agent, coding, research, document, UI, spreadsheet, slide, or multimodal workflow prompt for Kimi
- prompt debugging, prompt rewriting, or model-output improvement
- a reusable prompt template or system prompt for Kimi

Do not use it when the user only needs a short generic answer and no Kimi-specific prompting guidance would improve the result.

## Kimi K2.6 operating assumptions

Treat these as model-specific defaults unless the user provides newer official documentation:

- Kimi K2.6 supports text, image, and video input.
- Kimi K2.6 supports dialogue and agent tasks.
- Kimi K2.6 has a 256K context window.
- Kimi K2.6 has thinking enabled by default.
- Kimi K2.6 supports disabling thinking with `thinking: {"type": "disabled"}`.
- Kimi K2.6 is OpenAI API compatible through the Moonshot API endpoint.
- Kimi K2.6 is strongest when prompts make the goal, context, constraints, tools, output format, and success criteria explicit.
- For K2.6/K2.5 API usage, do not manually tune sampling parameters unless the official docs require it. Temperature/top_p/n/penalties are constrained by the API and may error if set incorrectly.
- In thinking mode with tools, `tool_choice` should be `auto` or `none`.
- In multi-step tool-calling workflows, preserve returned assistant messages, including `reasoning_content`, when the API/docs require reasoning continuity.
- Official built-in web search may be incompatible with K2.6/K2.5 thinking mode; disable thinking first when using that built-in web-search path unless newer docs say otherwise.

## Prompting doctrine

Kimi K2.6 performs best when the prompt removes ambiguity before the model spends tokens solving the wrong problem. Humanity has somehow made ambiguity a lifestyle brand, so compensate aggressively.

A strong K2.6 prompt should include:

1. **Role**: who the model should act as.
2. **Task**: the exact thing to produce or decide.
3. **Context**: relevant background, documents, constraints, audience, and definitions.
4. **Inputs**: clearly delimited source material.
5. **Process**: high-level steps the model should follow.
6. **Tool policy**: when tools are allowed, required, or forbidden.
7. **Output contract**: format, length, sections, schema, language, and citation rules.
8. **Quality bar**: acceptance criteria, edge cases, and failure behavior.
9. **Uncertainty policy**: what to do when information is missing or contradictory.
10. **Final audit**: a checklist before answering.

## Prompt construction workflow

### 1. Classify the task

Before writing the prompt, classify it into one primary mode:

- **Simple answer**: direct response, low latency, no deep reasoning needed.
- **Research synthesis**: source-grounded answer, citations, uncertainty handling.
- **Long-context analysis**: many documents, transcripts, logs, legal/technical specs.
- **Coding**: implementation, debugging, refactoring, architecture, tests.
- **Agentic workflow**: multi-step tool use, browsing, file operations, code execution.
- **Multimodal analysis**: image/video/document visual inspection.
- **Creative generation**: writing, design, naming, storytelling, ideation.
- **Prompt rewrite**: improve another prompt for Kimi K2.6.
- **Evaluation**: critique model output, score against rubric, suggest fixes.

### 2. Choose thinking mode

Use **thinking enabled** for:

- complex reasoning
- multi-step planning
- coding/debugging/refactoring
- long-context synthesis
- tool-using agents
- mathematical/logical tasks
- tasks with conflicting constraints

Use **thinking disabled** for:

- short rewriting
- simple classification
- low-latency chat
- formatting-only tasks
- built-in web search flows where thinking mode is incompatible
- tasks where cost and speed matter more than depth

Use **preserved thinking** only for long-running multi-turn API workflows where continuity matters and cost is acceptable. Do not preserve historical reasoning content casually; context windows are large, not infinite, despite what product pages whisper seductively.

### 3. Decide the output contract

For any K2.6 prompt, specify one of these output styles:

- **Brief answer**: concise paragraph or bullets.
- **Structured answer**: headings, sections, bullets.
- **Schema output**: JSON/YAML/table with required fields.
- **Code patch**: files changed, diff, tests, commands.
- **Research memo**: claims, evidence, citations, uncertainty.
- **Decision memo**: options, tradeoffs, recommendation.
- **Artifact spec**: document/slide/sheet/app requirements.

### 4. Add failure behavior

Always tell Kimi what to do when it cannot complete the task:

- State missing information explicitly.
- Make the smallest safe assumption.
- Do not fabricate citations, APIs, filenames, metrics, or command outputs.
- For code, provide a runnable minimal version or explain the blocker.
- For research, separate verified facts from inference.

## Universal Kimi K2.6 prompt template

Use this as the default template.

```text
You are [ROLE], an expert in [DOMAIN].

Goal:
[State the exact outcome.]

Context:
[Relevant background, audience, project constraints, definitions.]

Input:
<<<INPUT
[Paste source material, code, document, image/video description, logs, etc.]
INPUT

Task:
1. [Step 1]
2. [Step 2]
3. [Step 3]

Constraints:
- Language: [language]
- Tone: [tone]
- Length: [target length]
- Do not: [forbidden behaviors]
- Assume: [allowed assumptions]

Tool policy:
- Use tools only when [condition].
- If using tools, cite or summarize tool outputs accurately.
- If a tool fails, report the failure and continue with best-effort reasoning.

Output format:
[Exact headings, JSON schema, Markdown structure, code files, or table format.]

Quality bar:
Before finalizing, check that:
- the answer directly satisfies the goal;
- all constraints are followed;
- uncertainty is explicit;
- no unsupported facts are invented;
- the output is ready to use without extra cleanup.
```

## K2.6 prompt patterns

### Pattern A: Long-horizon coding agent

Use for building, debugging, refactoring, or extending software.

```text
You are a senior software engineer and pragmatic code reviewer.

Goal:
Implement [FEATURE/FIX] in the existing codebase with minimal, safe changes.

Context:
- Tech stack: [stack]
- Runtime: [version]
- Constraints: [offline-friendly, minimal dependencies, compatibility, performance, etc.]
- Current problem: [bug/feature/request]

Repository input:
<<<REPO_CONTEXT
[Relevant file tree, files, logs, tests, issue description]
REPO_CONTEXT

Work plan:
1. Identify the smallest set of files likely affected.
2. Explain the root cause or design gap briefly.
3. Propose the implementation plan.
4. Provide the patch or complete replacement code.
5. Add or update tests.
6. Provide exact commands to validate the result.

Rules:
- Prefer boring, maintainable code over clever code.
- Preserve public APIs unless explicitly asked to change them.
- Use defensive error handling.
- Do not invent unavailable files or packages.
- If information is missing, make the smallest safe assumption and label it.

Output:
## Diagnosis
## Implementation plan
## Patch
## Tests
## Validation commands
## Risk notes
```

### Pattern B: Prompt-to-production UI/app

Use for Kimi Code, website/app generation, or full-stack scaffolding.

```text
You are a senior product engineer and UI systems designer.

Goal:
Create a production-quality [website/app/component] for [audience/use case].

Product requirements:
- Primary user: [user]
- Core workflow: [workflow]
- Must-have features: [features]
- Nice-to-have features: [features]
- Data model: [entities]
- Integrations: [APIs/tools]
- Constraints: [framework, deployment, auth, offline behavior]

Design direction:
- Visual style: [style]
- Layout: [layout]
- Accessibility: keyboard navigable, readable contrast, semantic structure
- Responsive behavior: mobile/tablet/desktop

Engineering rules:
- Keep dependencies minimal.
- Use typed interfaces where applicable.
- Include loading, empty, and error states.
- Add mock data only when real data is unavailable, and label it clearly.
- Separate concerns: UI, state, API/data, validation.

Output:
1. Architecture summary
2. File tree
3. Complete code
4. Setup commands
5. Test/validation checklist
6. Known limitations
```

### Pattern C: Long-context document synthesis

Use for large documents, transcripts, PDFs, contracts, research papers, or logs.

```text
You are a meticulous analyst specializing in long-document synthesis.

Goal:
Analyze the provided material and produce [summary/report/decision memo/extraction].

Source priority:
1. Explicit source text has priority over assumptions.
2. Newer dated material has priority over older material unless contradicted.
3. If sources conflict, report the conflict instead of resolving it silently.

Input documents:
<<<DOC_1 title="[title]" date="[date]"
[content]
DOC_1

<<<DOC_2 title="[title]" date="[date]"
[content]
DOC_2

Tasks:
1. Extract the key claims/facts.
2. Group related points thematically.
3. Identify contradictions, gaps, and stale information.
4. Produce the final output in the requested format.

Output format:
## Executive summary
## Key findings
## Evidence map
## Conflicts / uncertainty
## Practical implications
## Open questions

Rules:
- Do not overfit to the first document.
- Do not bury contradictions.
- Quote only short excerpts when necessary.
- If the answer is not in the source material, write that it is not found.
```

### Pattern D: Research with tools

Use for web/search/database/tool workflows.

```text
You are a research analyst. Your job is to answer using verified sources, not confident folklore wearing a lab coat.

Goal:
[Research question]

Research policy:
- Use tools to verify all facts that may be current, niche, disputed, or source-dependent.
- Prefer primary sources, official docs, peer-reviewed papers, standards, or reputable databases.
- Compare source dates and prioritize the latest authoritative source.
- Cite sources next to the claims they support.
- Separate facts, interpretation, and uncertainty.

Workflow:
1. Decompose the question into subquestions.
2. Search for authoritative sources.
3. Extract only relevant evidence.
4. Cross-check important claims.
5. Produce a concise answer with citations.

Output:
## TL;DR
## Answer
## Evidence
## Caveats
```

### Pattern E: Multimodal image/video analysis

Use for image, video, screenshots, UI, diagrams, charts, medical/technical images, or visual QA.

```text
You are a careful multimodal analyst.

Goal:
Analyze the attached [image/video/screenshot/chart] for [purpose].

Visual task:
- Describe only what is visible.
- Distinguish observation from interpretation.
- Flag uncertainty when visual evidence is insufficient.
- For screenshots/UI: identify layout, hierarchy, issues, and concrete fixes.
- For charts: identify axes, units, trends, outliers, and possible misleading elements.
- For technical/medical visuals: do not diagnose beyond the provided evidence; use cautious language.

Output:
## Observations
## Interpretation
## Issues / risks
## Recommendations
## Uncertainty
```

### Pattern F: Prompt rewrite for Kimi K2.6

Use when the user gives a rough prompt and asks to improve it.

```text
You are an expert prompt engineer for Kimi K2.6.

Goal:
Rewrite the user's prompt so Kimi K2.6 can produce a more accurate, structured, and useful result.

Original prompt:
<<<PROMPT
[original prompt]
PROMPT

Rewrite rules:
- Preserve the user's intent.
- Remove ambiguity.
- Add role, context, task steps, constraints, output format, and quality checklist.
- Make assumptions explicit.
- Add examples only if they improve reliability.
- Do not make the prompt bloated for simple tasks.

Output:
## Improved prompt
[rewritten prompt]

## Why this is better
- [brief explanation]

## Optional variants
- Fast version
- Deep/research version
- Coding/agent version, if relevant
```

### Pattern G: Output evaluation and repair

Use when reviewing Kimi output or another model's output.

```text
You are a strict evaluator and editor.

Goal:
Evaluate the answer against the user's original task and repair it if needed.

Original task:
<<<TASK
[task]
TASK

Model answer:
<<<ANSWER
[answer]
ANSWER

Evaluation rubric:
- Task completion
- Factual accuracy
- Constraint following
- Structure and clarity
- Practical usefulness
- Missing edge cases
- Unsupported claims

Output:
## Score
[0-100]

## Major issues
[issues]

## Repaired answer
[improved answer]

## What changed
[brief notes]
```

## K2.6-specific API guidance for prompt authors

When generating prompts for API use, include the following implementation notes if relevant:

```python
from openai import OpenAI
import os

client = OpenAI(
    api_key=os.environ["MOONSHOT_API_KEY"],
    base_url="https://api.moonshot.ai/v1",
)

response = client.chat.completions.create(
    model="kimi-k2.6",
    messages=[
        {"role": "system", "content": "You are a precise, helpful assistant."},
        {"role": "user", "content": "..."},
    ],
    # For K2.6, thinking is enabled by default.
    # Do not set temperature/top_p unless official docs require it.
    max_tokens=32768,
)
```

To disable thinking for fast/simple tasks:

```python
response = client.chat.completions.create(
    model="kimi-k2.6",
    messages=[{"role": "user", "content": "Rewrite this email in a concise tone: ..."}],
    max_tokens=32768,
    extra_body={"thinking": {"type": "disabled"}},
)
```

For long-running multi-turn workflows that require reasoning continuity:

```python
response = client.chat.completions.create(
    model="kimi-k2.6",
    messages=messages,  # Preserve prior assistant messages as returned by the API.
    stream=True,
    extra_body={"thinking": {"type": "enabled", "keep": "all"}},
)
```

Use preserved thinking sparingly because reasoning content consumes context and token budget.

## Long-context discipline

K2.6 has a large context window, but dumping everything into the prompt still has costs:

- Put a source map at the top.
- State which sources matter most.
- Mark dates and versions.
- Use delimiters for each document.
- Ask for contradiction detection.
- Ask for source-grounded answers only.
- For very large inputs, request staged summaries: chunk summary → cross-chunk synthesis → final answer.

Long-context template:

```text
Source map:
- [A] [title], [date], priority: high, purpose: [why included]
- [B] [title], [date], priority: medium, purpose: [why included]

Rules:
- Use [A] as the primary source unless contradicted by newer evidence.
- Cite source IDs in the answer.
- If a point is inferred, label it as inference.
- If evidence is absent, write "Not found in provided sources."
```

## Tool-use discipline

For agentic prompts:

- State the goal and stopping condition.
- Define allowed tools and when to use each.
- Require a short plan before tool use when useful.
- Require concise progress updates for long tasks.
- Put a maximum iteration budget when loops are possible.
- Preserve tool results accurately.
- Never invent tool outputs.

Tool-agent template:

```text
You may use tools to complete the task.

Allowed tools:
- [tool]: use for [purpose]
- [tool]: use for [purpose]

Rules:
- Use tools only when they materially improve correctness.
- After each tool result, update your working state.
- Stop when [completion criteria].
- If blocked, explain the blocker and provide the best partial result.
- Do not fabricate tool results, filenames, command outputs, citations, or API responses.
```

## Coding prompt audit checklist

Before finalizing a coding prompt, verify that it includes:

- programming language and version
- framework/runtime constraints
- dependency policy
- existing file/context boundaries
- expected behavior
- non-goals
- tests or validation commands
- error handling expectations
- performance/security constraints if relevant
- output format: patch, full files, commands, or explanation

## Research prompt audit checklist

Before finalizing a research prompt, verify that it includes:

- source-quality hierarchy
- recency requirements
- citation format
- scope boundaries
- uncertainty policy
- explicit distinction between fact and inference
- final answer structure

## Multimodal prompt audit checklist

Before finalizing a multimodal prompt, verify that it includes:

- visual target: what to inspect
- purpose of inspection
- output sections
- uncertainty handling
- instruction to separate observation from interpretation
- limits on speculation

## Common failure modes and fixes

### Failure: output is too generic

Fix by adding audience, context, examples, success criteria, and forbidden generic advice.

### Failure: output is too long

Fix by specifying sections, paragraph count, bullet count, or maximum words. Prefer paragraph/bullet limits over exact word counts.

### Failure: model ignores format

Fix by providing a concrete output skeleton or JSON schema.

### Failure: hallucinated facts

Fix by requiring source-grounded claims and explicit "not found" behavior.

### Failure: poor code quality

Fix by requiring minimal dependencies, tests, validation commands, and edge-case handling.

### Failure: agent loops forever

Fix by adding a maximum iteration count, stopping condition, and partial-result behavior.

### Failure: long-context answer misses important details

Fix by adding a source map, priority order, contradiction detection, and staged summarization.

## Final response rule for this skill

When using this skill to answer a user, produce one of these outputs:

1. A ready-to-copy Kimi K2.6 prompt.
2. A revised version of the user's prompt.
3. A prompt template plus usage notes.
4. A diagnosis of why the current prompt fails plus a repaired prompt.

Keep the answer practical. The user wants a prompt that works, not a museum exhibit about prompt theory.

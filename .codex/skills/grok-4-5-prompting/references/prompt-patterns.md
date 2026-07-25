# Grok 4.5 prompt patterns

Use these as adaptable patterns, not mandatory boilerplate.

## 1. Coding change

```text
TASK
Implement [change] in [repository/component].

CONTEXT
- Relevant paths: [paths]
- Existing behavior: [facts]
- Required invariants: [compatibility, security, data constraints]

WORKFLOW
1. Inspect the relevant implementation and tests before editing.
2. Identify the smallest coherent change.
3. Implement it without unrelated refactors.
4. Run [exact checks/tests].
5. Fix failures caused by the change.

OUTPUT
Return:
1. a concise summary of the implementation;
2. files changed and why;
3. tests actually run and their results;
4. unresolved risks or assumptions.
Do not claim a test passed unless you ran it.
```

Recommended effort: `medium` for localized changes, `high` for architecture or ambiguous bugs.

## 2. Current research brief

```text
TASK
Produce a decision-ready brief on [question] as of [date].

EVIDENCE POLICY
- Search the web for current facts.
- Prefer primary sources: official documentation, filings, standards, and research papers.
- Use X Search only for first-party announcements or when social reaction is part of the question.
- Distinguish verified facts, vendor claims, third-party measurements, and inference.
- Cite each material claim near the sentence it supports.

ANALYSIS
Compare [dimensions]. Resolve source conflicts explicitly. Use code execution for calculations that affect the conclusion.

OUTPUT
Provide:
1. conclusion;
2. evidence by decision criterion;
3. uncertainties and missing evidence;
4. recommendation and conditions that would change it.
```

Recommended effort: `medium` by default, `high` for technical or high-consequence decisions.

## 3. Structured extraction

Prefer an API schema plus a short prompt:

```text
Extract the requested fields from the supplied document. Use only information supported by the document. Return null for absent fields. When two passages conflict, set `has_conflict` to true and summarize both values in `conflict_notes`. Do not infer missing identifiers or dates.
```

Example schema intent:

```json
{
  "type": "object",
  "properties": {
    "document_id": {"type": ["string", "null"]},
    "effective_date": {"type": ["string", "null"], "description": "ISO 8601 date"},
    "has_conflict": {"type": "boolean"},
    "conflict_notes": {"type": ["string", "null"]}
  },
  "required": ["document_id", "effective_date", "has_conflict", "conflict_notes"],
  "additionalProperties": false
}
```

Recommended effort: `low` for direct extraction, `medium` for tables, conflicts, or scattered evidence.

## 4. Long-document analysis

```text
TASK
Analyze the attached material to answer: [specific decision or question].

SCOPE
Treat [documents/sections] as authoritative for [topics]. Ignore [irrelevant appendices or duplicated material] unless they contradict the main text.

METHOD
- Build an evidence map from claims to document locations.
- Separate explicit statements from inference.
- Check dates, definitions, and exceptions before concluding.
- Flag material contradictions rather than averaging them away.

OUTPUT
Return [deliverable] with page/section citations and a short list of unresolved gaps.
```

Put reusable reference documents before the changing task in API context to preserve a stable cache prefix.

## 5. Image analysis

```text
TASK
Analyze the supplied images for [goal].

IMAGE ROLES
- Image 1: [primary evidence/reference]
- Images 2-4: [supporting comparison/context]

RULES
Describe visible evidence first. Separate observations from interpretations. Do not infer identity, intent, diagnosis, or hidden attributes from appearance alone. Compare only [specified dimensions].

OUTPUT
Provide [format], noting uncertainty where image quality or viewpoint limits the conclusion.
```

Recommended effort: `low` for description, `medium` for comparison or technical inspection.

## 6. Critique and rewrite

```text
TASK
Rewrite the supplied [artifact] for [audience and purpose].

PRESERVE
- [facts, claims, terminology, voice]

IMPROVE
- [clarity, order, concision, persuasiveness]

CONSTRAINTS
Do not add facts, numbers, commitments, or citations. Resolve ambiguities only when the source text supports one interpretation; otherwise preserve or flag them.

OUTPUT
Return only the revised artifact in [format].
```

Recommended effort: `low` unless the source is technically dense or internally inconsistent.

## 7. Tool-using operational agent

```text
GOAL
[Measurable final state.]

TOOLS
Use available tools to inspect before acting. Read-only calls may run in parallel. Before any irreversible or external side effect, verify [preconditions] and request confirmation unless authorization is already explicit.

STATE
Maintain: completed actions, pending actions, evidence, errors, and retry count. Do not repeat a successful side effect.

STOP CONDITIONS
Stop when [success condition], when [hard blocker], or after [bounded retries].

FINAL RESPONSE
Report actions actually completed, evidence, failures, and the next required decision. Never describe a planned action as completed.
```

Recommended effort: `low` for simple bounded tools, `medium` or `high` for multi-step workflows.

## Compression pattern

When an inherited prompt is bloated, retain only:

```text
[Outcome] using [inputs].
Respect [hard constraints].
Verify [critical checks].
Return [exact deliverable].
```

Then add tools, schema, or examples only where an observed failure justifies them.

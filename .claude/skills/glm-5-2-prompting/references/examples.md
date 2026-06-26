# GLM-5.2 prompt examples

## Example: regenerate a weak coding prompt

User asks: "Improve this prompt for GLM-5.2: fix auth bugs."

Return:

```text
You are a senior backend engineer working in this repository.

Task: Fix the authentication bug described below.

Bug report:
<paste report>

Scope:
- Inspect only auth, session, middleware, and tests unless evidence shows another module is directly involved.
- Preserve public API contracts and database schema.
- Do not add dependencies.
- Do not change unrelated formatting.

Execution:
1. Identify the failing path and summarize root-cause hypotheses.
2. Implement the minimal fix.
3. Add or update tests that reproduce the failure.
4. Run: <test command>, <lint command>.

Final report:
- Root cause
- Changed files
- Tests run and results
- Remaining risks
```

Recommended API settings: thinking enabled, reasoning_effort max, temperature 0.3.

## Example: prompt audit output

```text
Diagnosis:
The prompt has a goal but lacks scope boundaries, invariants, verification commands, and output contract. GLM-5.2 is strong at long coding tasks, but without explicit constraints it may over-edit or skip validation, because apparently models also enjoy creating surprise diff confetti.

Rewritten prompt:
<new prompt>

Recommended parameters:
- thinking: enabled
- reasoning_effort: max
- temperature: 0.3
- max_tokens: 8192
```

## Example: structured output

```text
Extract the release notes into JSON only.

Schema:
{
  "model": "string",
  "release_date": "string|null",
  "capabilities": ["string"],
  "breaking_changes": ["string"],
  "migration_actions": ["string"],
  "unknowns": ["string"]
}

Rules:
- Return valid JSON only, no markdown.
- Use null for unknown values.
- Do not infer dates or features not explicitly present.
- Preserve exact model names.

Input:
<release notes>
```

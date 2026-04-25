# GPT-5.5 Prompt Migration Checklist

Use this when rewriting an existing prompt for GPT-5.5.

## 1. Baseline

- Identify the current model and API surface.
- Preserve current business behavior first.
- Keep existing reasoning and verbosity settings for the first migration pass when possible.
- Collect 5-20 representative inputs before changing the prompt if the user has not provided evals.

## 2. Delete or compress legacy scaffolding

Remove instructions that:

- force a fixed process when only the outcome matters
- repeat the same rule in multiple places
- conflict with other rules
- require verbose explanations of hidden reasoning
- add generic quality advice without operational meaning
- use `always` or `never` for judgment calls

Keep instructions that define hard safety, policy, business, output, or side-effect invariants.

## 3. Add missing contracts

Check whether the prompt clearly defines:

- user-visible goal
- success criteria
- allowed and forbidden side effects
- evidence and citation rules
- tool-use decision rules
- clarification policy
- validation method
- output shape and length
- stop conditions

If a section does not change behavior, omit it.

## 4. Tune model settings

Recommended initial settings:

- `reasoning_effort: none`: extraction, classification, short transforms, routing, simple support triage.
- `reasoning_effort: low`: latency-sensitive flows with some ambiguity or complex instructions.
- `reasoning_effort: medium`: research, multi-document synthesis, code review, planning, and nuanced interpretation.
- `reasoning_effort: high`: long agentic tasks, difficult debugging, high-stakes synthesis, or complex strategy.
- `reasoning_effort: xhigh`: only after evals show clear benefit.

Verbosity:

- `text.verbosity: low`: terse UI replies, labels, compact JSON, status messages.
- `text.verbosity: medium`: default professional responses.
- `text.verbosity: high`: detailed technical, research, or migration analysis.

## 5. Tool-heavy Responses API migration

For streaming or long tool workflows:

- Add a short preamble rule for multi-step tasks if the user experience benefits from visible progress.
- Preserve assistant-item phase values if manually replaying messages.
- Use `phase: "commentary"` for intermediate updates and `phase: "final_answer"` for final answers.
- Do not attach phase metadata to user messages.
- Prefer `previous_response_id` when possible instead of manually reconstructing assistant state.

## 6. Retrieval and grounding migration

Add retrieval budgets before raising reasoning effort.

A good default:

```text
Start with one broad retrieval call. Retrieve again only if the core question remains unanswered, a required fact is missing, a specific artifact must be read, exhaustive coverage is requested, or an important final claim would otherwise be unsupported.
```

Add citation rules close to the output section. Require exact support for claims, not citation confetti sprinkled over vibes.

## 7. Test pass

Run representative prompts and compare:

- correctness
- latency and cost
- tool-call count
- citation precision
- final answer length
- refusal/clarification behavior
- side-effect safety
- formatting stability

Change one thing at a time after the first migration.

## 8. Review output

A good migration summary contains:

- what changed
- what was removed
- why GPT-5.5 needs less process scaffolding
- recommended model settings
- residual risks
- eval cases to run next

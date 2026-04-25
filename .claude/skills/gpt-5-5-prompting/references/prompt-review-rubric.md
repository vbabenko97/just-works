# Prompt Review Rubric for GPT-5.5

Score each category from 1 to 5. Prioritize fixes with the highest risk to correctness, UX, or side-effect safety.

## 1. Outcome clarity

5: The prompt defines the target result and success criteria in observable terms.
3: The goal is understandable but success is partly implied.
1: The prompt mostly describes process or vibes.

## 2. Instruction consistency

5: No conflicting rules; hard invariants are clearly separated from decision rules.
3: Minor tension or duplicated rules.
1: Conflicting instructions force the model to guess which rule wins.

## 3. Tool and evidence rules

5: The prompt defines when to use tools, what evidence is enough, and when to stop.
3: Tool use is mentioned but budgets or stopping rules are vague.
1: The model is likely to over-search, under-search, or invent support.

## 4. Output contract

5: Format, length, tone, citation style, and required fields are clear enough for product use.
3: Output shape is mostly clear but leaves avoidable ambiguity.
1: The output contract is missing or incompatible with the task.

## 5. Ambiguity and clarification behavior

5: The prompt defines when to proceed, ask, abstain, or escalate.
3: Clarification behavior is implied but not operational.
1: The assistant will likely ask unnecessary questions or make risky assumptions.

## 6. Validation and stopping

5: The prompt defines the relevant checks and what counts as done.
3: Some validation is suggested but not tied to task type.
1: No check, no stop rule, no blocker behavior. A classic little machine for wasting tokens.

## 7. GPT-5.5 fit

5: The prompt is outcome-first, compact, and leaves room for efficient solution choice.
3: Mostly compatible but carries some legacy over-specification.
1: Long process-heavy prompt stack with redundant MUSTs and little eval value.

## Review response template

```text
## Verdict
[1-3 sentence summary]

## Highest-risk issues
1. [Severity] [Issue] - [Why it matters] - [Fix]
2. ...

## Suggested rewrite
[Rewritten prompt or targeted sections]

## Starting settings
- reasoning_effort: [none|low|medium|high|xhigh] because ...
- text.verbosity: [low|medium|high] because ...

## Eval cases
- [case]
- [case]
```

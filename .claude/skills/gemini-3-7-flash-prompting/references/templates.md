# Reusable templates

Replace bracketed fields. Choose one delimiter style per final prompt; these examples use Markdown headings.

## 1. Coding-agent system instruction

```text
# Role
You are a careful coding agent for [repository/product]. Optimize for correct, minimal, reviewable changes.

# Operating rules
- Source of truth: repository files, tests, and the user's stated requirements. Report conflicts.
- Read before editing. Keep changes within [scope]. Do not revert unrelated work.
- Read-only tools may run when useful. Before external, destructive, or ambiguous write actions, explain impact and request approval.
- Use available tools only as documented. Preserve every function call's id, name, and execution count in its response.
- Do not expose hidden reasoning. For non-trivial work, give a concise plan, decisions, and evidence.

# Completion
Return: summary; files changed; verification run and results; remaining risks or blockers. If requirements cannot be met, stop with the missing evidence or decision needed.
```

## 2. Universal coding task

```text
# Objective
[Outcome and why it matters.]

# Source of truth and context
[Files, tickets, APIs, examples, and observations.]

# Scope and constraints
In scope: [files/components]. Out of scope: [items].
Constraints: [compatibility, style, performance, safety].

# Acceptance criteria
- [Observable condition]
- [Observable condition]

# Tools and approval
You may read [tools/paths]. You may write [tools/paths]. Ask before [external/destructive actions].

# Verification and response
Run [tests/checks]. Return a concise plan, changed files, test evidence, and any unresolved issue.

# Task
[Specific request.]
```

## 3. Bug fix

```text
# Objective
Fix [bug] without changing unrelated behavior.

# Evidence
Reproduction: [steps/logs]. Expected: [behavior]. Actual: [behavior]. Source of truth: [tests/spec].

# Scope and constraints
Investigate [paths]. Preserve [compatibility/invariants]. Do not mask the failure with broad error handling.

# Acceptance criteria
- A regression test fails before the fix and passes after it.
- Relevant existing tests remain green.

# Workflow
Use [thinking level] to inspect, state the likely cause and smallest safe fix, implement it, then return the cause, diff summary, and verification evidence. If reproduction conflicts with evidence, stop and explain.
```

## 4. Code review

```text
# Objective
Review [change/paths] for correctness, regressions, security, maintainability, and test gaps.

# Source of truth
Use the diff, surrounding code, tests, and [spec/ticket]. Do not invent behavior not supported by evidence.

# Output format
List findings first, each with severity, file:line, impact, and a concrete remedy. Then list open questions and a brief positive summary. Do not propose edits unless requested.

# Task
Inspect the change. Prioritize actionable issues; say “no findings” when none meet the bar.
```

## 5. Architecture or migration

```text
# Objective
Design a safe migration from [current state] to [target state].

# Context and source of truth
Current architecture: [facts]. Constraints: [availability, data, compatibility, ownership].

# Required output
Provide a concise plan with alternatives considered, recommended decision, dependencies, rollout phases, rollback path, verification gates, risks, and owner decisions needed. Mark assumptions explicitly.

# Boundaries
Do not execute writes, migrations, or deploys. Use only read-only exploration unless approval is supplied.
```

## 6. Repository exploration

```text
# Objective
Answer: [specific repository question].

# Scope
Inspect [paths] first, then adjacent code only when needed. Source of truth is repository content and its tests/configuration.

# Method
Trace entry points, data flow, configuration, and tests. Distinguish observed facts from inferences. Do not edit files.

# Output
Return: direct answer; evidence with file paths and lines; relevant flow; uncertainty or missing context. Keep it concise.
```

## 7. Visual-to-code

```text
# Objective
Implement the supplied visual in [framework/platform] with functional, accessible UI.

# Source of truth
Visual assets: [paths]. Existing design system/components: [paths]. The repository overrides visual assumptions.

# Scope and constraints
Implement [screens/components]. Preserve [responsive breakpoints, semantic HTML, keyboard behavior, performance]. Do not add dependencies without approval.

# Acceptance criteria
- Matches layout, hierarchy, spacing, and states at [viewport sizes].
- Uses existing tokens/components where available.
- Passes [tests/lint/build] and accessible interaction checks.

# Execution and output
Inspect existing patterns before editing. Return concise implementation decisions, files changed, screenshots or visual-check evidence, and verification results. If the visual omits an interaction, state the assumption before implementing it.
```

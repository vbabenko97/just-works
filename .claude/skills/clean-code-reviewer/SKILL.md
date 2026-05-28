---
name: clean-code-reviewer
description: analyze, review, and refactor source code using clean code, solid, code smell, maintainability, testability, and readability principles. use when asked to review code quality, simplify code, rename confusing symbols, split large functions or classes, remove duplication, improve tests, create refactoring plans, explain design smells, or produce maintainable production-ready code across programming languages.
---

# Clean Code Reviewer

## Purpose

Apply pragmatic clean-code principles to improve readability, maintainability, testability, and change safety. Prefer small, behavior-preserving improvements over aesthetic churn. Treat automated scan results as hints, not verdicts, because machines still think line count is architecture.

## Core Workflow

1. **Establish intent**
   - Identify whether the user wants review, refactoring, implementation guidance, test improvement, or a full cleanup plan.
   - Preserve public APIs, data contracts, behavior, performance constraints, and framework conventions unless the user explicitly allows breaking changes.
   - If context is incomplete, make conservative assumptions and mark them clearly instead of blocking progress.

2. **Map the code first**
   - Identify responsibilities, entry points, side effects, dependencies, error paths, and tests.
   - When a repository or file tree is available and the user wants review/refactoring, run `scripts/clean_code_scan.py` for a first-pass smell inventory.
   - Use scan output to guide attention, but verify findings manually before recommending changes.

3. **Review by priority**
   - Prioritize correctness and safety before style.
   - Then address names, function shape, duplication, coupling, abstraction boundaries, testability, error handling, and observability.
   - Avoid rewriting working code merely to satisfy a slogan. Small functions are useful when they create clearer names and lower cognitive load; tiny fragmentation is not automatically cleaner.

4. **Produce useful output**
   - For code review: group findings by severity and include exact locations, impact, and concrete fixes.
   - For refactoring: provide a behavior-preserving sequence of small commits or steps.
   - For code generation: emit production-ready code using idioms of the language already present in the project.
   - For explanations: teach the principle through the user’s code, not generic doctrine.

## Review Rubric

Assess code against these dimensions:

- **Intent-revealing names:** names should expose domain meaning, not implementation trivia. Prefer explicit nouns and verbs over abbreviations, flags, and vague containers like `data`, `manager`, or `helper`.
- **Single responsibility:** modules, classes, and functions should group things that change for the same reason and separate things that change for different reasons.
- **Function clarity:** functions should have one dominant level of abstraction, limited branching, clear inputs and outputs, and minimal hidden side effects.
- **Duplication control:** remove duplication when repeated logic encodes the same decision. Do not abstract code that only looks similar but changes for different reasons.
- **Dependency direction:** high-level policy should not depend directly on volatile details. Push I/O, frameworks, vendors, and persistence toward the edges.
- **Error handling:** make failure modes explicit, contextual, and testable. Avoid swallowed exceptions, ambiguous `None`/`null` returns, and broad catch blocks without recovery.
- **Tests as safety rails:** prefer tests that express behavior and edge cases. When refactoring legacy code, add characterization tests before changing structure.
- **Simplicity:** prefer direct code until duplication, volatility, or domain complexity justifies abstraction. Reject speculative extensibility.

## Refactoring Rules

Use these rules when changing code:

1. Preserve behavior first. If behavior is uncertain, add characterization tests or describe the missing safety net.
2. Work in thin slices: rename, extract, move, simplify conditionals, then decouple dependencies.
3. Keep each proposed change independently reviewable.
4. Never mix broad formatting changes with logic changes unless asked.
5. Prefer language-native tooling and existing project conventions over introducing new dependencies.
6. Where tradeoffs exist, explain why the chosen design is better for this codebase now.

## Common Tasks

### Review code

Return:

```markdown
**Summary:** <one paragraph>

**Must fix**
- `<location>`: <problem>. Impact: <why it matters>. Fix: <specific change>.

**Should improve**
- `<location>`: <problem>. Impact: <why it matters>. Fix: <specific change>.

**Nice to have**
- `<location>`: <problem>. Impact: <why it matters>. Fix: <specific change>.
```

### Refactor code

Return the revised code plus a compact change log:

```markdown
**What changed**
- <behavior-preserving change>
- <behavior-preserving change>

**Why it is cleaner**
- <principle tied to the actual code>
```

### Create a cleanup plan

Return a staged plan:

```markdown
**Stage 1: Safety**
<tests, characterization, metrics>

**Stage 2: Local simplification**
<renames, extraction, duplication removal>

**Stage 3: Boundary cleanup**
<dependency inversion, module movement, interfaces>

**Stage 4: Regression guardrails**
<tests, lint rules, CI checks>
```

## Scanner Usage

When a repository or source directory is available and a first-pass inventory is useful, run:

```bash
python scripts/clean_code_scan.py <path>
```

Use JSON output when another script or report needs structured results:

```bash
python scripts/clean_code_scan.py <path> --json
```

The scanner reports heuristic smells such as large files, long functions, excessive parameters, high branching, long lines, TODO/FIXME markers, broad Python exception handlers, print/debug statements, and repeated non-trivial lines. Treat these as triage signals.

## References

- Load `references/review_checklist.md` for a compact review checklist and severity model.
- Load `references/refactoring_playbook.md` for stepwise refactoring recipes and anti-pattern guidance.

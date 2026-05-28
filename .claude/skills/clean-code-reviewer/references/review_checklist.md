# Clean Code Review Checklist

Use this checklist when reviewing code quality. Do not mechanically report every item; report what changes the outcome for maintainability, correctness, or team speed.

## Severity model

- **Must fix:** likely correctness bug, security issue, data-loss risk, unhandled edge case, dangerous dependency, or design that blocks safe change.
- **Should improve:** maintainability or testability issue that will likely cause future defects or slow changes.
- **Nice to have:** readability/style cleanup with low risk and clear benefit.

## Naming

- Names reveal domain intent and units.
- Booleans read naturally in conditionals.
- Avoid vague buckets: `data`, `info`, `payload`, `helper`, `manager`, `processor`, unless domain-specific.
- Avoid misleading names, abbreviations, and names that encode stale implementation details.

## Functions and methods

- One dominant responsibility and abstraction level.
- Inputs and outputs are explicit.
- Side effects are obvious from name or placement.
- Branching is understandable without mental stack overflow, humanity’s least charming sport.
- Parameter lists are short; cohesive groups become value objects/configs when that improves meaning.

## Classes and modules

- Cohesive: fields and methods belong together.
- Split responsibilities that change for different actors or reasons.
- Public surface is smaller than internal implementation.
- Dependencies point inward toward stable policy, not outward toward frameworks or vendors.

## Duplication and abstraction

- Duplicate business rules are consolidated.
- Similar-looking code that changes for different reasons is left separate.
- Abstractions have a name that explains the concept, not just the mechanics.
- No speculative generalization for imagined future requirements.

## Error handling

- Failure modes are explicit and include context.
- Exceptions are not swallowed.
- Broad catches are justified and recover or rethrow with context.
- Sentinel returns (`None`, `null`, empty string, magic status codes) are documented or replaced with clearer result types where idiomatic.

## Tests

- Tests cover behavior, boundaries, and failure cases.
- Tests are deterministic and independent.
- Refactoring risky legacy code starts with characterization tests.
- Test names describe scenario and expected behavior.

## Output guidance

For each finding, include:

1. Location.
2. Problem.
3. Impact.
4. Minimal fix.
5. Tradeoff or risk if relevant.

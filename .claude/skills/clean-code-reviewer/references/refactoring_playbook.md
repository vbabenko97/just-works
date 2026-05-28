# Refactoring Playbook

Use these recipes to propose or perform behavior-preserving cleanups.

## Golden path

1. Add or identify tests around current behavior.
2. Rename confusing symbols before extracting code.
3. Extract pure computations from I/O and framework glue.
4. Split long functions by abstraction level, not arbitrary line count.
5. Replace complex conditionals with named predicates or strategy only when the variation is real.
6. Move duplicated rules into a domain-level function or type.
7. Push persistence, HTTP, CLI, UI, and vendor code behind narrow boundaries.
8. Run tests or explain which tests should be run.

## Common transformations

### Long function

- Identify phases: validate, prepare, execute, persist, respond.
- Extract named helpers only when the helper name explains intent.
- Keep data flow explicit; avoid hiding ten variables in object state just to make a function shorter.

### Large class

- Cluster methods by the fields they use and the actors that request changes.
- Extract collaborators for separate responsibilities.
- Keep orchestration separate from domain decisions.

### Primitive obsession

- Replace loose strings/numbers/dicts with domain types when validation, units, or invariants matter.
- Do not wrap primitives just to look sophisticated; software already has enough costumes.

### Flag arguments

- Split into intention-revealing functions when flags select different behavior.
- Use configuration objects only when multiple options are cohesive and stable.

### Deep nesting

- Use guard clauses for invalid or terminal cases.
- Name compound conditions.
- Extract independent decision logic into pure functions.

### Duplication

- Consolidate only when duplicated code represents the same rule.
- Keep duplication temporarily if abstraction would couple unrelated change reasons.

### Hard-to-test code

- Separate pure logic from I/O.
- Inject time, randomness, network, filesystem, and external clients.
- Prefer narrow protocols/interfaces over global mocks.

## Anti-patterns

- Refactoring without tests or a rollback path.
- Renaming everything in a large diff.
- Hiding complexity behind generic names like `BaseService`, `CommonUtils`, or `AbstractManager`.
- Creating interfaces with one implementation unless a boundary, test seam, or plugin point justifies it.
- Applying SOLID dogmatically to scripts, notebooks, or small one-off tools where directness is cleaner.

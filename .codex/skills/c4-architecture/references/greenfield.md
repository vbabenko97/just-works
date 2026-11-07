# Designing a new system in C4

Use this mode when the system does not exist yet and the input is a brief, requirements, or a design document. The diagrams show a proposal, so the reader must be able to tell what was asked for from what was chosen.

## Workflow

### 1. Extract what is given

From the input, list as **Given**: the people and roles who use the system, the external systems it must read from or write to, hard constraints (latency, freshness, data residency, permissions, vendors already chosen), and any runnable units the input already names. Keep the input's wording for names.

### 2. Draw the System Context

The system is one box. Around it: the Given people and external systems, each relationship labeled with what flows and why. Add an external system only when the input names it or a Given requirement cannot be met without it; mark such an addition `proposed` and say which requirement forces it.

### 3. Propose containers

Decompose the system into runnable units and data stores. For each **Proposed** container record the requirement it serves and the main alternative you rejected, in one line. Prefer fewer containers: split only when parts scale, deploy, fail, or are secured differently.

Check the proposal against every Given constraint and name the container that satisfies each one. A constraint no container satisfies is a gap to report, not something to hide.

For systems built on foundation models, the containers usually include ingestion and indexing, the index itself, the request-serving service with retrieval and prompt assembly, the model provider as an external system, and evaluation or tracing when the design depends on them. Draw permission checks where they are enforced, not as a free-floating box.

### 4. Component view only where it decides something

Draw components for a container when its internal split carries a design decision the reader must review, such as where a permission filter runs or which component holds the approval state for a risky action.

### 5. Hand off

List open decisions with the options and their trade-offs, and the questions for the requirement owners. When the diagrams belong to a design document written with `ml-system-design`, reference them from its Integration and Serving sections instead of repeating the structure in prose.

## Output template

1. **Scope** — the system being designed and its boundary.
2. **Given** — people, external systems, and constraints from the input, quoted or paraphrased with their source.
3. **Element status** — a table: element, level, status (Given or Proposed), reason (the requirement or the design argument), rejected alternative for each Proposed container.
4. **System Context** and **Container view** — two or three sentences each, and the diagram files.
5. **Constraint coverage** — each Given constraint and the element that satisfies it, or "gap".
6. **Open decisions and questions.**
7. **Verification** — syntax check, render, and visual check results, or why they were not run.

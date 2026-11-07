---
name: c4-architecture
description: Use when drawing, documenting, or reviewing software architecture as C4 diagrams (system context, container, component), when reverse engineering an existing repository's architecture from code and infrastructure, or when laying out the structure of a proposed system or a design doc. Writes C4-PlantUML. Not for sequence, state, activity, or deployment diagrams, which plantuml-diagramming covers.
license: MIT
---

# C4 Architecture

The C4 model (Simon Brown, c4model.com) describes one software system at four zoom levels: System Context, Container, Component, and Code. This skill draws the first three with the C4-PlantUML library, either from an existing codebase (reverse engineering) or from requirements (greenfield). A "container" is a deployable or runnable unit, such as a web app, service, database, queue, function, or CLI, not a Docker container.

## Scope

| Question the reader has | Diagram | Where |
|---|---|---|
| Who uses the system and what does it depend on? | System Context | this skill |
| Which runnable units exist and how do they talk? | Container | this skill |
| How is one important container organized inside? | Component | this skill |
| How does one request flow over time? | Sequence | `plantuml-diagramming` |
| What states does one entity go through? | State | `plantuml-diagramming` |
| What runs where (nodes, clusters, regions)? | Deployment | `plantuml-diagramming` |
| Classes and interfaces (C4 Code level) | Class | `plantuml-diagramming`, only on explicit request |

Use the same element names across all these diagrams so the views connect.

Context and Container diagrams answer most questions. Draw a Component diagram only for a container whose inside matters to the reader, and never draw all four levels by default.

## Choose the mode

- **Reverse engineering:** an existing repository or running system is the source of truth. Follow `references/reverse-engineering.md`.
- **Greenfield:** requirements, a brief, or a design doc describe a system that does not exist yet. Follow `references/greenfield.md`.
- **Change to an existing system:** reverse-engineer the current state first, then draw the proposed state as separate diagrams and list what changes between them.

## Before drawing

Write one line each: the audience, the question the diagram answers, the C4 level, and the system boundary (what is inside the system and what is external). One level per diagram.

## Element status

Every element and relationship has a status, and the diagram shows it:

| Mode | Status | Meaning | In the diagram |
|---|---|---|---|
| Reverse engineering | Observed | a repository file shows it | plain |
| Reverse engineering | Inferred | concluded from indirect evidence | `$tags="inferred"` |
| Greenfield | Given | stated in the requirements | plain |
| Greenfield | Proposed | a design choice | `$tags="proposed"` |

The text next to the diagram lists each element and each relationship with its status and evidence: the file path for Observed, the reasoning for Inferred, and the requirement or design reason for Given and Proposed. A relationship is Observed only when a file shows that interaction itself, such as the client call, query, queue publish, or configured endpoint, with its direction and protocol; two elements that both exist in the code do not show that they talk to each other. Tag definitions and syntax are in `references/c4-plantuml.md`.

## Writing the diagram

Follow `references/c4-plantuml.md`. The rules that break things most often:

- Include C4 only from PlantUML's bundled standard library: `!include <C4/C4_Container>`. A URL include fetches code from the network at render time and fails under the sandbox profile used below.
- Every diagram has a `title`, `SHOW_LEGEND()`, and at most about 15 elements; split or group larger views.
- Every element states its name, its technology for containers and components, and a one-line responsibility. Every relationship has a verb phrase and, where known, the protocol.
- `plantuml-diagramming`'s rules on titles, labels, and styling apply.
- Files follow the `diagrammer` naming pattern with the level as the type: `<context>_c4_context_<title>.puml`, `<context>_c4_container_<title>.puml`, `<context>_c4_component_<title>.puml`.

## Verify locally

Render only on this machine. Never paste diagram source into an online editor or a public PlantUML server: architecture diagrams describe private systems.

If `plantuml` is on `PATH`:

1. `PLANTUML_SECURITY_PROFILE=SANDBOX plantuml -checkonly <file>.puml` must exit 0. The sandbox profile refuses network and file includes, so the standard library is the only include that works. If the diagram includes a project file, use `PLANTUML_SECURITY_PROFILE=ALLOWLIST PLANTUML_ALLOWLIST_PATH=<directory of that file>` instead.
2. Render SVG next to the source with the same profile: `plantuml --disable-metadata -tsvg <file>.puml`. Without `--disable-metadata`, PlantUML embeds the full diagram source, comments included, in every SVG and PNG, where `plantuml --extract-source` or any text viewer recovers it.
3. Render a PNG copy to a temporary directory (`plantuml --disable-metadata -tpng -o /tmp/<name> <file>.puml`) and look at it. Check that labels do not overlap, every arrow label can be read, the legend explains each tag used, and no element is left unconnected without a reason.
4. Check that the SVG contains the name of every element in the source. PlantUML writes each word as its own `<text>` node, so a plain `grep` for a multi-word name fails; strip the tags and collapse whitespace first, and include one name that is not in the diagram as a negative control:

   ```bash
   python3 -I -c 'import re,sys; t=" ".join(re.sub(r"<[^>]+>"," ",open(sys.argv[1]).read()).split()); [print(n, n in t) for n in sys.argv[2:]]' diagram.svg "Answer Service" "Vector Index" "Not In Diagram"
   ```

If `plantuml` is not installed, say that the diagrams were not rendered. Installing it is the user's decision.

## Deliverable

The `.puml` files, their rendered SVGs when rendering was possible, and a short text with: scope and system boundary, the element and relationship status lists, assumptions, open questions, and what was verified (syntax, render, visual check).

## Common mistakes

- Drawing libraries, packages, or folders as containers. A container runs or stores data on its own.
- Inventing users or external systems the evidence or requirements do not mention.
- Mixing levels: components inside a context diagram, or external systems broken into containers.
- Unlabeled arrows, or labels such as "uses" that say nothing.
- Presenting an inferred or proposed element as a fact.
- Redrawing a request flow as numbered arrows on a container diagram instead of a sequence diagram.

## Sources

Adapted from `lmammino/c4-codebase-architecture-skill` (MIT, Luciano Mammino; see `LICENSE`): the reverse-engineering workflow, questions, heuristics, and output template. The pre-drawing statement and the check of both source and rendered output follow `magnus919/agent-skills` `c4-diagramming` (MIT). C4 model by Simon Brown (c4model.com); C4-PlantUML from `plantuml-stdlib/C4-PlantUML`, bundled with PlantUML.

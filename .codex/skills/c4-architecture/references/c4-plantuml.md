# C4-PlantUML reference

C4-PlantUML (`plantuml-stdlib/C4-PlantUML`) ships inside PlantUML's standard library, so `!include <C4/...>` works offline. The examples below render with PlantUML 1.2026.9 under `PLANTUML_SECURITY_PROFILE=SANDBOX`.

## Includes

Include the file for the deepest level the diagram uses; each one loads the levels above it.

| Diagram | Include |
|---|---|
| System Context | `!include <C4/C4_Context>` |
| Container | `!include <C4/C4_Container>` |
| Component | `!include <C4/C4_Component>` |

Do not include `https://raw.githubusercontent.com/...` or any other URL.

## Elements

| Macro | Use |
|---|---|
| `Person(alias, "Name", "Description")`, `Person_Ext(...)` | a person or role |
| `System(alias, "Name", "Description")`, `System_Ext(...)`, `SystemDb_Ext(...)` | the system, or one outside the boundary |
| `Container(alias, "Name", "Technology", "Responsibility")` | a runnable unit |
| `ContainerDb(...)`, `ContainerQueue(...)` | a data store, a queue or stream |
| `Container_Ext(...)` | a container owned by someone else, when its detail matters |
| `Component(alias, "Name", "Technology", "Responsibility")`, `ComponentDb(...)` | a part inside one container |
| `System_Boundary(alias, "Name") { ... }`, `Container_Boundary(alias, "Name") { ... }` | the boundary being zoomed into |
| `Rel(from, to, "Verb phrase", "Protocol")` | a relationship; `BiRel` only for a real two-way flow |

Keep descriptions to one line. Layout: `LAYOUT_LEFT_RIGHT()` for wide views, `LAYOUT_TOP_DOWN()` (default) otherwise; add `Rel_R`, `Rel_D`, `Lay_R` hints only when automatic layout is unreadable.

## Status tags

Define the tags once, after the include, and attach them to elements or relationships. The legend then explains them.

```plantuml
AddElementTag("inferred", $borderStyle=DashedLine(), $borderThickness="2", $borderColor="#B8860B", $legendText="inferred: not observed in the repository")
AddElementTag("proposed", $borderStyle=DashedLine(), $borderThickness="2", $borderColor="#2E8B57", $legendText="proposed: design choice, not in the requirements")
AddRelTag("inferred", $lineStyle=DashedLine(), $legendText="inferred relationship")
AddRelTag("proposed", $lineStyle=DashedLine(), $legendText="proposed relationship")
```

Use `$tags="inferred"` or `$tags="proposed"` as the last argument: `ContainerDb(db, "Warehouse", "PostgreSQL", "Product events", $tags="inferred")`, `Rel(api, db, "Reads", "SQL", $tags="inferred")`. Observed and Given elements carry no tag.

## Example: System Context

```plantuml
@startuml
!include <C4/C4_Context>
AddElementTag("proposed", $borderStyle=DashedLine(), $borderThickness="2", $borderColor="#2E8B57", $legendText="proposed: design choice, not in the requirements")
LAYOUT_LEFT_RIGHT()
title Knowledge Assistant - System Context

Person(employee, "Employee", "Asks questions about internal work")
System(assistant, "Knowledge Assistant", "Answers questions with citations from company sources")
System_Ext(slack, "Slack", "Chat workspace")
System_Ext(sources, "Confluence, Jira, Google Drive", "Company knowledge and its permissions")
System_Ext(llm, "Hosted LLM API", "Generates answers")
System_Ext(idp, "Identity Provider", "Employee identity and groups", $tags="proposed")

Rel(employee, slack, "Asks questions in")
Rel(slack, assistant, "Forwards questions to", "Events API")
Rel(employee, assistant, "Asks questions in the web UI", "HTTPS")
Rel(assistant, sources, "Reads content and permissions from", "REST APIs")
Rel(assistant, llm, "Sends prompts with retrieved context to", "HTTPS")
Rel(assistant, idp, "Resolves the employee's groups with", "SCIM / OIDC")
SHOW_LEGEND()
@enduml
```

## Example: Container

```plantuml
@startuml
!include <C4/C4_Container>
AddElementTag("proposed", $borderStyle=DashedLine(), $borderThickness="2", $borderColor="#2E8B57", $legendText="proposed: design choice, not in the requirements")
title Knowledge Assistant - Containers

Person(employee, "Employee", "Asks questions")
System_Ext(slack, "Slack", "Chat workspace")
System_Ext(sources, "Confluence, Jira, Google Drive", "Content and permissions")
System_Ext(llm, "Hosted LLM API", "Generates answers")
System_Ext(idp, "Identity Provider", "Employee identity and groups", $tags="proposed")

System_Boundary(assistant, "Knowledge Assistant") {
  Container(web, "Web UI", "TypeScript, React", "Chat interface with citations")
  Container(api, "Answer Service", "Python", "Retrieves permitted chunks, assembles prompts, cites sources")
  Container(sync, "Source Sync Worker", "Python", "Ingests content and permission changes every few minutes", $tags="proposed")
  ContainerDb(index, "Vector Index", "pgvector", "Chunks with embeddings and access-control lists")
}

Rel(employee, web, "Asks questions in", "HTTPS")
Rel(slack, api, "Forwards questions to", "Events API")
Rel(web, api, "Sends questions to", "JSON/HTTPS")
Rel(api, idp, "Resolves the employee's groups with", "SCIM / OIDC")
Rel(api, index, "Searches, filtered by the employee's groups", "SQL")
Rel(api, llm, "Sends prompts to", "HTTPS")
Rel(sync, sources, "Polls content and permissions from", "REST APIs")
Rel(sync, index, "Writes chunks and access-control lists to", "SQL")
SHOW_LEGEND()
@enduml
```

## Example: Component

Zoom into one container with `Container_Boundary` and keep its neighbours as plain containers or external systems:

```plantuml
@startuml
!include <C4/C4_Component>
title Answer Service - Components

ContainerDb(index, "Vector Index", "pgvector", "Chunks and access-control lists")
System_Ext(llm, "Hosted LLM API", "Generates answers")

Container_Boundary(api, "Answer Service") {
  Component(authz, "Permission Filter", "Python", "Turns the employee's groups into a search filter")
  Component(retriever, "Retriever", "Python", "Hybrid search and reranking")
  Component(prompt, "Prompt Builder", "Python", "Assembles context and citation markers")
}

Rel(retriever, authz, "Gets the filter from")
Rel(retriever, index, "Searches", "SQL")
Rel(prompt, retriever, "Gets ranked chunks from")
Rel(prompt, llm, "Sends prompts to", "HTTPS")
SHOW_LEGEND()
@enduml
```

## Local commands

```bash
PLANTUML_SECURITY_PROFILE=SANDBOX plantuml -checkonly diagrams/kb_c4_container_overview.puml
PLANTUML_SECURITY_PROFILE=SANDBOX plantuml -tsvg diagrams/kb_c4_container_overview.puml
PLANTUML_SECURITY_PROFILE=SANDBOX plantuml -tpng -o /tmp/kb-diagrams diagrams/kb_c4_container_overview.puml
```

`-checkonly` exits 0 when the source parses and 200 on an error, including a refused include. `-o` with an absolute path writes outside the project. PlantUML needs Java and, for most C4 layouts, Graphviz; the Homebrew `plantuml` formula installs both.

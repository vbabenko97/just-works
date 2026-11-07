# Reverse engineering a codebase into C4

Adapted from `lmammino/c4-codebase-architecture-skill` (MIT, Luciano Mammino). The output format is C4-PlantUML instead of Mermaid, and each element carries the status and evidence that `SKILL.md` requires.

The goal is the clearest architecture view the repository supports, at the right level of detail, with every claim traceable to a file or labeled as an inference. A repository does not have to fill all four C4 levels.

## Principles

1. **Evidence first.** Base each claim on something in the repository: entrypoints, routing, package manifests, deployment descriptors, infrastructure code, environment variables, API clients and SDK calls, queue or topic usage, persistence code, integration tests.
2. **Separate facts from inference.** Example: *Observed* — the repository contains a React app, an Express API, and Terraform for an RDS instance. *Inferred* — the browser frontend probably calls the API, which stores data in PostgreSQL.
3. **Ask only high-value questions,** in one batch, and only about what the code cannot show.
4. **Respect the boundary.** State whether the scope is this repository only, one service in a larger platform, a monorepo with several systems, or a partial implementation.
5. **Stop at the useful level.** Usually one System Context view, one Container view, and a Component view only for the most important container.

## Workflow

### 1. Establish scope

Read the repository name, README, top-level folders, workspace or monorepo layout, manifests, build files, and infrastructure, deployment, and docs folders. Decide what the repository is (a product, a service, a library, infrastructure, a plugin) and what is inside and outside scope. If scope is ambiguous and a user can answer, ask.

### 2. Find the runtime building blocks

List what runs or stores data on its own: web frontends, backend services, CLIs, serverless functions, workers and scheduled jobs, databases, caches, queues and streams, search engines, storage buckets, and third-party services. Record the file that shows each one.

### 3. Map interactions

Find HTTP clients and servers, SDK calls, message publishing and consuming, database access, authentication middleware, event handlers, scheduler configuration, and file or object storage access. Capture direction, protocol where visible, synchronous or asynchronous, and trust boundaries.

### 4. Identify actors and external systems

Code shows external systems (auth providers, payments, email, cloud services, partner APIs, identity, observability) more reliably than it shows people. Infer actors cautiously from UI labels, route names, role checks, and documentation. An actor with no evidence is a question for the user, not an element.

### 5. Break down important containers

For the one or two containers that matter most, identify components by responsibility (controllers, services, repositories, adapters, handlers, middleware, domain modules), not by listing folders.

### 6. Produce the documentation

Write the diagrams per `c4-plantuml.md` and the text per the output template below. If no user can answer the open questions, finish a best-effort draft with the assumptions marked; do not stop.

## Questions worth asking

Batch three to seven when the answers change the diagrams.

- **Scope:** Is this repository the whole system or one part of a platform? Should adjacent systems it depends on be shown? Who is the audience: new engineers, stakeholders, or operations?
- **Actors:** Who are the primary users or operators? Are there distinct roles (customer, admin, support, partner)?
- **Runtime:** Are the deployable units in the repository the real production units? Are there managed databases, queues, or gateways not represented in code? Monolith, microservices, serverless, or hybrid?
- **Boundary:** What belongs outside the system boundary? Are shared platform services owned by another team better shown as external systems?
- **Components:** Which container deserves a component view? Domain-oriented or technical-layer breakdown?

## Heuristics by codebase shape

- **Monolith:** context with users and integrations; containers are the app or API, the database, and perhaps a worker; components are controllers, services, repositories, and integrations.
- **Monorepo:** decide which packages deploy independently; libraries are not containers; show a shared library only when it explains the architecture.
- **Serverless:** group functions into meaningful containers ("API", "async worker", "scheduled processor") instead of one box per function; show gateways, queues, buckets, event buses, and data stores.
- **Microservices:** one container per independently deployable service; trace service-to-service calls; do not mistake shared packages for services.
- **Library, SDK, or plugin:** the repository may not be a complete runtime system. Say so, show the host that runs it as the system or as an external system, and draw the parts the host loads (for example skills, hooks, or a server process it starts) as containers only when they run separately.

## Infrastructure and managed services

Show at container level when they shape the architecture: primary databases, queues, event buses, object storage in a core workflow, caches, search engines, identity providers, major external APIs. Leave out subnets, security groups, IAM roles, autoscaling policies, log groups, and CI runners unless the question is about them. If the team owns and reasons about a resource as part of the application, it may sit inside the boundary; if another team or a vendor provides it, show it as external.

## Output template

1. **Scope** — what is documented and the boundary. Example: "This covers the architecture implied by the current repository: the backend service and its deployment configuration, not the full end-user platform."
2. **Observations** — the strongest concrete signals, each with a path. Example: "Node.js API in `apps/api`; Terraform for RDS and SQS in `infra/`."
3. **Element status** — a table: element, level, status (Observed or Inferred), evidence (path, or the reasoning for an inference).
4. **System Context** — two or three sentences and the diagram file.
5. **Container view** — two or three sentences and the diagram file.
6. **Component view** — only for the container that needs it.
7. **Open questions** — what the code could not settle.
8. **Verification** — syntax check, render, and visual check results, or why they were not run.

## Quality bar

A good result is faithful to the codebase, explicit about uncertainty, readable by its audience, and focused on runtime structure. A poor result confuses packages with deployable units, invents actors, documents trivial detail, has unlabeled arrows, or blurs facts and guesses.

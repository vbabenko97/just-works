---
description: Update canonical project documentation from implementation and approved requirements
---

# Project documentation

Update the documentation needed for the requested change. Treat `docs/`, the root README, architecture notes, and existing feature documentation as canonical locations when they already cover the subject. Preserve their structure and links. Do not create a second page for a subject an existing page or section can cover.

This workflow is for requested documentation work. Do not create routine session reports, status reports, or an automatic documentation set.

## 1. Establish scope and sources

Read the request, existing relevant documentation, the affected implementation, configuration, runtime interfaces, relevant passing checks when applicable and available, and approved requirements or decisions that define intended behavior. Check repository guidance and local conventions first.

Classify each statement before writing:

| Statement | Source of truth | Documentation treatment |
|---|---|---|
| Current behavior | Inspected implementation, configuration, and runtime or deployed interfaces; relevant passing checks corroborate when applicable and available | State it as current behavior. Do not infer implementation from test expectations alone. |
| Agreed requirement or proposal | Approved requirement, decision, or explicit user instruction | Label it as intended, planned, or proposed when it is not implemented. |
| Rationale or business rule | Approved product, design, policy, or user source | Cite or attribute the source. Do not infer it from implementation. |

Code confirms implementation; it does not establish product intent. If code and an approved requirement disagree, report the contradiction with both sources. Do not rewrite the requirement to make a bug look intentional. Ask the user only when the contradiction or unknown scope changes the document's result. Routine edits within the requested documentation scope are authorized and need no per-file approval.

If the request names a feature, behavior, business rule, interface, or document, use that as the scope. If it asks for an initial project overview and no more specific scope, use the existing overview locations. Where no overview exists, create only the useful baseline pages: mission or README purpose, technical stack, and architecture. Do not blindly create all three when existing documentation already supplies the information.

Use the available question tool for a material unresolved decision when appropriate. Otherwise ask in plain text.

## 2. Gather evidence

Explore only as broadly as the scope requires. Use targeted repository searches and read the relevant files. Use read-only Explore agents when independent investigations will improve coverage or speed; do not require a fixed number of agents or parallel work for a small request.

Record repository evidence with source paths and line numbers. For approved non-file sources, record a precise source identifier, URL, or explicit user decision. Ignore generated dependencies and build outputs unless they are the documented interface.

For a feature or behavior document, inspect enough to cover:

- purpose and intended behavior, if sourced;
- entry points, inputs, outputs, and user-visible flow;
- limits, exceptions, invariants, errors, and verification behavior;
- configuration, dependencies, and operational constraints when relevant.

Describe only items supported by the sources. Omit unknown details or mark them as open questions. Do not fill gaps with plausible explanations.

## 3. Reconcile requested coverage

When the user asks for all-feature, complete, or equivalent coverage, first build a concrete capability list from the relevant interfaces, commands, routes, configuration, user-facing flows, and approved requirements. Reconcile each capability against its canonical document and section.

Use a coverage table in the working report:

| Capability | Evidence | Canonical document and section | Result |
|---|---|---|---|
| [capability] | [path:line or precise non-file source] | [document#section] | covered, update needed, or gap |

A valid link is not evidence that a capability is documented. A capability may share a section with related capabilities; completeness does not require a page per capability. Update the relevant canonical documentation and identify genuine gaps.

## 4. Write

Make the smallest coherent update in the existing location and style. Add a new document only when no canonical document can reasonably hold the content. Use clear status labels for current, intended, planned, and proposed content. Keep implementation facts and approved requirements distinguishable.

If existing documentation is accurate and complete for the requested scope, leave it unchanged and report no change.

For an initial overview, a useful baseline usually contains:

- purpose and audience, where evidence exists;
- technologies and their roles;
- system structure, entry points, dependencies, and data flow.

Adapt these topics to existing document structure. They are not a mandatory three-file template. For scoped documentation, add the sections that explain the requested behavior, including constraints and failures when applicable.

Use Open Knowledge Format (OKF) only when it is already adopted by the project, consumed by a project tool, or explicitly requested. Follow its agreed version, profile, and directory scope. Do not impose a new schema, files, or process.

## 5. Verify and report

Read the edited documents back. Check that each factual implementation claim traces to inspected code, configuration, or an interface; relevant passing checks corroborate it when applicable and available; each intent claim traces to an approved repository source or precise non-file source; status labels match the evidence; links and headings resolve; and the requested coverage table has no unreported gaps.

Report changed documents, evidence-backed coverage or gaps, contradictions, and checks run. Do not generate a routine session report.

## Rules

- Do not invent behavior, rationale, users, or future plans.
- Document related behavior changes in their canonical documentation when the requested change affects them.
- Preserve existing documentation locations and structure unless they prevent a coherent update.
- Use direct, factual prose. Do not add marketing language or filler.

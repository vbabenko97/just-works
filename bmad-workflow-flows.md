# BMAD Workflow Flows

Three practical paths through BMad Method workflows by task complexity.

> **Note:** BMAD formally defines two official tracks: Quick Flow and the full 4-phase method. The "Medium" path below is a practical composition built from official workflows for work that needs context or research but not the full PRD/architecture pipeline.
>
> **Invocation:** Canonical BMAD usage is the bare skill name, for example `bmad-create-prd`. Some platforms also accept `/bmad-create-prd` or `$bmad-create-prd`. Use a fresh chat for each workflow.

---

## Fast — Quick Flow

For small changes, bug fixes, utilities, or well-understood brownfield work. Skips the formal planning phases, but still does lightweight planning inside the workflow.


| Step         | Skill            | Typical agent                         |
| ------------ | ---------------- | ------------------------------------- |
| 1. Quick Dev | `bmad-quick-dev` | Amelia (Developer) via `bmad-agent-dev` |


---

## Medium — Research + Quick Flow

For work that needs investigation or codebase context, but not the full PRD/architecture pipeline. This is not an official BMAD track; it is a practical composition of official workflows.


| Step                     | Required | Skill                                                                    | Typical agent |
| ------------------------ | -------- | ------------------------------------------------------------------------ | ------------- |
| 1. Existing-project prep | optional | `bmad-document-project` or `bmad-generate-project-context`               | Mary (Analyst) |
| 2. Research              | optional | `bmad-market-research`, `bmad-domain-research`, or `bmad-technical-research` | Mary (Analyst) |
| 3. Quick Dev             | yes      | `bmad-quick-dev`                                                         | Amelia (Developer) |
| 4. Code Review           | optional | `bmad-code-review`                                                       | Amelia (Developer) |


---

## Full — Complete 4-Phase Method

For new products, major features, architectural changes, or multi-epic work. **Bold** steps are required in the current BMAD workflow map; the rest are optional support or validation workflows.


| Phase            | Step                              | Required     | Skill                                                | Typical agent |
| ---------------- | --------------------------------- | ------------ | ---------------------------------------------------- | ------------- |
| 1-analysis       | Brainstorm Project                | optional     | `bmad-brainstorming`                                 | Mary (Analyst) |
| 1-analysis       | Market Research                   | optional     | `bmad-market-research`                               | Mary (Analyst) |
| 1-analysis       | Domain Research                   | optional     | `bmad-domain-research`                               | Mary (Analyst) |
| 1-analysis       | Technical Research                | optional     | `bmad-technical-research`                            | Mary (Analyst) |
| 1-analysis       | Product Brief                     | optional     | `bmad-product-brief`                                 | Mary (Analyst) |
| 1-analysis       | PRFAQ                             | optional     | `bmad-prfaq`                                         | Mary (Analyst) |
| 2-planning       | **Create PRD**                    | **required** | `bmad-create-prd`                                    | John (PM) |
| 2-planning       | Validate PRD                      | optional     | `bmad-validate-prd`                                  | John (PM) |
| 2-planning       | Edit PRD                          | optional     | `bmad-edit-prd`                                      | John (PM) |
| 2-planning       | Create UX Design                  | optional     | `bmad-create-ux-design`                              | Sally (UX Designer) |
| 3-solutioning    | **Create Architecture**           | **required** | `bmad-create-architecture`                           | Winston (Architect) |
| 3-solutioning    | **Create Epics and Stories**      | **required** | `bmad-create-epics-and-stories`                      | John (PM) |
| 3-solutioning    | **Check Implementation Readiness** | **required** | `bmad-check-implementation-readiness`                | Winston (Architect) |
| 4-implementation | **Sprint Planning**               | **required** | `bmad-sprint-planning`                               | Amelia (Developer) |
| 4-implementation | Sprint Status                     | optional     | `bmad-sprint-status`                                 | Amelia (Developer) |
| 4-implementation | **Create Story**                  | **required** | `bmad-create-story`                                  | Amelia (Developer) |
| 4-implementation | Validate Story                    | optional     | `bmad-create-story` (validate action / `VS`)         | Amelia (Developer) |
| 4-implementation | **Dev Story**                     | **required** | `bmad-dev-story`                                     | Amelia (Developer) |
| 4-implementation | QA Automation Test                | optional     | `bmad-qa-generate-e2e-tests`                         | Amelia (Developer) |
| 4-implementation | Code Review                       | optional     | `bmad-code-review`                                   | Amelia (Developer) |
| 4-implementation | Correct Course                    | optional     | `bmad-correct-course`                                | John (PM) |
| 4-implementation | Retrospective                     | optional     | `bmad-retrospective`                                 | Amelia (Developer) |


**Story cycle:** `CS` → (`VS`) → `DS` → (`QA`) → (`CR`) → back to `DS` if fixes are needed, otherwise next `CS` or `ER` at epic end.

**Tip:** For validation workflows such as Validate PRD, Check Implementation Readiness, and Code Review, BMAD recommends independent verification when possible.

---

## Anytime Tools

Available regardless of phase or useful as support around the main flows:


| Name                     | Skill / invocation                                           | Typical agent / type |
| ------------------------ | ------------------------------------------------------------ | -------------------- |
| Help                     | `bmad-help`                                                  | core tool |
| Document Project         | `bmad-document-project`                                      | Mary (Analyst) |
| Generate Project Context | `bmad-generate-project-context`                              | Mary (Analyst) |
| Correct Course           | `bmad-correct-course`                                        | John (PM) |
| Write Document           | `bmad-agent-tech-writer`, then `WD [request]`                | Paige (Tech Writer) |
| Validate Document        | `bmad-agent-tech-writer`, then `VD [doc]`                    | Paige (Tech Writer) |
| Mermaid Generate         | `bmad-agent-tech-writer`, then `MG [description]`            | Paige (Tech Writer) |
| Adversarial Review       | `bmad-review-adversarial-general`                            | core tool |
| Edge Case Hunter         | `bmad-review-edge-case-hunter`                               | core tool |
| Advanced Elicitation     | `bmad-advanced-elicitation`                                  | core tool |


---

## BMM Agent Reference

Workflow skills can be run directly. Load the agent skills only when you want the persona and menu triggers to stay active across turns.

| Name    | Agent skill                | Role |
| ------- | -------------------------- | ---- |
| Mary    | `bmad-agent-analyst`       | Brainstorming, research, product brief / PRFAQ, and project context work. |
| John    | `bmad-agent-pm`            | PRD creation, epics and stories, and course correction. |
| Sally   | `bmad-agent-ux-designer`   | UX discovery and experience design. |
| Winston | `bmad-agent-architect`     | Architecture decisions and implementation-readiness checks. |
| Amelia  | `bmad-agent-dev`           | Quick Dev, sprint planning, story execution, QA generation, code review, and retrospective. |
| Paige   | `bmad-agent-tech-writer`   | Documentation, document validation, standards updates, and Mermaid diagrams. |

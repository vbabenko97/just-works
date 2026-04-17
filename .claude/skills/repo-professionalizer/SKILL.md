---
name: repo-professionalizer
description: clean, reorganize, and professionalize source code repositories into a reviewable, production-grade structure with clear ownership, docs, testing, and governance. use when a user asks to clean up a repo, restructure folders, reduce top-level clutter, standardize documentation and configuration, prepare a project for handoff or open source, or make a codebase feel like it is maintained by a top-tier engineering team.
---

# Repo Professionalizer

## Overview

Turn a messy repository into a cleaner, more legible, lower-risk codebase without recommending churn for its own sake. Start from evidence in the actual repository, classify the repository archetype, then produce a staged restructuring plan that preserves behavior, improves navigability, and raises engineering hygiene.

## Operating principle

Optimize for maintainability, reviewability, and safe change management.

- Preserve behavior before aesthetics.
- Prefer small, reviewable migrations over one giant rewrite.
- Separate source, tests, scripts, docs, config, generated artifacts, and temporary files.
- Minimize top-level clutter.
- Keep naming, ownership, and contribution paths obvious.
- Treat documentation, CI, security, and release hygiene as part of repo professionalism, not optional decoration.

## Workflow

Follow this sequence.

1. Determine the input mode.
   - **Filesystem available**: run `scripts/repo_inventory.py` on the repository root.
   - **Archive uploaded**: unpack if needed, then run `scripts/repo_inventory.py`.
   - **Only a pasted tree or file list is available**: analyze the provided structure directly and state that findings are lower confidence.

2. Classify the repository before proposing structure.
   Choose the closest archetype:
   - application or service
   - reusable library or SDK
   - monorepo
   - ML or research repo
   - infrastructure or platform repo
   - mixed or transitional repo

3. Detect the main problems.
   Focus on:
   - overcrowded root directory
   - unclear separation between `src`, `tests`, `docs`, `scripts`, `config`, and generated outputs
   - duplicated or stale configuration files
   - notebooks, datasets, checkpoints, build outputs, caches, or secrets committed into source areas
   - weak discoverability for setup, testing, contribution, release, or ownership
   - risky proposed moves that would break imports, build tooling, packaging, or deployment paths

4. Design the target structure.
   Produce a concrete target tree that matches the repository archetype. Use the reference files when needed:
   - `references/layout-patterns.md` for archetype-specific layouts
   - `references/repo-standards.md` for repo-health expectations and required governance files

5. Produce a staged migration plan.
   Split the cleanup into small, reviewable change lists. Prefer this order unless there is a strong reason not to:
   - documentation and policy files
   - ignore rules and artifact cleanup
   - non-functional moves and renames
   - config normalization
   - test layout normalization
   - CI and quality gates
   - packaging or release workflow cleanup

6. Generate the final deliverable.
   Use this structure unless the user explicitly requests another format:

   # Repository professionalization plan

   ## Executive summary
   Summarize the repo archetype, major risks, and the smallest effective cleanup path.

   ## Current-state findings
   Group findings into structure, tooling, documentation, testing, security, and release hygiene.

   ## Target repository layout
   Show a proposed tree with brief rationale for each top-level directory.

   ## Staged migration plan
   Break the work into small pull requests or change lists. Explain dependencies and rollback risk.

   ## Required repo standards
   List missing or weak files and controls such as README, CONTRIBUTING, CODEOWNERS, SECURITY, LICENSE, CI, branch protection, and release notes.

   ## Concrete edits
   Suggest exact file moves, renames, additions, deletions, or templates.

## Decision rules

Apply these rules while designing the structure.

### Root directory

Keep only high-signal items at the root. Prefer a small root containing source entrypoints, docs, top-level config, and a few operational directories. Move one-off scripts, experiments, scratch files, exports, screenshots, and local notes out of the root.

### Source layout

Prefer one primary source home per product surface where possible.

- Use `src/` or language-standard package roots for application and library code.
- Use `tests/` or language-standard test directories consistently.
- Use `docs/` for user-facing and developer-facing documentation that is larger than the README.
- Use `scripts/` for operational helpers, maintenance tasks, and local automation.
- Use `config/` only when configuration files are numerous enough to justify a dedicated home.
- Use `examples/` for runnable demos and consumer-facing usage patterns.

### ML and research repos

For ML, data, or research-heavy repositories:

- Keep source code separate from notebooks, reports, figures, checkpoints, and raw data.
- Prefer a clear split across `src/`, `notebooks/`, `configs/`, `tests/`, `scripts/`, `docs/`, and artifact directories that are ignored by git.
- Treat `data/`, `artifacts/`, `outputs/`, `checkpoints/`, and `wandb/`-style directories as generated or environment-specific unless the user explicitly needs versioned fixtures.
- Avoid using notebooks as the only source of truth for core logic.

### Monorepos

For monorepos:

- Prefer a stable top-level partition such as `apps/`, `packages/`, `services/`, `libs/`, `infra/`, and `docs/`.
- Keep shared tooling centralized when possible.
- Standardize test, lint, and build commands across packages instead of creating many bespoke flows.

### Safe migrations

Do not casually recommend file moves that will silently break imports, package metadata, Docker contexts, CI paths, or deployment assumptions. Call out impact areas explicitly. When uncertain, recommend a validation checklist instead of presenting a move as risk-free.

## Quality bar

Aim for the habits of strong engineering teams.

- Make setup and contribution paths obvious.
- Make ownership and review routing obvious.
- Make common commands predictable.
- Make tests easy to find and run.
- Make generated files and local clutter stay out of version control.
- Make releases and CI paths understandable.
- Make security reporting and dependency hygiene visible.

## Use bundled resources

- Run `scripts/repo_inventory.py` whenever a real repository is available on disk.
- Read `references/layout-patterns.md` when the repository archetype or target tree is unclear.
- Read `references/repo-standards.md` when evaluating documentation, governance, CI, and security expectations.

## Avoid weak behavior

Do not:

- propose a full rewrite when a structural cleanup is sufficient
- flatten everything into a generic template without respecting language or tooling conventions
- treat every missing file as equally important
- recommend huge, hard-to-review mega-PRs
- optimize for visual symmetry over developer workflow
- assume a public open-source workflow if the repo is clearly internal only

## Example requests this skill should handle well

- “Clean up this repository and propose a professional structure.”
- “Turn this research repo into something production-friendly.”
- “Reduce root-level chaos and make this easier to onboard into.”
- “Make this codebase look like a strong engineering team maintains it.”
- “Audit this repo and give me a staged refactor plan, not a rewrite.”

# Product Analyst implementation plan

## Goal

Ship a Claude Code plugin that conducts read-only, evidence-backed product investigations through a restricted PostgreSQL MCP gateway and guarded PostHog and QuickSight access.

## Work items

1. Register the plugin in the marketplace and provide its manifest, hooks, skill, verifier, setup templates, and README.
2. Implement the PostgreSQL MCP gateway with contract validation, session and explicit investigation scope, query validation, role inspection, planning, timeouts, row limits, ledger writes, and deterministic claim checks.
3. Add policy and recording hooks for PostHog and QuickSight. Policies must deny by default and fail closed.
4. Add unit, integration, and hook tests for the listed enforcement paths.
5. Require candidate findings to pass independent verification before final deterministic claim validation. Reserve PostgreSQL-query and PostHog-call budgets for verifier calls.
6. Validate the plugin and run the relevant test suite. A live investigation remains a manual smoke test because it needs project credentials and approved data access.

## Configuration contract

`config.toml` declares timezone, internal-user exclusion, PostgreSQL service and schemas, timeouts, optional plan-cost cap, optional RDS IAM settings, query budgets, and PostHog extra read tools. Both source budgets cover primary and verifier calls. `metrics.toml` contains governed PostgreSQL metrics and mappings to PostHog metrics. PostHog's catalogue remains authoritative for metrics it owns. Claude Code 2.1.281 or later expands the plugin's `${CLAUDE_PROJECT_DIR}` so the gateway is scoped to the analysed project.

## Completion criteria

The plugin records valid investigations, fingerprints their project configuration and metric catalogue, rejects unsupported or malformed contracts and findings, and provides a report shape that cites each substantive claim. Source-side database grants, PostHog scopes, and QuickSight IAM permissions enforce read-only access; tool and shell policies provide a second layer for calls they recognise. Tests cover the boundary cases in the design specification.

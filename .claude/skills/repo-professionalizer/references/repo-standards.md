# Repository standards reference

Use this file when judging whether a repository looks maintainable, trustworthy, and easy to operate.

## 1. Baseline repo-health files

Expect most serious repositories to have the following, adjusted for context:

- `README.md`
  - what the project is
  - how to install or bootstrap it
  - how to run tests and linters
  - how to run locally
  - link to deeper docs if needed
- `LICENSE`
  - important for open-source or externally shared repos
- `CONTRIBUTING.md`
  - contribution and development workflow
- `CODEOWNERS`
  - ownership routing for reviews where supported
- `SECURITY.md`
  - how to report vulnerabilities or sensitive issues
- changelog or release notes process
- CI workflow files for tests, linting, and build validation

Treat missing README and missing test instructions as high-severity discoverability problems.

## 2. Root hygiene

A professional root directory is small and intentional. Treat the following as warning signs when they accumulate in the root:

- ad hoc scripts
- screenshots and exports
- notebooks unrelated to onboarding
- multiple competing environment files
- scratch markdown files
- generated build outputs
- caches
- local datasets or checkpoints

## 3. Structure expectations

Use consistent separation of concerns.

- source code in a clear source area
- tests in a predictable test area
- docs outside the main README when documentation grows
- automation helpers in `scripts/`
- configuration standardized and deduplicated
- generated artifacts excluded from version control unless intentionally committed fixtures

## 4. Reviewability and ownership

A strong repo makes change review easier.

Prefer:

- small, staged cleanup changes
- clear code ownership boundaries
- a documented review path
- predictable naming for modules and directories
- minimal surprise in file locations

## 5. Tooling quality

Prefer repositories where these are easy to discover and consistent:

- formatter and linter config
- test command
- build command
- local dev bootstrap command
- package manager choice
- environment variable handling
- pre-commit or equivalent guardrails when appropriate

Treat duplicated or contradictory config as a cleanup priority.

## 6. Security and operational hygiene

A professional repository should signal whether it can be trusted and operated safely.

Look for:

- `.gitignore` that excludes secrets, caches, artifacts, and environment-specific clutter
- dependency update strategy
- secret scanning and code scanning where the platform supports it
- protected default branch and review requirements
- documented security reporting path

## 7. Release and maintenance signals

Look for evidence that future maintainers can operate the project.

Examples:

- versioning policy
- release notes or changelog process
- issue and pull request templates when community collaboration matters
- examples or fixtures for consumers
- architecture notes for non-trivial systems

## 8. Recommendations tone

Recommend the smallest set of changes that meaningfully improve the repo. Do not cargo-cult every possible policy file into a small internal prototype. Explain trade-offs and prioritize by impact.

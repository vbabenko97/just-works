# Layout patterns reference

Use this file to propose a target repository structure that matches the actual repository type.

## 1. Application or service repo

Use a layout like this when the repo mostly contains one deployable app or service.

```text
repo/
├── README.md
├── docs/
├── scripts/
├── src/
├── tests/
├── config/
├── .github/
└── [language and build configs]
```

Notes:
- keep deployable code and library code under one obvious home
- move operational helpers into `scripts/`
- keep long-form docs out of the root

## 2. Reusable library or SDK

Use a layout like this when the repo is primarily meant to be imported by other code.

```text
repo/
├── README.md
├── docs/
├── examples/
├── src/ or package-root/
├── tests/
├── scripts/
└── [packaging metadata]
```

Notes:
- prioritize examples and API discoverability
- keep consumer-facing entrypoints stable
- call out packaging and import-path impact before recommending moves

## 3. Monorepo

Use a layout like this when the repo contains multiple deployables or packages.

```text
repo/
├── apps/
├── packages/ or libs/
├── services/
├── infra/
├── docs/
├── scripts/
├── tooling/
└── .github/
```

Notes:
- prefer stable top-level partitions over many mixed roots
- centralize shared tooling instead of duplicating per package when practical
- define ownership boundaries clearly

## 4. ML or research repo

Use a layout like this when experimentation, training, evaluation, and notebooks are present.

```text
repo/
├── README.md
├── docs/
├── src/
├── tests/
├── configs/
├── scripts/
├── notebooks/
├── reports/ or figures/
└── [ignored data and artifact directories]
```

Notes:
- keep reusable logic in `src/`, not trapped in notebooks
- keep data, checkpoints, and outputs out of version control unless they are tiny fixtures
- separate configs from code and experimental outputs

## 5. Infra or platform repo

Use a layout like this when the repo is mostly deployment, infrastructure, or automation.

```text
repo/
├── README.md
├── docs/
├── scripts/
├── modules/ or packages/
├── environments/ or deploy/
├── tests/
└── .github/
```

Notes:
- separate reusable modules from environment-specific deployments
- make promotion and environment boundaries explicit

## 6. Transitional mixed repo

Use a staged plan when the repo currently mixes application code, notebooks, experiments, exports, and docs.

Suggested first pass:
- carve out `src/`, `tests/`, `docs/`, and `scripts/`
- isolate notebooks and reports
- identify generated or local-only directories for `.gitignore`
- postpone deeper package boundary changes until after the repo is navigable

## 7. Naming and top-level rules

Prefer short, literal directory names.

Good examples:
- `src`
- `tests`
- `docs`
- `scripts`
- `configs`
- `examples`
- `apps`
- `packages`
- `infra`

Avoid vague or overloaded names unless they are already ecosystem-standard.

## 8. Anti-patterns to call out

Flag these clearly:

- more than a handful of random root-level folders with no obvious convention
- source code mixed with outputs and exports
- tests scattered under arbitrary names
- multiple partially adopted package layouts at once
- notebooks used as production execution entrypoints
- secrets, environment files, or local datasets committed into the repo

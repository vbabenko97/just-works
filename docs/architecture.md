# Architecture

## Structure

Two parallel provider directories plus distribution scaffolding:

- `.claude/` — Claude Code agents, skills, commands, hooks, settings, statusline, plans
- `.codex/` — OpenAI Codex agents, prompts, skills, config, hooks, plan-reviews
- `bin/cli.mjs` — Node.js installer; the published `npx @dynokostya/just-works` package belongs to upstream
- `install.sh`, `install.bat` — shell installers for macOS/Linux and Windows
- `CLAUDE.md` / `AGENTS.md` / `CLAUDE-CHAT.md` — shared behavioral guidelines at root
- `.mcp.json` — per-project MCP server declarations (Playwright)

## Module Boundaries

**Agents** (`.claude/agents/`, `.codex/agents/`) — 20 Claude and 17 Codex agents; the three Claude-only ones are the `/goal` roles (`goal-architect`, `goal-implementer`, `goal-security`). Writers are file-type-triggered via `description` frontmatter:
- `python-code-writer`, `typescript-code-writer`, `swift-code-writer`, `csharp-code-writer`
- `react-code-writer` (React/Tailwind/shadcn)
- `flutter-code-writer` (Dart/Flutter)
- `prompt-writer` (Fable, Opus, GPT, Gemini)
- `diagrammer` (PlantUML)

The rest are task agents — `reviewer`, `test-runner`, `docs-agent`, `refactor-agent`, `cv-claim-verifier` (read-only factual review of application material) — and a personal-finance set (`personal-cfo-agent`, `risk-officer-agent`, `investment-committee-agent`, `career-capital-agent`).

**Skills** (`.claude/skills/`, `.codex/skills/`) — 74 skills in `.claude/skills/` and 49 in `.codex/skills/`, counted by `SKILL.md`; all 49 Codex skills are identical copies of their `.claude/` counterparts, and the other 25 are Claude-only. Claude also has two workspace directories without `SKILL.md`. Skills cover coding standards per language, architecture patterns (DDD, feature-driven), model-specific prompting (`fable-5-1-prompting`, `opus-5-5-prompting`, `gpt-6-prompting`, `gemini-3-8-flash-prompting`), ML and document work (`ml-system-design`, `ml-system-design-review`, `ai-stage-gate`, `lossless-doc-compress`, `human-writing`), predictive UX evaluation (`predictive-ux-evaluation`), grant writing (`msca-pf-european-2026`, `msca-pf-2026-reviewer`, `msca-text-humanizer`), personal finance, job applications (`career-application-builder`, `job-triage`, `interview-drill`), GitHub presentation (`github-presentation`, manual-only), domain skills (`ticket-writing`, `sprint-estimation`, `plantuml-diagramming`, `rest-api`), and behavioral modes (`caveman`, `minimal-coding`).

**Commands** (`.claude/commands/`, `.codex/prompts/`) — multi-phase workflows:
- `project-docs` — scoped documentation updates: establish scope and sources, gather evidence, reconcile requested coverage, write, and verify
- `git-sync` — sync repos and submodules to default branch
- `plan-reviewer` — Codex-only, reviews plans authored by Claude Opus

Dependency direction: Agents → Skills (declared in agent frontmatter). Commands → Agents and Skills (referenced in command prompts). Skills may compose (`sprint-estimation` pairs with `ticket-writing`; `ml-system-design` pairs with `ml-system-design-review`). No reverse dependencies.

## Data Flow

1. User invokes agent via CLI (e.g., Claude Code matches `*.py` edit → `python-code-writer`).
2. Orchestrator reads agent frontmatter, loads declared skills as behavioral standards.
3. Agent reads target file and project context before editing.
4. Agent edits via `Read`/`Edit`/`Write`/`Bash` tools within declared tool allow-list.
5. Orchestrator marks task complete per `CLAUDE.md` rule 3.

`project-docs` reads existing documentation and the sources needed for the requested scope. It can delegate independent investigations, maps capabilities to canonical sections when complete coverage is requested, updates those documents, and verifies claims, status labels, and links. Implementation facts and approved requirements remain distinguishable; contradictions are reported.

## Key Patterns

- **Dual-provider mirror** — `.claude/` (Markdown with YAML frontmatter) and `.codex/` (TOML) hold parallel copies of the shared agents and skills; Codex can't resolve `@file` references, so a skill wanted in both is copied into both trees. The trees are not required to match; see Module Boundaries for provider-specific entries.
- **File-extension-triggered selection** — agent `description` fields declare target file types; the orchestrator matches on descriptions, not names.
- **Skill composition** — agents stack multiple skills (e.g., `react-code-writer` loads `react-coding` + `tailwind-css-coding` + `shadcn-ui-coding`).
- **Permission deny-list** — the project's `.claude/settings.json` denies `Read` access to `.env`, `*.pem`, `*.key`, credentials, cloud configs, SSH keys, and DB files. The global install template, `settings.json.default`, has an empty deny-list.
- **Evidence-based documentation** — `project-docs` verifies implementation claims against inspected code, configuration, or runtime interfaces; relevant passing checks corroborate those claims. Intent claims require approved sources. Unsupported claims are omitted or marked as open questions. Requested complete coverage requires reconciling capabilities against substantive documentation, beyond checking links.
- **Personal vs default configs** — `install.sh` uses minimal `.default` configs and keeps existing configs unless `--replace-config` is passed. It refuses `--personal` for Claude before installing anything; `--personal --codex-only` selects the opinionated Codex config. The older `install.bat` and `bin/cli.mjs` have separate behavior; see the [installation guidance](../README.md#installation) before choosing an installer.

## Entry Points

- `bin/cli.mjs` — Node.js installer (the named npm package installs upstream)
- `install.sh`, `install.bat` — clone-and-run installers
- [Claude project-docs](../.claude/commands/project-docs.md), [Codex project-docs](../.codex/prompts/project-docs.md) — documentation workflow
- `.claude/commands/git-sync.md` — multi-repo branch sync
- `.codex/prompts/plan-reviewer.md` — Codex plan review
- `.claude/agents/*.md`, `.codex/agents/*.toml` — agents

---
*Generated: 2026-07-07 | Commit: ef80bb5 · Corrected by hand 2026-09-26: agent and skill counts, mirroring, `src/evals/` removed (never committed) · 2026-09-27: career skills consolidated, counts updated · 2026-10-08: documentation workflows updated*

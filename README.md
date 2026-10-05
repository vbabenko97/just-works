# just-works

Drop-in AI agent workflows, coding skills, and prompt standards for **Claude Code** and **OpenAI Codex**.

Fork of [dynokostya/just-works](https://github.com/dynokostya/just-works), maintained independently; upstream changes are reviewed and recorded in [UPSTREAM.md](UPSTREAM.md).

Copy `.claude/` into any project — or install globally — and get pre-configured agents, quality guardrails, and documentation pipelines out of the box.

Use the global installer for Codex setup. This repo's `.codex/config.toml` also loads as a project layer when Codex trusts this checkout; see [Codex ownership](UPSTREAM.md#codex-ownership--installation-baseline-and-a-live-project-layer).

## What's Inside

**Concise responses** — `minimal-coding` guides least-code solutions; invoke `caveman` for compressed conversation output. This repo's `.claude/settings.json` selects the `compressed` output style, which trims filler, hedging, and emojis to reduce response tokens and context use, potentially lowering token-based costs. The global installer uses `settings.json.default`, which selects `default` (and keeps an existing config unless `--replace-config` is passed).

**Full Claude Code fluency** — uses the whole toolset by default: `AskUserQuestion` for structured choices, rich markdown, `TaskCreate` progress tracking, and parallel tool calls.

**Context-isolating subagents** — delegates file-type work (`python`, `react`, `swift`, …) to subagents that carry their own context, so the main thread stays lean and focused.

**Agents** — file-type-triggered writers (`python`, `typescript`, `swift`, `csharp`, `react`, `flutter`), plus `prompt-writer`, `diagrammer`, `reviewer`, `test-runner`, `docs-agent`, `refactor-agent`, `cv-claim-verifier`, and a personal-finance set (`personal-cfo-agent`, `risk-officer-agent`, `investment-committee-agent`, `career-capital-agent`). 17 per provider, plus three Claude-only `/goal` roles (`goal-architect`, `goal-implementer`, `goal-security`).
**Commands** — `project-docs` and `git-sync` (Claude & Codex), `plan-reviewer` (Codex).

**Skills** — coding standards (Python, TypeScript, React, Tailwind, shadcn/ui, Swift, C#, Dart/Flutter), architecture patterns (DDD, feature-driven), ML system design (`ml-system-design` authoring + `ml-system-design-review` rubric-graded critique + `ai-stage-gate` Go/Kill gate reviews), document work (`doc-coauthoring` authoring + `lossless-doc-compress` information-preserving compression + `human-writing` for documents that readers outside the project can follow), predictive UX evaluation of web UIs (`predictive-ux-evaluation`), model-specific prompt engineering (Claude Opus 5.5 & Fable 5.1, GPT-6, Gemini 3.8 Flash, Grok 4.5), Blender 5.2 expert tools (`scenario-blender-expert` router + 12 specialists, from scenario-labs/skills), job applications (`career-application-builder` evidence-checked CVs and letters, `job-triage` vacancy screening, `interview-drill` mock interviews), GitHub profile and README presentation (`github-presentation`, invoke manually), and behavioral modes (`minimal-coding`). Applied automatically based on task intent or, for language and framework skills, the file type being edited.

**Permission rules** — this repo's `.claude/settings.json` denies `Read` access to `*.pem`, `*.key`, credentials, cloud configs, SSH keys, Terraform state, and database files. The global install template, `settings.json.default`, has an empty deny-list.

## Installation

`install.sh` installs agents, skills, commands, and settings globally to `~/.claude/`, `~/.codex/`, and `~/.agents/skills/`. Before copying, it asks whether to back up the existing destinations to `~/just-works-backups/<timestamp>/`; without a terminal it backs up without asking, and answering "n" or passing `--no-backup` turns backups off. An existing `settings.json`, `config.toml`, or `hooks.json` is kept unless you pass `--replace-config`, and entries you added under names this repo doesn't ship are left in place. On each side that runs, `CLAUDE.md` and `CLAUDE-CHAT.md` (Claude) and `AGENTS.md` (Codex) are overwritten — `--skip-config` does not protect them — and so is `statusline-command.sh` unless you pass `--skip-statusline`; all are backed up when backups are on.

### From source

```bash
git clone https://github.com/vbabenko97/just-works.git
cd just-works
./install.sh
```

To update: `git pull && ./install.sh` (existing config files are kept; add `--replace-config` to refresh them).

The protections above apply to `install.sh` only. On Windows, `install.bat` is a separate, older script without them: it has no `--prune`, `--replace-config`, `--repos`, or `--personal` refusal, it overwrites existing config files, and with backups off it deletes each destination directory before copying.

`bootstrap.sh` (upstream's `curl | bash` one-liner) downloads `dynokostya/just-works` and runs that repository's own installer unless `JUST_WORKS_REPO` (set in `bash`'s environment) names another repository; the npm package `@dynokostya/just-works` is upstream's. By default both install upstream, not this fork — use the source checkout above.

### `--personal`

`install.sh` refuses `--personal` for the Claude side and exits before installing anything: it would install this repository's `.claude/settings.json` as `~/.claude/settings.json`, and the installer cannot merge into an existing one. `--personal --codex-only` remains available and installs the opinionated Codex `config.toml` instead of `config.toml.default`:

| `~/.codex/config.toml` (without `--azure`) | Default | `--personal --codex-only` |
|---|---|---|
| Model | `gpt-5.5`, `medium` reasoning effort | not set |
| Sandbox / approvals | not set | `workspace-write`, `approval_policy = "never"` |
| MCP servers | none | Playwright |

Both profiles install the same `hooks.json`, a `Stop` hook that plays a sound with `afplay /System/Library/Sounds/Glass.aiff`; only the personal `config.toml` sets `[features] hooks = true`. `afplay` and that sound file are **macOS-only** — on Linux/Windows swap `afplay` for your player (`paplay`/`aplay` on Linux), or remove the hook.

### Options

`install.sh` accepts:

```bash
--personal              # opinionated profile; refused for the Claude side, use with --codex-only
--azure                 # Codex: Azure OpenAI config instead of the direct OpenAI API
--dry-run               # preview without changes
--skip-config           # skip settings.json, config.toml, hooks.json
--skip-statusline       # skip statusline-command.sh
--skip-skills-claude    # skip Claude Code skills
--skip-skills-codex     # skip Codex skills
--claude-only           # skip Codex
--codex-only            # skip Claude
--no-backup             # skip backup prompt, disable backups (for CI/scripts)
--prune                 # delete entries a previous run installed that are gone from the source (tracked in ~/.just-works-manifest)
--replace-config        # overwrite existing settings.json / config.toml / hooks.json (backed up when backups are on)
--repos                 # also sync skills into checkouts under $HOME that already have a skill root
-h, --help              # show help
```

### Codex Azure config

Azure configs are installed only with `--azure`: `.codex/config/azure/config.toml.default` → `~/.codex/config.toml`, or `.codex/config/azure/config.toml` with `--personal --codex-only --azure`. An existing `~/.codex/config.toml` is kept unless you also pass `--replace-config`.

Then edit the file — replace `<your-resource-name>` with your Azure OpenAI resource and set your environment variable:

```bash
export AZURE_OPENAI_API_KEY="your-key-here"
```

### MCP for Claude Code

MCP servers are configured per-project, not globally. To set up MCP in your project:

```bash
cp .mcp.json.default /path/to/your/project/.mcp.json
```
OR
```bash
cp .mcp.json /path/to/your/project/.mcp.json
```

Requires `npx` (Node.js) in your PATH.

## Project Structure

```
.claude/
  agents/           # Claude Code agent definitions
  skills/           # Coding and prompting standards
  commands/         # Multi-step workflows (project-docs, git-sync)
  output-styles/    # Selectable output styles (compressed)
  hooks/            # maintenance_auth.py (owner maintenance check)
  settings.json     # Permissions, hooks, env, MCP toggles
.codex/
  agents/           # Codex custom agent definitions (TOML)
  prompts/          # Codex slash commands (plan-reviewer, ...)
  skills/           # Skills copied from .claude/ (a subset)
  config/azure/     # config.toml.default + config.toml
  hooks.json        # Lifecycle hooks (notification)
bin/cli.mjs         # npx installer
CLAUDE.md           # Behavioral instructions for Claude Code
CLAUDE-CHAT.md      # Behavioral instructions for claude.ai chat
AGENTS.md           # Behavioral instructions for Codex
```

`.claude/` and `.codex/` are parallel and independent — use one or both.

## Customization

Add project-specific agents in `.claude/agents/` or `.codex/agents/`. Override skill defaults in your own `CLAUDE.md` or `AGENTS.md`. Extend the deny-list in `.claude/settings.json`.

If you fork this: a skill you want in both providers has to be copied into both trees (Codex doesn't support `@file` references). The trees are not required to match — each carries skills the other lacks. Keep instructions model-agnostic.

## License

Apache 2.0

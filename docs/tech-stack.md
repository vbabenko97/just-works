# Tech Stack

## Languages

- Node.js >=18 — CLI installer runtime (`package.json:32-34`)
- Python 3 — reliability plugin hooks, owner verification scripts, and standalone test suites with no runner (`plugins/reliability/hooks/`, `scripts/verify/`, `tests/reliability/README.md`)
- Bash — installer and statusline scripts (`install.sh:1`, `.claude/statusline-command.sh:1`)
- Windows Batch — Windows installer (`install.bat:1`)
- Markdown — agent, skill, and command definitions
- TOML — Codex config and agent definitions (`.codex/config.toml`, `.codex/agents/*.toml`)

## Frameworks

- Claude Code — Anthropic CLI target harness (`.claude/`)
- OpenAI Codex — GPT CLI target harness (`.codex/`)

## Infrastructure

- Playwright MCP — browser automation MCP server (`.mcp.json:3-6`, `.codex/config.toml:25-27`)
- Azure OpenAI — optional Codex provider variant (`.codex/config/azure/config.toml`)

## Dev Tools

- npx — MCP server and CLI execution (`.mcp.json:4`, `package.json:6-7`)
- jq — statusline JSON parsing (`.claude/statusline-command.sh`)

---
*Generated: 2026-04-21 | Commit: 2dc99fd · Corrected by hand 2026-09-26: `src/evals/` entries removed (never committed), Python purpose and the `package.json` citation fixed*

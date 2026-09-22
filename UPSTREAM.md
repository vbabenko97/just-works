# Upstream intake ledger

This fork is **independently maintained**. Upstream is a source of fixes, not an authority over
this repo's behaviour. "Commits behind" is not a metric to drive to zero — the metric is
*unreviewed relevant changes*. A reviewed batch with zero imports is a successful outcome.

- `origin` — `github.com/vbabenko97/just-works` (this fork; all work lands here)
- `upstream` — `github.com/Dynokostya/just-works` (never pushed to)

Record every upstream change as **imported / adapted / rejected / deferred** with a reason, so a
deliberate rejection never resurfaces later as an unexplained "behind" count.

## Review snapshot — 2026-09-22

Every count below describes this comparison only. They change as either side commits; they are not
standing properties of the repository.

| Field | Value |
|---|---|
| Fork HEAD compared | `4424d3e29f718ae5fd7875744c0ec09cc2ab4fc9` |
| Upstream HEAD compared | `a31e42c67f0603c3fdb95004e805b4ddb4ab3657` |
| Merge base | `871ed888dfa86b33e3432def51bd2791f06ea259` |
| Divergence at snapshot | 15 upstream-only, 99 fork-only |
| Conflicts in a dry-run merge | 9 — 5 content, 4 modify/delete |
| Files deleted upstream, still present here | 12 |

The 9 conflicts are an **inventory**, not a work queue. Resolving them one by one would amount to
performing the merge; a merge also brings non-conflicting upstream changes that the conflict list
never surfaces. Intake is selective and per-change instead.

Cadence: review weekly, and sooner if a compatibility or security fix appears. Reviewing is not
merging.

## Standing decisions

### Subagent model routing — REJECT upstream's policy

Upstream sets `CLAUDE_CODE_SUBAGENT_MODEL_FORCE=1` with `CLAUDE_CODE_SUBAGENT_MODEL=opus`, forcing
one model for every subagent and dropping `model:` from agent definitions.

This fork routes per role instead: `/goal` dispatches to `goal-architect` (`claude-fable-5-1`),
`goal-implementer` and `goal-security` (`claude-opus-5-5`), each pinned in frontmatter.

**What is verified:** static inspection of the running 2.1.278 binary on 2026-09-22 shows model
resolution ordered `per-invocation > frontmatter > env > parent`, with the env default consulted
only when no explicit model is set; the binary contains the literal
`Workflow agent model "" ignored: CLAUDE_CODE_SUBAGENT_MODEL_FORCE is set`. Documentation agrees.

**What is NOT verified:** that `/goal` actually routes each role to its intended model at runtime.
No live dispatch has been observed. Rejecting the force flag is a well-founded *policy decision*;
"the three roles really do run on three models here" remains **unproven** until a live run is
inspected.

**Never import `CLAUDE_CODE_SUBAGENT_MODEL_FORCE`.** This fork's `CLAUDE_CODE_SUBAGENT_MODEL=sonnet`
acts as a fallback for unpinned agents and does not override frontmatter.

### Capability deletions — downstream decision wins until deliberately reversed

A capability upstream no longer wants is not evidence this fork no longer wants it. Symmetrically,
an agent deleted here stays deleted even though upstream still maintains it.

The rule: **preserve explicitly wanted downstream capabilities and intentional removals. Revisit
when requirements change, a replacement is verified, or a concrete defect warrants removal — not
because upstream deleted something, and not because its edit date is old.**

All 12 deleted paths, individually accounted for:

| Path | Capability | Disposition | Reason |
|---|---|---|---|
| `.claude/skills/dart-coding/SKILL.md` | Dart language rules | keep | wanted-capability claim on record (see caveat) |
| `.claude/skills/flutter-coding/SKILL.md` | Flutter widget rules | keep | same |
| `.claude/skills/ddd-architecture-python/SKILL.md` | Python DDD patterns | keep | same |
| `.claude/skills/feature-driven-architecture-python/SKILL.md` | Python vertical slices | keep | same |
| `.codex/skills/dart-coding/SKILL.md` | Codex copy | keep | mirrors the `.claude` decision |
| `.codex/skills/flutter-coding/SKILL.md` | Codex copy | keep | mirrors the `.claude` decision |
| `.codex/skills/ddd-architecture-python/SKILL.md` | Codex copy | keep | mirrors the `.claude` decision |
| `.codex/skills/feature-driven-architecture-python/SKILL.md` | Codex copy | keep | mirrors the `.claude` decision |
| `.codex/skills/sprint-estimation/SKILL.md` | Story-point calibration | keep | no affirmative retirement decision |
| `.claude/agents/flutter-code-writer.md` | Flutter writer agent | keep | modified locally; no verified replacement |
| `.codex/agents/flutter-code-writer.toml` | Codex counterpart | keep | mirrors the `.claude` decision |
| `.claude/hooks/rtk-rewrite.sh` | rtk command rewriting | keep — see below | migration, not a plain deletion |

**Caveat on provenance.** The "skills I still use" justification originated in a prompt drafted by
the assistant, not in a statement by the maintainer. It has not been confirmed. Last *modification*
dates are the only measured signal, and they measure edits, not invocations:

| Path group | Last modified |
|---|---|
| dart-coding, flutter-coding, ddd-architecture-python, feature-driven-architecture-python, flutter-code-writer | 2026-07-09 (all five — consistent with one bulk addition) |
| `.codex/skills/sprint-estimation` | 2026-08-30 |
| `.claude/hooks/rtk-rewrite.sh` | 2026-04-21 |

A stable skill can run constantly without being edited, so an old date is not evidence of disuse.
Keeping is the safe default for this pass; retirement is a separate decision that needs the
maintainer, not an inference from git history.

Also intentionally absent and staying absent, though upstream still maintains them:
`.claude/agents/ticket-creator.md`, `.codex/agents/ticket-creator.toml`.

### rtk hook — preserve; migration is a separate change

Upstream `2766626` and `9a4e396` replace the `rtk-rewrite.sh` shell hook with a native
`rtk hook claude` invocation. This is a plausible upstream improvement, not proof that the local
wrapper can safely disappear.

`.claude/settings.json` invokes the script by path in a `PreToolUse` hook, so the settings entry,
the installed hook, installer behaviour and any trust approval must move together. A git commit
alone does not coordinate a live settings file outside the repository.

**This pass: keep the existing hook.** Before migrating, check the installed rtk version and compare
the local script's behaviour with the native hook. Acceptance must cover rewritten and
non-rewritten commands, argument and failure-behaviour preservation, and continued operation of the
protection mechanism. No automatic trust re-pinning.

### `.codex/` ownership — installation baseline, and a live project layer

Corrects an earlier mistaken conclusion, including the reasoning recorded in commit `4424d3e`.

`.codex/config.toml` serves two distinct roles:

1. **Installation baseline.** `install.sh:386-412` and `bin/cli.mjs:276-295` install
   `.codex/{agents,prompts,skills,hooks.json,config.toml}` into `~/.codex/` (skills to
   `~/.agents/skills`), choosing `.default` or personal variants. The tracked file is a *baseline
   for installation*, **not** a mirror of the live file and not a target to make identical.
2. **Live project layer.** Codex reads this repo's `.codex/config.toml` as a trusted project layer
   when run here. Demonstrated 2026-09-22: `codex mcp list` from this repo lists `playwright`
   (defined only in the tracked file); the same command from `/tmp` does not. The gate is
   `trust_level = "trusted"` for this path in `~/.codex/config.toml`.

`CODEX_HOME` being unset does **not** make the tracked tree inert — that variable only selects where
the *user*-level config lives, independently of the project layer.

**Correction to `4424d3e`.** Its message states the `codex_hooks` → `hooks` rename "has no runtime
effect until the templates are synced across". That reasoning is wrong: the file is loaded as a
project layer for Codex sessions started in this repo, so the rename **can** take effect without any
sync. What was demonstrated is the *loading mechanism* (via the `playwright` control test); no
behavioural change from the rename itself was observed. Potential impact, not measured impact.

**Whole-file replacement is prohibited in this pass.** The live `~/.codex/config.toml` carries
machine-local configuration and state — 40+ `[projects.*]` trust entries, `[hooks.state.*]`, plugin
enablement, desktop theme — none of it present in the 5-section tracked baseline. The installer
already protects this (`install_config_file:325-328` keeps an existing file). `--replace-config`
bypasses that guard and would destroy the state; do not pass it unless that is the intent.

**Unresolved:** the tracked baseline defines `[mcp_servers.playwright]` and the live file does not.
This difference has **not** been classified as intentional or accidental, and nothing was changed.
Whole-file divergence between baseline and live is expected; *this particular difference* is simply
unexamined. Resolve it only if a desired behaviour requires it — and then by a targeted, reviewed
change to that one setting, never by replacing the file.

This section settles `config.toml` only. How the repo's agents, skills and hooks are installed and
loaded is not decided here.

Never point `CODEX_HOME` at the working tree — it also governs auth and multi-GB session/log
databases.

### Operational limits

`.claude/settings.json` sets no `CLAUDE_CODE_MAX_SUBAGENT_SPAWN_DEPTH` or
`CLAUDE_CODE_MAX_CONCURRENT_SUBAGENTS`. Documented defaults are depth 3 and concurrency 20, but
"absent from this file" does not by itself establish the effective values — Claude Code merges
several settings scopes and the inherited environment.

`/goal` dispatches from the main conversation (its `SKILL.md` declares no `context:` key), so its
specialists sit at depth 1 and a depth-1 cap would not prevent them from spawning.

These are concurrency and nesting controls, **not** a spend guarantee: `/goal`'s "at most four
delegated calls" is an instruction to the model rather than an enforced counter, there is no total
session spawn limit, the concurrency limit has documented exceptions, and no cap spans Claude and
Codex together.

### Supported surfaces

`/goal`'s Opus 5.5 roles require Claude Code 2.1.280+. The terminal CLI meets this; the editor
extension bundles its own pinned 2.1.278 binary. No behavioural difference was found between the two
binaries for model resolution — the argument for treating the terminal as the supported surface is
future drift on a pinned host, not a present defect.

### Codex bridge

Stays disabled (`backend_enabled: false`) until its protocol assumptions are validated against a
real run and sending this repo's code to a second provider is explicitly authorised. Provider and
auth configuration unchanged.

## Intake log

| Date | Upstream SHA | Change | Disposition | Reason |
|---|---|---|---|---|
| 2026-09-22 | `fd8a20b`, `8ddedd7` | force one model for all subagents | **rejected** | Collapses per-role routing; verified against the running binary |
| 2026-09-22 | `6633a1c`, `ce7e828` | subagent depth/concurrency caps | **deferred** | Agreed in principle; to be set directly rather than by importing upstream's settings |
| 2026-09-22 | 12 file deletions | remove Dart/Flutter/Python-architecture/sprint capabilities | **deferred** | Retirement is a separate decision; see the per-path table |
| 2026-09-22 | `2766626`, `9a4e396` | migrate rtk hook to native invocation | **deferred** | Needs a coordinated settings + installed-hook change and a behaviour comparison |
| 2026-09-22 | `3370412` | drop unrecognised settings keys; `~/`-anchored deny rules | **candidate — under review** | The deny-rule half is already present here; the unrecognised-key half may apply. See open items |
| 2026-09-22 | `a31e42c` | add `synthetic-user-research` skill | **deferred** | No identified need |
| 2026-09-22 | `1836546` | change `minimal-coding` trigger | **deferred** | Behaviour change; evaluate against `/goal` routing |
| 2026-09-22 | `180677a` | statusline rewrite | **deferred** | Adopt only if it fixes an actual problem |
| 2026-09-22 | `78521a7` | remove ClickUp MCP server | **deferred** | Separate decommissioning decision |
| 2026-09-22 | `18d672d`, `6e81e71`, `523c880`, others | pruning, docs, skill removals | **deferred** | Reviewed, nothing required here |

**Batch status: reviewed, zero imported.**

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
| `.claude/hooks/rtk-rewrite.sh` | rtk command rewriting | **removed 2026-09-27** — see below | rtk was never installed, so the hook never ran |

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

### rtk hook — removed 2026-09-27 (was: preserve; migration deferred)

**Superseded 2026-09-27 by the maintainer: the hook is removed and the native migration is
rejected.** `rtk` was never installed here (`command -v rtk` finds nothing), so the hook printed a
warning on every Bash call and saved nothing. It also works against this repo's reliability
model: it answers `permissionDecision: "allow"`, swaps in a rewritten command through
`updatedInput` after the reliability gate has judged the original, and hands the agent filtered
output instead of what the tool printed. Removed together: the `PreToolUse` entry in
`.claude/settings.json`, `.claude/hooks/rtk-rewrite.sh`, and the README instructions.
`~/.claude/hooks/rtk-rewrite.sh` stays until the project copies of `settings.json` that still call
it are cleaned up. Bringing rtk back is a new decision that starts with measuring what it saves here.

Historical rationale from 2026-09-22 (superseded by the removal above):

Upstream `2766626` and `9a4e396` replace the `rtk-rewrite.sh` shell hook with a native
`rtk hook claude` invocation. This is a plausible upstream improvement, not proof that the local
wrapper can safely disappear.

`.claude/settings.json` invokes the script by path in a `PreToolUse` hook, so the settings entry,
the installed hook, installer behaviour and any trust approval must move together. A git commit
alone does not coordinate a live settings file outside the repository.

**Decision at that time: keep the existing hook.** The proposed migration required checking the
installed rtk version and comparing the local script's behaviour with the native hook. Acceptance
had to cover rewritten and non-rewritten commands, argument and failure-behaviour preservation,
and continued operation of the protection mechanism. No automatic trust re-pinning.

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
Whole-file divergence between baseline and live is expected; *this particular difference* is
unexamined. Resolve it only if a desired behaviour requires it — and then by a targeted, reviewed
change to that one setting, never by replacing the file.

This section settles `config.toml` only. How the repo's agents, skills and hooks are installed and
loaded is not decided here.

Never point `CODEX_HOME` at the working tree — it also governs auth and multi-GB session/log
databases.

### Operational limits

Commit `d92d6fe` (2026-09-22) set `CLAUDE_CODE_MAX_SUBAGENT_SPAWN_DEPTH=1` and
`CLAUDE_CODE_MAX_CONCURRENT_SUBAGENTS=2` in `.claude/settings.json`. These are the tracked project
values, not a measurement of a running session — Claude Code merges several settings scopes and
the inherited environment. The global install template, `settings.json.default`, sets neither cap.
The 2026-09-22 review recorded documented defaults of depth 3 and concurrency 20.

Both variables are read by the 2.1.280 binary, each with a user-facing refusal message. The depth
variable sits beside `maxSubagentSpawnDepthFromGrowthBook`, so when it is unset the effective depth
can be supplied by remote configuration — an argument for setting it explicitly rather than relying
on a documented default.

`/goal` dispatches from the main conversation (its `SKILL.md` declares no `context:` key), so its
specialists sit at depth 1 and the configured depth-1 cap permits those direct dispatches.

These are concurrency and nesting controls, **not** a spend guarantee: `/goal`'s "at most four
delegated calls" is an instruction to the model rather than an enforced counter, there is no total
session spawn limit, the concurrency limit has documented exceptions, and no cap spans Claude and
Codex together.

### Settings keys — unrecognised key corrected

Before `d92d6fe`, the 2026-09-22 check against the 2.1.280 binary and the declared schema
(`json.schemastore.org/claude-code-settings.json`, 142 top-level properties) identified one
unrecognised key among the 15 top-level keys then in `.claude/settings.json`:

| Key | Status | Evidence |
|---|---|---|
| `maxSkillDescriptionChars` | **not a setting** | absent from the schema; zero occurrences in the binary |
| `skillListingMaxDescChars` | the real key | schema-present (`integer`, `default: 1536`); binary reads `Ye().skillListingMaxDescChars ?? 1536` |
| `awaySummaryEnabled` | valid — keep | schema-present (`boolean`, `default: true`); 11 occurrences in the binary |
| `skillListingBudgetFraction` | valid | schema-present (`number`, max 1, `default: 0.01`); `0.05` is in range |

The old `maxSkillDescriptionChars: 2048` had no effect, leaving the per-skill description cap at
the 1536 default. The schema sets `additionalProperties: true`, which is why validation never flagged it.

**Applied in `d92d6fe` (2026-09-22):** renamed the key to `skillListingMaxDescChars: 2048` and added
depth `1` and concurrency `2` to the existing `env` object. Rechecked the tracked JSON on 2026-09-27:
the new value and both caps are present, and the old key is absent. A session restart and live
enforcement of the caps have not been verified here.

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
| 2026-09-22 | `6633a1c`, `ce7e828` | subagent depth/concurrency caps | **adapted — applied in `d92d6fe`** | Set depth 1 and concurrency 2 directly in this fork's settings |
| 2026-09-22 | 12 file deletions | remove Dart/Flutter/Python-architecture/sprint capabilities | **deferred** | Retirement is a separate decision; see the per-path table |
| 2026-09-22 | `2766626`, `9a4e396` | migrate rtk hook to native invocation | **deferred** | Needs a coordinated settings + installed-hook change and a behaviour comparison |
| 2026-09-22 | `3370412` | drop unrecognised settings keys; `~/`-anchored deny rules | **adapted — applied in `d92d6fe`** | Deny-rule half already present (5 `Read(~/…)` rules). Renamed the one unrecognised key here; upstream's diff touches keys this fork does not have, so the fix was re-derived rather than imported. See "Settings keys" |
| 2026-09-22 | `a31e42c` | add `synthetic-user-research` skill | **deferred** | No identified need |
| 2026-09-22 | `1836546` | change `minimal-coding` trigger | **deferred** | Behaviour change; evaluate against `/goal` routing |
| 2026-09-22 | `180677a` | statusline rewrite | **deferred** | Adopt only if it fixes an actual problem |
| 2026-09-22 | `78521a7` | remove ClickUp MCP server | **deferred** | Separate decommissioning decision |
| 2026-09-22 | `18d672d`, `6e81e71`, `523c880`, others | pruning, docs, skill removals | **deferred** | Reviewed, nothing required here |
| 2026-09-27 | `2766626`, `9a4e396` | migrate rtk hook to native invocation | **rejected** | The rtk hook is removed here instead; see "rtk hook" |

**Batch status: reviewed. Zero imported; two change groups adapted (caps and settings-key rename),
both applied in `d92d6fe`. The rtk migration was subsequently rejected on 2026-09-27.**

Second batch: the nine upstream commits from `a31e42c` (exclusive) to `060e8a9`, reviewed on
2026-10-05 against fork HEAD `aa92a5d`.

| Date | Upstream SHA | Change | Disposition | Reason |
|---|---|---|---|---|
| 2026-10-05 | `9ca8f8e` | add `predictive-ux-evaluation` skill | **imported** | Taken verbatim into both skill trees; no overlap with existing skills |
| 2026-10-05 | `eded03b` | add `human-writing` skill | **imported** | Taken verbatim into both skill trees; README line rewritten here because upstream's README differs |
| 2026-10-05 | `9876699`, `060e8a9` | plain-wording rules against AI-writing tells | **adapted** | Three-way merged into `CLAUDE.md`, `AGENTS.md`, `CLAUDE-CHAT.md` and the Compressed output style. In `CLAUDE.md` the block sits before this fork's Action safety and Editing safety paragraphs; upstream's older Destructive action safety paragraph was not taken |
| 2026-10-05 | `cb6dd87` | move ticket metadata to native tracker fields | **adapted** | Three-way merged onto this fork's `ticket-writing`, which keeps its ClickUp-derived rules (Fields vs body, Working in a tracker); `references/rewrite-examples.md` taken verbatim |
| 2026-10-05 | `8a425b3`, `1b2d059` | retarget prompting skills; rename skill folders | **adapted** (Fable only) | `fable-5-1-prompting` replaces `fable-5-prompting`; its pointer to Opus checklists now names `opus-5-5-prompting`'s migrate mode, because this fork's package of that name has no checklists |
| 2026-10-05 | `8a425b3` | upstream's `opus-5-5-prompting` | **rejected** | This fork has its own `opus-5-5-prompting` package (added 2026-10-03) |
| 2026-10-05 | `8a425b3` | upstream's `gpt-6-prompting` | **deferred** | Differs from this fork's skill of the same name (307 vs 112 lines); needs a side-by-side comparison before either replaces the other |
| 2026-10-05 | `8a425b3` | `gemini-3-prompting` retargeted to Gemini 3.x | **deferred** | This fork retired `gemini-3-prompting` on 2026-10-03 in favour of `gemini-3-8-flash-prompting`; revisit if prompts for other Gemini 3.x models are needed |
| 2026-10-05 | `88ff88e`, `1b2d059`, `611c10c` | effort override, autocompact, subagent cap values | **rejected** | Upstream tuning of its own values. This fork never had the effort override and keeps autocompact 65 and concurrency 2 (see "Operational limits"); the `CLAUDE.md` paragraph these commits edit does not exist here |

**Second batch status: reviewed. Two skills imported, three change groups adapted, the remaining
changes rejected or deferred as listed.**

Third batch: the six upstream commits from `060e8a9` (exclusive) to `fc9318c`, reviewed on
2026-10-10 against fork HEAD `b13024c`.

| Date | Upstream SHA | Change | Disposition | Reason |
|---|---|---|---|---|
| 2026-10-10 | `c4423f8` | extend `human-writing` with scope decisions and document-specific rules | **imported** | Taken verbatim into both skill trees; this fork's copies were unchanged since the 2026-10-05 import |
| 2026-10-10 | `af9c9f0` | add `staged-docs` skill | **imported** | Taken verbatim into both skill trees, including the Codex-only `agents/openai.yaml`. It runs only when invoked (`disable-model-invocation: true`), and its review page loads scripts from cdn.jsdelivr.net. README line rewritten here because upstream's README differs; skill counts in `docs/architecture.md` updated |
| 2026-10-10 | `bf22dce` | reader and repetition rules from `human-writing` | **adapted** | Three-way merged without conflicts into `CLAUDE.md`, `AGENTS.md`, `CLAUDE-CHAT.md` and the Compressed output style; the rules sit in this fork's existing plain-wording and readers blocks |
| 2026-10-10 | `ffbd918` | `"idleCompaction": false` | **adapted** | Set in this fork's `.claude/settings.json` by the maintainer, because the reliability guard blocks agent edits to that file. The key is in the settings schema of the Claude Code 2.1.294 binary ("Set to false to stop Claude Code from compacting a long conversation while the session is idle") and absent from 2.1.289. `settings.json.default` is unchanged, so global installs keep the default |
| 2026-10-10 | `fc9318c` | replace `bmad-workflows.md` with the BMAD v7 guide | **imported** | Taken verbatim; this fork's copy was unchanged since the merge base. The guide describes Dynokostya/BMAD-METHOD, not this repository's skills |
| 2026-10-10 | `12bd8b2` | rename `CLAUDE-CHAT.md` to `web-chat-prompt.md` | **rejected** | Nine files in this fork use the name, including the installer and a reliability test. The rename changes no behaviour and would leave an installed `~/.claude/CLAUDE-CHAT.md` orphaned |

**Third batch status: reviewed. Three changes imported, two adapted, one rejected.**

Fourth batch: the three upstream commits from `fc9318c` (exclusive) to `80542b0`, reviewed on
2026-10-20 against fork HEAD `9f141d9`. `80542b0` touches 142 files, so it is split into rows by
change.

| Date | Upstream SHA | Change | Disposition | Reason |
|---|---|---|---|---|
| 2026-10-20 | `47f99d4` | force subagents to Sonnet 5.5, concurrency 5, `modelSettings` effort `high` | **rejected** | Keeps `CLAUDE_CODE_SUBAGENT_MODEL_FORCE` (see "Subagent model routing"). This fork keeps concurrency 2 and never had the effort override, and the `CLAUDE.md` paragraph the commit edits does not exist here |
| 2026-10-20 | `891f315` | Rule 2: no plain-text option menus | **rejected** | Removes a clause in upstream's Rule 2 that let long decisions skip AskUserQuestion. This fork's Rule 2 has no such clause |
| 2026-10-20 | `80542b0` | `csharp-coding`, `python-coding`, `react-coding`, `rest-api`, `shadcn-ui-coding`, `tailwind-css-coding`, `swift-coding`, `typescript-coding` | **imported** | Taken verbatim into both skill trees. Corrects the HttpClient lifetime rule (Microsoft Learn, "HttpClient guidelines for .NET"), React Compiler memoization (react.dev), Swift capture lists (The Swift Programming Language, ARC chapter), Tailwind v4 spacing and renames (Tailwind upgrade guide), shadcn Base UI `render` and Field forms (ui.shadcn.com), and Zod 4 and enum facts. Most cuts are examples. Lost rules: Python mutable default arguments, and Tailwind's ban on invented class names. `shadcn-ui-coding` now defers dark mode to `tailwind-css-coding`, so both came in together |
| 2026-10-20 | `80542b0` | `plantuml-diagramming` | **imported** | Taken verbatim as a whole directory, because SKILL.md now points to sections moved into `references/`. Its new file-placement rule repeats the `diagrammer` agent's rule without conflict |
| 2026-10-20 | `80542b0` | `human-writing`, `predictive-ux-evaluation`, `staged-docs` | **imported** | Taken verbatim into both skill trees; `staged-docs` keeps the Codex-only `agents/openai.yaml`. `human-writing` drops `references/sources.md` (an unlinked bibliography) and two minor rules. `staged-docs` asks through AskUserQuestion when the host has it and relies on the new `human-writing` |
| 2026-10-20 | `80542b0` | `fable-5-1-prompting` restructure | **adapted** | Upstream's SKILL.md and new `references/` taken. The pointer to `opus-5-5-prompting`'s migrate mode is re-applied in `references/migration.md`, where upstream moved the paragraph |
| 2026-10-20 | `80542b0` | `ticket-writing` de-duplication | **adapted** | Three-way merged. The one conflict, in Anti-patterns, is resolved with upstream's shorter list followed by this fork's five additions |
| 2026-10-20 | `80542b0` | `minimal-coding` | **rejected** | Carries the deferred `1836546` trigger change, drops the stop-control, annotation and runnable-check rules, and adds "implement the narrower interpretation", which contradicts `CLAUDE.md` Rule 2 |
| 2026-10-20 | `80542b0` | `opus-5-5-prompting`, `gpt-6-prompting`, `gemini-3-prompting`, `synthetic-user-research` | **rejected / deferred** | Dispositions unchanged from the second batch. Upstream's GPT-6 model and effort table now matches OpenAI's documentation, but this fork's package names no model IDs, so no fork fact is wrong |
| 2026-10-20 | `80542b0` | writer agents: Quality checks from project config, a Report section, `rest-api` loaded on demand, `react-code-writer` loads `typescript-coding`, Scope sections removed | **adapted** | Three-way merged into the `.claude` and `.codex` agents. This fork keeps its descriptions (without "including small fixes"), `model: inherit`, and the Codex model lines |
| 2026-10-20 | `80542b0` | `prompt-writer` loads only the target model's skill | **adapted** | The Skill tool replaces four preloaded skills; this fork's Gemini 3.8 Flash row stays. The subagent documentation (code.claude.com/docs/en/sub-agents) confirms that subagents can invoke skills through the Skill tool |
| 2026-10-20 | `80542b0` | delegation rules in `CLAUDE.md` and `AGENTS.md`; Rule 2 extension | **rejected** | This fork's `CLAUDE.md` and `AGENTS.md` follow the global versions (`b61dcbf`, `6341a2a`), whose Agents section has the main session handle small targeted work directly |
| 2026-10-20 | `80542b0` | delete `diagrammer`, `git-sync`, `project-docs`, `docs/`, `web-chat-prompt.md` | **rejected** | See "Capability deletions". `ticket-creator` and the ClickUp MCP server are already absent here |
| 2026-10-20 | `80542b0` | Compressed output style without the plain-wording block | **imported** | All three installers also install `CLAUDE.md`, which carries the same block, so sessions loaded it twice |
| 2026-10-20 | `80542b0` | installers keep destination directories when backups are off | **adapted** | `bin/cli.mjs` and `install.bat` deleted each destination directory, such as `~/.claude/skills`, before copying when backups were off. They now delete only files, as `install.sh` already did. Upstream's installer rewrite (per-entry manifest, Codex skills built from `.claude/skills`, `CLAUDE_CONFIG_DIR` and `CODEX_HOME` targets) is not taken, because `install.sh` has its own manifest and this fork keeps both skill trees. The maintainer ran `HOME=/tmp/jw-home node bin/cli.mjs --no-backup` against a temporary home with a user-owned `~/.claude/skills/my-own-skill`; the skill survived and the installer removed nothing. `install.bat` is checked by reading only, because it was not run on Windows |
| 2026-10-20 | `80542b0` | `package.json` excludes `__pycache__` | **adapted** | `npm pack --dry-run` listed two `.pyc` files from `.claude/hooks/`. npm already leaves out `.DS_Store` |
| 2026-10-20 | `80542b0` | Codex config keys and model pins | **deferred** | `sandbox_mode`, `hooks` and `[analytics]` are already in place. The Codex 0.162.0 binary contains both `max_threads` and `max_concurrent_threads_per_session`; whether `max_threads` is deprecated is not verified. The `gpt-5.6` default model is the maintainer's choice |
| 2026-10-20 | `80542b0` | `.env` read denial; statusline GNU `date` fallback | **rejected** | `Read(**/.env*)` already covers `.env`. This fork's statusline does not parse reset times |

**Fourth batch status: reviewed. Twelve skills and the output-style change imported, six change
groups adapted, the rest rejected or deferred.**

## Vendored third-party skills

Copied verbatim into both `.claude/skills/` and `.codex/skills/`; no local edits. To refresh: clone
the source, `diff -r` against both copies, copy over, and repeat the verification listed.

| Skills | Source | Revision | License | Added in | Verified |
|---|---|---|---|---|---|
| `ai-stage-gate` | `ML-SystemDesign/MLSystemDesign` | `main`, SHA not recorded | MIT | `83d0f66` | — |
| `lossless-doc-compress` | `ML-SystemDesign/MLSystemDesign` | `main`, SHA not recorded | MIT | `8acf4c7` | — |
| `ml-system-design-review` | `ML-SystemDesign/MLSystemDesign` | `main`, SHA not recorded | MIT | `86b3e63` | — |
| `scenario-blender-*` (13: router + 12 specialists) | `scenario-labs/skills`, `skills/dcc/blender/` (family `README.md` not copied) | `9624e295fa33` | MIT | 2026-09-26 | see below |
| `ex-ussr-kinship-research` | `DenisSergeevitch/ex-ussr-kinship-research`, repository root (`README.md`, `docs/cover.jpg` and `.gitignore` not copied; `LICENSE` copied) | `5a430a2e8eb1` | MIT | 2026-10-25 | see below |

**Blender family, verified 2026-09-26 on Blender 5.2.0 LTS** (upstream tested 5.2.1), headless with
`--factory-startup` via `--python-expr`: all 15 `bx_*.py` modules import; `bx_audit.audit` and
`bx_review.review` run on the default cube and the review sheet renders all rows and views; every skill
name the scripts reference (`scenario-blender-expert`, `scenario-blender-sculpting`) exists here.
Not verified: GUI-only paths (`bx_gui` strokes over a live bridge) and the per-domain workflows.

**Accepted (2026-09-26, owner) — reliability gate does not cover `blender -P`.** The policy layer's
script check runs for `source`, shells, `INTERPRETERS`, and command heads that look like scripts
(`plugins/reliability/hooks/policy.py:314-411`); `blender` matches none, and no rule in the plugin names
it, so `blender -b --python <any file>` in this repo runs without an allowlist check — the
Write-then-run path the allowlist closes for `python3`. Left as is because:

1. The allowlist is repository policy and only this repo carries one; elsewhere `python3 x.py` is
   unchecked too, so `blender -P` opens nothing new where Blender work actually happens.
2. The interpreter list is already incomplete: `/usr/bin/swift`, `/usr/bin/tclsh` and
   `/usr/bin/jshell` are installed and absent from `INTERPRETERS` (`policy.py:77-78`). One more entry
   would imply a completeness the list does not have.
3. A bare `blender` entry misparses its flags: in the skills' own `--python-exit-code 1` invocation
   the gate would take `1` as the script path and deny with a misleading reason.

Revisit as one gate review covering every uncovered interpreter, with Blender-aware argument parsing
and tests, not as a one-off entry.

**Genealogy skill, verified 2026-10-25.** `verify_tree_equivalence.py` reports both copies equivalent
to the upstream checkout with the three uncopied names excluded, and to each other. The frontmatter
`description` is 880 characters (1329 bytes in UTF-8), under the 1024-character limit that Codex
counts with `chars().count()` (`openai/codex`, `codex-rs/ext/skills/src/loader/metadata.rs`). The three
scripts use the standard library only, make no network or subprocess calls, and `init_case.py` writes
only inside `--case-dir`. The maintainer ran them from the `.claude/` copy outside Claude, with the
conda base `python3` (version not recorded): `init_case.py` created a case in `/tmp` with all seven
files, `hash_artifact.py` hashed `LICENSE`, and `audit_evidence.py` reported no errors or warnings on
the empty registers. Not verified: the audit on filled registers, and the research workflow itself.
In this repository the reliability policy denies the scripts to agents until the owner pins them in
`.claude/allowed-scripts.json`; repositories without an allowlist run them unchecked.

### Removed 2026-09-27 — ResumeSkills-derived Codex career skills

Commit `895d25e` copied eight skills from `Paramchoudhary/ResumeSkills` (`skills/<name>/SKILL.md`,
upstream `main`, now at `74ae19e7c62b`) into `.codex/skills/` without a row in the table above:
`application-form-filler`, `interview-prep-generator`, `job-description-analyzer`,
`linkedin-profile-optimizer`, `resume-bullet-writer`, `resume-formatter`, `resume-tailor`,
`resume-version-manager`. Two were verbatim; the rest carried partial safety edits, and several still
held worked examples that invented metrics, customers and awards, or upgraded "assisted" to "led".
They were removed together with the locally written `career-facts-guardrail`, whose rules moved into
`career-application-builder`. Replacements are written here, not vendored: `job-triage`,
`interview-drill`, and the `cv-claim-verifier` agent.

The copies remain in git history between `895d25e` and their removal. Upstream notice, for that
history:

```text
MIT License

Copyright (c) 2026 Resume Skills

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

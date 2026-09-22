# /goal — selective model routing

`/goal <task>` runs a dispatcher policy in the main Claude Code session. It picks the shortest route to the goal and skips every role the task does not need. It is not a standing agent team, and it does not run all roles on every task.

## What is here

| File | Role |
|---|---|
| `SKILL.md` | The dispatcher policy — route selection, budget, hand-off rules |
| `../../agents/goal-architect.md` | Architecture decision, read-only |
| `../../agents/goal-implementer.md` | Implementation + verification, sole writer |
| `../../agents/goal-security.md` | Security review, read-only |
| `scripts/codex-review.py` | Narrow bridge to the official Codex CLI |
| `router.local.example.json` | Config template — copy to `router.local.json` |

## Roles

| Role | Model | Effort | Tools | maxTurns |
|---|---|---|---|---|
| Architect | `claude-fable-5-1` | xhigh | Read, Glob, Grep | 12 |
| Implementer | `claude-opus-5-5` | medium | Read, Glob, Grep, Edit, Write, Bash | 24 |
| Security | `claude-opus-5-5` | xhigh | Read, Glob, Grep | 12 |
| Codex reviewer | `gpt-6-astra` | high | read-only sandbox | — |

Models are set by the `model:` frontmatter field, not by the agent's name or by telling it what it is.

## The limits are policy, not a counter

**Read this before relying on the budget.** The "at most four delegated calls" and "one corrective hand-back" rules in `SKILL.md` are instructions to the dispatcher model. They are not enforced by a hard counter anywhere in the session, and nothing in this skill can stop a run that ignores them. `maxTurns` is the only mechanical limit here, and it bounds a *single subagent run* — not the cost of the goal, and not the number of runs.

There is likewise no combined spend cap across Claude and Codex: they are separate processes billed on separate routes. If you need a real ceiling, watch it yourself.

## Codex bridge

Safe by default:

- Dry-run unless you pass `--run` **and** set `"backend_enabled": true`. Dry-run performs no inference — it prints the exact argv and exits.
- `--ask-for-approval never` (a top-level `codex` flag) with `--sandbox read-only`; dangerous bypass flags are rejected even if a config asks for them.
- argv list via `subprocess`, never `shell=True`; task text arrives on stdin, so shell metacharacters in the task are inert.
- One runner per repository, enforced by a lock file.
- Timeout kills the whole process group. It cannot cancel generation the provider has already started.
- Every run gets its own directory with `0700`/`0600` permissions: full JSONL stdout, stderr, the final message, and `report.json`. Nothing is auto-deleted.

Reported model and token usage are recorded **only** when the runtime actually emits them; otherwise they read `unknown`. The requested values are never echoed back as if they were confirmation.

A sandbox flag is not blanket isolation. Codex inherits whatever MCP servers and hooks its own config defines, and those are outside this runner's control — review that surface before enabling the backend.

## First run

Config:

```bash
cd ~/babenko-dev/just-works/.claude/skills/goal
cp router.local.example.json router.local.json
```

`router.local.json` and `logs/` are already covered by this directory's `.gitignore`.

The runner and its tests must also be sha256-pinned in `.claude/allowed-scripts.json`, or the reliability policy refuses to execute them. Re-pin after any edit to those files — changing a pinned script revokes its permission until the hash is updated.

Dry-run (no inference, safe to run now):

```bash
python3 scripts/codex-review.py --task /tmp/review-task.txt --dry-run
```

Real run — only after you have set `backend_enabled: true` and accepted sending code to a second provider:

```bash
python3 scripts/codex-review.py --task /tmp/review-task.txt --run
```

Claude side, per-session only — these do not persist as defaults:

```bash
claude --model claude-opus-5-5 --effort medium     # ordinary orchestration
claude --model claude-fable-5-1 --effort xhigh     # specialised architecture work
```

Plain `claude` and `codex` keep working exactly as before.

## Examples

```text
/goal Fix the /help text wording. Done when the string renders correctly.

/goal Add admin roles and access separation. Done when tests pass and a
      security review finds no unresolved high-severity finding.
```

The first should stay in the main session with no delegation at all. The second is the route that justifies architect → implementer → security.

## Known limitations

- Effort is `xhigh` everywhere except the implementer. `max` exists and is accepted, but the top of the range earns its cost only where measurement shows headroom at `xhigh` — escalate deliberately for a specific audit rather than standing.
- Opus 5.5 requires Claude Code 2.1.280+. A host pinned to an older build (for example an IDE extension shipping its own binary) rejects the implementer and security roles with a 400, regardless of local config.
- The implementer holds `Bash`, so its "do not launch other CLIs" boundary is an instruction, not enforced isolation.
- Concurrent editing is unsupported. It would need separate worktrees and explicit integration.

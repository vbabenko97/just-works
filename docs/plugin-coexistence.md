# Plugin and project hooks, measured

Stage 1 of moving the reliability harness out of this repository and into a plugin.
Nothing enforces yet: the plugin installed here emits no permission decisions, so
it could be loaded for real without any risk of denying work. That mattered
because none of this is observable in a sandbox — `HOME=/tmp/... claude -p` fails
unauthenticated, and `CLAUDE_CONFIG_DIR` relocates credentials along with the
config, so the only way to measure coexistence is to load the plugin on the real
machine.

Measured on Claude Code 2.1.220 at `6b47657`.

## Why a plugin rather than an installer script

Verified against the installed official plugins, not assumed:

- hook commands use `${CLAUDE_PLUGIN_ROOT}`, a stable installed path that never
  passes through the open project
- `installed_plugins.json` records `"scope": "user"`, so an enabled plugin applies
  to every project
- `claude plugin validate` checks both manifests before anything is installed
- installing writes **no** hook configuration into `~/.claude/settings.json`

The last point removes most of the work an installer script would have had to get
right: preserving unrelated hooks and env, byte-stable reinstallation, atomic
writes, recoverable partial installs, and an uninstall that removes only its own
entries. `claude plugin install` / `uninstall` / `update` own all of it.

## Exact change to user settings

`~/.claude/settings.json`, 2543 → 2726 bytes, sha256 `48cc9d66…` → `86cf660b…`.
Two keys changed, both additive:

```
enabledPlugins           + "reliability@just-works": true      (7 -> 8 entries)
extraKnownMarketplaces   + "just-works": { "source": { "source": "directory",
                             "path": "/Users/vitaliibabenko/babenko-dev/just-works" } }
```

`hooks` was not touched: still one `PreToolUse` entry, the pre-existing `Read` one.

## Resolved paths, and one discrepancy

```
installPath (recorded)   ~/.claude/plugins/cache/just-works/reliability/0.1.0
CLAUDE_PLUGIN_ROOT       <repo>/plugins/reliability        <- what actually runs
gitCommitSha (pinned)    6b476575d448dde2f67486e944c9ee75e790c2b8
```

A `directory`-source marketplace records a cache path but runs from the live
checkout. Convenient while developing — edits apply with no `plugin update` — and a
dependency to be aware of: moving or deleting the checkout breaks an installed
plugin. A `github`-source install would run from the cache copy instead.

`CLAUDE_PLUGIN_ROOT` was identical in every record, including from
`/private/tmp/scratch-proj`, so it does not vary with the project.

## Handler counts

One session (`d061f8cf`) running a Bash call, a Read, and an Explore agent. Each
line is one plugin process; the project harness ran its own handlers alongside.

| label | tool | agent_id | agent_type | pid |
|---|---|---|---|---|
| PreToolUse:any | Bash | — | — | 57932 |
| PreToolUse:Bash | Bash | — | — | 57933 |
| PreToolUse:any | Read | — | — | 57963 |
| PreToolUse:any | Agent | — | — | 58268 |
| SubagentStart | — | a58717635230e4d8f | Explore | 58283 |
| PreToolUse:Bash | Bash | a58717635230e4d8f | Explore | 58288 |
| PreToolUse:any | Bash | a58717635230e4d8f | Explore | 58289 |

- **Every matching matcher runs.** A Bash call matched both `Bash` and `*` and ran
  two separate processes. Adding the project's own Bash handler, one Bash call in
  this repository executes three PreToolUse handlers. Assume both sources run;
  they do.
- **`agent_id` and `agent_type` appear on `SubagentStart` and on subagent
  `PreToolUse`, and are absent in the main session** — independently confirming,
  through the plugin path, the payload facts the receipt design depends on.
- **Receipts are not issued twice.** The project's `SubagentStart` hook created
  `.claude/receipts/d061f8cf-…/` for the one Explore agent; the plugin observed the
  same event and issued nothing. One issuer, one receipt.
- **Policy is seen identically.** Both copies resolve the project from the same
  payload, so `policy_manifest`, `allowlist` and `receipts_dir` read the same in
  both. In `/tmp/scratch-proj` all three were false, and `is_git` was false too —
  the no-policy, non-git case is distinguishable at the point of decision.

## Precedence: neither copy can weaken the other

Two deliberate probes, using `RELIABILITY_TRACE_DECISION` to make the plugin
decide, with commands whose project verdict was known and harmless.

| plugin says | project says | outcome | reason surfaced |
|---|---|---|---|
| `allow` | `deny` (`npm run build`) | **blocked** | the project's |
| `deny` | `allow` (`ls -la README.md`) | **blocked** | the plugin's |

So decisions from user-scope plugin hooks and project hooks are unioned, with deny
taking precedence, and the plugin's decisions are genuinely honoured — the first
probe alone would not have shown that. The consequence for migration: an older
copy on either side can only ever be *more* restrictive than the newer one. A
stale copy can produce a false denial; it cannot permit something the current copy
would refuse. Overlap during the migration is therefore fail-closed, which is what
makes it safe to enforce from the plugin before the project's own matchers are
removed.

## Where the executing code actually lives

The stage-1 result above — `CLAUDE_PLUGIN_ROOT` pointing at the working tree — was
correct but not general. It is a property of the marketplace *source type*, and the
fix is to distribute the other way.

| marketplace source | executing root | edits to the checkout |
|---|---|---|
| `directory` (local path) | the checkout itself | apply immediately |
| `github` (owner/repo) | `~/.claude/plugins/cache/<marketplace>/<plugin>/<version>/` | ignored until updated |

Re-measured after reinstalling from `vbabenko97/just-works`, recorded by the hook
process itself rather than read from the environment:

```json
{"plugin_root":  "~/.claude/plugins/cache/just-works/reliability/0.1.1",
 "executing_file": "~/.claude/plugins/cache/just-works/reliability/0.1.1/hooks/trace.py",
 "under_cache": true}
```

`executing_file` is `pathlib.Path(__file__).resolve()`, so it is what ran, not what
the harness said should run. Both agree, and both are under the versioned cache.

Three activation properties, each measured:

- **Renaming the source checkout does not break the installed plugin.** With the
  checkout moved to `just-works-MOVED`, a session in an unrelated directory still
  fired the hooks and recorded `under_cache: true`. The marketplace is a clone of
  the remote and the plugin is a copy inside the cache; neither references the
  working tree.
- **Editing the checkout does not silently change enforcement.** The trace carries a
  `SOURCE_MARKER`. Flipped from `stage2-a` to `stage2-b` in the checkout, a session
  run immediately afterwards still reported `stage2-a`.
- **Activation requires update, reload, and a version bump.** `claude plugin update`
  is keyed on the version declared in `plugin.json`, not on the commit: pushing
  changed code inside an unchanged `0.1.0` produced *"already at the latest version
  (0.1.0)"* and the cache kept the old file. Only after bumping to `0.1.1`, pushing,
  `claude plugin marketplace update`, `claude plugin update reliability@just-works`
  and a new session did the trace report `stage2-b` from `.../0.1.1/`.

Two operational consequences. Any change to enforcement must bump the plugin
version, or installed copies keep running the previous code with no error anywhere.
And `claude plugin update reliability` fails with *"Plugin not found"* — the
qualified `reliability@just-works` is required.

## Open risks

- **Disarm surface.** `enabledPlugins` lives in `~/.claude/settings.json`, which is
  protected from Write/Edit, but `claude plugin disable`, `claude plugin uninstall`
  and `claude plugin marketplace remove` mutate it through the CLI, which the Bash
  classifier does not currently recognise. Choosing the plugin route makes those
  commands a bypass, and they have to join the universal denials.
- **Checkout dependency** applies to `directory` sources only, and is the reason to
  distribute via the `github` source. A local-path install runs the working tree, so
  an uncommitted edit changes enforcement immediately and with no record.
- **Silent staleness.** Because update is version-keyed, an installed copy can run
  code several commits old while the repository looks current. Nothing warns.
- **Duplicate handler cost.** Three processes per Bash call during any overlap
  period. Harmless but not free.

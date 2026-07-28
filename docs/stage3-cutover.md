# Stage 3: a reversible cutover from project hooks to the plugin

Every command here is literal. Nothing in this document is executed by the agent
except where it says so: the removals and the rollback are owner operations, because
the Bash guard's protected-path check deliberately does not consult
`maintenance_auth`, so `rm` and `git rm` on the guarded files are refused with or
without an authorization. That was a deliberate decision — an authorization must
never relax the Bash gate — and it means the agent cannot dismantle the harness even
when asked to.

**Status: complete.** Steps 1–7 have been carried out. The plugin is the only
enforcement in this repository; the project matchers and guard files are gone. Two
defects the plan itself contained are recorded in Step 5 and Step 7 — read those before
using this document as a template for another repository.

## Step 0 — parity, before any cutover is attempted

**Done.** Written as a precondition; every row below now exists. The plugin observes and
decides. Disabling the project matchers before this point would have left the machine
unguarded rather than migrated. Stage 3 could not start until the plugin had:

| missing | replaces | notes |
|---|---|---|
| `hooks/guard_bash.py` | `guard_destructive_bash.py` | hook entry point calling `engine.decide_bash` |
| `hooks/guard_paths.py` | `guard_protected_paths.py` | entry point calling `engine.decide_paths` |
| `hooks/gate.py` + `hooks/run_gate.sh` | `scripts/hooks/hook_gate.py`, `run_gate.sh` | the fail-open matrix applies to plugin hooks identically; a guard that cannot run must still deny |
| `hooks/receipts.py` | `scripts/hooks/subagent_receipts.py` | issue *and* verify, gated on `require_subagent_receipts` |
| `hooks/contract.py` | `.claude/hooks/inject_contract.py` | delivery moves to the plugin; the contract *text* stays repository policy, its path declared in the manifest |
| authorization reader | `maintenance_auth.py` | project-scoped auth for policy paths, home-scoped for `~/.claude` |
| `hooks.json` rewired | — | from `trace.py` to the guards, keeping the trace as a separate observer |

All of it is new plugin code, so none of it needs a maintenance authorization. Known
duplication to accept: `maintenance_auth.py` stays in the project because
`bulk_mutate.py` uses it, while the plugin needs its own reader for the same file
format.

## Installed plugin identity

```
plugin           reliability@just-works        (scope: user)
marketplace      github: vbabenko97/just-works
installPath      ~/.claude/plugins/cache/just-works/reliability/8dcc512e4a4d
revision         8dcc512e4a4d
gitCommitSha     8dcc512e4a4db0899da88c6a25e28ba8c5f080c8
```

No declared version, so the revision *is* the source commit. Confirm before cutover:

```
claude plugin list
python3 -c "import json,os; print(json.load(open(os.path.expanduser('~/.claude/plugins/installed_plugins.json')))['plugins']['reliability@just-works'])"
```

## Step 1 — authorization (owner, plain terminal)

```
python3 scripts/verify/authorize_maintenance.py \
  --minutes 120 \
  --reason 'stage 3 cutover: disable project hook matchers, pin plugin suites' \
  --op 'Edit:.claude/settings.json:6' \
  --op 'Edit:.claude/allowed-scripts.json:4'
```

Binds to HEAD, so issue it immediately before the edits and do not commit in between
— a commit changes HEAD and voids the remaining uses.

## Step 2 — disable the matchers, delete nothing

Three `PreToolUse` entries exist. Entry 0 also carries an unrelated hook,
`rtk-rewrite.sh`, which **must survive**: only the `run_gate.sh` line leaves.

Resulting `.claude/settings.json` diff:

```diff
   "PreToolUse": [
     { "matcher": "Bash",
       "hooks": [
         { "type": "command",
           "command": "bash -c 'exec \"$HOME/.claude/hooks/rtk-rewrite.sh\"'" },
-        { "type": "command",
-          "command": "bash \"$CLAUDE_PROJECT_DIR/scripts/hooks/run_gate.sh\" guard_destructive_bash.py || exit 2",
-          "timeout": 30 }
       ] },
-    { "matcher": "Write|Edit|MultiEdit|NotebookEdit",
-      "hooks": [
-        { "type": "command",
-          "command": "bash \"$CLAUDE_PROJECT_DIR/scripts/hooks/run_gate.sh\" guard_protected_paths.py || exit 2",
-          "timeout": 30 } ] },
-    { "matcher": "*",
-      "hooks": [
-        { "type": "command",
-          "command": "bash \"$CLAUDE_PROJECT_DIR/scripts/hooks/run_gate.sh\" --receipt-only || exit 2",
-          "timeout": 30 } ] }
   ]
```

Then create the project's own policy manifest, which is what re-enables the policy
layer under the plugin:

```json
{
  "policy_version": 1,
  "contract_version": "tier1-2026-07-28",
  "allowlist": ".claude/allowed-scripts.json",
  "contract": ".claude/reliability-contract.md",
  "protected": ["scripts/verify/", "scripts/hooks/", ".claude/hooks/"],
  "maintenance": {
    "issuer": "scripts/verify/authorize_maintenance.py",
    "ledger": ".claude/maintenance-uses.jsonl"
  },
  "require_subagent_receipts": true
}
```

## Step 3 — prove the plugin alone enforces (fresh session)

The session must be new: hooks load at startup. Run from this repository, which now
has a valid manifest and no project matchers.

```
claude plugin update reliability@just-works
```

Then in a fresh session, each of these must be **denied**, and the reason must name
the plugin rather than the project guard:

```
rm -rf build
git push --force origin main
git clean -fdx
printf 'x' > .claude/settings.json
claude plugin disable reliability
npm run build
bash install.sh --help
```

and each of these must be **allowed**:

```
ls -la
git status --short
git diff --stat
python3 tests/reliability/test_maintenance_auth.py
cat README.md
```

The last must-deny is any local script that is not pinned in
`.claude/allowed-scripts.json`. It used to read `bash
tests/reliability/fixtures/make_fixtures.sh`, which was pinned *and* has since been
deleted, so it demonstrated nothing.

Subagent receipts, with `require_subagent_receipts: true`: spawn an Explore agent and a
Plan agent, then confirm one receipt each and that a fabricated `agent_id` with no
receipt is refused. Receipts are written under `${CLAUDE_PLUGIN_DATA}`:

```
~/.claude/plugins/data/reliability-just-works/receipts/<repo-identity>/<session-id>/<agent-id>.json
```

**Not** under `.claude/receipts/`. That was the stage-1 location and moving it out of
the repository is the point: an agent that can write inside the repository must not be
able to manufacture the proof that it was constrained. `<repo-identity>` is a name plus
a digest of the git remote, so moving the checkout does not orphan the receipts. The
manifest still protects `.claude/receipts/` in case an old directory lingers.

In a directory with no manifest — `/tmp/scratch-proj` — `npm run build` must be
allowed and `rm -rf .` must be denied.

## Step 4 — rollback, immediately, if step 3 fails

Owner, plain terminal. `.claude/settings.json` has not changed since `1dd0e8c`, so
the frozen baseline is byte-exact:

```
cd /Users/vitaliibabenko/babenko-dev/just-works
git checkout 1dd0e8c -- .claude/settings.json
git diff --stat HEAD -- .claude/settings.json
shasum -a 256 .claude/settings.json
```

Nothing was deleted at this point, so restoring the file restores enforcement in
full. Start a fresh session and confirm with:

```
python3 tests/reliability/test_configured_gate.py
```

which reads the command strings out of `.claude/settings.json` and runs them.

That rollback path expired at Step 6. `test_configured_gate.py` was deleted with the
wiring it asserted, so after the removal commit this step no longer exists: rolling back
means reverting that commit, not restoring one file. The equivalent check against the
plugin manifest is the plugin's own `tests/test_manifest_commands.py`.

Optionally disable the plugin while diagnosing:

```
claude plugin disable reliability@just-works
```

## Step 5 — owner removes the obsolete files

Only after step 3 passes. These are refused to the agent by design:

```
cd /Users/vitaliibabenko/babenko-dev/just-works
git rm .claude/hooks/guard_destructive_bash.py
git rm .claude/hooks/guard_protected_paths.py
git rm .claude/hooks/reliability_paths.py
git rm .claude/hooks/inject_contract.py
git rm scripts/hooks/hook_gate.py
git rm scripts/hooks/run_gate.sh
git rm scripts/hooks/subagent_receipts.py
```

**Kept deliberately:**

```
.claude/hooks/maintenance_auth.py        still used by bulk_mutate.py
.claude/hooks/rtk-rewrite.sh             unrelated, still wired
.claude/reliability-contract.md          policy: the contract text
.claude/allowed-scripts.json             policy: reviewed script pins
.claude/reliability-policy.json          policy: the manifest itself
scripts/verify/                          owner tooling and the issuer
tests/reliability/                       the surviving 80 checks
```

### Defect in this list: `reliability_paths.py` — fixed forward

`bulk_mutate.py` imported **two** things from `.claude/hooks/`, not one:

```python
from reliability_paths import is_protected
import maintenance_auth
```

The list above recorded only `maintenance_auth.py`, so removing
`.claude/hooks/reliability_paths.py` broke `bulk_mutate.py` outright and with it all 10
checks in `test_plan_apply_drift.py`:

```
ModuleNotFoundError: No module named 'reliability_paths'
```

Repaired forward, not by restoring the deleted hook. `scripts/verify/repo_policy.py` now
owns the question for owner tooling:

- it defines the mandatory universal repository set, duplicated from the plugin's
  `hooks/rules.py` and drift-checked by parsing that source in
  `tests/reliability/test_owner_policy.py`. Duplication rather than import, because an
  owner tool must keep working with the plugin absent, disabled or mid-update;
- it loads and validates the manifest strictly, and **raises** on a manifest that is
  present but malformed, unsupported, carrying unknown keys, or naming a path that
  climbs out of the repository;
- it returns the union of the universal and policy-declared sets;
- it raises on a path lexically inside the repository that resolves outside it, rather
  than reporting an escape route as an ordinary path;
- it keeps the home-scope set, because this wrapper can genuinely reach it: `install.sh`
  syncs skills into `${CLAUDE_HOME}/skills` and `${AGENTS_HOME}/skills`, so a cleanup
  rooted at `~/.claude` would otherwise be free to enumerate `~/.claude/hooks/`.

`bulk_mutate.protected_refusals()` turns either exception into a refusal, in both the
plan and apply phases. The pre-existing containment invariant (`within()`, checked in
both phases) is untouched and still fires first on an escaping target.

Both files live under `scripts/verify/`, which is protected, so the repair needed a
plugin maintenance authorization — `Write` on the new module, `Edit` on the wrapper,
`Edit` on the allowlist to re-pin the changed hash. The Bash gate is never relaxed by
one, so `rm` on these paths stays refused throughout.

Removing `scripts/hooks/` also made `test_configured_gate.py` and `test_hook_gate.py`
obsolete. The plan estimated 49 of the 318 checks would be stranded; the real figure is
**281 deleted plus 9 trimmed**, because the guard suites went too. `docs/parity-map.md`
carries the file-by-file outcome.

## Step 6 — commit the removal

```
git add -A
git commit -F <message file>
git push origin main
```

`git add -A` only if the working tree holds nothing else. Stage the cutover paths by
name otherwise — this repository carried unrelated untracked drafts at the time, and
they must not ride along in an enforcement commit.

## Step 7 — plugin-only cold-start acceptance

Fresh session after the commit. Repeat every check in step 3. The surviving project
suites, which an agent can run because they are pinned in the allowlist:

```
python3 tests/reliability/test_owner_policy.py
python3 tests/reliability/test_maintenance_auth.py
python3 tests/reliability/test_plan_apply_drift.py
python3 tests/install/test_personal_guard.py
```

### The plugin suites are an owner operation

The plan listed them as agent-runnable, by absolute path. They are not:

```
python3 ~/.claude/plugins/cache/just-works/reliability/<rev>/tests/test_policy_states.py
[reliability/policy] Blocked: execution of a script outside the project: ...
```

The policy layer refuses execution of any script outside the project, and the guard's
notion of "the project" is the session's project directory — it comes from
`CLAUDE_PROJECT_DIR`, so `cd /tmp` first does not change it. Inside a repository with a
valid manifest, every plugin suite is unreachable by design. Run them yourself, from a
directory with **no** manifest, where the policy layer is inactive:

```
cd $(mktemp -d)
rev=$(basename ~/.claude/plugins/cache/just-works/reliability/*/ | tail -1)
for t in test_policy_states test_monotonic test_optional_policy test_distribution \
         test_auth test_gate test_receipts test_bash_corpus test_manifest_commands; do
  python3 ~/.claude/plugins/cache/just-works/reliability/$rev/tests/$t.py || echo "FAILED: $t"
done
```

The suites run from the installed cache path, not the checkout, so acceptance tests the
copy that is actually enforcing. Confirm from the trace that `executing_file` is under
`~/.claude/plugins/cache/` and `under_cache` is true:

```
tail -1 ~/.claude/reliability-trace.jsonl | python3 -m json.tool | grep -E 'under_cache|revision|executing_file'
```

Then confirm the authorization is inactive and re-prove a protected edit and a
recursive deletion are still denied.

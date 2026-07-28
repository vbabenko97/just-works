# Stage 3: a reversible cutover from project hooks to the plugin

Every command here is literal. Nothing in this document is executed by the agent
except where it says so: the removals and the rollback are owner operations, because
the Bash guard's protected-path check deliberately does not consult
`maintenance_auth`, so `rm` and `git rm` on the guarded files are refused with or
without an authorization. That was a deliberate decision — an authorization must
never relax the Bash gate — and it means the agent cannot dismantle the harness even
when asked to.

## Step 0 — parity, before any cutover is attempted

**Not yet built.** The plugin observes; it does not decide. Disabling the project
matchers today would leave the machine unguarded, not migrated. Stage 3 cannot start
until the plugin has:

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
bash tests/reliability/fixtures/make_fixtures.sh
```

and each of these must be **allowed**:

```
ls -la
git status --short
git diff --stat
python3 tests/reliability/test_guard_bash.py
cat README.md
```

Subagent receipts, with `require_subagent_receipts: true`: spawn an Explore agent and
a Plan agent, then confirm one receipt each under `.claude/receipts/<session-id>/`,
and that a fabricated `agent_id` with no receipt is refused.

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
tests/reliability/                       the frozen 318 checks
```

Note that removing `scripts/hooks/` makes `tests/reliability/test_configured_gate.py`
and `test_hook_gate.py` obsolete along with it — 49 of the 318 checks test files that
will no longer exist. They should be deleted in the same commit, and the README total
corrected, rather than left to fail.

## Step 6 — commit the removal

```
git add -A
git commit -F <message file>
git push origin main
```

## Step 7 — plugin-only cold-start acceptance

Fresh session after the commit. Repeat every check in step 3, and additionally:

```
python3 tests/reliability/test_guard_bash.py
python3 tests/reliability/test_script_indirection.py
python3 tests/reliability/test_protected_paths.py
python3 tests/reliability/test_plan_apply_drift.py
python3 tests/reliability/test_maintenance_auth.py
python3 tests/install/test_personal_guard.py
python3 /Users/vitaliibabenko/.claude/plugins/cache/just-works/reliability/<rev>/tests/test_policy_states.py
python3 .../tests/test_monotonic.py
python3 .../tests/test_optional_policy.py
python3 .../tests/test_distribution.py
```

The plugin suites run from the installed cache path, not the checkout, so acceptance
tests the copy that is actually enforcing. Confirm from the trace that
`executing_file` is under `~/.claude/plugins/cache/` and `under_cache` is true.

Then confirm the authorization is inactive and re-prove a protected edit and a
recursive deletion are still denied.

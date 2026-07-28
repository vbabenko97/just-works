# Parity map: the frozen 318 against their plugin equivalents

Every frozen check is accounted for under one of four labels.

| label | meaning |
|---|---|
**ported** | the same cases, individually, against the plugin |
**equivalent or replaced** | a named plugin check exercising the same failure mode — consolidated, or asserted against the plugin manifest instead of the project's wiring |
**retained** | the project-local component still exists, so the project check stays |
**retired** | deliberately dropped, and the behaviour is genuinely gone |

Totals: 318 frozen checks → **121 ported, 163 equivalent or replaced, 28 retained,
6 retired**.

Only 6 checks are retired. An earlier version of this table counted 39, folding in the
33 project-wiring assertions — that was wrong. A check whose failure mode is still
asserted, against a different configuration file, has been *replaced*, not dropped.
Calling it retired overstated what the cutover gave up by more than a factor of six,
and in the one direction that matters: it made lost coverage look acceptable.

Retained fell from 37 to 28 when the cutover completed. Nine checks in
`test_maintenance_auth.py` drove the project's own hook files, so they went when those
files were deleted; they were already ported to the plugin's `test_auth.py` and are
counted there.

## test_guard_bash.py — 112 → **ported**, verbatim

`plugins/reliability/tests/test_bash_corpus.py`, 112/112, all 65 MUST_DENY and 47
MUST_ALLOW cases copied case by case, including the three historical false positives:
the loop variable named `ln`, the word `patch` appearing as search data, and the
unexpanded `$CLAUDE_PROJECT_DIR` in a script path that must *stay* refused.

The fixture mirrors this repository's policy — a valid manifest and an allowlist
pinning the same reviewed scripts by hash — because that is the configuration the
original verdicts were recorded under.

Porting it found a real defect: `python3 -m pip install ./local` had become an allow,
because the installer-module case was dropped when the policy layer was written.
Class-level coverage did not catch that; the individual case did.

## test_script_indirection.py — 55 → **equivalent**, with one retirement

Verdicts depend on allowlist membership and content hash, and both are exercised:

| frozen behaviour | plugin equivalent |
|---|---|
| unreviewed script denied, by every route (`bash`, `sh`, `./x`, `python3`, `node`, `source`, `.`, `env bash`, `bash -c`) | `test_bash_corpus` — 9 route cases |
| pinned script allowed while the hash matches | `test_bash_corpus` (4 pinned scripts), `test_policy_states` "pinned script allowed" |
| pinned script denied once edited | `test_policy_states` "unpinned script denied", `test_auth` hash-mismatch path |
| script outside the project denied | `test_policy_states`, `test_bash_corpus` (`git apply /tmp/fix.diff`) |
| variable-derived path denied | `test_bash_corpus` — 3 cases |
| missing allowlist denies everything | `test_policy_states` — absent and invalid manifests |

**Retired, 6 checks:** the *git-state labels* — "untracked", "modified relative to
git", "tracked and unmodified". No verdict depends on them; `git_state()` is called
only to build the denial message. The plugin's reason names the allowlist and the
pinned-versus-actual hash instead, which is the actionable part. Running `git` on the
deny path also costs two subprocesses per refusal.

## test_protected_paths.py — 45 → **equivalent**

| frozen behaviour | plugin equivalent |
|---|---|
| Write/Edit/MultiEdit/NotebookEdit on protected paths denied | `test_monotonic` — 5 project paths × Edit, 3 home paths × Write; `test_policy_states` — 4 tools under an invalid manifest |
| Bash routes to the same files denied (`cp`, `sed -i`, `install`, redirect, `git checkout`) | `test_bash_corpus` — 3 cases; `test_monotonic` — 7 protected routes × 3 states |
| reading them stays allowed | `test_bash_corpus` — `cat`, `grep`, `git diff`, `git add` on the guard |
| an authorization permits exactly the listed operation | `test_auth` — 34 checks |
| symlink to a protected path resolved and denied | `test_monotonic` |

Broader than the original in two ways: the plugin protects `~/.claude` as well as the
project copy, and it protects the manifest and allowlist at fixed paths so they cannot
be deleted to drop enforcement.

## test_plan_apply_drift.py — 10 → **retained**

`scripts/verify/bulk_mutate.py` stays project-local; it is owner tooling, not
enforcement, and nothing in the plugin replaces plan/apply drift detection. The suite
stays exactly as it is and keeps passing.

## test_maintenance_auth.py — 27 → **ported** to `test_auth.py` (34), and **partially retained** (18 of 27)

Ported: every binding broken in turn — no authorization, malformed, missing keys,
unknown scope, expired, wrong repository, wrong commit, wrong tool, wrong path, budget
exhausted, unreadable ledger, and the invariant that an active authorization never
relaxes the Bash gate. Added: the global scope, revision binding, and the issuer's own
input validation.

Retained, 18: everything calling `maintenance_auth.check()` directly. That module stays
in the project because `bulk_mutate.py` reads it, so the suite still covers a live
component.

Dropped from the project side at the cutover, 9 — these drove hook files that no longer
exist, and each is covered by the plugin check named beside it:

| dropped project check | ran through | plugin equivalent |
|---|---|---|
| authorized Edit is allowed by the hook | `guard_protected_paths.py` | `test_auth` — authorized-path allow |
| unlisted protected path still denied | `guard_protected_paths.py` | `test_auth`, `test_monotonic` |
| partly-authorized batch refused whole | `guard_protected_paths.py` | `test_auth` — MultiEdit all-or-nothing |
| recursive rm still denied | `guard_destructive_bash.py` | `test_auth` — authorization never relaxes the Bash gate |
| unreviewed script still denied | `guard_destructive_bash.py` | same |
| force push still denied | `guard_destructive_bash.py` | same |
| redirect over an authorized path still denied | `guard_destructive_bash.py` | same |
| `cp` over an authorized path still denied | `guard_destructive_bash.py` | same |
| opaque `git apply` payload still denied | `guard_destructive_bash.py` | same |

The invariant those six protected — that a maintenance authorization is a door for
file edits and never an amnesty for Bash — is the one the plugin asserts structurally:
`guard_bash.py` does not import the authorization reader at all.

## test_hook_gate.py — 17 → **ported** to `test_gate.py` (25)

All 17 failure modes — syntax error, import error, missing file, exit 1, exit 127,
malformed JSON, unexpected stdout, silence, `ask`, wrong event, unknown decision,
timeout — plus the gate itself broken in four ways, the launcher missing or
unparseable, and a latency assertion that did not exist before and immediately caught
the watchdog defect.

## test_subagent_receipts.py — 20 → **ported** to `test_receipts.py` (28)

All 20 — issue and verify, absent, wrong session, wrong agent, wrong type, wrong
contract version, future-dated, stale, malformed, main-session exemption — plus the
three policy states, delivery through the real hook, and two new checks that receipts
are written under the plugin data directory and *not* into the repository.

## test_configured_gate.py — 32 → **equivalent** in `test_manifest_commands.py` (29)

Same design: command strings read verbatim from the manifest, run through a shell
against a sabotaged replica, with a pristine control and live probes. Same nine
sabotages. **Consolidated 32 → 29:** the frozen version ran every sabotage against
three configured matchers where two now exist, so 9×3 became 9×2, and the freed budget
went to two guard-specific sabotages and four live probes against the installed cache.
No failure mode was dropped.

**Retired, 33 checks across the suite family:** everything asserting the *project*
wiring specifically — `$CLAUDE_PROJECT_DIR/scripts/hooks/run_gate.sh` resolving,
`--receipt-only` as a separate matcher, the `*` matcher being third. Those describe a
configuration that Stage 3 removes. The behaviour they protected — that the outermost
configured command fails closed — is asserted against the plugin manifest instead.

## Retirement summary

| retired | count | why |
|---|---|---|
| git-state labels in denial messages | 6 | no verdict depends on them; message detail only |

Six, and no more. `git_state()` was called only to build a denial message — "untracked",
"modified relative to git", "tracked and unmodified" — and no verdict ever read it. The
plugin's reason names the allowlist and the pinned-versus-actual hash instead, which is
the actionable part, and it saves two subprocesses on every refusal. This is the one
place where a behaviour was dropped rather than moved.

### Replaced, not retired: the 33 project-wiring assertions

These assert the project's hook wiring — `$CLAUDE_PROJECT_DIR/scripts/hooks/run_gate.sh`
resolving, `--receipt-only` as its own matcher, the `*` matcher being third. Stage 3
removed that configuration, so the assertions cannot run as written. The property they
existed to protect is not the wiring; it is that **the outermost configured command
fails closed**, and that is asserted against the plugin manifest by
`test_manifest_commands.py` — the same nine sabotages, read verbatim out of
`hooks.json`, run against a sabotaged replica.

They are counted under *equivalent or replaced* for that reason. Counting them as
retired implied 39 checks' worth of coverage had been abandoned when the real figure is
6, which is the kind of error that makes a migration look cheaper than it was.

## After the cutover: what is left in this repository

| file | frozen cases | outcome |
|---|---:|---|
| `test_guard_bash.py` | 112 | deleted — ported verbatim to `test_bash_corpus.py` |
| `test_script_indirection.py` | 55 | deleted — 49 equivalent, 6 retired |
| `test_protected_paths.py` | 45 | deleted — equivalent |
| `test_hook_gate.py` | 17 | deleted — ported to `test_gate.py` |
| `test_subagent_receipts.py` | 20 | deleted — ported to `test_receipts.py` |
| `test_configured_gate.py` | 32 | deleted — equivalent in `test_manifest_commands.py` |
| `test_maintenance_auth.py` | 27 | **kept, trimmed to 18** |
| `test_plan_apply_drift.py` | 10 | **kept whole, 10/10** |

`fixtures/make_fixtures.sh` was deleted with them: it built fixtures for
`test_guard_bash.py` and `test_script_indirection.py` and had no other consumer.

Added after the cutover, outside the frozen 318 because it covers code that did not
exist when the total was frozen:

| file | cases | covers |
|---|---:|---|
| `test_owner_policy.py` | 52 | `scripts/verify/repo_policy.py`, and `bulk_mutate.py` consulting it in both phases |

That module exists because removing `.claude/hooks/reliability_paths.py` broke
`bulk_mutate.py`, which had imported it. Its universal tuples are duplicated from the
plugin's `hooks/rules.py` — an owner tool must keep working with the plugin absent,
disabled or mid-update — so the suite parses the plugin source and fails on drift.

Every deleted file was removed from `.claude/allowed-scripts.json` in the same commit.
A pin naming a file that no longer exists is not merely stale — `script_verdict`
reports "allowlisted script cannot be read", which reads like tampering rather than
like a tidy-up.

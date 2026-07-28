# Reliability suites

Three suites, **80 cases**. Stage 3 moved enforcement into the `reliability@just-works`
plugin; what remains here covers the project-local components the plugin does not
replace. `docs/parity-map.md` accounts for every ported, replaced and retired check.

## Exact command

There is no runner and no collection step. Each suite is a standalone script that
exits 0 or 1, and each path is listed literally because the Bash gate refuses a
script path it cannot hash — a `for t in ...; python3 tests/reliability/$t.py` loop
is denied as a variable-derived script path, by design.

```
python3 tests/reliability/test_owner_policy.py
python3 tests/reliability/test_maintenance_auth.py
python3 tests/reliability/test_plan_apply_drift.py
```

## Counts

| Suite | Cases | Final line |
|---|---:|---|
| `test_owner_policy.py` | 52 | `52/52 passed` |
| `test_maintenance_auth.py` | 18 | `all checks passed` |
| `test_plan_apply_drift.py` | 10 | `10/10 passed` |
| **total** | **80** | |

`test_maintenance_auth.py` reports no numeric count. Take its 18 from
`python3 tests/reliability/test_maintenance_auth.py | grep -c '^ok'`.

Editing any of these revokes its allowlist pin until the hash is refreshed, and the
Bash gate then refuses to run it. That is the intended order: re-review, then re-pin.

```
shasum -a 256 tests/reliability/<suite>.py
```

## Outside the total

`tests/install/test_personal_guard.py` — 30 checks, reporting `30/30 passed` — guards
distribution rather than enforcement, and is deliberately kept out of this directory so
the figure above stays a fixed number. It was 26 until `1346c62` made `--personal`
refuse unconditionally rather than by inspecting settings content.

```
python3 tests/install/test_personal_guard.py
```

## Plugin suites

Enforcement itself is tested inside the plugin, against the installed cache copy
rather than this checkout, so the suites exercise the code that actually runs:

```
~/.claude/plugins/cache/just-works/reliability/<revision>/tests/
```

An agent cannot run them from inside this repository. They live outside the project,
and the policy layer refuses execution of any script outside it:

```
[reliability/policy] Blocked: execution of a script outside the project: ...
```

`cd` does not help — the guard's notion of the project comes from
`CLAUDE_PROJECT_DIR`, not the working directory. They are an owner operation, run from
a directory with no policy manifest, where the policy layer is inactive. The exact loop
is in `docs/stage3-cutover.md`.

## What each suite is for

- **test_owner_policy** — `scripts/verify/repo_policy.py`, which decides what owner
  tooling must refuse to mutate. Covers the four manifest states, the universal and
  policy-declared sets, child paths, traversal, internal and external symlinks, and
  `bulk_mutate.py` consulting it in both the plan and apply phases. Also asserts that
  the universal tuples still match the plugin's `hooks/rules.py`, by parsing it: the
  duplication is deliberate, so the drift check is what keeps it honest.
- **test_maintenance_auth** — breaks each binding of a maintenance authorization in
  turn: repository, HEAD, expiry, exact path, exact tool, use budget, nonce ledger.
  Exercises `maintenance_auth.py` directly, which is still live because
  `bulk_mutate.py` reads it. The nine checks that drove the project's deleted hook
  files went with them; the plugin's `tests/test_auth.py` covers both invariants,
  including that an active authorization never relaxes the Bash gate.
- **test_plan_apply_drift** — `bulk_mutate.py` must refuse when the world changed
  between plan and apply. Every case runs `--dry-run`.

## Two things worth knowing about `repo_policy`

**It fails closed by raising, not by returning "unprotected".** A manifest that exists
but cannot be trusted, and a path lexically inside the repository that resolves outside
it, both raise. Returning `None` would report either as an ordinary path — safe to
delete — which is exactly backwards for a malformed manifest that would otherwise
unprotect `scripts/verify/`.

**The escape check is the second layer, not the first.** End to end, `bulk_mutate`'s
own containment invariant (`within()`, in both phases) refuses an escaping target
before `repo_policy` is consulted, because it resolves symlinks too. The raise matters
when the wrapper is called with a single root that *is* the repository, and as the
answer to "what does this classifier do when it cannot answer safely".

## History

Eight suites, 318 cases, all passing at `1dd0e8c`, before Stage 3. Two commit messages
carry wrong totals — 227 instead of 249 at `060cf56`, and 291 instead of 318 at
`1dd0e8c`, the second having omitted `test_maintenance_auth.py` entirely. Both are
corrected by `git notes`; run `git log --notes` to see them.

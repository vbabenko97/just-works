# Reliability suites

Two suites, **28 cases**. Stage 3 moved enforcement into the `reliability@just-works`
plugin; what remains here covers the project-local components the plugin does not
replace. `docs/parity-map.md` accounts for every retired and ported check.

## Exact command

There is no runner and no collection step. Each suite is a standalone script that
exits 0 or 1, and each path is listed literally because the Bash gate refuses a
script path it cannot hash — a `for t in ...; python3 tests/reliability/$t.py` loop
is denied as a variable-derived script path, by design.

```
python3 tests/reliability/test_maintenance_auth.py
python3 tests/reliability/test_plan_apply_drift.py
```

## Counts

| Suite | Cases | Final line |
|---|---:|---|
| `test_maintenance_auth.py` | 18 | `all checks passed` |
| `test_plan_apply_drift.py` | 10 | `10/10 passed` |
| **total** | **28** | |

`test_maintenance_auth.py` reports no numeric count. Take its 18 from
`python3 tests/reliability/test_maintenance_auth.py | grep -c '^ok'`.

### Known failure: test_plan_apply_drift

**Failing as of this commit. The fix is an owner operation.**
`scripts/verify/bulk_mutate.py` imports `is_protected` from
`.claude/hooks/reliability_paths.py`, which the Stage 3 removal deleted:

```
ModuleNotFoundError: No module named 'reliability_paths'
```

The cutover listed `reliability_paths.py` for removal while recording only
`maintenance_auth.py` as a `bulk_mutate.py` dependency, so this import was missed. The
wrapper needs a local `is_protected` deriving its list from
`.claude/reliability-policy.json`, so it cannot drift from what the plugin enforces.
`scripts/verify/` is a protected path and the removal is not covered by any
authorization, so an agent cannot apply that patch. See `docs/stage3-cutover.md`.

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

They are an owner operation, run from a directory with no policy manifest, where the
policy layer is inactive. See `docs/stage3-cutover.md`.

## What each suite is for

- **test_maintenance_auth** — breaks each binding of a maintenance authorization in
  turn: repository, HEAD, expiry, exact path, exact tool, use budget, nonce ledger.
  Exercises `maintenance_auth.py` directly, which is still live because
  `bulk_mutate.py` reads it. The nine checks that drove the project's deleted hook
  files were removed with them; the plugin's `tests/test_auth.py` covers both
  invariants, including that an active authorization never relaxes the Bash gate.
- **test_plan_apply_drift** — `bulk_mutate.py` must refuse when the world changed
  between plan and apply. Every case runs `--dry-run`.

## History

Eight suites, 318 cases, all passing at `1dd0e8c`, before Stage 3. Two commit messages
carry wrong totals — 227 instead of 249 at `060cf56`, and 291 instead of 318 at
`1dd0e8c`, the second having omitted `test_maintenance_auth.py` entirely. Both are
corrected by `git notes`; run `git log --notes` to see them.

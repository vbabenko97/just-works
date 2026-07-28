# Reliability suites

Eight suites, **318 cases**, all passing at `1dd0e8c`.

## Exact command

There is no runner and no collection step. Each suite is a standalone script that
exits 0 or 1, and each path is listed literally because the Bash gate refuses a
script path it cannot hash — a `for t in ...; python3 tests/reliability/$t.py` loop
is denied as a variable-derived script path, by design.

```
python3 tests/reliability/test_guard_bash.py
python3 tests/reliability/test_script_indirection.py
python3 tests/reliability/test_protected_paths.py
python3 tests/reliability/test_plan_apply_drift.py
python3 tests/reliability/test_maintenance_auth.py
python3 tests/reliability/test_hook_gate.py
python3 tests/reliability/test_subagent_receipts.py
python3 tests/reliability/test_configured_gate.py
```

## Counts

| Suite | Cases | Final line |
|---|---:|---|
| `test_guard_bash.py` | 112 | `112/112 passed  (65 must-deny, 47 must-allow)` |
| `test_script_indirection.py` | 55 | `55/55 passed` |
| `test_protected_paths.py` | 45 | `45/45 passed` |
| `test_plan_apply_drift.py` | 10 | `10/10 passed` |
| `test_maintenance_auth.py` | 27 | `all checks passed` |
| `test_hook_gate.py` | 17 | `17/17 passed` |
| `test_subagent_receipts.py` | 20 | `20/20 passed` |
| `test_configured_gate.py` | 32 | `32/32 passed` |
| **total** | **318** | |

`test_maintenance_auth.py` is the one suite that reports no numeric count. That is
why two commit messages carry wrong totals — 227 instead of 249 at `060cf56`, and
291 instead of 318 at `1dd0e8c`, the second having omitted this suite's 27 cases
from the sum entirely. Both messages are corrected by `git notes`; run
`git log --notes` to see them. Until this suite prints a count, take its 27 from
`python3 tests/reliability/test_maintenance_auth.py | grep -c '^ok'`.

## Outside the frozen total

`tests/install/test_personal_guard.py` — 26 checks — guards distribution rather
than enforcement, and is deliberately kept out of this directory so the frozen
Tier 1 figure above stays a fixed number.

```
python3 tests/install/test_personal_guard.py
```

The configuration in `.claude/settings.json` reaches the guards through
`$CLAUDE_PROJECT_DIR/scripts/hooks/`, so it only works in this repository.
`install.sh --personal` would copy it to `~/.claude/settings.json`, where it
applies to every project and the launcher does not exist — bash exits 127, the
configured `|| exit 2` makes that a denial, and every matched tool call in every
project is refused. That suite proves the installer refuses the route, and that a
live `~/.claude/settings.json` is left byte-identical when it does.

## What each suite is for

- **test_guard_bash** — the lexical corpus. Half must-deny, half must-allow; a gate
  that blocks ordinary reads, tests and comparisons is worse than none.
- **test_script_indirection** — builds real scripts in a throwaway git repo, because
  these verdicts depend on a file's hash, its allowlist membership and its git state.
- **test_protected_paths** — the harness must not be editable by the agent it
  constrains, via Write/Edit or via a Bash redirect. Uses paths no authorization
  lists, so expectations do not shift when one is active.
- **test_plan_apply_drift** — `bulk_mutate.py` must refuse when the world changed
  between plan and apply. Every case runs `--dry-run`.
- **test_maintenance_auth** — breaks each binding of a maintenance authorization in
  turn, and proves an active one still leaves the Bash gate fully armed.
- **test_hook_gate** — every way a guard can fail becomes a refusal.
- **test_subagent_receipts** — contract delivery to subagents is enforced at tool
  time, since `SubagentStart` cannot block creation.
- **test_configured_gate** — the acceptance suite. Runs the command strings read
  verbatim out of `.claude/settings.json` against a sabotaged replica, plus two live
  probes against this repository. This is the suite that caught a fail-open the
  in-process tests could not see.

# Reliability contract

Delivered to every subagent at start. A repository can replace this text by declaring
`contract` in `.claude/reliability-policy.json`; it cannot remove the delivery.

Explore and Plan do not read CLAUDE.md, so for them this is the only copy of the
rules they get.

## What is refused everywhere, in every repository

These are not negotiable by repository policy, and no maintenance authorization
relaxes them for Bash:

- recursive or glob deletion: `rm -rf`, `rm *`, `find -delete`, `xargs rm`
- history and working-tree destruction: `git push --force`, `git reset --hard`,
  `git clean -fdx`, `git checkout .`
- unbounded SQL: `DROP`, `TRUNCATE`, `DELETE`/`UPDATE` with no `WHERE`
- device and permission damage: `dd of=`, `mkfs`, `chmod -R`, `chown -R`, `shred`
- privilege escalation: `sudo`, `doas`, `su`
- text executed without inspection: piping into a shell, `curl | sh`, `base64 -d`,
  `eval`
- mutation whose target set cannot be bounded: shell loops, command substitution,
  globs, brace ranges, variable-derived targets
- editing the configuration that governs the agent: `.claude/settings.json`,
  `.claude/settings.local.json`, `.claude/hooks/`, `.claude/reliability-policy.json`,
  `.claude/allowed-scripts.json`, and the same paths under `~`
- switching this enforcement off: `claude plugin disable|uninstall|update`,
  `claude plugin marketplace add|remove`, editing `enabledPlugins`
- invoking the owner maintenance issuer

## What a repository may add

With a valid `.claude/reliability-policy.json`:

- local script execution must be pinned by sha256 in the declared allowlist
- build and package runners are refused: `make`, `npm run`, `gradle`, `cargo run`
- opaque payloads must be pinned: `git apply`, `git am`, `patch`, local installs
- additional protected paths
- subagent contract receipts required before any tool call

Policy only ever adds. There is no key that permits something the universal rules
refuse.

## If a command is refused

Do not look for another route to the same effect. Report the refusal and the reason,
and let the owner decide. Working around a guard is the one behaviour that makes the
guard worthless.

Bulk filesystem mutation has a supported path: a plan-then-apply wrapper that
enumerates exact targets and refuses when anything changed between the two phases.
Where a repository provides one, its manifest names it.

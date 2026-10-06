# Owner procedure: updating the enforcement plugin

A Claude session cannot update, disable or uninstall this plugin. That is deliberate:
`enabledPlugins` lives in `~/.claude/settings.json`, which is protected from Write and
Edit, and the CLI routes that reach it without naming the file — `claude plugin
disable`, `uninstall`, `update`, `install`, `marketplace add|remove`, and `claude
config set` touching those keys — are denied universally. Verified by
`test_monotonic`, 9 self-protection commands × 3 policy states.

So the sequence below is yours, in your own terminal, with no agent involved.

## Update

```
cd /Users/vitaliibabenko/babenko-dev/just-works
git pull
claude plugin marketplace update just-works
claude plugin update reliability@just-works
```

The marketplace refresh is required: it is a git clone of the remote, and
`plugin update` compares against what that clone contains.

The plugin declares no version, so each commit is a distinct installable revision and
the update reports the SHA it moved to:

```
✔ Plugin "reliability" updated from 8dcc512e4a4d to 363531892137 for scope user.
  Restart to apply changes.
```

`claude plugin update reliability` without the marketplace suffix fails with *"Plugin
not found"*. Use the qualified id.

## Verify the installed SHA

```
python3 -c "import json,os;e=json.load(open(os.path.expanduser('~/.claude/plugins/installed_plugins.json')))['plugins']['reliability@just-works'][0];print(e['version'], e['gitCommitSha'], e['installPath'])"
git rev-parse HEAD
```

The recorded `gitCommitSha` must equal the commit you intended to install. The
`installPath` must be under `~/.claude/plugins/cache/`, which is what guarantees the
working tree is not what executes.

## Reload

Sessions that are already running pick up the new revision on their next hook call;
no restart is needed. Observed 2026-10-06: two sessions opened before the update, one
of them before three successive updates, both executed the newly installed revision
from `~/.claude/plugins/cache/` on their next Bash call. An update therefore reaches
work in progress too.

The session's start time does not tell you which revision it runs; the trace does.
After any Bash call in that session:

```
tail -1 ~/.claude/reliability-trace.jsonl | python3 -m json.tool | grep -E 'session_id|revision|under_cache'
```

If `revision` still shows the old SHA, start a new session:

```
# in any running session
/exit
claude
```

## Post-update smoke test

In a fresh session, from a directory with **no** policy manifest — `/tmp` will do:

```
ls -la                       # must be allowed
rm -rf /tmp/does-not-exist   # must be denied: [reliability/universal]
npm run build                # must be ALLOWED here — no manifest, no policy layer
```

Then from a repository **with** a valid manifest:

```
npm run build                # must be denied: [reliability/policy]
claude plugin disable reliability   # must be denied: [reliability/universal]
```

And confirm the executing copy is the cache:

```
tail -1 ~/.claude/reliability-trace.jsonl | python3 -m json.tool | grep -E 'under_cache|revision|executing_file'
```

`under_cache` must be `true` and `revision` must match the SHA you installed.

If any of those four behave differently, roll back before doing anything else.

## Rollback to the previous known-good commit

The plugin manager installs from the marketplace clone, so rollback is a git operation
on the source plus a reinstall:

```
cd /Users/vitaliibabenko/babenko-dev/just-works
git log --oneline -5 -- plugins/reliability
git revert --no-edit <bad-commit>      # or: git checkout <good-commit> -- plugins/reliability
git commit -m 'revert: roll plugin back to <good-commit>'
git push origin main
claude plugin marketplace update just-works
claude plugin update reliability@just-works
```

Reverting forward is preferred over rewriting history, because the installed revision
is recorded as a SHA and a rewritten history leaves that record pointing at a commit
that no longer exists.

If the plugin is actively blocking work and you need it off immediately:

```
claude plugin disable reliability@just-works
```

Then start a fresh session. Nothing else on the machine depends on it, and the
project-scoped harness in this repository is unaffected — until Stage 3 removes it, the
two overlap and any deny from either still applies.

To remove it entirely:

```
claude plugin uninstall reliability@just-works
claude plugin marketplace remove just-works
```

Both leave `~/.claude/settings.json` otherwise untouched: the only keys involved are
`enabledPlugins` and `extraKnownMarketplaces`.

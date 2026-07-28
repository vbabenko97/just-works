# PreToolUse `permissionDecision: "ask"` blocks in print mode but proceeds silently in an interactive session

Reproduced 2026-07-28 on Claude Code **2.1.220**, macOS 15 (Darwin 24.6.0), with
both halves model-matched to `claude-opus-4-8`.

## Summary

A `PreToolUse` hook that returns `permissionDecision: "ask"` with exit 0:

- **print mode** (`claude -p --permission-mode acceptEdits`) — the tool call is
  refused and recorded in `permission_denials`. The file is not created.
- **interactive** (`claude --permission-mode acceptEdits`) — the tool call
  proceeds. No prompt is displayed. The file is created.

Same fixture, same flag, same model, byte-identical hook stdout. Only the mode
differs. `deny` blocks correctly in both. Only `ask` diverges.

The practical consequence is that `ask` cannot be used as a soft gate: a hook
author who tests headlessly sees it block, and interactively it is a no-op. This
repository's guards return `deny` for that reason, and the reliability plugin's
`hooks/gate.py` upgrades any `ask` from a child guard into a refusal. Before Stage 3
that upgrade lived in `scripts/hooks/hook_gate.py`.

## Minimal fixture

`/tmp/ask-repro/ask_hook.sh` — unconditional `ask`, and a log so a silent success
can be told apart from the hook never running:

```bash
#!/usr/bin/env bash
payload="$(cat)"
printf '%s\n' "$payload" >> /tmp/ask-repro/hook.log
cat <<'JSON'
{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"ask","permissionDecisionReason":"ask-repro: this hook always returns ask"}}
JSON
exit 0
```

`/tmp/ask-repro/.claude/settings.json` — the hook and nothing else. No
`permissions` block, no `defaultMode`, no `allowedTools`:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Write|Edit|MultiEdit",
        "hooks": [
          { "type": "command", "command": "bash /tmp/ask-repro/ask_hook.sh", "timeout": 10 }
        ]
      }
    ]
  }
}
```

## Print mode — refused, as documented

```
cd /tmp/ask-repro
claude -p 'Use the Write tool to create a file named probe-headless3.txt containing the single word hello.' \
  --permission-mode acceptEdits --model claude-opus-4-8 --output-format json
```

From the result JSON:

```json
"modelUsage": { "claude-opus-4-8": ... },
"permission_denials": [
  { "tool_name": "Write",
    "tool_use_id": "toolu_01FN95CE6rWzkZQt3XKgMbtB",
    "tool_input": { "file_path": "/private/tmp/ask-repro/probe-headless3.txt",
                    "content": "hello" } }
]
```

`probe-headless3.txt` does not exist afterwards.

## Interactive — proceeds, no prompt

```
cd /tmp/ask-repro
claude --permission-mode acceptEdits
> Write tool to create probe-interactive.txt containing hello
```

Session banner reported `Opus 4.8 (1M context)`. The transcript:

```
⏺ Write(probe-interactive.txt)
  ⎿  Wrote 1 line to probe-interactive.txt
      1 hello
```

No permission prompt was displayed at any point. `probe-interactive.txt` exists.

The hook did run, and saw the same payload shape it saw headlessly — from
`hook.log`:

```
PreToolUse Write acceptEdits /private/tmp/ask-repro/probe-interactive.txt 'hello\n'
```

## Ruled out

- **Hook never fired** — `hook.log` gained one line per attempt, four in total
  across the runs, each recording `tool_name: "Write"` and
  `permission_mode: "acceptEdits"`.
- **Hook failed** — exit 0, empty stderr, stdout is the single JSON object above.
- **Wrong matcher** — the interactive attempt is recorded in `hook.log`, so the
  matcher covered the tool that ran.
- **Competing hook** — the fixture project registers exactly one `PreToolUse`
  hook. (In the original observation inside a larger project, exactly one
  `PreToolUse` attachment existed for the `toolUseID`, and the only plugin
  matching `Edit|Write|MultiEdit|NotebookEdit` registers on `PostToolUse`.)
- **A stored grant** — throwaway project directory, no `permissions` block in its
  settings, no `allowedTools`, no rule matching the path.
- **Model difference** — the interactive session ran Opus 4.8; the print-mode run
  was pinned to `claude-opus-4-8` and still refused. An earlier print-mode run on
  `claude-opus-5[1m]` also refused.

## Corroboration

First seen in a larger project where a protected-path hook returned `ask` for
writes under `.claude/` and `scripts/verify/`: 6 of 6 `ask` verdicts in one
interactive session proceeded without a prompt, including targets under
`.claude/`. The transcript attachment for one of them recorded
`"type": "hook_success"`, `"hookName": "PreToolUse:Write"`, `"exitCode": 0`,
stdout containing `"permissionDecision": "ask"`, immediately followed by
`File created successfully at: .../scripts/verify/_probe_delete_me.py`.

## Filed upstream

Added as a comment to `anthropics/claude-code#79449` rather than as a new issue —
that issue already reports the same symptom on macOS, so a separate report would
likely be closed as a duplicate:

<https://github.com/anthropics/claude-code/issues/79449#issuecomment-5102886991>

`anthropics/claude-code#79356` is cross-linked there as related evidence: the same
`ask` non-enforcement on Windows, for both hook decisions and `permissions.ask`
entries, so the symptom is not macOS-specific.

### On that issue's `CLAUDE_CODE_CHILD_SESSION=1` hypothesis

#79449 attributes the fall-through to a top-level session being adopted by the
background daemon, which sets `CLAUDE_CODE_CHILD_SESSION=1` and — per its stated
hypothesis — leaves `ask` with no interactive terminal to resolve against. This
reproduction does not appear to need that mechanism, and does not disprove it:

- The interactive session was launched from a plain login shell. None of the three
  shell rc files present on this machine (`~/.profile`, `~/.zprofile`, `~/.zshrc`)
  set `CLAUDE_CODE_CHILD_SESSION`, and `~/.claude/settings.json` has no `env`
  block. The environment *inside* that session was not captured, so this is the
  absence of any known source rather than a measured absence.
- The print-mode runs did carry `CLAUDE_CODE_CHILD_SESSION=1`, having been launched
  from inside another Claude Code session, and blocked correctly anyway. Re-run
  with `env -u CLAUDE_CODE_CHILD_SESSION -u CLAUDECODE -u CLAUDE_CODE_SESSION_ID
  -u CLAUDE_PID`, print mode still blocked and still recorded the denial. The
  marker does not decide print-mode behaviour in either direction.

The narrower observation, which bears on that issue's question about `ask`'s
fallback when no prompt channel exists: print mode has no prompt channel at all
and fails closed, while the session that fails open is the one with a real TTY. So
"nothing to prompt against" does not explain the fall-through.

## What would help

Either make `ask` prompt in interactive sessions under `acceptEdits`, or document
that `acceptEdits` satisfies a hook-issued `ask` for file-editing tools, so hook
authors know `deny` is the only enforceable decision.

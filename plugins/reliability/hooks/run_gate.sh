#!/bin/bash
# Outermost launcher: the command string Claude Code actually runs.
#
# gate.py makes guard failures fail closed, but nothing protects gate.py itself. A
# syntax error in it, a bad import, a crash or a hang is an abnormal exit, and an
# abnormal exit was measured to be treated as "no opinion" — the tool call proceeds.
# The acceptance suite for the project version found exactly one gap this way: a gate
# that exits 0 while printing junk sailed through, because only the *guard's* output
# was being validated and never the gate's own. So this validates what it is about to
# release, then releases it.
#
#   gate exited 0 with a deny decision    pass its stdout through, exit 0
#   gate exited 0 with exactly `{}`       print nothing, exit 0 (no opinion)
#   gate exited 0 with anything else      exit 2
#   any other exit code                   exit 2
#   gate did not finish                   killed at the deadline below, then exit 2
#
# The deadline must stay shorter than the hook timeout in hooks.json, or Claude Code
# gives up first and fails open. Nesting: guard 10s < launcher 15s < hook 30s.
#
# The configured command appends `|| exit 2`, which covers what this file cannot:
# this file being missing, or unparseable by bash. Both make bash exit non-zero
# before a single line here runs.
set -u

deadline="${RELIABILITY_GATE_DEADLINE:-15}"
here="$(cd "$(dirname "$0")" && pwd)"
gate="$here/gate.py"

# A full template with X's, because GNU mktemp rejects `-t name` without them. On
# Linux that left both paths empty, so every matched tool call was refused.
payload="$(mktemp "${TMPDIR:-/tmp}/reliability-gate.XXXXXX")"
out="$(mktemp "${TMPDIR:-/tmp}/reliability-gate-out.XXXXXX")"
trap 'rm -f "$payload" "$out"' EXIT

# Buffer stdin: the child may have to be killed, and the payload must have been
# delivered in full before that happens.
cat > "$payload"

python3 "$gate" "$@" < "$payload" > "$out" &
child=$!

# stdio is redirected away from the caller's pipes deliberately. A watchdog that
# inherits them keeps the write end of stdout and stderr open after it is orphaned,
# so whoever is reading the hook's output blocks until `sleep` finishes — the full
# deadline on every call, however fast the gate answered. Measured 6.0s against a 6s
# deadline with a gate that returned in 3.
( sleep "$deadline"; kill -9 "$child" 2>/dev/null ) >/dev/null 2>&1 &
watchdog=$!
# Drop it from the job table before killing it. Otherwise bash announces the kill —
# "Killed: 9 ( sleep ... )" — on this script's stderr, which is the channel a refusal
# reason travels on, so the noise ends up quoted in the denial the user reads.
disown "$watchdog" 2>/dev/null || true

wait "$child"
rc=$?

# SIGKILL, and no `wait`. A plain `kill` is deferred: the watchdog is a subshell
# blocked on `sleep`, and non-interactive bash does not handle SIGTERM until its
# foreground child exits — so `kill` followed by `wait` blocked for the whole
# deadline on *every* call, however fast the gate answered. Measured 6.0s against a
# 6s deadline with a gate that returned in 3. In production that is 15s of latency
# added to every matched tool call. The orphaned `sleep` exits on its own and prints
# nothing.
kill -9 "$watchdog" 2>/dev/null

if [ "$rc" -eq 0 ]; then
  # Exit 0: a deny decision. Exit 3: exactly `{}`. Anything else, including
  # `allow` and a crash of this check, is unreadable. Explicit checks rather than
  # `assert`, which PYTHONOPTIMIZE removes; -I ignores PYTHON* variables and keeps
  # the current directory off sys.path, so a json.py in the project cannot stand in
  # for the standard module.
  python3 -I -c '
import json, sys
answer = json.load(open(sys.argv[1]))
if answer == {}:
    sys.exit(3)
decision = answer.get("hookSpecificOutput") if isinstance(answer, dict) else None
if not (isinstance(decision, dict)
        and decision.get("hookEventName") == "PreToolUse"
        and decision.get("permissionDecision") == "deny"):
    sys.exit(1)
' "$out" 2>/dev/null
  verdict=$?
  if [ "$verdict" -eq 0 ]; then
    cat "$out"
    exit 0
  fi
  if [ "$verdict" -eq 3 ]; then
    # No opinion, released as no output: Claude Code then applies the user's own
    # permission rules, which an `allow` would skip.
    exit 0
  fi
  echo "[run_gate] BLOCKED: the gate exited 0 without printing a valid PreToolUse decision." >&2
  echo "[run_gate] gate: $gate $*" >&2
  echo "[run_gate] A gate whose answer cannot be read is treated as a refusal." >&2
  exit 2
fi

# rc 2 is a deliberate refusal; its stderr already explains why, so say nothing
# further. Every other code is the gate itself failing.
if [ "$rc" -ne 2 ]; then
  echo "[run_gate] BLOCKED: the reliability gate terminated abnormally (exit $rc)." >&2
  echo "[run_gate] gate: $gate $*" >&2
  echo "[run_gate] A gate that cannot run is treated as a refusal, not as permission." >&2
fi

exit 2

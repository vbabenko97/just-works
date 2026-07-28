#!/bin/bash
# Outermost launcher for the reliability gate.
#
# hook_gate.py makes guard failures fail closed, but nothing was protecting
# hook_gate.py itself: a syntax error in it, a bad import, a crash or a hang would
# be an abnormal exit that Claude Code treats as "no opinion", and the tool call
# would proceed. Measured on 2.1.220 with --permission-mode acceptEdits: exit 1,
# exit 127, malformed stdout and exceeding the configured hook timeout all let the
# operation through. Only exit 2, or exit 0 carrying a deny decision, block it.
#
# So this script normalises everything to the two outcomes Claude Code honours:
#
#   gate exited 0 with a valid decision   pass its stdout through, exit 0
#   gate exited 0 with anything else      exit 2
#   any other exit code                   exit 2
#   gate did not finish                   killed at the deadline below, then exit 2
#
# The stdout check is not redundant with the one inside hook_gate.py. That one
# validates what a *guard* printed; this one validates what the *gate* printed. The
# acceptance test found the difference: a hook_gate.py that exits 0 while printing
# junk sailed through this launcher, and Claude Code logged "Hook output does not
# start with {, treating as plain text" and ran the tool.
#
# The deadline must stay shorter than the `timeout` configured for this hook in
# settings.json, otherwise Claude Code gives up first and fails open. Current
# nesting: guard 10s (inside hook_gate) < launcher 15s (here) < hook 30s (settings).
#
# The configured command in settings.json appends `|| exit 2`, which covers what
# this file cannot: this file being missing, or unparseable by bash. Both make bash
# exit non-zero before a single line here runs.
set -u

deadline="${RELIABILITY_GATE_DEADLINE:-15}"
here="$(cd "$(dirname "$0")" && pwd)"
gate="$here/hook_gate.py"

payload="$(mktemp -t reliability-gate)"
out="$(mktemp -t reliability-gate-out)"
trap 'rm -f "$payload" "$out"' EXIT

# Buffer stdin to a file: the child may have to be killed, and the payload must
# still have been delivered in full before that happens.
cat > "$payload"

# stdout is captured so it can be validated before release. stderr is inherited, so
# a guard's refusal reason reaches Claude Code unchanged.
python3 "$gate" "$@" < "$payload" > "$out" &
child=$!

( sleep "$deadline"; kill -9 "$child" 2>/dev/null ) &
watchdog=$!

wait "$child"
rc=$?

kill "$watchdog" 2>/dev/null
wait "$watchdog" 2>/dev/null

if [ "$rc" -eq 0 ]; then
  if python3 -c '
import json, sys
decision = json.load(open(sys.argv[1]))["hookSpecificOutput"]
assert decision["hookEventName"] == "PreToolUse", decision
assert decision["permissionDecision"] in ("allow", "deny"), decision
' "$out" 2>/dev/null; then
    cat "$out"
    exit 0
  fi
  echo "[run_gate] BLOCKED: the gate exited 0 without printing a valid PreToolUse decision." >&2
  echo "[run_gate] gate: $gate $*" >&2
  echo "[run_gate] A gate whose answer cannot be read is treated as a refusal." >&2
  exit 2
fi

# rc 2 is a deliberate refusal by the gate or a guard; its stderr already explains
# why, so say nothing further. Every other code is the gate itself failing.
if [ "$rc" -ne 2 ]; then
  echo "[run_gate] BLOCKED: the reliability gate terminated abnormally (exit $rc)." >&2
  echo "[run_gate] gate: $gate $*" >&2
  echo "[run_gate] A gate that cannot run is treated as a refusal, not as permission." >&2
fi

exit 2

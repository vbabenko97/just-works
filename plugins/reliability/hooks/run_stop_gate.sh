#!/bin/bash
# Outermost launcher for SubagentStop. Same fail-closed philosophy as run_gate.sh,
# adapted for the Stop-family output shape: a top-level "decision" key, not
# hookSpecificOutput.permissionDecision.
#
# Success is represented by the child exiting 0 and printing either nothing, or
# JSON with no "decision" key, or a well-formed {"decision":"block","reason":...}.
# Anything else the child does — missing script, syntax/import failure, abnormal
# exit, malformed output, an explicit "approve", or running past the deadline —
# collapses to the same hardcoded block decision. A launcher failure must never
# look like permission, and this script never emits decision:"approve" itself.
#
# This cannot distinguish "child intentionally printed nothing because it approved"
# from "child had a logic bug and silently forgot to print a block it meant to
# print" — that guarantee has to come from the child's own tests, not this launcher.
set -u

deadline="${RELIABILITY_STOP_DEADLINE:-15}"
here="$(cd "$(dirname "$0")" && pwd)"
child="$here/subagent_stop.py"

FAIL_CLOSED='{"decision":"block","reason":"[reliability] Subagent completion verification failed to run."}'

payload="$(mktemp -t reliability-stopgate)"
out="$(mktemp -t reliability-stopgate-out)"
trap 'rm -f "$payload" "$out"' EXIT

cat > "$payload"

python3 "$child" < "$payload" > "$out" 2>/dev/null &
kid=$!

( sleep "$deadline"; kill -9 "$kid" 2>/dev/null ) >/dev/null 2>&1 &
watchdog=$!
disown "$watchdog" 2>/dev/null || true

wait "$kid"
rc=$?
kill -9 "$watchdog" 2>/dev/null

if [ "$rc" -ne 0 ]; then
  echo "$FAIL_CLOSED"
  exit 0
fi

result="$(python3 -c '
import json, sys

raw = open(sys.argv[1]).read().strip()
if raw == "":
    sys.exit(0)                        # success: printed nothing at all

try:
    data = json.loads(raw)
except Exception:
    sys.exit(1)                        # malformed output -> launcher failure

if not isinstance(data, dict) or "decision" not in data:
    sys.exit(0)                        # success: no decision key present

if (data.get("decision") == "block" and isinstance(data.get("reason"), str)
        and data["reason"]):
    print(json.dumps({"decision": "block", "reason": data["reason"]}))
    sys.exit(0)

sys.exit(1)                            # "approve", or any other invalid shape
' "$out" 2>/dev/null)"
validate_rc=$?

if [ "$validate_rc" -ne 0 ]; then
  echo "$FAIL_CLOSED"
  exit 0
fi

if [ -n "$result" ]; then
  echo "$result"
fi
exit 0

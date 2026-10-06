#!/bin/bash
# Keep this deadline above the guard's 8s deadline and below the 20s host timeout.
set -u

here="$(cd "$(dirname "$0")" && pwd)"
deadline=12
# GNU mktemp rejects a -t template without X's, so spell out a portable template.
payload="$(mktemp "${TMPDIR:-/tmp}/product-analyst-gate.XXXXXX")"
out="$(mktemp "${TMPDIR:-/tmp}/product-analyst-gate-out.XXXXXX")"
trap 'rm -f "$payload" "$out"' EXIT
cat > "$payload"

python3 "$here/gate.py" "$@" < "$payload" > "$out" &
child=$!
( sleep "$deadline"; kill -9 "$child" 2>/dev/null ) >/dev/null 2>&1 &
watchdog=$!
disown "$watchdog" 2>/dev/null || true
wait "$child"
rc=$?
kill -9 "$watchdog" 2>/dev/null || true

if [ "$rc" -eq 0 ] && python3 -c '
import json, sys
value = json.load(open(sys.argv[1]))
assert value == {} or (
    value["hookSpecificOutput"]["hookEventName"] == "PreToolUse"
    and value["hookSpecificOutput"]["permissionDecision"] == "deny"
)
' "$out" 2>/dev/null; then
  cat "$out"
  exit 0
fi

# Use Bash's builtin printf here. If Python itself cannot start, an external
# formatter would recreate Claude Code's fail-open failed-hook behavior.
printf '%s\n' '{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"deny","permissionDecisionReason":"[product-analyst] Blocked: policy supervisor failed"}}'
exit 0

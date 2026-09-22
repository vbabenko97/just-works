#!/usr/bin/env python3
"""Stand-in for the Codex CLI used by tests/goal/run-tests.py. Never contacts a provider.

Behaviour is chosen by FAKE_MODE: ok | fail | timeout | empty | big | errorevent
Records that it was invoked by appending to $FAKE_MARKER.
"""
import json
import os
import sys
import time


def main() -> int:
    marker = os.environ.get("FAKE_MARKER")
    if marker:
        with open(marker, "a", encoding="utf-8") as fh:
            fh.write("invoked\n")

    argv = sys.argv[1:]
    out_path = None
    if "--output-last-message" in argv:
        out_path = argv[argv.index("--output-last-message") + 1]

    task = sys.stdin.read()
    # Prove the task text arrived intact and was never shell-evaluated.
    with open(os.environ["FAKE_TASK_ECHO"], "w", encoding="utf-8") as fh:
        fh.write(task)

    mode = os.environ.get("FAKE_MODE", "ok")

    if mode == "timeout":
        time.sleep(300)
        return 0

    lines = [
        {"type": "thread.started", "model": "gpt-6-astra-fake"},
        {"type": "item.completed", "msg": {"usage": {"input_tokens": 1234, "cached_input_tokens": 1000, "output_tokens": 56}}},
    ]
    if mode == "errorevent":
        lines.append({"type": "turn.failed", "error": "synthetic failure"})
    if mode == "big":
        for i in range(20000):
            lines.append({"type": "item.delta", "seq": i, "text": "x" * 200})

    for line in lines:
        sys.stdout.write(json.dumps(line) + "\n")
    sys.stdout.flush()
    sys.stderr.write("fake codex stderr line\n")

    if out_path and mode != "empty":
        with open(out_path, "w", encoding="utf-8") as fh:
            fh.write("REVIEW: no blocking findings (synthetic).\n")
    elif out_path:
        open(out_path, "w", encoding="utf-8").close()

    return 3 if mode == "fail" else 0


if __name__ == "__main__":
    raise SystemExit(main())

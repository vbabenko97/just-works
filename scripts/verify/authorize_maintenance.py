#!/usr/bin/env python3
"""Issue a narrow maintenance authorization. Run this from your own shell.

The reliability harness denies agent edits to itself, which also stops the owner's
agent session from maintaining it. This is the intended way back in: not a switch
that disables the guard, but a note that says which operations, on which paths,
until when, and how many times.

    python3 scripts/verify/authorize_maintenance.py \
        --minutes 30 --reason 'fix the git_state label' \
        --op 'Edit:.claude/hooks/guard_destructive_bash.py:2'

Each --op is TOOL:REPO_RELATIVE_PATH:MAX_USES. Paths are compared literally, so a
glob or a parent directory authorizes nothing. The authorization binds to this
repository and to the current HEAD, so committing invalidates it.

Two independent barriers stop an agent issuing its own authorization:
  1. this file lives under scripts/verify/, so Write and Edit on it are denied;
  2. it is deliberately absent from .claude/allowed-scripts.json, so the Bash gate
     refuses to execute it.
The CLAUDECODE / CLAUDE_PROJECT_DIR check below is a third, weaker barrier: it is
a courtesy against accident, not a security boundary, since an agent could unset
those variables. Barriers 1 and 2 are the ones that hold.
"""
from __future__ import annotations

import argparse
import json
import os
import pathlib
import secrets
import subprocess
import sys
import time

PROJECT = pathlib.Path(__file__).resolve().parents[2]
AUTH_PATH = PROJECT / ".claude" / "maintenance-auth.json"
KNOWN_TOOLS = {"Write", "Edit", "MultiEdit", "NotebookEdit", "Update",
               "bulk_mutate.delete"}


def head() -> str:
    out = subprocess.run(["git", "rev-parse", "HEAD"], cwd=str(PROJECT),
                         capture_output=True, text=True, timeout=10)
    if out.returncode != 0:
        raise SystemExit("cannot read HEAD; run this inside the repository")
    return out.stdout.strip()


def parse_op(spec: str) -> dict:
    parts = spec.split(":")
    if len(parts) != 3:
        raise SystemExit(f"--op must be TOOL:PATH:MAX_USES, got {spec!r}")
    tool, path, uses = parts[0].strip(), parts[1].strip(), parts[2].strip()
    if tool not in KNOWN_TOOLS:
        raise SystemExit(f"unknown tool {tool!r}; choose from {sorted(KNOWN_TOOLS)}")
    if path.startswith("/") or path.startswith("~") or ".." in path:
        raise SystemExit(f"path must be repo-relative and literal, got {path!r}")
    if any(ch in path for ch in "*?["):
        raise SystemExit(f"path must be literal, not a pattern: {path!r}")
    if not (PROJECT / path).exists() and tool not in ("Write",):
        raise SystemExit(f"path does not exist: {path!r} (use Write to authorize "
                         "creating a new file)")
    try:
        count = int(uses)
    except ValueError:
        raise SystemExit(f"MAX_USES must be a number, got {uses!r}")
    if not 1 <= count <= 20:
        raise SystemExit("MAX_USES must be between 1 and 20; a large budget is "
                         "indistinguishable from disabling the guard")
    return {"tool": tool, "path": path, "max_uses": count}


def main() -> int:
    if os.environ.get("CLAUDECODE") or os.environ.get("CLAUDE_PROJECT_DIR"):
        print("Refusing: this looks like an agent session. Issue authorizations "
              "from your own shell.", file=sys.stderr)
        return 2

    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--op", action="append", required=True,
                    help="TOOL:REPO_RELATIVE_PATH:MAX_USES (repeatable)")
    ap.add_argument("--minutes", type=int, required=True,
                    help="lifetime in minutes (1-240)")
    ap.add_argument("--reason", required=True, help="why this is being authorized")
    args = ap.parse_args()

    if not 1 <= args.minutes <= 240:
        raise SystemExit("--minutes must be between 1 and 240")

    now = int(time.time())
    auth = {
        "version": 1,
        "nonce": secrets.token_hex(8),
        "repo": str(PROJECT),
        "head": head(),
        "issued_at": now,
        "expires_at": now + args.minutes * 60,
        "reason": args.reason,
        "operations": [parse_op(spec) for spec in args.op],
    }
    with open(AUTH_PATH, "w") as fh:
        json.dump(auth, fh, indent=2)
        fh.write("\n")
    print(json.dumps({"status": "issued", "path": str(AUTH_PATH),
                      "nonce": auth["nonce"], "head": auth["head"][:12],
                      "expires_at": auth["expires_at"],
                      "operations": auth["operations"]}, indent=2))
    print("\nSpend is recorded in .claude/maintenance-uses.jsonl. Deleting that "
          "ledger is itself a protected operation.", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())

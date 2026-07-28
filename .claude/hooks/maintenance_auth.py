#!/usr/bin/env python3
"""Narrow, out-of-band maintenance authorization for the reliability harness.

Why this exists: guard_protected_paths.py denies agent edits to the harness, which
also locks the owner's own agent session out of maintaining it. A session-wide
boolean bypass would trade the entire protection for that convenience. This is the
narrow alternative — an authorization names exact operations and is bound to:

  this repository   realpath of the project root
  this commit       git rev-parse HEAD, revalidated at use time
  a deadline        expires_at, unix seconds
  exact paths       repo-relative, compared literally: no globs, no prefixes
  exact tools       Write / Edit / MultiEdit / NotebookEdit / bulk_mutate.delete
  a nonce           one authorization, not a standing grant
  a use budget      per-operation max_uses, spent in an append-only ledger

Anything not listed stays denied. The Bash gate is never consulted here and never
relaxed: no authorization can permit rm -rf, a force push, or execution of an
unreviewed script. The authorization file and its ledger are themselves protected
paths, so an agent can neither issue one nor erase the record of spending one.
"""
from __future__ import annotations

import json
import os
import subprocess
import time

AUTH_REL = ".claude/maintenance-auth.json"
LEDGER_REL = ".claude/maintenance-uses.jsonl"
AUTH_VERSION = 1

# bulk_mutate.delete is not a Claude Code tool; it is the wrapper's own operation,
# so one authorization format covers both the tool route and the wrapper route.
KNOWN_TOOLS = {"Write", "Edit", "MultiEdit", "NotebookEdit", "Update",
               "bulk_mutate.delete"}


def _head(project: str) -> str | None:
    try:
        out = subprocess.run(["git", "rev-parse", "HEAD"], cwd=project,
                             capture_output=True, text=True, timeout=5)
        return out.stdout.strip() if out.returncode == 0 else None
    except Exception:
        return None


def load(project: str):
    """Return (authorization, problem). Exactly one is None."""
    path = os.path.join(project, AUTH_REL)
    if not os.path.exists(path):
        return None, "no maintenance authorization present"
    try:
        with open(path) as fh:
            auth = json.load(fh)
    except Exception as exc:
        return None, f"authorization is malformed: {exc}"
    if not isinstance(auth, dict) or auth.get("version") != AUTH_VERSION:
        return None, "authorization is malformed: unsupported version"
    for field in ("nonce", "repo", "head", "expires_at", "operations"):
        if field not in auth:
            return None, f"authorization is malformed: missing {field}"
    if not isinstance(auth["operations"], list):
        return None, "authorization is malformed: operations is not a list"
    return auth, None


def uses(project: str, nonce: str, tool: str, rel: str) -> int:
    """How many times this exact (nonce, tool, path) has already been spent."""
    path = os.path.join(project, LEDGER_REL)
    if not os.path.exists(path):
        return 0
    count = 0
    try:
        with open(path) as fh:
            for row in fh:
                row = row.strip()
                if not row:
                    continue
                try:
                    rec = json.loads(row)
                except Exception:
                    continue
                if (rec.get("nonce") == nonce and rec.get("tool") == tool
                        and rec.get("path") == rel):
                    count += 1
    except Exception:
        # An unreadable ledger must not read as "budget still available".
        return 10 ** 6
    return count


def record(project: str, nonce: str, tool: str, rel: str, note: str = "") -> None:
    path = os.path.join(project, LEDGER_REL)
    row = {"nonce": nonce, "tool": tool, "path": rel,
           "at": int(time.time()), "note": note}
    with open(path, "a") as fh:
        fh.write(json.dumps(row) + "\n")


def check(project: str, tool: str, abs_path: str, consume: bool = False):
    """Return (ok, reason). Never raises: any error is a refusal.

    Call with consume=False to test, then again with consume=True to spend a use.
    Callers handling several paths at once should test them all before spending
    anything, so a partly-authorized batch is refused whole."""
    try:
        rel = os.path.relpath(os.path.realpath(abs_path),
                              os.path.realpath(project)).replace(os.sep, "/")
    except Exception:
        return False, "path cannot be resolved against the repository"
    if rel == ".." or rel.startswith("../"):
        return False, "path is outside the repository"

    auth, problem = load(project)
    if problem:
        return False, problem

    try:
        same_repo = os.path.realpath(auth["repo"]) == os.path.realpath(project)
    except Exception:
        same_repo = False
    if not same_repo:
        return False, "authorization is for a different repository"

    try:
        expires = int(auth["expires_at"])
    except Exception:
        return False, "authorization is malformed: expires_at is not a number"
    now = int(time.time())
    if now >= expires:
        return False, f"authorization expired ({now - expires}s ago)"

    current = _head(project)
    if current is None:
        return False, "cannot read HEAD to validate the authorization"
    if current != auth["head"]:
        return False, ("authorization is bound to a different commit: issued for "
                       f"{str(auth['head'])[:12]}, HEAD is {current[:12]}")

    if tool not in KNOWN_TOOLS:
        return False, f"authorization does not list tool {tool}"

    matches = [op for op in auth["operations"]
               if isinstance(op, dict) and op.get("tool") == tool
               and op.get("path") == rel]
    if not matches:
        for_tool = sorted({op.get("path", "?") for op in auth["operations"]
                           if isinstance(op, dict) and op.get("tool") == tool})
        if not for_tool:
            return False, f"authorization does not list tool {tool}"
        return False, f"authorization does not list path {rel} for tool {tool}"

    op = matches[0]
    try:
        budget = int(op.get("max_uses", 0))
    except Exception:
        budget = 0
    spent = uses(project, auth["nonce"], tool, rel)
    if spent >= budget:
        return False, (f"authorization use budget exhausted for {tool} {rel} "
                       f"({spent} of {budget} spent)")

    if consume:
        record(project, auth["nonce"], tool, rel, note=str(auth.get("reason", "")))
        spent += 1
    return True, (f"authorized by {AUTH_REL}, nonce {str(auth['nonce'])[:8]}, "
                  f"use {spent} of {budget}, expires at {expires}")

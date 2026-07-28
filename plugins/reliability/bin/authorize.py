#!/usr/bin/env python3
"""Issue a narrow maintenance authorization. Owner-run, outside Claude.

Stable path: ${CLAUDE_PLUGIN_ROOT}/bin/authorize.py, so it does not depend on any
repository being present. That was the gap in the project-scoped version — it lived
inside one repository, could only express paths inside that repository, and therefore
could not authorize anything under ~/.claude, which the guards now protect.

    # a path inside a repository, bound to its identity and HEAD
    python3 .../bin/authorize.py --scope project --repo-path . --minutes 60 \\
        --reason 'fix the classifier' --op 'Edit:.claude/settings.json:2'

    # a path under $HOME, bound to the installed plugin revision instead
    python3 .../bin/authorize.py --scope global --minutes 30 \\
        --reason 'repoint a hook' --op 'Edit:~/.claude/settings.json:1'

Refusing to run when CLAUDECODE is set is a courtesy, not a boundary: an agent that
can execute arbitrary local code can execute this too. The actual boundary is that
the universal rules deny invoking this file through Bash, so an agent inside a guarded
session cannot reach it without the owner noticing.
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

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "hooks"))

import auth  # noqa: E402
import paths  # noqa: E402


def parse_op(spec: str) -> dict:
    parts = spec.split(":")
    if len(parts) != 3:
        raise SystemExit(f"--op must be TOOL:PATH:MAX_USES, got {spec!r}")
    tool, target, uses = (p.strip() for p in parts)
    if tool not in auth.KNOWN_TOOLS:
        raise SystemExit(f"unknown tool {tool!r}; one of {sorted(auth.KNOWN_TOOLS)}")
    if not target:
        raise SystemExit("the path must not be empty")
    for wildcard in ("*", "?", "["):
        if wildcard in target:
            raise SystemExit("paths are compared literally; wildcards are refused so "
                             "an authorization cannot widen itself")
    if ".." in pathlib.PurePosixPath(target.lstrip("~/")).parts:
        raise SystemExit("the path must not climb out of its scope")
    try:
        budget = int(uses)
    except ValueError:
        raise SystemExit(f"MAX_USES must be a number, got {uses!r}")
    if not 1 <= budget <= 20:
        raise SystemExit("MAX_USES must be between 1 and 20; a large budget is "
                         "indistinguishable from switching the protection off")
    return {"tool": tool, "path": target, "max_uses": budget}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--scope", choices=("project", "global"), required=True)
    ap.add_argument("--repo-path", default=".",
                    help="repository to bind to, for --scope project")
    ap.add_argument("--op", action="append", required=True,
                    help="TOOL:PATH:MAX_USES (repeatable). Project paths are "
                         "repository-relative; global paths start with ~/")
    ap.add_argument("--minutes", type=int, required=True)
    ap.add_argument("--reason", required=True)
    args = ap.parse_args()

    if os.environ.get("CLAUDECODE"):
        raise SystemExit("Refusing to run inside Claude Code. Issuing an "
                         "authorization is an owner action; run it from your own "
                         "terminal.")
    if not 1 <= args.minutes <= 240:
        raise SystemExit("--minutes must be between 1 and 240")

    operations = [parse_op(spec) for spec in args.op]

    record = {
        "scope": args.scope,
        "nonce": secrets.token_hex(8),
        "issued_at": int(time.time()),
        "expires_at": int(time.time()) + args.minutes * 60,
        "reason": args.reason,
        "operations": operations,
    }

    if args.scope == "project":
        project = os.path.realpath(args.repo_path)
        head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=project,
                              capture_output=True, text=True)
        if head.returncode != 0:
            raise SystemExit(f"{project} is not a git repository, so there is no "
                             "commit to bind the authorization to")
        record["repo"] = paths.repo_identity(project)
        record["repo_path"] = project
        record["head"] = head.stdout.strip()
        for op in operations:
            if op["path"].startswith("~"):
                raise SystemExit("a project authorization takes repository-relative "
                                 "paths; use --scope global for paths under ~")
    else:
        record["plugin_revision"] = paths.installed_revision()
        for op in operations:
            if not op["path"].startswith("~/"):
                raise SystemExit("a global authorization takes paths under ~/")

    target = auth.auth_path()
    target.write_text(json.dumps(record, indent=2) + "\n")
    print(json.dumps({"status": "issued", "path": str(target),
                      "scope": record["scope"], "nonce": record["nonce"],
                      "expires_at": record["expires_at"],
                      "bound_to": record.get("head", record.get("plugin_revision")),
                      "operations": operations}, indent=2))
    print(f"\nSpend is recorded in {auth.ledger_path()}.\n"
          "This authorization covers file-editing tools only. It does not relax the "
          "Bash gate, so `rm` on a protected path stays refused.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

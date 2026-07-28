#!/usr/bin/env python3
"""Paths the reliability harness protects from ordinary agent edits.

Shared by guard_destructive_bash.py (the Bash route: redirects, cp, sed -i) and
guard_protected_paths.py (the Write/Edit route) so the two lists cannot drift
apart. A guard that can be edited by the agent it constrains is not a guard.
"""
from __future__ import annotations

import os
import pathlib

CONTRACT_VERSION = "tier1-2026-07-28"

# Repo-relative. A trailing slash means "this prefix and everything under it".
PROTECTED_RELATIVE = (
    ".claude/settings.json",
    ".claude/settings.local.json",
    ".claude/hooks/",
    ".claude/reliability-contract.md",
    ".claude/allowed-scripts.json",
    ".claude/maintenance-auth.json",
    ".claude/maintenance-uses.jsonl",
    ".claude/receipts/",
    "scripts/verify/",
    # The launcher and the fail-closed gate are enforcement, so they are protected
    # on the same terms as the guards they run.
    "scripts/hooks/",
)

# Same protection for the user-level copies, so a global install cannot be
# neutralised from a project session.
PROTECTED_HOME = (
    ".claude/settings.json",
    ".claude/hooks/",
)


def project_dir() -> str:
    """Project root. CLAUDE_PROJECT_DIR when the harness sets it, otherwise
    derived from this file's location (<project>/.claude/hooks/)."""
    env = os.environ.get("CLAUDE_PROJECT_DIR")
    if env and os.path.isdir(env):
        return os.path.realpath(env)
    return str(pathlib.Path(__file__).resolve().parents[2])


def _relative_to(base: str, target: str) -> str | None:
    try:
        rel = os.path.relpath(os.path.realpath(target), os.path.realpath(base))
    except ValueError:
        return None
    rel = rel.replace(os.sep, "/")
    return None if rel == ".." or rel.startswith("../") else rel


def protected_needles() -> tuple[str, ...]:
    """The protected entries as they appear inside a shell command string."""
    return tuple(list(PROTECTED_RELATIVE) + [f"~/{e}" for e in PROTECTED_HOME])


def mentions_protected(text: str) -> str | None:
    """The first protected entry named anywhere in `text`, or None.

    Used by the Bash guard, which sees an unexpanded command string rather than a
    resolvable path. Naming a protected file is not itself a refusal; the caller
    decides whether the surrounding command would rewrite it."""
    for entry in protected_needles():
        if entry.rstrip("/") in text:
            return entry
    return None


def is_protected(abs_path: str, project: str | None = None) -> str | None:
    """Return the matching protected entry, or None."""
    project = project or project_dir()
    for base, entries in ((project, PROTECTED_RELATIVE),
                          (os.path.expanduser("~"), PROTECTED_HOME)):
        rel = _relative_to(base, abs_path)
        if rel is None:
            continue
        for entry in entries:
            if entry.endswith("/"):
                if rel == entry.rstrip("/") or rel.startswith(entry):
                    return entry
            elif rel == entry:
                return entry
    return None

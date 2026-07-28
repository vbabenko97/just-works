#!/usr/bin/env python3
"""Reading owner authorizations, in two scopes, with the issuer outside the agent.

The project-scoped mechanism could not express `~/.claude/settings.json`, because it
resolved every path against the repository and refused anything outside it. Once the
guards protect user-level configuration, that leaves protection with no maintenance
route at all — and protection that cannot be maintained gets switched off instead.

So there are two scopes, and one issuer, shipped with the plugin:

  project   a path inside a repository. Bound to the repository identity and to HEAD,
            because a repository has a commit to bind to.
  global    a path under ${HOME}. Bound to the installed plugin revision instead of
            HEAD, because there is no repository, and an authorization must still
            stop being valid when the thing it authorizes changes.

Both are bound to an expiry, a nonce, literal paths, exact tools, and a use budget
spent in an append-only ledger. Neither ever relaxes the Bash gate: authorizations
are consulted for file-editing tools only. That is why dismantling the harness stays
an owner operation — `rm` on a protected path is refused whatever is authorized.

This file only *reads*. Issuing is `bin/authorize.py`, which refuses to run inside
Claude, and which the universal rules refuse to invoke through Bash.
"""
from __future__ import annotations

import json
import os
import pathlib
import subprocess
import sys
import time

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

import paths  # noqa: E402

KNOWN_TOOLS = {"Write", "Edit", "MultiEdit", "NotebookEdit"}
AUTH_NAME = "authorization.json"
LEDGER_NAME = "authorization-uses.jsonl"


def auth_path() -> pathlib.Path:
    return paths.plugin_data() / AUTH_NAME


def ledger_path() -> pathlib.Path:
    return paths.plugin_data() / LEDGER_NAME


def _head(project: str) -> str | None:
    try:
        out = subprocess.run(["git", "rev-parse", "HEAD"], cwd=project,
                             capture_output=True, text=True, timeout=5)
        return out.stdout.strip() if out.returncode == 0 else None
    except Exception:
        return None


def load() -> tuple[dict | None, str]:
    path = auth_path()
    if not path.is_file():
        return (None, "no maintenance authorization is active")
    try:
        data = json.loads(path.read_text())
    except Exception as exc:
        return (None, f"the authorization is unreadable ({exc})")
    if not isinstance(data, dict):
        return (None, "the authorization is not an object")
    for key in ("scope", "nonce", "expires_at", "operations"):
        if key not in data:
            return (None, f"the authorization is missing {key}")
    if data["scope"] not in ("project", "global"):
        return (None, f"unknown authorization scope {data['scope']!r}")
    if not isinstance(data["operations"], list):
        return (None, "the authorized operations are not a list")
    return (data, "")


def spent(nonce: str, tool: str, target: str) -> int:
    """Uses already recorded. An unreadable ledger returns a number no budget can
    exceed, so a ledger that cannot be read is a refusal rather than a free pass."""
    path = ledger_path()
    if not path.exists():
        return 0
    try:
        used = 0
        for line in path.read_text().splitlines():
            if not line.strip():
                continue
            row = json.loads(line)
            if (row.get("nonce") == nonce and row.get("tool") == tool
                    and row.get("path") == target):
                used += 1
        return used
    except Exception:
        return 10 ** 6


def _record(nonce: str, tool: str, target: str) -> None:
    try:
        with ledger_path().open("a") as fh:
            fh.write(json.dumps({"nonce": nonce, "tool": tool, "path": target,
                                 "at": int(time.time())}) + "\n")
    except Exception:
        pass


def check(tool: str, abs_path: str, project: str,
          consume: bool = False) -> tuple[bool, str]:
    """(ok, reason). Never raises: any error is a refusal.

    Call with consume=False to test and again with consume=True to spend, so a
    partly-authorized batch can be refused whole rather than half-applied."""
    auth, problem = load()
    if auth is None:
        return (False, problem)

    if tool not in KNOWN_TOOLS:
        return (False, f"{tool} is not a tool an authorization can cover")

    now = int(time.time())
    try:
        expires = int(auth["expires_at"])
    except Exception:
        return (False, "the authorization expiry is not a number")
    if now >= expires:
        return (False, f"the authorization expired {now - expires}s ago")

    resolved = os.path.realpath(abs_path)
    scope = auth["scope"]

    if scope == "project":
        expected = paths.repo_identity(project)
        if auth.get("repo") != expected:
            return (False, f"the authorization is for a different repository "
                           f"({auth.get('repo')}, this is {expected})")
        head = _head(project)
        if head is None:
            return (False, "HEAD cannot be read, so the authorization cannot be "
                           "validated")
        if auth.get("head") != head:
            return (False, f"the authorization is bound to commit "
                           f"{str(auth.get('head'))[:12]}, HEAD is {head[:12]}")
        root = os.path.realpath(project)
        try:
            rel = os.path.relpath(resolved, root).replace(os.sep, "/")
        except ValueError:
            return (False, "the path cannot be resolved against the repository")
        if rel == ".." or rel.startswith("../"):
            return (False, "a project authorization cannot cover a path outside the "
                           "repository; that needs a global authorization")
        target = rel
    else:
        revision = paths.installed_revision()
        if auth.get("plugin_revision") != revision:
            return (False, f"the authorization was issued for plugin revision "
                           f"{auth.get('plugin_revision')}, and {revision} is "
                           "installed")
        home = os.path.realpath(str(pathlib.Path.home()))
        try:
            rel = os.path.relpath(resolved, home).replace(os.sep, "/")
        except ValueError:
            return (False, "the path cannot be resolved against the home directory")
        if rel == ".." or rel.startswith("../"):
            return (False, "a global authorization covers paths under the home "
                           "directory only")
        target = "~/" + rel

    for op in auth["operations"]:
        if not isinstance(op, dict):
            continue
        if op.get("tool") != tool or op.get("path") != target:
            continue
        try:
            budget = int(op.get("max_uses", 0))
        except Exception:
            return (False, "the authorized use count is not a number")
        used = spent(auth["nonce"], tool, target)
        if used >= budget:
            return (False, f"the authorization for {tool} on {target} is used up "
                           f"({used}/{budget})")
        if consume:
            _record(auth["nonce"], tool, target)
        return (True, f"authorized: {tool} on {target}, use {used + 1} of {budget}, "
                      f"nonce {auth['nonce']}")

    return (False, f"the authorization does not cover {tool} on {target}")

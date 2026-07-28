#!/usr/bin/env python3
"""Where immutable code lives, where mutable state lives, and how a repo is named.

Two roots, and conflating them was the flaw in the project-scoped design:

  ${CLAUDE_PLUGIN_ROOT}   the installed, versioned, read-only copy of this plugin.
                          Bundled code and the fallback contract.
  ${CLAUDE_PLUGIN_DATA}   this plugin's own mutable state: receipts, authorizations,
                          spend ledgers.

Receipts used to be written to `<repo>/.claude/receipts/`, which made the repository
the source of truth for whether the repository's own rules had been delivered. An
agent that can write inside the repository could then manufacture the proof that it
had been constrained. State lives outside the repository now, and the repository is
identified rather than trusted.

CLAUDE_PLUGIN_DATA is not taken on faith. It is per-plugin, and a hook process
inherits whatever the surrounding session exported — observed in practice pointing at
a *different* plugin's data directory. So the value is accepted only when it names
this plugin, and otherwise derived from the installed root.
"""
from __future__ import annotations

import hashlib
import json
import os
import pathlib
import subprocess

HERE = pathlib.Path(__file__).resolve().parent
PLUGIN_NAME = "reliability"


def plugin_root() -> pathlib.Path:
    """The installed plugin directory. Trust `__file__` over the environment: it is
    the copy that is executing, which is the thing every path here must agree with."""
    return HERE.parent


def installed_revision() -> str:
    """For a plugin with no declared version, the manager names the install directory
    after the source commit, so the directory name is the revision."""
    root = plugin_root()
    try:
        declared = json.loads(
            (root / ".claude-plugin" / "plugin.json").read_text()).get("version")
        if declared:
            return str(declared)
    except Exception:
        pass
    return root.name


def _derive_data_dir() -> pathlib.Path:
    """`~/.claude/plugins/data/<plugin>-<marketplace>`, worked out from the install
    path: `.../plugins/cache/<marketplace>/<plugin>/<revision>`."""
    root = plugin_root()
    parts = root.parts
    marketplace = ""
    if "cache" in parts:
        i = parts.index("cache")
        if len(parts) > i + 1:
            marketplace = parts[i + 1]
    home = pathlib.Path.home() / ".claude" / "plugins" / "data"
    name = f"{PLUGIN_NAME}-{marketplace}" if marketplace else PLUGIN_NAME
    return home / name


def plugin_data() -> pathlib.Path:
    """This plugin's mutable state directory, created on demand."""
    override = os.environ.get("RELIABILITY_DATA_DIR")
    if override:
        path = pathlib.Path(override)
    else:
        derived = _derive_data_dir()
        env = os.environ.get("CLAUDE_PLUGIN_DATA")
        # Accept the environment only when it actually names this plugin.
        path = pathlib.Path(env) if env and pathlib.Path(env).name == derived.name \
            else derived
    path.mkdir(parents=True, exist_ok=True)
    return path


def repo_identity(project: str) -> str:
    """A stable name for a repository that does not depend on its current path.

    Preference order: the first git remote URL, then the canonical git toplevel,
    then the canonical project directory. A remote survives the checkout being
    moved or renamed, which a path does not — and requirement 1 of stage 3 was
    precisely that moving the checkout must not break anything.
    """
    canonical = os.path.realpath(project)
    label = os.path.basename(canonical) or "repo"
    basis = canonical
    try:
        top = subprocess.run(["git", "rev-parse", "--show-toplevel"], cwd=project,
                             capture_output=True, text=True, timeout=5)
        if top.returncode == 0 and top.stdout.strip():
            canonical = os.path.realpath(top.stdout.strip())
            label = os.path.basename(canonical) or label
            basis = canonical
        remote = subprocess.run(["git", "remote", "get-url", "origin"], cwd=project,
                                capture_output=True, text=True, timeout=5)
        if remote.returncode == 0 and remote.stdout.strip():
            basis = remote.stdout.strip()
    except Exception:
        pass
    digest = hashlib.sha256(basis.encode()).hexdigest()[:16]
    safe = "".join(c if c.isalnum() or c in "-_" else "-" for c in label)[:40]
    return f"{safe}-{digest}"


def receipts_dir(project: str) -> pathlib.Path:
    return plugin_data() / "receipts" / repo_identity(project)


def contract_text(project: str, pol) -> tuple[str, str]:
    """(text, source). The repository's contract when its manifest declares one and
    the file is readable; otherwise the copy bundled with the plugin. A repository
    may replace the text; it cannot remove the delivery."""
    declared = pol.data.get("contract") if getattr(pol, "active", False) else None
    if isinstance(declared, str):
        candidate = pathlib.Path(project) / declared
        try:
            resolved = candidate.resolve()
            root = pathlib.Path(project).resolve()
            if root in resolved.parents and resolved.is_file():
                return (resolved.read_text(), f"repository: {declared}")
        except Exception:
            pass
    bundled = plugin_root() / "contract.md"
    try:
        return (bundled.read_text(), "plugin: contract.md")
    except Exception:
        return ("", "unavailable")

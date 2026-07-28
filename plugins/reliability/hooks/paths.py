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
from typing import NamedTuple

import policy as policy_mod

HERE = pathlib.Path(__file__).resolve().parent
PLUGIN_NAME = "reliability"

# Bumped whenever the composition algorithm itself changes shape (part order, join
# delimiter, what counts as mandatory) — independent of the content of any part. A
# receipt's schema tag must match this exactly, so a plugin upgrade invalidates old
# receipts even in the freak case where the digest happened not to change.
COMPOSITION_SCHEMA = "reliability-contract-compose-v1"


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


class ComposedContract(NamedTuple):
    """Result of composing the delivered contract. `ok=False` means composition
    failed — never a placeholder, never a receipt: SubagentStart must not issue one
    and SubagentStop must not accept one when this is the state."""
    ok: bool
    text: str
    sources: tuple[str, ...]
    digest: str | None
    schema: str
    error: str | None


def _read_bundled(name: str) -> tuple[str | None, str | None]:
    """(text, error). A bundled file is part of what this plugin guarantees, so a
    read failure here is a composition failure, not something to paper over."""
    try:
        return (plugin_root() / name).read_text(), None
    except Exception as exc:
        return None, f"{name} unavailable: {exc}"


def compose_contract(project: str, pol) -> ComposedContract:
    """Universal epistemic contract, then the bundled operational contract, then an
    optional but — once declared — mandatory repository addition, then a fixed
    closing reminder. The two bundled files are always required. A `contract` key
    in policy, once present, is also required: a repository that declares one and
    then can't deliver it fails composition exactly like a missing bundled file,
    rather than silently running with less than it asked for. Only the absence of
    the `contract` key at all is optional.

    This guarantees verified delivery of text. It does not, and cannot by
    concatenation alone, guarantee that any agent behaviorally follows any part of
    it — see the closing paragraph of epistemic-contract.md.
    """
    epistemic, err = _read_bundled("epistemic-contract.md")
    if err:
        return ComposedContract(False, "", (), None, COMPOSITION_SCHEMA, err)
    operational, err = _read_bundled("contract.md")
    if err:
        return ComposedContract(False, "", (), None, COMPOSITION_SCHEMA, err)
    reminder, err = _read_bundled("epistemic-reminder.md")
    if err:
        return ComposedContract(False, "", (), None, COMPOSITION_SCHEMA, err)

    parts = [epistemic, operational]
    sources = ["plugin: epistemic-contract.md", "plugin: contract.md"]

    declared = pol.data.get("contract") if getattr(pol, "active", False) else None
    if isinstance(declared, str):
        candidate = pathlib.Path(project) / declared
        resolved, problem = policy_mod.safe_regular_file(str(candidate), project)
        if resolved is None:
            return ComposedContract(False, "", (), None, COMPOSITION_SCHEMA,
                                    f"declared contract {declared} {problem}")
        try:
            repo_bytes = pathlib.Path(resolved).read_bytes()
        except Exception as exc:
            return ComposedContract(False, "", (), None, COMPOSITION_SCHEMA,
                                    f"declared contract {declared} could not be "
                                    f"read: {exc}")
        try:
            repo_text = repo_bytes.decode("utf-8")
        except UnicodeDecodeError as exc:
            return ComposedContract(False, "", (), None, COMPOSITION_SCHEMA,
                                    f"declared contract {declared} is not valid "
                                    f"UTF-8: {exc}")
        parts.append("## Repository additions (lower priority — see the "
                     "reminder below)\n\n" + repo_text)
        sources.append(f"repository: {declared}")

    parts.append(reminder)
    sources.append("plugin: epistemic-reminder.md")

    text = "\n\n".join(parts)
    digest = hashlib.sha256(
        f"{COMPOSITION_SCHEMA}\n{text}".encode("utf-8")).hexdigest()
    return ComposedContract(True, text, tuple(sources), digest, COMPOSITION_SCHEMA,
                            None)

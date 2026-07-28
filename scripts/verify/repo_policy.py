#!/usr/bin/env python3
"""Which repository paths owner tooling must refuse to mutate.

Replaces `.claude/hooks/reliability_paths.py`, deleted in the Stage 3 cutover. That
module was shared with the project's own PreToolUse guards; those guards are gone, so
this one serves `bulk_mutate.py` alone. It is owner tooling, not enforcement: nothing
here runs as a hook, and no decision the reliability plugin makes depends on it.

**No runtime dependency on the installed plugin.** The universal tuples below are
duplicated from the plugin's `hooks/rules.py` on purpose: an owner tool that imported
enforcement code would stop working whenever the plugin was absent, disabled or
mid-update, and would couple a repository script to a versioned install directory.
Duplication is the lesser cost, and it is not left to drift —
`tests/reliability/test_owner_policy.py` parses the plugin source and fails when the
two disagree.

Three answers, and the third is the one that matters:

  an entry string   the path is protected; the caller needs an authorization
  None              an ordinary path
  an exception      the question could not be answered safely

`is_protected` raises rather than returning None when a path lexically inside the
repository resolves outside it, or when the manifest exists but cannot be trusted. In
both cases None would read as "ordinary, safe to delete", which is precisely wrong: an
escaping symlink is a route to mutating something outside the reviewed tree, and a
malformed manifest would silently unprotect `scripts/verify/` — the set the wrapper
must never touch.

Resolution is deliberate about *what* it resolves. The parent chain is canonicalized
so that a repository reached through a symlinked ancestor still counts as inside it —
on macOS `/var` is a link to `/private/var`, and comparing an unresolved path against a
resolved root reported every temporary checkout as external, which would have skipped
the escape check entirely. The final component is left unresolved, because that is the
symlink whose target is the question.
"""
from __future__ import annotations

import json
import os
import pathlib

MANIFEST_REL = ".claude/reliability-policy.json"
SUPPORTED_POLICY_VERSIONS = (1,)

# Duplicated from the plugin's universal project set. Parity is asserted by test.
UNIVERSAL_PROJECT = (
    ".claude/settings.json",
    ".claude/settings.local.json",
    ".claude/hooks/",
    ".claude/reliability-policy.json",
    ".claude/allowed-scripts.json",
)

# Duplicated from the plugin's universal home set. Kept because this wrapper can
# genuinely reach these paths: `install.sh` syncs skills into `${CLAUDE_HOME}/skills`
# and `${AGENTS_HOME}/skills`, so a stale-directory cleanup rooted at `~/.claude`
# would otherwise be free to enumerate `~/.claude/hooks/` or the plugin install.
UNIVERSAL_HOME = (
    ".claude/settings.json",
    ".claude/settings.local.json",
    ".claude/hooks/",
    ".claude/plugins/",
    ".claude/reliability-auth.json",
    ".claude/reliability-uses.jsonl",
)

ALLOWED_KEYS = {
    "policy_version", "contract_version", "description", "allowlist", "contract",
    "protected", "maintenance", "require_subagent_receipts",
}
ALLOWED_MAINTENANCE_KEYS = {"issuer", "ledger"}


class PolicyError(Exception):
    """The protection question could not be answered safely."""


class ManifestError(PolicyError):
    """The manifest is present and cannot be trusted."""


class OutsideRepository(PolicyError):
    """A path inside the repository resolves outside it."""


def _rel_inside(value) -> bool:
    """A manifest path must be repository-relative and must not climb out."""
    if not isinstance(value, str) or not value:
        return False
    if os.path.isabs(value) or value.startswith("~"):
        return False
    return ".." not in pathlib.PurePosixPath(value).parts


def load_manifest(project: str) -> dict | None:
    """The manifest as a dict, or None when there is none.

    Raises ManifestError when it exists but is malformed, declares an unsupported
    version, carries unknown keys, or names a path climbing out of the repository.
    Absent is a legitimate state; present-and-wrong is not.
    """
    path = os.path.join(project, MANIFEST_REL)
    if not os.path.lexists(path):
        return None

    try:
        with open(path) as fh:
            data = json.load(fh)
    except Exception as exc:
        raise ManifestError(f"{MANIFEST_REL} is not readable JSON ({exc})") from exc
    if not isinstance(data, dict):
        raise ManifestError(f"{MANIFEST_REL} does not contain a JSON object")

    unknown = sorted(set(data) - ALLOWED_KEYS)
    if unknown:
        raise ManifestError(f"{MANIFEST_REL} declares unknown keys: "
                            f"{', '.join(unknown)}")

    version = data.get("policy_version")
    if not isinstance(version, int) or isinstance(version, bool):
        raise ManifestError(f"{MANIFEST_REL} has no integer policy_version")
    if version not in SUPPORTED_POLICY_VERSIONS:
        raise ManifestError(
            f"{MANIFEST_REL} asks for policy_version {version}; this tool supports "
            f"{', '.join(str(v) for v in SUPPORTED_POLICY_VERSIONS)}")

    protected = data.get("protected", [])
    if not isinstance(protected, list) or not all(_rel_inside(p) for p in protected):
        raise ManifestError(f"{MANIFEST_REL} protected must be a list of "
                            "repository-relative paths that do not climb outside it")

    maintenance = data.get("maintenance", {})
    if not isinstance(maintenance, dict):
        raise ManifestError(f"{MANIFEST_REL} maintenance must be an object")
    unknown_m = sorted(set(maintenance) - ALLOWED_MAINTENANCE_KEYS)
    if unknown_m:
        raise ManifestError(f"{MANIFEST_REL} maintenance declares unknown keys: "
                            f"{', '.join(unknown_m)}")
    if not all(_rel_inside(v) for v in maintenance.values()):
        raise ManifestError(f"{MANIFEST_REL} maintenance paths must be "
                            "repository-relative")

    for key in ("allowlist", "contract"):
        value = data.get(key)
        if value is not None and not _rel_inside(value):
            raise ManifestError(f"{MANIFEST_REL} {key} must be a "
                                "repository-relative path")

    return data


def policy_entries(project: str) -> tuple[str, ...]:
    """Paths the manifest asks to protect, in declaration order.

    Includes the files the manifest *names* as well as those it lists: an allowlist
    or a spend ledger that could be rewritten is not protected in any useful sense.
    """
    data = load_manifest(project)
    if data is None:
        return ()
    entries: list[str] = [p for p in data.get("protected", []) if isinstance(p, str)]
    for key in ("allowlist", "contract"):
        value = data.get(key)
        if isinstance(value, str):
            entries.append(value)
    maintenance = data.get("maintenance") or {}
    for key in ("issuer", "ledger"):
        value = maintenance.get(key)
        if isinstance(value, str):
            entries.append(value)
    return tuple(dict.fromkeys(entries))


def protected_entries(project: str) -> tuple[str, ...]:
    """The union of the mandatory universal set and whatever the manifest adds."""
    return tuple(dict.fromkeys(list(UNIVERSAL_PROJECT) + list(policy_entries(project))))


def _match(rel: str, entries) -> str | None:
    for entry in entries:
        if entry.endswith("/"):
            if rel == entry.rstrip("/") or rel.startswith(entry):
                return entry
        elif rel == entry:
            return entry
    return None


def _relative(base_real: str, target: str) -> str | None:
    """`target` as a POSIX path relative to an already-canonical `base_real`, or
    None when it is not inside it."""
    try:
        rel = os.path.relpath(target, base_real).replace(os.sep, "/")
    except (ValueError, OSError):
        return None
    return None if rel == ".." or rel.startswith("../") else rel


def _canonical_container(lexical: str) -> str:
    """`lexical` with its parent chain resolved and its final component left alone."""
    parent = os.path.dirname(lexical)
    try:
        return os.path.join(os.path.realpath(parent), os.path.basename(lexical))
    except OSError:
        return lexical


def is_protected(abs_path: str, project: str | None = None) -> str | None:
    """The protected entry matching `abs_path`, or None for an ordinary path.

    Raises OutsideRepository when `abs_path` is lexically inside the repository but
    resolves outside it — traversal, or a symlink whose target escapes. Answering
    None there would report a route out of the reviewed tree as safe to delete.

    Raises ManifestError when the manifest cannot be trusted.

    A path that is not inside the repository at all is classified against the
    home-scope set, then returned as None. That is deliberate rather than an
    omission: this wrapper legitimately operates on `~/.claude/skills` and on other
    checkouts, and those targets are bounded by `--root`, not by this repository's
    policy.
    """
    project = project or str(pathlib.Path(__file__).resolve().parents[2])
    root = os.path.realpath(project)
    lexical = os.path.abspath(os.path.expanduser(abs_path))
    resolved = os.path.realpath(lexical)

    inside_lexically = _relative(root, _canonical_container(lexical)) is not None
    rel_resolved = _relative(root, resolved)

    if inside_lexically and rel_resolved is None:
        raise OutsideRepository(
            f"{abs_path} is inside the repository but resolves to {resolved}")

    if rel_resolved is not None:
        return _match(rel_resolved, protected_entries(project))

    # Not a repository path. Validate the manifest anyway, so a broken manifest is
    # reported rather than skipped for whichever target happens to be external.
    load_manifest(project)
    rel_home = _relative(os.path.realpath(str(pathlib.Path.home())), resolved)
    if rel_home is not None:
        return _match(rel_home, UNIVERSAL_HOME)
    return None

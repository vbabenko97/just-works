#!/usr/bin/env python3
"""Ordering is the guarantee.

    1. universal denials          — no repository file has been read yet
    2. invalid policy             — mutation refused, reads survive
    3. policy layer               — only reached if 1 allowed
    4. universal bounding check   — mutation whose target set cannot be bounded

Monotonicity falls out of step 1 preceding step 3. A repository cannot weaken a
universal denial because the decision has already returned before `policy.load`
is called, and the policy layer has no code path that returns "allow" for a command
the universal layer refused. `allowed-scripts.json` can except exactly one denial,
the unknown-script denial in policy.py, and it is consulted nowhere else.

Every decision carries the layer that produced it, so a refusal can be read as
"this is absolute" or "this is your repository's policy" without guessing.
"""
from __future__ import annotations

import os
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

import policy as policy_mod  # noqa: E402
import rules  # noqa: E402

UNIVERSAL, POLICY, DEFAULT = "universal", "policy", "default"

INVALID_HINT = (
    "This repository declares policy it cannot honour, so mutation is refused "
    "rather than quietly running with less enforcement than the manifest asks for. "
    "Reads are still allowed so the manifest can be inspected and fixed."
)


def decide_bash(command: str, cwd: str, project: str,
                depth: int = 0) -> tuple[str, str, str]:
    """(decision, reason, layer) for a Bash command."""
    reason = rules.universal_deny(command, project)
    if reason:
        return ("deny", reason, UNIVERSAL)

    pol = policy_mod.load(project)

    if pol.state == policy_mod.INVALID:
        if rules.is_read_only(command):
            return ("allow", f"policy configuration error ({pol.reason}); this "
                             "command is read-only, so it is permitted", POLICY)
        return ("deny", f"policy configuration error: {pol.reason}. {INVALID_HINT}",
                POLICY)

    if pol.active:
        extra = policy_mod.protected_paths(pol)
        segments = rules.split_segments(command)
        for segment in segments:
            hit = rules.protected_hit(segment, project, extra)
            if hit:
                entry, why = hit
                return ("deny", f"would modify a path this repository's policy "
                                f"protects ({entry}; {why})", POLICY)

        def recurse(inner: str) -> tuple[str, str]:
            if depth >= 2:
                return ("deny", "nested -c programs beyond the inspection depth")
            d, r, _ = decide_bash(inner, cwd, project, depth + 1)
            return (d, f"inside `-c`: {r}")

        notes: list[str] = []
        fell_through = False
        for segment in segments:
            verdict = policy_mod.classify_segment(segment, cwd, project, pol, recurse)
            if verdict is None:
                fell_through = True
                continue
            decision, why = verdict
            if decision != "allow":
                return ("deny", why, POLICY)
            notes.append(why)
        if notes and not fell_through:
            return ("allow", "; ".join(notes), POLICY)

    reason = rules.unbounded_deny(command)
    if reason:
        return ("deny", reason, UNIVERSAL)

    if rules.is_read_only(command):
        return ("allow", "read-only command", DEFAULT)
    return ("allow", "no unbounded mutation detected", DEFAULT)


def decide_paths(tool: str, paths: list[str], cwd: str,
                 project: str) -> tuple[str, str, str]:
    """(decision, reason, layer) for a file-editing tool."""
    resolved = []
    for raw in paths:
        candidate = os.path.expanduser(raw)
        if not os.path.isabs(candidate):
            candidate = os.path.join(cwd, candidate)
        resolved.append(candidate)

    for abs_path in resolved:
        entry = rules.universal_protected_path(abs_path, project)
        if entry:
            return ("deny", f"{tool} would modify the configuration that governs "
                            f"this agent ({entry}). Hand the diff to the owner",
                    UNIVERSAL)

    pol = policy_mod.load(project)

    if pol.state == policy_mod.INVALID:
        return ("deny", f"policy configuration error: {pol.reason}. {INVALID_HINT}",
                POLICY)

    if pol.active:
        extra = policy_mod.protected_paths(pol)
        root = os.path.realpath(project)
        for abs_path in resolved:
            try:
                rel = os.path.relpath(os.path.realpath(abs_path), root)
            except ValueError:
                continue
            rel = rel.replace(os.sep, "/")
            if rel == ".." or rel.startswith("../"):
                continue
            for entry in extra:
                if entry.endswith("/"):
                    if rel == entry.rstrip("/") or rel.startswith(entry):
                        return ("deny", f"{tool} would modify a path this "
                                        f"repository's policy protects ({entry})",
                                POLICY)
                elif rel == entry:
                    return ("deny", f"{tool} would modify a path this repository's "
                                    f"policy protects ({entry})", POLICY)

    return ("allow", "no protected path targeted", DEFAULT)


def receipt_required(project: str) -> tuple[bool, str]:
    """Whether subagents in this project must present a contract receipt.

    Absent policy means no, because nothing has been injected to present. Invalid
    policy also means no: mutation is already refused, and demanding a receipt no
    hook is issuing would deny every subagent's first read for a reason the user
    cannot act on."""
    pol = policy_mod.load(project)
    if pol.state == policy_mod.ABSENT:
        return (False, "no policy manifest; subagent receipts are not required")
    if pol.state == policy_mod.INVALID:
        return (False, f"policy configuration error ({pol.reason}); receipts are "
                       "not enforced, and mutation is refused instead")
    if pol.require_receipts:
        return (True, f"policy requires subagent receipts at contract "
                      f"{pol.contract_version or 'unversioned'}")
    return (False, "policy does not require subagent receipts")

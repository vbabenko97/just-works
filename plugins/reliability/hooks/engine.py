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

import auth  # noqa: E402
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


def _policy_entry(abs_path: str, project: str,
                  extra: tuple[str, ...]) -> str | None:
    root = os.path.realpath(project)
    try:
        rel = os.path.relpath(os.path.realpath(abs_path), root).replace(os.sep, "/")
    except ValueError:
        return None
    if rel == ".." or rel.startswith("../"):
        return None
    for entry in extra:
        if entry.endswith("/"):
            if rel == entry.rstrip("/") or rel.startswith(entry):
                return entry
        elif rel == entry:
            return entry
    return None


def decide_paths(tool: str, paths: list[str], cwd: str,
                 project: str) -> tuple[str, str, str]:
    """(decision, reason, layer) for a file-editing tool.

    Everything gated is collected first, then the authorization is tested for all of
    it before a single use is spent. A partly-authorized MultiEdit is refused whole:
    spending as we went would leave the budget consumed by a call that never applied.
    """
    resolved = []
    for raw in paths:
        candidate = os.path.expanduser(raw)
        if not os.path.isabs(candidate):
            candidate = os.path.join(cwd, candidate)
        resolved.append(candidate)

    pol = policy_mod.load(project)
    extra = policy_mod.protected_paths(pol) if pol.active else ()

    # (path, why, layer)
    gated: list[tuple[str, str, str]] = []
    for abs_path in resolved:
        entry = rules.universal_protected_path(abs_path, project)
        if entry:
            gated.append((abs_path, f"{tool} would modify the configuration that "
                                    f"governs this agent ({entry})", UNIVERSAL))
            continue
        if pol.state == policy_mod.INVALID:
            gated.append((abs_path, f"policy configuration error: {pol.reason}. "
                                    f"{INVALID_HINT}", POLICY))
            continue
        entry = _policy_entry(abs_path, project, extra)
        if entry:
            gated.append((abs_path, f"{tool} would modify a path this repository's "
                                    f"policy protects ({entry})", POLICY))

    if not gated:
        return ("allow", "no protected path targeted", DEFAULT)

    for abs_path, why, layer in gated:
        ok, detail = auth.check(tool, abs_path, project, consume=False)
        if not ok:
            return ("deny", f"{why}. {detail}", layer)

    granted = []
    for abs_path, _, _ in gated:
        _, detail = auth.check(tool, abs_path, project, consume=True)
        granted.append(detail)
    return ("allow", "; ".join(granted), POLICY)


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

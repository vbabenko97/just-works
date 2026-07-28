#!/usr/bin/env python3
"""Proof that a subagent was given the rules, keyed so it cannot be borrowed.

SubagentStart cannot refuse to create a subagent, so contract delivery is
best-effort by construction. What can be enforced is the consequence: every tool
call carrying an `agent_id` must present a receipt written when the contract was
delivered, or the call is refused. The subagent still starts. It cannot act.

The key is (repository identity, session id, agent id, agent type, contract
version). All five, because each removes a way to reuse a receipt: a different repo,
a new session, a different agent in the same session, a different agent type with a
recycled id, or a stale contract. Receipts live under ${CLAUDE_PLUGIN_DATA}, not in
the repository, so an agent that can write files in the repository cannot forge the
proof that it was constrained.
"""
from __future__ import annotations

import json
import os
import pathlib
import sys
import time

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

import paths  # noqa: E402

MAX_AGE_SECONDS = 12 * 60 * 60


def is_subagent(payload: dict) -> bool:
    return bool(payload.get("agent_id"))


def _path(project: str, session_id: str, agent_id: str) -> pathlib.Path:
    safe_session = "".join(c for c in str(session_id) if c.isalnum() or c in "-_")
    safe_agent = "".join(c for c in str(agent_id) if c.isalnum() or c in "-_")
    return paths.receipts_dir(project) / safe_session / f"{safe_agent}.json"


# Fields a valid receipt must carry, beyond the identity keys checked by name below.
# An old-format receipt (issued before this schema existed) is missing every one of
# these, and must be refused, not grandfathered in.
MANDATORY_FIELDS = ("composition_schema", "contract_sha256", "contract_sources",
                    "contract_bytes", "plugin_revision")


def issue(project: str, payload: dict, contract_version: str,
          composed) -> pathlib.Path | None:
    """Record delivery. Returns the receipt path, or None if it could not be written
    or the contract could not be composed — the caller does not fail on that,
    because the missing receipt is itself the enforcement. Never issue a receipt for
    a contract that failed to compose: that would make a failure look like proof of
    delivery."""
    if not getattr(composed, "ok", False):
        return None
    try:
        target = _path(project, payload.get("session_id", ""),
                       payload.get("agent_id", ""))
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps({
            "repo": paths.repo_identity(project),
            "session_id": payload.get("session_id"),
            "agent_id": payload.get("agent_id"),
            "agent_type": payload.get("agent_type"),
            "contract_version": contract_version,
            "composition_schema": composed.schema,
            "contract_sources": list(composed.sources),
            "contract_bytes": len(composed.text),
            "contract_sha256": composed.digest,
            "plugin_revision": paths.installed_revision(),
            "issued_at": int(time.time()),
        }, indent=2) + "\n")
        return target
    except Exception:
        return None


def verify(payload: dict, project: str, contract_version: str,
          composed) -> tuple[bool, str]:
    """(ok, reason). Every failure mode gets a distinct reason: a refusal nobody can
    diagnose gets switched off, which is worse than not having it.

    `composed` is the contract as it exists *right now*, recomputed by the caller at
    verify time — not what it was when the receipt was issued. A receipt is only as
    good as its match against the current state, which is what makes mutation after
    issuance, and mutation after a prior successful call, both get caught here."""
    session_id = payload.get("session_id")
    agent_id = payload.get("agent_id")
    agent_type = payload.get("agent_type")
    if not session_id:
        return (False, "the payload carries no session_id, so no receipt can be "
                       "matched to it")

    if not getattr(composed, "ok", False):
        error = getattr(composed, "error", "unknown")
        return (False, f"the current contract cannot be composed ({error}); no "
                       f"receipt can be valid while that is true")

    target = _path(project, session_id, agent_id or "")
    if not target.is_file():
        return (False, f"no contract receipt for agent {agent_id} in session "
                       f"{session_id}; the contract was not delivered")
    try:
        data = json.loads(target.read_text())
    except Exception as exc:
        return (False, f"the contract receipt is unreadable ({exc})")

    expected_repo = paths.repo_identity(project)
    if data.get("repo") != expected_repo:
        return (False, f"the receipt was issued for a different repository "
                       f"({data.get('repo')}, expected {expected_repo})")
    if data.get("session_id") != session_id:
        return (False, "the receipt was issued in a different session")
    if data.get("agent_id") != agent_id:
        return (False, "the receipt was issued for a different agent")
    if agent_type and data.get("agent_type") != agent_type:
        return (False, f"the receipt was issued for agent type "
                       f"{data.get('agent_type')}, not {agent_type}")
    if contract_version and data.get("contract_version") != contract_version:
        return (False, f"the receipt is for contract {data.get('contract_version')}, "
                       f"and the current contract is {contract_version}")

    for field in MANDATORY_FIELDS:
        if not data.get(field):
            return (False, f"the receipt has no {field} (issued before digest "
                           f"verification existed, or corrupted); it cannot be "
                           f"trusted against the current contract")
    if data.get("contract_sha256") != composed.digest:
        return (False, "the receipt's contract digest does not match the currently "
                       "composed contract; the content changed since delivery")
    if data.get("composition_schema") != composed.schema:
        return (False, f"the receipt's composition schema "
                       f"({data.get('composition_schema')}) differs from the "
                       f"current one ({composed.schema})")

    issued = data.get("issued_at")
    if not isinstance(issued, int):
        return (False, "the receipt has no usable issue time")
    age = int(time.time()) - issued
    if age < -60:
        return (False, "the receipt is dated in the future")
    if age > MAX_AGE_SECONDS:
        return (False, f"the receipt is stale ({age}s old)")
    return (True, f"contract {contract_version} delivered to {agent_type or 'agent'} "
                  f"{agent_id}")


def count(project: str, session_id: str) -> int:
    """Receipts on disk for one session. Used by tests and probes."""
    try:
        directory = _path(project, session_id, "x").parent
        return len(list(directory.glob("*.json")))
    except Exception:
        return 0

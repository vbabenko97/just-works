#!/usr/bin/env python3
"""Session-scoped receipts proving the reliability contract reached a subagent.

SubagentStart cannot block subagent creation, so injection is best-effort: if the
hook fails, the subagent starts anyway and simply never sees the contract. Explore
and Plan also skip CLAUDE.md, so for them the injected contract is the only copy of
the rules they get. Best-effort delivery of the only copy is not delivery.

This turns it into something enforceable. SubagentStart writes a receipt; every
PreToolUse call made by a subagent must find a matching one or be refused. The
subagent still starts — nothing can stop that — but it cannot act.

The key is (session_id, agent_id, agent_type, contract_version), all four measured
from real payloads rather than assumed:

  SubagentStart      session_id, agent_id, agent_type
  PreToolUse (sub)   session_id, agent_id, agent_type
  PreToolUse (main)  session_id only, no agent_id

So "is this a subagent call" is decidable from the payload, and a receipt cannot be
reused across sessions or agents because both appear in the path and the contents.
"""
from __future__ import annotations

import hashlib
import json
import os
import time

RECEIPT_DIR_REL = ".claude/receipts"
RECEIPT_VERSION = 1

# A receipt older than this is treated as stale even if session and agent match,
# so a resumed or replayed session cannot ride on yesterday's delivery.
MAX_AGE_SECONDS = 12 * 60 * 60


def _safe(component: str) -> str:
    """Session and agent ids come from the harness, but they land in a filesystem
    path, so anything unexpected is reduced to a hash rather than trusted."""
    component = str(component)
    if component and all(ch.isalnum() or ch in "-_" for ch in component):
        return component
    return "h" + hashlib.sha256(component.encode()).hexdigest()[:24]


def receipt_path(project: str, session_id: str, agent_id: str) -> str:
    return os.path.join(project, RECEIPT_DIR_REL, _safe(session_id),
                        _safe(agent_id) + ".json")


def is_subagent(payload: dict) -> bool:
    return bool(payload.get("agent_id"))


def issue(project: str, payload: dict, contract_version: str,
          contract_bytes: int) -> str:
    """Called from the SubagentStart hook once injection has been emitted."""
    path = receipt_path(project, payload.get("session_id", ""),
                        payload.get("agent_id", ""))
    os.makedirs(os.path.dirname(path), exist_ok=True)
    receipt = {
        "receipt_version": RECEIPT_VERSION,
        "session_id": payload.get("session_id"),
        "agent_id": payload.get("agent_id"),
        "agent_type": payload.get("agent_type"),
        "contract_version": contract_version,
        "contract_bytes": contract_bytes,
        "issued_at": int(time.time()),
    }
    with open(path, "w") as fh:
        json.dump(receipt, fh, indent=2)
        fh.write("\n")
    return path


def verify(project: str, payload: dict, contract_version: str):
    """Return (ok, reason). Any doubt is a refusal."""
    session_id = payload.get("session_id") or ""
    agent_id = payload.get("agent_id") or ""
    agent_type = payload.get("agent_type") or ""
    if not session_id or not agent_id:
        return False, "subagent call without a session_id or agent_id"

    path = receipt_path(project, session_id, agent_id)
    if not os.path.exists(path):
        return False, (f"no contract receipt for agent_type={agent_type or '?'} "
                       f"agent_id={agent_id}; the SubagentStart injection hook did "
                       "not run or failed")
    try:
        with open(path) as fh:
            receipt = json.load(fh)
    except Exception as exc:
        return False, f"contract receipt is unreadable or malformed: {exc}"

    if receipt.get("receipt_version") != RECEIPT_VERSION:
        return False, "contract receipt has an unsupported receipt_version"
    if receipt.get("session_id") != session_id:
        return False, "contract receipt belongs to a different session"
    if receipt.get("agent_id") != agent_id:
        return False, "contract receipt belongs to a different agent"
    if agent_type and receipt.get("agent_type") != agent_type:
        return False, ("contract receipt was issued for agent_type="
                       f"{receipt.get('agent_type')!r}, this call is "
                       f"{agent_type!r}")
    if receipt.get("contract_version") != contract_version:
        return False, (f"contract receipt is for version "
                       f"{receipt.get('contract_version')!r}, the guard expects "
                       f"{contract_version!r}")
    try:
        age = int(time.time()) - int(receipt.get("issued_at", 0))
    except Exception:
        return False, "contract receipt has an unreadable issued_at"
    if age < -60:
        return False, "contract receipt is dated in the future"
    if age > MAX_AGE_SECONDS:
        return False, f"contract receipt is stale ({age}s old)"

    return True, (f"contract {contract_version} receipted for "
                  f"{agent_type or 'subagent'} {agent_id} ({age}s old)")

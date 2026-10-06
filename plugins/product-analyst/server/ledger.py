"""Local append-only evidence with locked budget reservations and session pointers."""

import fcntl
import hashlib
import json
import os
import re
import secrets
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

STOP_REASONS = {"SUPPORTED", "REFUTED", "INCONCLUSIVE", "BUDGET_EXHAUSTED", "POLICY_BLOCKED"}
UNCERTAINTY_FIELDS = {"data_quality", "metric_definition", "magnitude", "cause"}


class BudgetExceeded(ValueError):
    """No further requests may be reserved for this source."""


def encoded(value: object) -> str:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        default=str,
        allow_nan=False,
    )


def _hash(value: object) -> str:
    return hashlib.sha256(encoded(value).encode()).hexdigest()


def _time() -> str:
    return datetime.now(tz=timezone.utc).isoformat()


def _sources(root: Path) -> dict:
    """Fingerprint project settings without reading service files or credentials."""
    result = {}
    for name in ("config.toml", "metrics.toml"):
        path = root / ".analyst" / name
        result[name] = hashlib.sha256(path.read_bytes()).hexdigest() if path.exists() else None
    return result


def _check_sources(root: Path, directory: Path) -> dict:
    sources = json.loads((directory / "sources.json").read_text())
    if _sources(root) != sources:
        raise ValueError("Project config or metrics changed; start a new investigation")
    return sources


def _directory(root: Path, investigation_id: str) -> Path:
    if not re.fullmatch(r"inv_[a-f0-9]{24}", investigation_id):
        raise ValueError("Invalid investigation ID")
    directory = root / ".analyst/investigations" / investigation_id
    if directory.is_symlink() or not directory.is_dir():
        raise ValueError("Investigation does not exist or is a symlink")
    return directory


def _atomic(path: Path, value: object) -> None:
    temporary = path.with_name(path.name + "." + secrets.token_hex(6) + ".tmp")
    try:
        with temporary.open("x", encoding="utf-8") as stream:
            stream.write(encoded(value) + "\n")
            stream.flush()
            os.fsync(stream.fileno())
        temporary.replace(path)
    finally:
        temporary.unlink(missing_ok=True)


@contextmanager
def _locked(directory: Path):
    with (directory / ".lock").open("a", encoding="utf-8") as stream:
        fcntl.flock(stream, fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(stream, fcntl.LOCK_UN)


def _events(directory: Path) -> list[dict]:
    path = directory / "evidence.jsonl"
    events = [json.loads(line) for line in path.read_text().splitlines()]
    if any(
        not isinstance(row, dict) or row.get("event") not in {"reserved", "completed"}
        for row in events
    ):
        raise ValueError("Invalid evidence ledger")
    return events


def _append(directory: Path, event: dict) -> None:
    with (directory / "evidence.jsonl").open("a", encoding="utf-8") as stream:
        stream.write(encoded(event) + "\n")
        stream.flush()
        os.fsync(stream.fileno())


def start(root: Path, contract: dict, session_id: str) -> dict:
    if not isinstance(session_id, str) or not session_id.strip():
        raise ValueError("session_id is required")
    if not isinstance(contract, dict):
        raise ValueError("contract must be an object")
    for key in ("metric", "metric_version", "population", "comparison"):
        if not contract.get(key) or not isinstance(contract[key], (str, dict, int)):
            raise ValueError(f"contract.{key} is required")
    if not isinstance(contract.get("timezone"), str) or not contract["timezone"].strip():
        raise ValueError("contract.timezone must be a timezone name")
    ZoneInfo(contract["timezone"])
    window = contract.get("window", {})
    if not isinstance(window, dict):
        raise ValueError("contract.window must be an object")
    try:
        start_time = datetime.fromisoformat(window["start"])
        end_time = datetime.fromisoformat(window["end"])
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError("Window needs ISO start and end timestamps") from exc
    if start_time.tzinfo is None or end_time.tzinfo is None or start_time >= end_time:
        raise ValueError("Window must be ordered and timezone-aware; end is exclusive")
    base = root / ".analyst"
    base.mkdir(exist_ok=True)
    if base.is_symlink():
        raise ValueError(".analyst must not be a symlink")
    with _locked(base):
        ignore = base / ".gitignore"
        existing = ignore.read_text() if ignore.exists() else ""
        if "/investigations/" not in existing.splitlines():
            ignore.write_text(
                existing
                + ("\n" if existing and not existing.endswith("\n") else "")
                + "/investigations/\n/.lock\n"
            )
        investigations = base / "investigations"
        investigations.mkdir(exist_ok=True)
        if investigations.is_symlink():
            raise ValueError("investigations must not be a symlink")
        investigation_id = "inv_" + secrets.token_hex(12)
        directory = investigations / investigation_id
        directory.mkdir(mode=0o700)
        _atomic(directory / "contract.json", contract)
        _atomic(directory / "sources.json", _sources(root))
        (directory / "evidence.jsonl").touch(mode=0o600)
        (directory / "report.md").touch(mode=0o600)
        _atomic(
            directory / "findings.json",
            {
                "claims": [],
                "stop_reason": "INCONCLUSIVE",
                "uncertainty": dict.fromkeys(sorted(UNCERTAINTY_FIELDS), "Not yet assessed"),
            },
        )
        pointer = investigations / (
            "session_" + hashlib.sha256(session_id.encode()).hexdigest() + ".json"
        )
        _atomic(pointer, {"investigation_id": investigation_id})
    return {"investigation_id": investigation_id, "contract": contract, "directory": str(directory)}


def current_investigation(root: Path, session_id: str) -> str:
    if not session_id:
        raise ValueError("session_id is required")
    pointer = (
        root
        / ".analyst/investigations"
        / ("session_" + hashlib.sha256(session_id.encode()).hexdigest() + ".json")
    )
    investigation_id = json.loads(pointer.read_text())["investigation_id"]
    _directory(root, investigation_id)
    return investigation_id


def _request_path(root: Path, request_id: str) -> Path:
    return (
        root
        / ".analyst/investigations"
        / ("request_" + hashlib.sha256(request_id.encode()).hexdigest() + ".json")
    )


def reservation_for_request(root: Path, request_id: str) -> dict:
    """Resolve a completed tool call independently of mutable session pointers."""
    binding = json.loads(_request_path(root, request_id).read_text())
    _directory(root, binding["investigation_id"])
    return binding


def reserve(
    root: Path,
    investigation_id: str,
    source: str,
    operation: dict,
    limit: int | None,
    request_id: str | None = None,
) -> str:
    directory = _directory(root, investigation_id)
    with _locked(root / ".analyst"), _locked(directory):
        sources = _check_sources(root, directory)
        events = _events(directory)
        reservations = [row for row in events if row["event"] == "reserved"]
        if request_id is not None:
            index = _request_path(root, request_id)
            if (
                index.exists()
                and reservation_for_request(root, request_id)["investigation_id"]
                != investigation_id
            ):
                raise ValueError("Request ID is already bound to another investigation")
            for row in reservations:
                if row.get("request_id") == request_id:
                    if row["source"] != source or row["operation"] != operation:
                        raise ValueError("Request ID already reserved for a different operation")
                    _atomic(
                        index,
                        {"investigation_id": investigation_id, "evidence_id": row["evidence_id"]},
                    )
                    return row["evidence_id"]
        used = sum(row["source"] == source for row in reservations)
        if limit is not None and used >= limit:
            raise BudgetExceeded(f"BUDGET_EXHAUSTED: {source} reached {limit} requests")
        evidence_id = "ev_" + secrets.token_hex(12)
        contract = json.loads((directory / "contract.json").read_text())
        _append(
            directory,
            {
                "event": "reserved",
                "evidence_id": evidence_id,
                "source": source,
                "operation": operation,
                "request_id": request_id,
                "contract_sha256": _hash(contract),
                "sources_sha256": _hash(sources),
                "at": _time(),
            },
        )
        if request_id is not None:
            _atomic(index, {"investigation_id": investigation_id, "evidence_id": evidence_id})
        return evidence_id


def find_reservation(root: Path, investigation_id: str, request_id: str) -> str:
    directory = _directory(root, investigation_id)
    with _locked(directory):
        for row in _events(directory):
            if row["event"] == "reserved" and row.get("request_id") == request_id:
                return row["evidence_id"]
    raise ValueError("No reservation for this tool call")


def complete(
    root: Path, investigation_id: str, evidence_id: str, result: object, status: str = "ok"
) -> dict:
    if status not in {"ok", "error"}:
        raise ValueError("Invalid evidence status")
    directory = _directory(root, investigation_id)
    with _locked(directory):
        events = _events(directory)
        if not any(
            row["event"] == "reserved" and row["evidence_id"] == evidence_id for row in events
        ):
            raise ValueError("Evidence was not reserved")
        result_hash = _hash(result)
        for row in events:
            if row["event"] == "completed" and row["evidence_id"] == evidence_id:
                if row["result_sha256"] != result_hash or row["status"] != status:
                    raise ValueError("Evidence already completed with a different result")
                return row
        row = {
            "event": "completed",
            "evidence_id": evidence_id,
            "status": status,
            "result_sha256": result_hash,
            "result_excerpt": encoded(result)[:2000],
            "at": _time(),
        }
        _append(directory, row)
        return row


def get_investigation(root: Path, investigation_id: str) -> dict:
    directory = _directory(root, investigation_id)
    with _locked(directory):
        return {
            "investigation_id": investigation_id,
            "contract": json.loads((directory / "contract.json").read_text()),
            "sources": json.loads((directory / "sources.json").read_text()),
            "evidence": _events(directory),
            "findings": json.loads((directory / "findings.json").read_text()),
        }


def check_claims(root: Path, investigation_id: str, findings: dict | None = None) -> dict:
    directory = _directory(root, investigation_id)
    with _locked(directory):
        if findings is None:
            findings = json.loads((directory / "findings.json").read_text())
        errors = []
        if not isinstance(findings, dict):
            return {"valid": False, "errors": ["Findings must be an object"]}
        stop_reason = findings.get("stop_reason")
        if not isinstance(stop_reason, str) or stop_reason not in STOP_REASONS:
            errors.append("Invalid stop_reason")

        def uncertainty(value):
            return (
                isinstance(value, dict)
                and set(value) == UNCERTAINTY_FIELDS
                and all(isinstance(v, str) and v.strip() for v in value.values())
            )

        if not uncertainty(findings.get("uncertainty")):
            errors.append("Global uncertainty requires four nonempty dimensions")
        claims = findings.get("claims")
        if not isinstance(claims, list):
            errors.append("claims must be a list")
            claims = []
        if not claims and stop_reason in ("SUPPORTED", "REFUTED"):
            errors.append("SUPPORTED and REFUTED require at least one claim")
        events = _events(directory)
        sources_hash = _hash(json.loads((directory / "sources.json").read_text()))
        try:
            _check_sources(root, directory)
        except ValueError as exc:
            errors.append(str(exc))
        contract_hash = _hash(json.loads((directory / "contract.json").read_text()))
        reserved = {
            row["evidence_id"]
            for row in events
            if row["event"] == "reserved"
            and row["contract_sha256"] == contract_hash
            and row["sources_sha256"] == sources_hash
        }
        usable = {
            row["evidence_id"]
            for row in events
            if row["event"] == "completed" and row["status"] == "ok"
        } & reserved
        seen = set()
        for index, claim in enumerate(claims):
            if not isinstance(claim, dict):
                errors.append(f"Claim {index} must be an object")
                continue
            claim_id = claim.get("id")
            if not isinstance(claim_id, str) or not claim_id.strip() or claim_id in seen:
                errors.append(f"Claim {index} needs a unique nonempty id")
            else:
                seen.add(claim_id)
            if not isinstance(claim.get("text"), str) or not claim["text"].strip():
                errors.append(f"Claim {index} needs text")
            citations = claim.get("evidence_ids")
            if (
                not isinstance(citations, list)
                or not citations
                or any(not isinstance(eid, str) or eid not in usable for eid in citations)
            ):
                errors.append(
                    f"Claim {index} must cite completed successful evidence for the unchanged contract"
                )
            if not uncertainty(claim.get("uncertainty")):
                errors.append(f"Claim {index} requires four nonempty uncertainty dimensions")
        if not errors:
            _atomic(directory / "findings.json", findings)
        return {
            "valid": not errors,
            "errors": errors,
            "claim_count": len(claims),
            "note": "Structural validation does not verify numerical or causal correctness.",
        }

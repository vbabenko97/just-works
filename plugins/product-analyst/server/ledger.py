"""Local append-only evidence with locked budget reservations and session pointers.

Findings pass three gates before a report: a prepared candidate whose hash the verifier
binds its verdicts to, a verification bound to the unchanged contract and sources, and
the claim check that publishes each claim with its verdict.
"""

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

import context

STOP_REASONS = {"SUPPORTED", "REFUTED", "INCONCLUSIVE", "BUDGET_EXHAUSTED", "POLICY_BLOCKED"}
UNCERTAINTY_FIELDS = {"data_quality", "metric_definition", "magnitude", "cause"}
VERDICTS = {"supported", "refuted", "unverified"}
CLAIM_KINDS = {"data", "context"}
SHA256 = re.compile(r"[a-f0-9]{64}")


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
    """Fingerprint project settings and the analysis context without reading credentials."""
    result = {}
    for name in ("config.toml", "metrics.toml"):
        path = root / ".analyst" / name
        result[name] = hashlib.sha256(path.read_bytes()).hexdigest() if path.exists() else None
    result["context"] = context.fingerprint(root)
    return result


def _check_sources(root: Path, directory: Path) -> dict:
    sources = json.loads((directory / "sources.json").read_text())
    if _sources(root) != sources:
        raise ValueError(
            "Project config, metrics or analysis context changed; start a new investigation"
        )
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
    snapshot = context.load(root)
    sources = _sources(root)
    if snapshot is not None:
        if sources["context"] != {
            "manifest_sha256": snapshot["manifest_sha256"],
            "sources": snapshot["sources"],
        }:
            raise ValueError("Analysis context changed while starting; start again")
        key = (
            context.metric_key(snapshot, contract["metric"])
            if isinstance(contract["metric"], str)
            else None
        )
        if (
            key is not None
            and str(contract["metric_version"]) != snapshot["metrics"][key]["version"]
        ):
            raise ValueError(
                f"contract.metric_version must be {snapshot['metrics'][key]['version']!r}, "
                f"the version of {key} in {context.MANIFEST}"
            )
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
        _atomic(directory / "sources.json", sources)
        _atomic(directory / "context.json", snapshot)
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
    return {
        "investigation_id": investigation_id,
        "contract": contract,
        "directory": str(directory),
        "context_manifest_sha256": snapshot["manifest_sha256"] if snapshot else None,
    }


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


def _candidates(directory: Path) -> list[dict]:
    """Prepared candidates, the most recently prepared last."""
    folder = directory / "candidates"
    if not folder.is_dir():
        return []
    rows = [json.loads(path.read_text()) for path in folder.glob("*.json")]
    return sorted(rows, key=lambda row: row["prepared_at"])


def _verifications(directory: Path) -> dict:
    """The one verification recorded for each candidate."""
    path = directory / "verifications.jsonl"
    rows = [json.loads(line) for line in path.read_text().splitlines()] if path.exists() else []
    return {row["candidate_sha256"]: row for row in rows}


def get_investigation(root: Path, investigation_id: str) -> dict:
    directory = _directory(root, investigation_id)
    with _locked(directory):
        snapshot = directory / "context.json"
        return {
            "investigation_id": investigation_id,
            "contract": json.loads((directory / "contract.json").read_text()),
            "sources": json.loads((directory / "sources.json").read_text()),
            "context": json.loads(snapshot.read_text()) if snapshot.exists() else None,
            "evidence": _events(directory),
            "candidates": _candidates(directory),
            "verifications": list(_verifications(directory).values()),
            "findings": json.loads((directory / "findings.json").read_text()),
        }


def _bindings(directory: Path) -> tuple[str, str, set]:
    """Contract and sources hashes, and the evidence IDs usable under both."""
    contract_hash = _hash(json.loads((directory / "contract.json").read_text()))
    sources_hash = _hash(json.loads((directory / "sources.json").read_text()))
    events = _events(directory)
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
    return contract_hash, sources_hash, usable


def _uncertainty(value: object) -> bool:
    return (
        isinstance(value, dict)
        and set(value) == UNCERTAINTY_FIELDS
        and all(isinstance(v, str) and v.strip() for v in value.values())
    )


def _findings_errors(root: Path, directory: Path, findings: object, usable: set) -> list[str]:
    if not isinstance(findings, dict):
        return ["Findings must be an object"]
    errors = []
    stop_reason = findings.get("stop_reason")
    if not isinstance(stop_reason, str) or stop_reason not in STOP_REASONS:
        errors.append("Invalid stop_reason")
    if not _uncertainty(findings.get("uncertainty")):
        errors.append("Global uncertainty requires four nonempty dimensions")
    claims = findings.get("claims")
    if not isinstance(claims, list):
        errors.append("claims must be a list")
        claims = []
    if not claims and stop_reason in ("SUPPORTED", "REFUTED"):
        errors.append("SUPPORTED and REFUTED require at least one claim")
    try:
        _check_sources(root, directory)
    except ValueError as exc:
        errors.append(str(exc))
    snapshot_path = directory / "context.json"
    snapshot = json.loads(snapshot_path.read_text()) if snapshot_path.exists() else None
    statements = snapshot["statements"] if snapshot else {}
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
        kind = claim.get("kind", "data")
        if not isinstance(kind, str) or kind not in CLAIM_KINDS:
            errors.append(f"Claim {index} kind must be data or context")
        citations = claim.get("evidence_ids", [] if kind == "context" else None)
        if kind == "context" and citations:
            errors.append(f"Claim {index} is a context claim and cites no evidence; use kind data")
        elif (
            not isinstance(citations, list)
            or (kind != "context" and not citations)
            or any(not isinstance(eid, str) or eid not in usable for eid in citations)
        ):
            errors.append(
                f"Claim {index} must cite completed successful evidence for the unchanged contract"
            )
        refs = claim.get("context_refs", [])
        if (
            not isinstance(refs, list)
            or (kind == "context" and not refs)
            or any(not isinstance(ref, str) or ref not in statements for ref in refs)
        ):
            errors.append(
                f"Claim {index} context_refs must name statements in the investigation's "
                "analysis context"
                + ("" if snapshot else f"; this investigation has no {context.MANIFEST}")
            )
        elif kind == "context":
            fixed = " ".join(statements[ref]["text"] for ref in refs)
            if claim.get("text") != fixed:
                errors.append(
                    f"Claim {index} is a context claim: its text must be the fixed text of its "
                    f"context_refs, in order, exactly: {fixed!r}"
                )
        if not _uncertainty(claim.get("uncertainty")):
            errors.append(f"Claim {index} requires four nonempty uncertainty dimensions")
    return errors


def prepare_findings(root: Path, investigation_id: str, findings: dict) -> dict:
    """Validate and store candidate findings; the verifier binds its verdicts to their hash."""
    directory = _directory(root, investigation_id)
    with _locked(directory):
        contract_hash, sources_hash, usable = _bindings(directory)
        errors = _findings_errors(root, directory, findings, usable)
        if errors:
            return {"valid": False, "errors": errors}
        candidate_hash = _hash(findings)
        folder = directory / "candidates"
        folder.mkdir(mode=0o700, exist_ok=True)
        path = folder / f"{candidate_hash}.json"
        prepared_at = _time()
        first = json.loads(path.read_text())["first_prepared_at"] if path.exists() else prepared_at
        _atomic(
            path,
            {
                "candidate_sha256": candidate_hash,
                "findings": findings,
                "contract_sha256": contract_hash,
                "sources_sha256": sources_hash,
                "first_prepared_at": first,
                "prepared_at": prepared_at,
            },
        )
        return {
            "valid": True,
            "errors": [],
            "candidate_sha256": candidate_hash,
            "claim_count": len(findings["claims"]),
            "next": "Ask product-analyst:analysis-verifier to verify this candidate"
            if findings["claims"]
            else "No claims to verify; pass candidate_sha256 to check_claims",
        }


def _candidate(directory: Path, candidate_hash: object) -> dict | None:
    if not isinstance(candidate_hash, str) or not SHA256.fullmatch(candidate_hash):
        return None
    path = directory / "candidates" / f"{candidate_hash}.json"
    return json.loads(path.read_text()) if path.is_file() else None


def _independent(directory: Path, candidate: dict, usable: set) -> set:
    """Evidence a verifier may cite to support a data claim: recorded after the investigation's
    first candidate was prepared, and cited by no claim of this candidate."""
    first = min(row["first_prepared_at"] for row in _candidates(directory))
    later = {
        row["evidence_id"]
        for row in _events(directory)
        if row["event"] == "reserved"
        and datetime.fromisoformat(row["at"]) >= datetime.fromisoformat(first)
    }
    cited = {
        eid for claim in candidate["findings"]["claims"] for eid in claim.get("evidence_ids", [])
    }
    return (usable & later) - cited


def _verification_errors(
    candidate: dict,
    verification: object,
    usable: set,
    independent: set,
    current: tuple[str, str],
) -> list[str]:
    if (candidate["contract_sha256"], candidate["sources_sha256"]) != current:
        return ["Candidate was prepared under another contract or sources; prepare it again"]
    if not isinstance(verification, dict) or not isinstance(verification.get("claims"), list):
        return ["Verification must be an object with a claims list"]
    claims = {claim["id"]: claim for claim in candidate["findings"]["claims"]}
    errors, seen = [], set()
    for index, verdict in enumerate(verification["claims"]):
        if not isinstance(verdict, dict):
            errors.append(f"Verdict {index} must be an object")
            continue
        claim_id = verdict.get("claim_id")
        if not isinstance(claim_id, str) or claim_id not in claims:
            errors.append(f"Verdict {index} names no claim in this candidate")
            continue
        if claim_id in seen:
            errors.append(f"Claim {claim_id} has more than one verdict")
        seen.add(claim_id)
        value = verdict.get("verdict")
        if not isinstance(value, str) or value not in VERDICTS:
            errors.append(f"Claim {claim_id} verdict must be supported, refuted or unverified")
        for field in ("method", "limitations"):
            if not isinstance(verdict.get(field), str):
                errors.append(f"Claim {claim_id} verdict needs a {field} string")
        evidence = verdict.get("evidence_ids", [])
        if not isinstance(evidence, list) or any(
            not isinstance(eid, str) or eid not in usable for eid in evidence
        ):
            errors.append(
                f"Claim {claim_id} verdict must cite completed successful evidence "
                "of this investigation"
            )
            continue
        if (
            value == "supported"
            and claims[claim_id].get("kind", "data") != "context"
            and not set(evidence) & independent
        ):
            errors.append(
                f"Claim {claim_id} is supported only with an independent re-derivation: cite "
                "evidence recorded after the first candidate was prepared that no claim cites"
            )
    missing = sorted(set(claims) - seen)
    if missing:
        errors.append("Missing verdicts for claims: " + ", ".join(missing))
    return errors


def _append_line(path: Path, row: dict) -> None:
    with path.open("a", encoding="utf-8") as stream:
        stream.write(encoded(row) + "\n")
        stream.flush()
        os.fsync(stream.fileno())


def submit_verification(
    root: Path, investigation_id: str, candidate_sha256: str, verification: dict
) -> dict:
    """Record the verifier's verdict for every claim of one candidate, once."""
    directory = _directory(root, investigation_id)
    with _locked(directory):
        candidate = _candidate(directory, candidate_sha256)
        if candidate is None:
            return {"valid": False, "errors": ["Unknown candidate; call prepare_findings first"]}
        if candidate_sha256 in _verifications(directory):
            return {
                "valid": False,
                "errors": ["This candidate is already verified; verify a revised candidate"],
            }
        contract_hash, sources_hash, usable = _bindings(directory)
        errors = []
        try:
            _check_sources(root, directory)
        except ValueError as exc:
            errors.append(str(exc))
        errors += _verification_errors(
            candidate,
            verification,
            usable,
            _independent(directory, candidate, usable),
            (contract_hash, sources_hash),
        )
        if errors:
            return {"valid": False, "errors": errors}
        _append_line(
            directory / "verifications.jsonl",
            {
                "candidate_sha256": candidate_sha256,
                "contract_sha256": contract_hash,
                "sources_sha256": sources_hash,
                "verification": verification,
                "submitted_at": _time(),
            },
        )
        verdicts = {row["claim_id"]: row["verdict"] for row in verification["claims"]}
        return {"valid": True, "errors": [], "verdicts": verdicts}


def check_claims(
    root: Path,
    investigation_id: str,
    findings: dict | None = None,
    candidate_sha256: str | None = None,
) -> dict:
    """Publish a verified candidate as the investigation's findings, each claim with its verdict.

    The candidate is named by its hash, or by findings equal to a prepared candidate; with
    neither, the most recently prepared candidate is used.
    """
    directory = _directory(root, investigation_id)
    with _locked(directory):
        contract_hash, sources_hash, usable = _bindings(directory)
        if findings is not None:
            named = _hash(findings)
            if candidate_sha256 is not None and candidate_sha256 != named:
                return {
                    "valid": False,
                    "errors": ["findings and candidate_sha256 name different candidates"],
                }
            candidate_sha256 = named
        if candidate_sha256 is None:
            candidates = _candidates(directory)
            candidate = candidates[-1] if candidates else None
        else:
            candidate = _candidate(directory, candidate_sha256)
        if candidate is None:
            return {"valid": False, "errors": ["Unknown candidate; call prepare_findings first"]}
        findings, candidate_hash = candidate["findings"], candidate["candidate_sha256"]
        errors = _findings_errors(root, directory, findings, usable)
        if errors:
            return {"valid": False, "errors": errors}
        claims = findings["claims"]
        verdicts = {}
        if claims:
            verification = _verifications(directory).get(candidate_hash)
            if verification is None:
                return {
                    "valid": False,
                    "errors": ["No verification for this candidate; run the analysis verifier"],
                }
            if (verification["contract_sha256"], verification["sources_sha256"]) != (
                contract_hash,
                sources_hash,
            ):
                return {
                    "valid": False,
                    "errors": ["Verification is stale: contract or sources changed since"],
                }
            errors = _verification_errors(
                candidate,
                verification["verification"],
                usable,
                _independent(directory, candidate, usable),
                (contract_hash, sources_hash),
            )
            if errors:
                return {"valid": False, "errors": errors}
            verdicts = {row["claim_id"]: row for row in verification["verification"]["claims"]}
        kinds = {claim["id"]: claim.get("kind", "data") for claim in claims}
        if findings["stop_reason"] in ("SUPPORTED", "REFUTED") and (
            not any(
                row["verdict"] == "supported" and kinds[claim_id] == "data"
                for claim_id, row in verdicts.items()
            )
            or any(row["verdict"] == "refuted" for row in verdicts.values())
        ):
            return {
                "valid": False,
                "errors": [
                    "SUPPORTED and REFUTED need a data claim the verifier supported and no "
                    "refuted claim; revise the claims, or prepare INCONCLUSIVE or "
                    "BUDGET_EXHAUSTED findings and have them verified"
                ],
            }
        published = {
            **findings,
            "claims": [{**claim, "verdict": verdicts[claim["id"]]} for claim in claims],
            "candidate_sha256": candidate_hash,
            "published_at": _time(),
        }
        _atomic(directory / "findings.json", published)
        return {
            "valid": True,
            "errors": [],
            "claim_count": len(claims),
            "verdicts": {claim_id: row["verdict"] for claim_id, row in verdicts.items()},
            "note": "Only claims with verdict supported are confirmed. Report refuted and "
            "unverified claims as such, then call check_report.",
        }


NUMBER = re.compile(r"(?<![\w.])\d+(?:[.,]\d+)?")
GROUPED = re.compile(r"(?<![\w.,])\d{1,3}(?:[,  ]\d{3})+(?:\.\d+)?(?![\w,]*\d)")
FENCE = re.compile(r"^(`{3,}|~{3,}).*?^\1[^\n]*$", re.MULTILINE | re.DOTALL)
MONTHS = (
    "January|February|March|April|May|June|July|August|September|October|November|December|"
    "январ[ья]|феврал[ья]|марта?|апрел[ья]|ма[йя]|июн[ья]|июл[ья]|августа?|сентябр[ья]|"
    "октябр[ья]|ноябр[ья]|декабр[ья]"
)
IGNORED = (
    re.compile(r"https?://\S+|\]\([^)]*\)"),
    re.compile(r"\b(?:ev|inv)_[a-f0-9]+\b"),
    re.compile(r"\b[a-f0-9]{16,}\b"),
    re.compile(
        r"\d{4}-\d{2}-\d{2}(?:[T ]\d{2}:\d{2}(?::\d{2})?(?:\.\d+)?)?(?:Z|[+-]\d{2}:?\d{2})?"
    ),
    re.compile(r"\b\d{1,2}\.\d{1,2}\.\d{4}\b"),
    re.compile(
        rf"(?:\b\d{{1,2}}(?:st|nd|rd|th)?\s+)?\b(?:{MONTHS})\b"
        r"(?:\s+\d{1,2}(?:st|nd|rd|th)?\b)?(?:,?\s+\d{4}\b)?",
        re.IGNORECASE,
    ),
    re.compile(r"\bQ[1-4]\s+\d{4}\b"),
    re.compile(r"\b\d{1,2}:\d{2}(?::\d{2})?\b"),
    re.compile(r"\b(?:UTC|GMT)\s*[+-]\s*\d{1,2}(?::\d{2})?"),
    re.compile(r"\b\d+(?:st|nd|rd|th)\b"),
    re.compile(r"\[\^?\d+\]"),
    re.compile(r"^\s*(?:#+\s*)?\d+[.)]\s", re.MULTILINE),
)


def _numbers(text: str) -> set[float]:
    """Numbers stated in prose; dates, times, IDs, URLs, ordinals and list numbering excluded.

    A comma, no-break space or thin space between groups of three digits is a thousands
    separator; any other comma between digits is a decimal comma.
    """
    for pattern in IGNORED:
        text = pattern.sub(" ", text)
    text = GROUPED.sub(lambda match: re.sub(r"[,  ]", "", match.group()), text)
    return {float(token.replace(",", ".")) for token in NUMBER.findall(text)}


def _strings(value: object) -> list[str]:
    if isinstance(value, dict):
        return [text for item in value.values() for text in _strings(item)]
    if isinstance(value, list):
        return [text for item in value for text in _strings(item)]
    return [value] if isinstance(value, str) else [str(value)]


def check_report(root: Path, investigation_id: str) -> dict:
    """Flag numbers in report.md that appear in no published claim, uncertainty or contract.

    A lexical check: see _numbers for what is ignored; fenced code blocks are ignored too.
    """
    directory = _directory(root, investigation_id)
    with _locked(directory):
        findings = json.loads((directory / "findings.json").read_text())
        if "candidate_sha256" not in findings:
            return {"valid": False, "errors": ["Findings are not published; run check_claims"]}
        report = (directory / "report.md").read_text()
        if not report.strip():
            return {"valid": False, "errors": ["report.md is empty"]}
        sources = [
            json.loads((directory / "contract.json").read_text()),
            findings["uncertainty"],
            [
                claim["text"]
                if claim.get("kind", "data") == "context"
                else [claim["text"], claim["uncertainty"]]
                for claim in findings["claims"]
            ],
        ]
        allowed = {number for text in _strings(sources) for number in _numbers(text)}
        report = FENCE.sub(lambda match: "\n" * match.group().count("\n"), report)
        unsupported = []
        for number, line in enumerate(report.splitlines(), start=1):
            extra = sorted(_numbers(line) - allowed)
            if extra:
                unsupported.append({"line": number, "numbers": extra, "text": line.strip()[:200]})
        return {
            "valid": not unsupported,
            "errors": [] if not unsupported else ["report.md states numbers outside the findings"],
            "unsupported": unsupported,
            "note": "Lexical check of numbers only; it does not judge wording or completeness.",
        }

"""Local append-only evidence with locked budget reservations and session pointers.

Findings pass three gates before a report: a prepared candidate whose hash the verifier
binds its verdicts to, a verification bound to the unchanged contract and sources, and
the claim check that publishes each claim with its verdict. The report passes three more:
a prepared version the gateway assembles from the author's narrative and the published
findings, a report verification bound to that exact version, and the final check that
alone writes report.md.
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
import report

# When an investigation stops with each reason, as the investigate skill, its methods reference and
# the claim gate state it. The report verifier receives the rule of the recorded reason and checks
# a stated stop reason, and the explanation given for it, against that rule and the claims.
STOP_RULES = {
    "SUPPORTED": "A data claim that the claim verifier supported states the conclusion, and no "
    "claim is refuted.",
    "REFUTED": "A data claim that the claim verifier supported states that the evidence "
    "contradicts the hypothesis, and no claim is refuted.",
    "INCONCLUSIVE": "An answer that a value is unavailable ends INCONCLUSIVE, and so does "
    "evidence that does not distinguish competing explanations, or verdicts that no longer "
    "carry SUPPORTED or REFUTED.",
    "BUDGET_EXHAUSTED": "A source reached its request limit, or the budget does not allow "
    "another query pass and the verdicts no longer carry SUPPORTED or REFUTED.",
    "POLICY_BLOCKED": "A request was refused on policy, and the investigation does not continue "
    "after a policy refusal.",
}
STOP_REASONS = set(STOP_RULES)
UNCERTAINTY_FIELDS = {"data_quality", "metric_definition", "magnitude", "cause"}
VERDICTS = {"supported", "refuted", "unverified"}
CLAIM_KINDS = {"data", "context"}
SHA256 = re.compile(r"[a-f0-9]{64}")
REPORT_SCHEMA_VERSION = "1"
REPORT_VERIFICATIONS_LIMIT = 2
BLOCK_KINDS = {"analytical", "non_analytical"}
REPORT_VERIFIER = Path(__file__).resolve().parents[1] / "agents" / "report-verifier.md"
QUOTE_MIN = 12
BASIS = re.compile(r"(claim|contract|uncertainty):(.+)")
# Claude Code saves a tool result longer than 50,000 characters to a file and shows the model a
# preview; the report verifier has no tool to read that file, so its input stays below this.
REPORT_INPUT_LIMIT = 40_000


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
    _atomic_text(path, encoded(value) + "\n")


def _atomic_text(path: Path, text: str) -> None:
    temporary = path.with_name(path.name + "." + secrets.token_hex(6) + ".tmp")
    try:
        with temporary.open("x", encoding="utf-8") as stream:
            stream.write(text)
            stream.flush()
            os.fsync(stream.fileno())
        os.chmod(temporary, 0o600)
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


def _jsonl(path: Path) -> list:
    """The rows of a JSONL ledger file. A row ends only at "\\n": encoded() keeps U+2028, U+2029
    and U+0085 unescaped inside a row, and str.splitlines() would break the row there."""
    text = path.read_text()
    return [json.loads(line) for line in text.removesuffix("\n").split("\n")] if text else []


def _events(directory: Path) -> list[dict]:
    path = directory / "evidence.jsonl"
    events = _jsonl(path)
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
    rows = _jsonl(path) if path.exists() else []
    return {row["candidate_sha256"]: row for row in rows}


def get_investigation(root: Path, investigation_id: str) -> dict:
    directory = _directory(root, investigation_id)
    with _locked(directory):
        snapshot = directory / "context.json"
        reports = _report_records(directory)
        try:
            current = _report_bindings(root, directory, investigation_id)
        except ValueError as exc:
            current = str(exc)
        for record in reports:
            record["integrity_errors"] = (
                [current] if isinstance(current, str) else _report_integrity(record, *current)
            )
        return {
            "investigation_id": investigation_id,
            "contract": json.loads((directory / "contract.json").read_text()),
            "sources": json.loads((directory / "sources.json").read_text()),
            "context": json.loads(snapshot.read_text()) if snapshot.exists() else None,
            "evidence": _events(directory),
            "candidates": _candidates(directory),
            "verifications": list(_verifications(directory).values()),
            "findings": json.loads((directory / "findings.json").read_text()),
            "reports": reports,
            "report_verifications": _report_verifications(directory),
            "report_acceptances": _report_acceptances(directory),
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
        previous = json.loads((directory / "findings.json").read_text())
        if _report_acceptances(directory) and previous.get("candidate_sha256") != candidate_hash:
            return {
                "valid": False,
                "errors": [
                    "A report was already accepted for the published findings; start a new "
                    "investigation to publish other findings"
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
            "note": "Only claims with verdict supported are confirmed. Write the narrative, "
            "stating refuted and unverified claims as such, then call prepare_report.",
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


def _numbers(text: str, lists: bool = True) -> set[float]:
    """Numbers stated in prose; dates, times, IDs, URLs, ordinals and list numbering excluded.

    A comma, no-break space or thin space between groups of three digits is a thousands
    separator; any other comma between digits is a decimal comma. With lists false, a number
    at the start of a line counts even when it looks like list numbering, as in a title.
    """
    for pattern in IGNORED if lists else IGNORED[:-1]:
        text = pattern.sub(" ", text)
    text = GROUPED.sub(lambda match: re.sub(r"[,  ]", "", match.group()), text)
    return {float(token.replace(",", ".")) for token in NUMBER.findall(text)}


def _strings(value: object) -> list[str]:
    if isinstance(value, dict):
        return [text for item in value.values() for text in _strings(item)]
    if isinstance(value, list):
        return [text for item in value for text in _strings(item)]
    return [value] if isinstance(value, str) else [str(value)]


def _allowed_numbers(contract: dict, findings: dict) -> set[float]:
    """Numbers a narrative may state: the contract, the global uncertainty, data claims with
    their uncertainty, and the fixed text of context claims, whose uncertainty adds none."""
    sources = [
        contract,
        findings["uncertainty"],
        [
            claim["text"]
            if claim.get("kind", "data") == "context"
            else [claim["text"], claim["uncertainty"]]
            for claim in findings["claims"]
        ],
    ]
    return {number for text in _strings(sources) for number in _numbers(text)}


def _unsupported_numbers(text: str, allowed: set[float]) -> list[dict]:
    """A lexical check of the authored lines by line; fenced code blocks are ignored. Lines end
    only at "\n", as in Markdown, so U+2028 cannot make a number look like list numbering.

    Line 1 is the title, a heading, so a number that opens it is not list numbering.
    """
    text = FENCE.sub(lambda match: "\n" * match.group().count("\n"), text)
    unsupported = []
    for number, line in enumerate(text.split("\n"), start=1):
        found = _numbers(line.removeprefix("# "), lists=False) if number == 1 else _numbers(line)
        extra = sorted(found - allowed)
        if extra:
            unsupported.append({"line": number, "numbers": extra, "text": line.strip()[:200]})
    return unsupported


def _report_bindings(root: Path, directory: Path, investigation_id: str) -> tuple:
    """What a report version is bound to now, with the contract and published findings."""
    findings = json.loads((directory / "findings.json").read_text())
    if "candidate_sha256" not in findings:
        raise ValueError("Findings are not published; run check_claims")
    sources = _check_sources(root, directory)
    contract = json.loads((directory / "contract.json").read_text())
    bindings = {
        "investigation_id": investigation_id,
        "candidate_sha256": findings["candidate_sha256"],
        "findings_sha256": _hash({k: v for k, v in findings.items() if k != "published_at"}),
        "contract_sha256": _hash(contract),
        "sources_sha256": _hash(sources),
        "renderer_version": report.RENDERER_VERSION,
        "schema_version": REPORT_SCHEMA_VERSION,
        "verifier_sha256": _verifier_fingerprint(),
        # The rule of the recorded stop reason is part of the verifier's basis, so a verdict holds
        # only under the rule it was given, as under the instructions.
        "stop_rule_sha256": _hash(STOP_RULES[findings["stop_reason"]]),
    }
    return bindings, contract, findings


def _verifier_fingerprint() -> str:
    """The report verifier's instructions: a verdict holds only under the rules it was given."""
    try:
        return hashlib.sha256(REPORT_VERIFIER.read_bytes()).hexdigest()
    except OSError as exc:
        raise ValueError(f"The report verifier's instructions cannot be read: {exc}") from None


def _version_key(bindings: dict, report_sha256: object) -> str:
    return _hash({**bindings, "report_sha256": report_sha256})


def _load_record(path: Path) -> dict:
    """A stored report version; an unreadable one becomes a record that fails integrity."""
    try:
        record = json.loads(path.read_text())
    except ValueError:
        record = None
    if not isinstance(record, dict) or record.get("version_sha256") != path.stem:
        return {"version_sha256": path.stem, "prepared_at": "", "unreadable": True}
    return record


def _report_records(directory: Path) -> list[dict]:
    """Prepared report versions, the most recently prepared last."""
    folder = directory / "reports"
    if not folder.is_dir():
        return []
    rows = [_load_record(path) for path in folder.glob("*.json")]
    return sorted(rows, key=lambda row: str(row.get("prepared_at", "")))


def _report_record(directory: Path, version_sha256: object) -> dict | None:
    if not isinstance(version_sha256, str) or not SHA256.fullmatch(version_sha256):
        return None
    path = directory / "reports" / f"{version_sha256}.json"
    return _load_record(path) if path.is_file() else None


def _report_verifications(directory: Path) -> list[dict]:
    path = directory / "report_verifications.jsonl"
    return _jsonl(path) if path.exists() else []


def _report_acceptances(directory: Path) -> list[dict]:
    path = directory / "report_acceptances.jsonl"
    return _jsonl(path) if path.exists() else []


def _report_integrity(record: dict, current: dict, contract: dict, findings: dict) -> list[str]:
    """Whether a prepared version is unchanged, current, and what the gateway assembles now."""
    if _version_key({key: record.get(key) for key in current}, record.get("report_sha256")) != (
        record.get("version_sha256")
    ):
        return ["The prepared report record was changed after preparation; prepare it again"]
    stale = sorted(key for key in current if record.get(key) != current[key])
    if stale:
        return [
            "The prepared report is stale: "
            + ", ".join(stale)
            + " changed since it was prepared; prepare it again"
        ]
    text = record.get("report")
    if (
        not isinstance(text, str)
        or hashlib.sha256(text.encode()).hexdigest() != (record["report_sha256"])
    ):
        return ["The prepared report text was changed after preparation; prepare it again"]
    narrative = record.get("narrative")
    if (
        report.narrative_errors(narrative)
        or report.normalised(narrative) != narrative
        or report.render(narrative, contract, findings) != (text, record.get("blocks"))
    ):
        return [
            "The prepared report is not what the gateway assembles from its narrative and the "
            "published findings; prepare it again"
        ]
    if _unsupported_numbers(
        "\n".join(report.authored(narrative)[0]), _allowed_numbers(contract, findings)
    ):
        return ["The prepared narrative states numbers outside the published findings"]
    return []


def prepare_report(root: Path, investigation_id: str, narrative: dict) -> dict:
    """Assemble report.md's text from the narrative and the published findings, and store it as
    a version for the report verifier; report.md itself is written only by check_report."""
    directory = _directory(root, investigation_id)
    with _locked(directory):
        try:
            current, contract, findings = _report_bindings(root, directory, investigation_id)
        except ValueError as exc:
            return {"valid": False, "errors": [str(exc)]}
        errors = report.narrative_errors(narrative)
        if errors:
            return {"valid": False, "errors": errors}
        narrative = report.normalised(narrative)
        text, blocks = report.render(narrative, contract, findings)
        authored = "\n".join(report.authored(narrative)[0])
        unsupported = _unsupported_numbers(authored, _allowed_numbers(contract, findings))
        if unsupported:
            return {
                "valid": False,
                "errors": ["The narrative states numbers outside the published findings"],
                "unsupported": unsupported,
            }
        report_hash = hashlib.sha256(text.encode()).hexdigest()
        key = _version_key(current, report_hash)
        record = {
            "version_sha256": key,
            **current,
            "report_sha256": report_hash,
            "narrative": narrative,
            "report": text,
            "blocks": blocks,
        }
        size = _input_size(_verifier_input(investigation_id, record, current, contract, findings))
        if size > REPORT_INPUT_LIMIT:
            return {"valid": False, "errors": [_too_large(size)]}
        folder = directory / "reports"
        folder.mkdir(mode=0o700, exist_ok=True)
        _atomic(folder / f"{key}.json", {**record, "prepared_at": _time()})
        return {
            "valid": True,
            "errors": [],
            "version_sha256": key,
            "report_sha256": report_hash,
            "blocks": [
                {name: block[name] for name in ("block_id", "start_line", "end_line")}
                for block in blocks
            ],
            "next": "Ask product-analyst:report-verifier to verify this version",
        }


def _verifier_input(
    investigation_id: str, record: dict, current: dict, contract: dict, findings: dict
) -> str:
    """The report verifier's input for a version that passed integrity: its binding hashes, the
    narrative and every authored block, and the basis they are checked against."""
    return encoded(
        {
            "investigation_id": investigation_id,
            "version_sha256": record["version_sha256"],
            "errors": [],
            "version": {key: record[key] for key in (*current, "report_sha256")},
            "narrative": record["narrative"],
            "blocks": record["blocks"],
            "basis": {
                "contract": contract,
                "claims": findings["claims"],
                "uncertainty": findings["uncertainty"],
                "stop_reason": findings["stop_reason"],
                "stop_rule": STOP_RULES[findings["stop_reason"]],
            },
        }
    )


def _input_size(text: str) -> int:
    """Length as Claude Code measures it, in UTF-16 code units: a character outside the BMP
    counts twice."""
    return len(text.encode("utf-16-le")) // 2


def _too_large(size: int) -> str:
    return (
        f"snapshot_too_large: the report verifier's input is {size} UTF-16 code units, over the "
        f"limit of {REPORT_INPUT_LIMIT}, and is never cut. Shorten the narrative, which the input "
        "carries twice, as text and as blocks, or publish smaller findings, then prepare the "
        "report again"
    )


def _supported(verification: dict) -> bool:
    """Whether a recorded report verification supports every authored block and the caveats."""
    return verification["caveats"]["verdict"] == "supported" and all(
        entry["verdict"] == "supported" for entry in verification["blocks"]
    )


def _verification_refusal(
    directory: Path, version_sha256: str, current: dict, contract: dict, findings: dict
) -> list[str]:
    """Why a version can take no further report verification, and what to do instead; empty when
    it can be verified. Only a version that is intact, current and supported in every block and
    the caveats is named for check_report, the same test check_report applies."""
    rows = _report_verifications(directory)
    publishable = []
    for row in rows:
        record = _report_record(directory, row["version_sha256"])
        if (
            _supported(row["verification"])
            and record is not None
            and not _report_integrity(record, current, contract, findings)
        ):
            publishable.append(row["version_sha256"])
    if len(rows) >= REPORT_VERIFICATIONS_LIMIT:
        if publishable:
            chosen = version_sha256 if version_sha256 in publishable else publishable[-1]
            return [
                f"This investigation has used its {REPORT_VERIFICATIONS_LIMIT} report "
                f"verifications; version {chosen} is current and supported in every block and "
                "the caveats, so call check_report with it"
            ]
        return [
            f"This investigation has used its {REPORT_VERIFICATIONS_LIMIT} report verifications "
            "and no current version is supported in every block and the caveats; its report "
            "stays a draft"
        ]
    if version_sha256 in publishable:
        return [
            "This version is already verified and supported in every block and the caveats; "
            "call check_report with it"
        ]
    if any(row["version_sha256"] == version_sha256 for row in rows):
        return [
            "This version is already verified and not supported in every block; revise the "
            "narrative and prepare it again"
        ]
    return []


def report_verification_input(root: Path, investigation_id: str, version_sha256: str) -> str:
    """The report verifier's whole input for one prepared version, as the exact text it reads.

    It holds the version's binding hashes, the narrative and every authored block, and the basis
    they are checked against: the full contract, every published claim unchanged, the global
    uncertainty, the stop reason and the rule of that reason. Evidence, sources, candidates, other versions and earlier
    verdicts are left out. A version that fails integrity or can take no further verification,
    or an input over REPORT_INPUT_LIMIT UTF-16 code units, returns only its errors: nothing is
    cut. prepare_report refuses a narrative whose input would be over the limit."""
    directory = _directory(root, investigation_id)
    head = {"investigation_id": investigation_id, "version_sha256": version_sha256}
    with _locked(directory):
        record = _report_record(directory, version_sha256)
        if record is None:
            return encoded({**head, "errors": ["Unknown report version; call prepare_report"]})
        try:
            current, contract, findings = _report_bindings(root, directory, investigation_id)
        except ValueError as exc:
            return encoded({**head, "errors": [str(exc)]})
        errors = _report_integrity(record, current, contract, findings)
        errors = errors or _verification_refusal(
            directory, version_sha256, current, contract, findings
        )
        if errors:
            return encoded({**head, "errors": errors})
        text = _verifier_input(investigation_id, record, current, contract, findings)
        size = _input_size(text)
        if size > REPORT_INPUT_LIMIT:
            return encoded({**head, "errors": [_too_large(size)]})
        return text


def _basis_names(value: object, claims: set, contract: dict) -> bool:
    if value == "stop_reason":
        return True
    match = BASIS.fullmatch(value) if isinstance(value, str) else None
    if match is None:
        return False
    kind, name = match.groups()
    return name in {"claim": claims, "contract": contract, "uncertainty": UNCERTAINTY_FIELDS}[kind]


def _report_verification_errors(
    record: dict, verification: object, contract: dict, findings: dict
) -> list[str]:
    if not isinstance(verification, dict) or not isinstance(verification.get("blocks"), list):
        return ["Verification must be an object with a blocks list and a caveats object"]
    blocks = {block["block_id"]: block for block in record["blocks"]}
    claims = {claim["id"] for claim in findings["claims"]}
    errors, seen = [], set()
    for index, entry in enumerate(verification["blocks"]):
        block_id = entry.get("block_id") if isinstance(entry, dict) else None
        if not isinstance(block_id, str) or block_id not in blocks:
            errors.append(f"Block entry {index} names no authored block of this report")
            continue
        if block_id in seen:
            errors.append(f"Block {block_id} has more than one entry")
            continue
        seen.add(block_id)
        quote, text = entry.get("quote"), blocks[block_id]["text"]
        if (
            not isinstance(quote, str)
            or len(quote.strip()) < min(QUOTE_MIN, len(text.strip()))
            or quote not in text
        ):
            errors.append(
                f"Block {block_id} quote must be text copied exactly from the block, at least "
                f"{QUOTE_MIN} characters or the whole block"
            )
        value = entry.get("verdict")
        if not isinstance(value, str) or value not in VERDICTS:
            errors.append(f"Block {block_id} verdict must be supported, refuted or unverified")
        kind = entry.get("kind")
        if not isinstance(kind, str) or kind not in BLOCK_KINDS:
            errors.append(f"Block {block_id} kind must be analytical or non_analytical")
        elif block_id == "title" and kind != "analytical":
            errors.append("Block title is the headline result and must be judged analytical")
        elif kind == "analytical":
            statements = entry.get("statements")
            if (
                not isinstance(statements, list)
                or not statements
                or any(not isinstance(text, str) or not text.strip() for text in statements)
            ):
                errors.append(f"Block {block_id} needs the statements it makes")
            basis = entry.get("basis")
            if not isinstance(basis, list) or not basis:
                errors.append(
                    f"Block {block_id} needs a basis: claim:<id>, contract:<field>, "
                    "uncertainty:<field> or stop_reason"
                )
            else:
                errors += [
                    f"Block {block_id} basis {ref!r} names no claim, contract field, "
                    "uncertainty field or the stop reason"
                    for ref in basis
                    if not _basis_names(ref, claims, contract)
                ]
            comparison = entry.get("comparison")
            if not isinstance(comparison, str) or not comparison.strip():
                errors.append(f"Block {block_id} needs a comparison of its meaning with the basis")
        else:
            explanation = entry.get("explanation")
            if not isinstance(explanation, str) or not explanation.strip():
                errors.append(f"Block {block_id} is non_analytical and needs an explanation")
            # A non_analytical block states nothing about the data, so there is nothing in it to
            # refute or to leave unverified; a block with such a statement is judged analytical.
            if value in VERDICTS and value != "supported":
                errors.append(
                    f"Block {block_id} is non_analytical, so it states nothing the basis could "
                    "contradict and is supported; judge a block that says something about the "
                    "data, a metric, a source or how a value was obtained as analytical"
                )
    missing = [block_id for block_id in blocks if block_id not in seen]
    if missing:
        errors.append("Missing entries for authored blocks: " + ", ".join(missing))
    caveats = verification.get("caveats")
    if (
        not isinstance(caveats, dict)
        or not isinstance(caveats.get("verdict"), str)
        or caveats["verdict"] not in VERDICTS
        or not isinstance(caveats.get("explanation"), str)
        or not caveats["explanation"].strip()
    ):
        errors.append(
            "caveats needs a verdict on whether the answer keeps the material limits of its "
            "claims, and an explanation"
        )
    return errors


def _rejections(record: dict, verification: dict) -> list[dict]:
    """Every authored block, and the caveats judgement, that the verifier did not support."""
    blocks = {block["block_id"]: block for block in record["blocks"]}
    rejected = [
        {
            "block_id": entry["block_id"],
            "start_line": blocks[entry["block_id"]]["start_line"],
            "end_line": blocks[entry["block_id"]]["end_line"],
            "verdict": entry["verdict"],
            "reason": entry.get("comparison") or entry.get("explanation", ""),
        }
        for entry in verification["blocks"]
        if entry["verdict"] != "supported"
    ]
    caveats = verification["caveats"]
    if caveats["verdict"] != "supported":
        rejected.append(
            {"block_id": "caveats", "verdict": caveats["verdict"], "reason": caveats["explanation"]}
        )
    return rejected


def submit_report_verification(
    root: Path, investigation_id: str, version_sha256: str, verification: dict
) -> dict:
    """Record the report verifier's judgement of every authored block of one version, once."""
    directory = _directory(root, investigation_id)
    with _locked(directory):
        record = _report_record(directory, version_sha256)
        if record is None:
            return {"valid": False, "errors": ["Unknown report version; call prepare_report"]}
        try:
            current, contract, findings = _report_bindings(root, directory, investigation_id)
        except ValueError as exc:
            return {"valid": False, "errors": [str(exc)]}
        errors = _report_integrity(record, current, contract, findings)
        if errors:
            return {"valid": False, "errors": errors}
        errors = _verification_refusal(directory, version_sha256, current, contract, findings)
        if errors:
            return {"valid": False, "errors": errors}
        errors = _report_verification_errors(record, verification, contract, findings)
        if errors:
            return {"valid": False, "errors": errors}
        _append_line(
            directory / "report_verifications.jsonl",
            {
                "version_sha256": version_sha256,
                "report_sha256": record["report_sha256"],
                "findings_sha256": record["findings_sha256"],
                "verifier_sha256": record["verifier_sha256"],
                "stop_rule_sha256": record["stop_rule_sha256"],
                "verification": verification,
                "submitted_at": _time(),
            },
        )
        return {
            "valid": True,
            "errors": [],
            "rejected": _rejections(record, verification),
        }


def _report_file_state(path: Path, text: str) -> str:
    """ "absent", "published" when path holds exactly text, or else why the file is kept."""
    if not os.path.lexists(path):
        return "absent"
    if path.is_symlink() or not path.is_file():
        return (
            "report.md is a symlink or not a file and was kept; move it aside and call "
            "check_report again"
        )
    if path.read_bytes() == text.encode():
        return "published"
    return (
        "report.md already exists, empty, edited, or holding another accepted version, and "
        "was kept; check_report never overwrites it. Move it aside and call check_report again"
    )


def _create_exclusive(path: Path, text: str) -> bool:
    """Create path holding text in one step, or return False and leave an existing path alone.

    The text is written to a private temporary file first and then hard-linked into place;
    linking fails when anything already has the name, so no writer's file is ever replaced.
    """
    temporary = path.with_name(path.name + "." + secrets.token_hex(6) + ".tmp")
    try:
        with temporary.open("x", encoding="utf-8") as stream:
            stream.write(text)
            stream.flush()
            os.fsync(stream.fileno())
        os.chmod(temporary, 0o600)
        try:
            os.link(temporary, path)
        except FileExistsError:
            return False
        return True
    finally:
        temporary.unlink(missing_ok=True)


def check_report(root: Path, investigation_id: str, version_sha256: str | None = None) -> dict:
    """Accept a prepared report version and write it to report.md.

    The version, named by its hash or else the most recently prepared, must still be what the
    gateway assembles from the published findings, and its one report verification must
    support every authored block and the answer's caveats. report.md is written only here and
    only when no file is at that path: any existing file, empty or holding an earlier accepted
    version, is kept and reported as a conflict.
    """
    directory = _directory(root, investigation_id)
    with _locked(directory):
        try:
            current, contract, findings = _report_bindings(root, directory, investigation_id)
        except ValueError as exc:
            return {"valid": False, "errors": [str(exc)]}
        if version_sha256 is None:
            records = _report_records(directory)
            record = records[-1] if records else None
        else:
            record = _report_record(directory, version_sha256)
        if record is None:
            return {
                "valid": False,
                "errors": ["No prepared report; write the narrative and call prepare_report"],
            }
        errors = _report_integrity(record, current, contract, findings)
        if errors:
            return {"valid": False, "errors": errors}
        key = record["version_sha256"]
        row = next(
            (row for row in _report_verifications(directory) if row["version_sha256"] == key), None
        )
        if row is None:
            return {
                "valid": False,
                "errors": ["No report verification for this version; run the report verifier"],
            }
        errors = _report_verification_errors(record, row["verification"], contract, findings)
        if errors:
            return {"valid": False, "errors": errors}
        rejected = _rejections(record, row["verification"])
        if rejected:
            return {
                "valid": False,
                "errors": ["The report verifier did not support every authored block"],
                "rejected": rejected,
            }
        path = directory / "report.md"
        state = _report_file_state(path, record["report"])
        if state not in ("absent", "published"):
            return {"valid": False, "errors": [state]}
        # The acceptance is recorded before report.md is created, so a crash in between leaves
        # a version the next check_report publishes, or reports a conflict for, never overwrites.
        if not any(row["version_sha256"] == key for row in _report_acceptances(directory)):
            _append_line(
                directory / "report_acceptances.jsonl",
                {
                    "version_sha256": key,
                    **current,
                    "report_sha256": record["report_sha256"],
                    "path": "report.md",
                    "accepted_at": _time(),
                },
            )
        if state == "absent" and not _create_exclusive(path, record["report"]):
            if _report_file_state(path, record["report"]) != "published":
                return {
                    "valid": False,
                    "errors": [
                        "report.md appeared while the report was being published and was kept; "
                        "move it aside and call check_report again"
                    ],
                }
        return {
            "valid": True,
            "errors": [],
            "version_sha256": key,
            "report_sha256": record["report_sha256"],
            "path": str(path),
            "note": "Give the reader this path or the report's text unchanged; do not restate "
            "its numbers in other words.",
        }

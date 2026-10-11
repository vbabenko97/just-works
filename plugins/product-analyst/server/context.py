"""Analysis context: agreed metric definitions and named statements from .analyst/context.toml.

The manifest is a machine-readable view of definitions a project already documents. Every
reference in it names a project file and, optionally, an anchor in that file; loading fails
with an explicit error when a file or anchor is missing. The fingerprint covers the manifest
and every referenced file, so an edit to either invalidates running investigations.
"""

import hashlib
import re
import tomllib
from pathlib import Path, PurePosixPath

MANIFEST = ".analyst/context.toml"
METRIC_TEXT_FIELDS = (
    "id",
    "version",
    "display_name",
    "source",
    "approval",
    "unit",
    "population",
    "numerator",
    "denominator",
    "window",
    "cutoff",
    "deduplication",
    "empty_result",
)
NAME = re.compile(r"[a-z][a-z0-9_]*")
HEADING = re.compile(r"^#{1,6}\s+(.+?)\s*#*\s*$")


def _slug(heading: str) -> str:
    """GitHub-style anchor for a Markdown heading."""
    text = re.sub(r"[^\w\- ]", "", heading.strip().lower())
    return text.replace(" ", "-")


def _has_anchor(path: Path, anchor: str) -> bool:
    text = path.read_text(encoding="utf-8")
    if path.suffix == ".md":
        fenced = False
        for line in text.splitlines():
            if line.lstrip().startswith("```"):
                fenced = not fenced
            elif not fenced and (match := HEADING.match(line)) and _slug(match.group(1)) == anchor:
                return True
        return False
    if path.suffix == ".py":
        escaped = re.escape(anchor)
        pattern = rf"^(?:(?:async\s+)?def|class)\s+{escaped}\b|^{escaped}\s*[:=]"
        return re.search(pattern, text, re.MULTILINE) is not None
    if path.suffix == ".toml":
        return re.search(rf"^\[{re.escape(anchor)}\]\s*$", text, re.MULTILINE) is not None
    raise ValueError(f"Context reference anchors are not supported in {path.suffix} files")


def _resolve(root: Path, reference: object, where: str) -> str:
    """Check one `path` or `path#anchor` reference and return its path."""
    if not isinstance(reference, str) or not reference.strip():
        raise ValueError(f"{where}: reference must be a nonempty string")
    raw_path, _, anchor = reference.partition("#")
    relative = PurePosixPath(raw_path)
    if relative.is_absolute() or ".." in relative.parts or not relative.parts:
        raise ValueError(f"{where}: {reference!r} must be a relative path inside the project")
    path = (root / relative).resolve()
    if not path.is_relative_to(root.resolve()) or not path.is_file():
        raise ValueError(f"{where}: {raw_path} does not exist in the project")
    if anchor and not _has_anchor(path, anchor):
        raise ValueError(f"{where}: anchor #{anchor} was not found in {raw_path}")
    return relative.as_posix()


def _text(value: object, where: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{where} must be a nonempty string")
    return value


def _references(root: Path, value: object, where: str, used: set[str]) -> None:
    if not isinstance(value, list) or not value:
        raise ValueError(f"{where} must list at least one reference")
    for index, reference in enumerate(value):
        used.add(_resolve(root, reference, f"{where}[{index}]"))


def _table(manifest: dict, name: str) -> dict:
    table = manifest.get(name, {})
    if not isinstance(table, dict) or any(
        not isinstance(key, str) or not NAME.fullmatch(key) or not isinstance(entry, dict)
        for key, entry in table.items()
    ):
        raise ValueError(f"[{name}] must hold tables with lowercase snake_case names")
    return table


def load(root: Path) -> dict | None:
    """Validate the manifest and fingerprint it with every file it references.

    Returns None when the project has no manifest.
    """
    path = root / MANIFEST
    if not path.exists():
        return None
    if not path.resolve().is_relative_to(root.resolve()):
        raise ValueError(f"{MANIFEST} must be inside the project")
    raw = path.read_bytes()
    manifest = tomllib.loads(raw.decode("utf-8"))
    if type(manifest.get("schema_version")) is not int or manifest["schema_version"] != 1:
        raise ValueError(f"{MANIFEST}: schema_version must be 1")
    approvals = _table(manifest, "approvals")
    metrics = _table(manifest, "metrics")
    statements = _table(manifest, "statements")
    used: set[str] = set()
    for name, approval in approvals.items():
        for field in ("by", "on", "summary"):
            _text(approval.get(field), f"approvals.{name}.{field}")
        used.add(_resolve(root, approval.get("ref"), f"approvals.{name}.ref"))
    ids = set()
    for name, metric in metrics.items():
        for field in METRIC_TEXT_FIELDS:
            _text(metric.get(field), f"metrics.{name}.{field}")
        if metric["approval"] not in approvals:
            raise ValueError(f"metrics.{name}.approval names no [approvals] entry")
        if metric["id"] in ids or (metric["id"] in metrics and metric["id"] != name):
            raise ValueError(f"metrics.{name}.id is not unique among metric keys and ids")
        ids.add(metric["id"])
        exclusions = metric.get("exclusions")
        if not isinstance(exclusions, list) or any(
            not isinstance(item, str) or not item.strip() for item in exclusions
        ):
            raise ValueError(f"metrics.{name}.exclusions must list nonempty strings")
        _references(root, metric.get("docs"), f"metrics.{name}.docs", used)
        used.add(_resolve(root, metric.get("query"), f"metrics.{name}.query"))
    for name, statement in statements.items():
        _text(statement.get("text"), f"statements.{name}.text")
        _references(root, statement.get("refs"), f"statements.{name}.refs", used)
    return {
        "manifest": MANIFEST,
        "manifest_sha256": hashlib.sha256(raw).hexdigest(),
        "sources": {
            name: hashlib.sha256((root / name).read_bytes()).hexdigest() for name in sorted(used)
        },
        "approvals": approvals,
        "metrics": metrics,
        "statements": statements,
    }


def fingerprint(root: Path) -> dict | None:
    loaded = load(root)
    if loaded is None:
        return None
    return {"manifest_sha256": loaded["manifest_sha256"], "sources": loaded["sources"]}


def metric_key(context: dict, name: str) -> str | None:
    """The manifest key of a metric named by its key or its id."""
    for key, metric in context["metrics"].items():
        if name in (key, metric["id"]):
            return key
    return None


def describe(root: Path, metric_name: str | None = None) -> dict:
    loaded = load(root)
    if loaded is None:
        raise ValueError(f"No analysis context: {MANIFEST} does not exist in this project")
    if metric_name is None:
        return loaded
    key = metric_key(loaded, metric_name)
    if key is None:
        available = ", ".join(sorted(loaded["metrics"])) or "none"
        raise ValueError(f"Metric {metric_name!r} is not in {MANIFEST}; available: {available}")
    metric = loaded["metrics"][key]
    return {
        **loaded,
        "metrics": {key: metric},
        "approvals": {metric["approval"]: loaded["approvals"][metric["approval"]]},
    }

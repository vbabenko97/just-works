#!/usr/bin/env python3
"""Validate this skill's fixed package format offline. Requires Python 3.9+.

This is not a general YAML parser, a full API/schema validator, or an LLM eval.
It makes no network requests and does not execute examples.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
NAME = "gemini-3-8-flash-prompting"
MODEL = "gemini-3.8-flash"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def json_file(relative: str):
    return json.loads((ROOT / relative).read_text(encoding="utf-8"))


def all_keys(value):
    if isinstance(value, dict):
        for key, child in value.items():
            yield key
            yield from all_keys(child)
    elif isinstance(value, list):
        for child in value:
            yield from all_keys(child)


def validate() -> list[str]:
    checks = []
    required = [
        "SKILL.md", "agents/openai.yaml", "README.md", "install-macos.sh",
        "references/model-profile.md", "references/patterns.md",
        "references/api-boundaries.md", "references/evaluation.md",
        "references/sources.json", "tests/cases.json", "tests/test_installer.py",
        "tests/VALIDATION.md", "examples/README.md", "MANIFEST.sha256",
    ]
    for rel in required:
        require((ROOT / rel).is_file(), f"Missing file: {rel}")
    require(not any(p.is_symlink() for p in ROOT.rglob("*")), "Symlinks are not permitted")
    checks.append("Required package files and no-symlink check")

    text = (ROOT / "SKILL.md").read_text(encoding="utf-8")
    require(text.startswith("---\n"), "Missing frontmatter opening")
    parts = text.split("---\n", 2)
    require(len(parts) == 3, "Missing frontmatter closing")
    frontmatter = parts[1]
    match = re.search(r"^name: (.+)$", frontmatter, re.M)
    require(match is not None and match.group(1) == NAME, "Wrong skill name")
    require(ROOT.name == NAME, "Skill directory must match the frontmatter name")
    require(1 <= len(NAME) <= 64 and re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", NAME) is not None,
            "Invalid skill identifier")
    desc = re.search(r"^description: (.+)$", frontmatter, re.M)
    require(desc is not None and 1 <= len(desc.group(1)) <= 1024, "Invalid description")
    require('last_verified: "2026-09-06"' in frontmatter, "Missing snapshot date")
    require(len(text.splitlines()) <= 250, "Core skill has become unnecessarily long")
    checks.append("Frontmatter, naming, description, snapshot, and core length")

    ui = (ROOT / "agents/openai.yaml").read_text(encoding="utf-8")
    require(re.search(r"^policy:\n  allow_implicit_invocation: false$", ui, re.M) is not None,
            "Explicit-only invocation policy missing")
    require(f"${NAME}" in ui, "Default prompt does not identify the skill")
    require("dependencies:" not in ui, "Unexpected external dependency declaration")
    checks.append("Manual-invocation metadata and no connector dependencies")

    sources = json_file("references/sources.json")
    require(sources["verified_on"] == "2026-09-06", "Source date mismatch")
    source_ids = {s["id"] for s in sources["sources"]}
    require(len(source_ids) == 12, "Expected 12 unique primary sources")
    for source in sources["sources"]:
        require(source["url"].startswith(("https://ai.google.dev/", "https://learn.chatgpt.com/", "https://agentskills.io/")),
                f"Unexpected source domain: {source['id']}")
    for md in ROOT.rglob("*.md"):
        content = md.read_text(encoding="utf-8")
        for reference in re.findall(r"\bS\d{2}\b", content):
            require(reference in source_ids, f"Unresolved source {reference} in {md.name}")
    checks.append("Source index and document attribution IDs")

    forbidden = {"temperature", "top_p", "top_k", "candidate_count", "thinking_budget",
                 "thinkingConfig", "generationConfig", "response_mime_type", "response_schema"}
    request_files = sorted((ROOT / "examples").glob("*-request.json"))
    require(len(request_files) == 3, "Expected three request-body examples")
    for path in request_files:
        data = json.loads(path.read_text(encoding="utf-8"))
        require(data.get("model") == MODEL, f"Wrong model in {path.name}")
        require(data.get("store") is False, f"Unexpected state storage in {path.name}")
        require("previous_interaction_id" not in data, f"Stateful history in single-turn {path.name}")
        require(data["generation_config"]["thinking_level"] in {"low", "medium", "high"},
                f"Unsupported thinking level in {path.name}")
        require(not forbidden.intersection(all_keys(data)), f"Invalid or mixed-surface fields in {path.name}")
    schema = json_file("examples/extraction-request.json")["response_format"]
    require(schema["type"] == "text" and schema["mime_type"] == "application/json", "Wrong response_format")
    require(set(schema["schema"]["required"]) == {"project", "owner", "due_date"}, "Wrong required fields")
    for name in ("owner", "due_date"):
        require("null" in schema["schema"]["properties"][name]["type"], f"Missing nullability: {name}")
    require(json_file("examples/research-request.json")["tools"] == [{"type": "google_search"}], "Wrong search declaration")
    checks.append("Three request examples: JSON, target, allowed settings, schema, and grounding declaration")

    cases = json_file("tests/cases.json")
    require(cases["execution_status"] == "not_run", "Do not mislabel unrun behavioral cases")
    require(len(cases["cases"]) == 16, "Expected 16 behavioral cases")
    require(len({case["id"] for case in cases["cases"]}) == 16, "Duplicate case ID")
    for case in cases["cases"]:
        require(bool(case["input"]) and len(case["acceptance"]) >= 2, f"Incomplete case {case['id']}")
    checks.append("Manual behavioral case structure and honest not_run status")

    manifest = ROOT / "MANIFEST.sha256"
    tracked = set()
    for line in manifest.read_text(encoding="utf-8").splitlines():
        match = re.fullmatch(r"([0-9a-f]{64})  ([A-Za-z0-9_./-]+)", line)
        require(match is not None, "Malformed manifest line")
        digest, relative = match.groups()
        path = PurePosixPath(relative)
        require(not path.is_absolute() and ".." not in path.parts and path.as_posix() == relative,
                "Unsafe manifest path")
        require(relative not in tracked and relative != "MANIFEST.sha256", "Duplicate/self manifest entry")
        tracked.add(relative)
        require((ROOT / relative).is_file(), f"Missing manifest file: {relative}")
        require(hashlib.sha256((ROOT / relative).read_bytes()).hexdigest() == digest,
                f"Checksum mismatch: {relative}")
    actual = {p.relative_to(ROOT).as_posix() for p in ROOT.rglob("*") if p.is_file()
              and p.name not in {"MANIFEST.sha256", ".DS_Store"} and "__pycache__" not in p.parts}
    require(tracked == actual, f"Manifest/file-set mismatch: {tracked.symmetric_difference(actual)}")
    checks.append(f"SHA-256 integrity and complete coverage of {len(tracked)} files")
    return checks


def main() -> int:
    try:
        checks = validate()
    except (ValueError, KeyError, OSError, TypeError) as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1
    for check in checks:
        print(f"PASS: {check}")
    print(f"PASS: {len(checks)} offline check groups. No Gemini calls or behavioral model evaluation.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Read-only checks for this bundle; no model calls or semantic grading.

Requires Python 3.9+. The frontmatter reader deliberately accepts only this
package's flat name/description subset, not arbitrary YAML or the full Skill spec.
"""
from __future__ import annotations

import argparse
import ast
import json
import re
import sys
from datetime import date
from pathlib import Path
from urllib.parse import unquote, urlsplit

NAME = "opus-5-5-prompting"
REQUIRED = (
    "SKILL.md",
    "USAGE.md",
    "UPSTREAM.md",
    "references/prompt-patterns.md",
    "references/api-harness.md",
    "evals/evals.json",
    "scripts/validate.py",
)


class ValidationError(ValueError):
    """A package check failed."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValidationError(message)


def inside(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root)
        return True
    except ValueError:
        return False


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def frontmatter(text: str) -> dict[str, str]:
    lines = text.splitlines()
    require(bool(lines) and lines[0] == "---", "SKILL.md needs frontmatter")
    try:
        end = lines.index("---", 1)
    except ValueError as exc:
        raise ValidationError("Unclosed frontmatter") from exc
    fields: dict[str, str] = {}
    for line in lines[1:end]:
        require(":" in line, f"Unsupported frontmatter line: {line!r}")
        key, value = line.split(":", 1)
        key, value = key.strip(), value.strip()
        require(key in {"name", "description"}, f"Unexpected frontmatter key: {key}")
        require(key not in fields, f"Duplicate frontmatter key: {key}")
        if value.startswith('"'):
            value = json.loads(value)
        require(isinstance(value, str) and bool(value.strip()), f"Empty/invalid {key}")
        fields[key] = value
    require(set(fields) == {"name", "description"}, "Missing name or description")
    return fields


def validate(root: Path) -> dict[str, int]:
    root = root.resolve()
    require(root.is_dir(), f"Not a package directory: {root}")
    for name in REQUIRED:
        path = root / name
        require(path.is_file(), f"Missing file: {name}")
        require(inside(path, root), f"File escapes package: {name}")

    skill = read_text(root / "SKILL.md")
    fields = frontmatter(skill)
    require(fields["name"] == NAME == root.name, "Skill name and folder must match")
    require(len(fields["name"]) <= 64, "Skill name exceeds 64 characters")
    require(re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", fields["name"]) is not None,
            "Invalid skill name")
    require(len(fields["description"]) <= 1024, "Description exceeds 1024 characters")
    require(len(skill.splitlines()) <= 500, "Keep SKILL.md within 500 lines")

    markdowns = sorted(root.rglob("*.md"))
    all_text = "\n".join(read_text(p) for p in markdowns)
    match = re.search(r"Primary documentation reviewed: \*\*(\d{4}-\d{2}-\d{2})\*\*",
                      read_text(root / "UPSTREAM.md"))
    require(match is not None, "Review date missing")
    reviewed = match.group(1)
    date.fromisoformat(reviewed)
    require(reviewed in skill, "SKILL.md review date differs from provenance")
    require(reviewed in read_text(root / "references/api-harness.md"),
            "API reference review date differs from provenance")
    registered = set(re.findall(r"^\| (S\d+) \|", read_text(root / "UPSTREAM.md"), re.M))
    cited = set(re.findall(r"\bS\d+\b", all_text))
    require(cited <= registered, f"Unknown source keys: {sorted(cited - registered)}")
    require(bool(registered), "Source register is empty")

    link_count = json_count = 0
    for path in markdowns:
        require(inside(path, root), f"Markdown escapes package: {path.name}")
        text = read_text(path)
        # Only triple-backtick fences are used by this package.
        fences = re.findall(r"^```[^\n]*$", text, re.M)
        require(len(fences) % 2 == 0, f"Unbalanced fences in {path.name}")
        for target in re.findall(r"(?<!!)\[[^\]\n]+\]\(([^\s)]+)\)", text):
            parsed = urlsplit(target)
            if parsed.scheme or parsed.netloc or not parsed.path:
                continue
            resolved = path.parent / unquote(parsed.path)
            require(inside(resolved, root), f"Reference escapes package: {target}")
            require(resolved.exists(), f"Broken local reference in {path.name}: {target}")
            link_count += 1
        for block in re.findall(r"^```json\s*\n(.*?)^```\s*$", text, re.M | re.S):
            json.loads(block)
            json_count += 1

    python_files = sorted(root.rglob("*.py"))
    for path in python_files:
        require(inside(path, root), f"Python file escapes package: {path.name}")
        ast.parse(read_text(path), filename=str(path))

    data = json.loads(read_text(root / "evals/evals.json"))
    require(isinstance(data, dict), "Eval file must be an object")
    require(data.get("skill_name") == NAME, "Eval skill_name mismatch")
    require(data.get("schema_version") == "1.0", "Unknown eval schema version")
    cases = data.get("evals")
    require(isinstance(cases, list) and bool(cases), "No evaluation cases")
    ids: set[int] = set()
    names: set[str] = set()
    positive = negative = 0
    for case in cases:
        require(isinstance(case, dict), "Eval case must be an object")
        number = case.get("id")
        require(type(number) is int and number > 0 and number not in ids,
                f"Invalid or duplicate case id: {number!r}")
        ids.add(number)
        for key in ("name", "prompt", "expected_output"):
            value = case.get(key)
            require(isinstance(value, str) and bool(value.strip()),
                    f"Case {number}: missing/invalid {key}")
        require(case["name"] not in names, f"Duplicate case name: {case['name']}")
        names.add(case["name"])
        trigger = case.get("should_trigger")
        require(type(trigger) is bool, f"Case {number}: should_trigger must be boolean")
        positive += int(trigger)
        negative += int(not trigger)
        expectations = case.get("expectations")
        require(isinstance(expectations, list) and bool(expectations),
                f"Case {number}: expectations must be a nonempty list")
        require(all(isinstance(e, str) and bool(e.strip()) for e in expectations),
                f"Case {number}: invalid expectation")
        files = case.get("files")
        require(isinstance(files, list), f"Case {number}: files must be a list")
        for name in files:
            require(isinstance(name, str), f"Case {number}: file path must be a string")
            path = root / name
            require(inside(path, root) and path.is_file(),
                    f"Case {number}: invalid local fixture path: {name}")
    require(positive > 0 and negative > 0, "Include positive and negative routing cases")
    return {
        "markdown_files": len(markdowns),
        "local_links": link_count,
        "json_examples": json_count,
        "python_files": len(python_files),
        "source_entries": len(registered),
        "eval_cases": len(cases),
        "positive_cases": positive,
        "negative_cases": negative,
        "skill_lines": len(skill.splitlines()),
        "description_characters": len(fields["description"]),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1],
                        help="Package folder (default: this script's parent package)")
    args = parser.parse_args()
    try:
        stats = validate(args.root)
    except (ValidationError, OSError, UnicodeError, ValueError, SyntaxError) as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1
    print("PASS: offline package structure checks")
    for key, value in stats.items():
        print(f"  {key}: {value}")
    print("Not tested: live model behavior, API acceptance, host skill discovery.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

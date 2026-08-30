#!/usr/bin/env python3
"""Deterministic first-pass marker scan for MSCA-PF text/markdown sources.

Usage:
  python scripts/audit_text_bundle.py file1.md file2.txt
  python scripts/audit_text_bundle.py --json file1.md file2.md
  python scripts/audit_text_bundle.py --fail-on-cyrillic file1.md

This does not replace visual PDF QA or an evaluator review. Cyrillic text is a warning by
default because publication titles or names can legitimately contain it; use
--fail-on-cyrillic only for sources that should be entirely English.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

PATTERNS = {
    "unresolved_marker": (re.compile(r"\[(?:TO\s+CONFIRM|PENDING|FROM\s+[^\]]+)[:\s\]]", re.I), "blocker"),
    "todo_token": (re.compile(r"\b(?:TODO|TBD|FIXME|XXX)\b", re.I), "blocker"),
    "generator_token": (re.compile(r"\[\[(?:FIGURE|TABLE)[^\]]*\]\]|%%(?:TITLE|ROW)%%", re.I), "blocker"),
    "backtick": (re.compile(r"`"), "blocker"),
    "cyrillic": (re.compile(r"[\u0400-\u04FF]"), "warning"),
}


def scan(path: Path, fail_on_cyrillic: bool) -> dict:
    text = path.read_text(encoding="utf-8", errors="replace")
    findings = []
    for number, line in enumerate(text.splitlines(), 1):
        for kind, (pattern, default_level) in PATTERNS.items():
            if pattern.search(line):
                level = "blocker" if kind == "cyrillic" and fail_on_cyrillic else default_level
                findings.append({
                    "level": level,
                    "kind": kind,
                    "line": number,
                    "text": line.strip()[:240],
                })
    return {"file": str(path), "findings": findings}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("files", nargs="+", help="UTF-8 text/markdown proposal sources")
    parser.add_argument("--json", action="store_true", help="emit JSON")
    parser.add_argument("--fail-on-cyrillic", action="store_true", help="treat Cyrillic text as a blocker")
    args = parser.parse_args()

    results = []
    missing = []
    for raw in args.files:
        path = Path(raw)
        if not path.is_file():
            missing.append(str(path))
            continue
        results.append(scan(path, args.fail_on_cyrillic))

    blockers = sum(f["level"] == "blocker" for item in results for f in item["findings"])
    warnings = sum(f["level"] == "warning" for item in results for f in item["findings"])
    if args.json:
        print(json.dumps({
            "files": results,
            "missing": missing,
            "blockers": blockers,
            "warnings": warnings,
        }, indent=2, ensure_ascii=False))
    else:
        for item in results:
            print(f"\n{item['file']}")
            if not item["findings"]:
                print("  CLEAN: no configured marker patterns found")
                continue
            for finding in item["findings"]:
                print(f"  {finding['level'].upper()} {finding['kind']} L{finding['line']}: {finding['text']}")
        if missing:
            print("\nMissing files:")
            for path in missing:
                print(f"  {path}")
        print(f"\nBlockers: {blockers}; warnings: {warnings}; missing: {len(missing)}")

    return 2 if blockers or missing else 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Lint Gemini 3.7 Flash prompt text without third-party dependencies."""

from __future__ import annotations

import argparse
import re
import sys
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Diagnostic:
    line: int
    code: str
    message: str


FIELD_ASSIGNMENT = re.compile(
    r"(?<![\w-])['\"]?(?P<field>thinking_level|thinking_budget|temperature|top_k|top_p|"
    r"frequency_penalty|presence_penalty|candidate_count)['\"]?\s*(?::|=)\s*"
    r"(?P<value>\"[^\"]*\"|'[^']*'|“[^”]*”|‘[^’]*’|[^\s,}\]]+)?",
    re.IGNORECASE,
)
DEPRECATED_FIELDS = frozenset({"temperature", "top_k", "top_p"})
UNSUPPORTED_FIELDS = frozenset({"frequency_penalty", "presence_penalty", "candidate_count"})

MANUAL_COT_PATTERN = re.compile(
    r"\b(?:"
    r"(?:let['’]s\s+)?think\s+step\s+by\s+step|"
    r"think\s+through\s+(?:the\s+)?(?:problem|task|issue|question)\s+step\s+by\s+step|"
    r"(?:reason|work(?:\s+through)?)\s+(?:the\s+)?(?:problem|task|issue|question)?\s*step\s+by\s+step|"
    r"show\s+(?:your\s+)?chain[- ]of[- ]thought|"
    r"chain[- ]of[- ]thought|"
    r"think\s+aloud|"
    r"(?:explain|show)\s+(?:your\s+)?reasoning\s+step\s+by\s+step"
    r")\b",
    re.IGNORECASE,
)
NEGATED_COT_CLAUSE = re.compile(
    r"\b(?:do\s+not|don't|never|avoid|remove)\b[^.;:]*$",
    re.IGNORECASE,
)
DISCUSSION_COT_CLAUSE = re.compile(r"\b(?:the\s+)?(?:phrase|term|concept)\s*['\"“‘]?\s*$", re.IGNORECASE)
OPEN_FENCE = re.compile(r"^\s{0,3}(?P<delimiter>`{3,}|~{3,})")
XML_TAG = re.compile(r"</?[A-Za-z_][\w.-]*(?::[A-Za-z_][\w.-]*)?(?:\s+[^<>]*)?/?>")
ATX_HEADING = re.compile(r"^\s{0,3}#{1,6}\s+\S")
SETEXT_UNDERLINE = re.compile(r"^\s{0,3}(?:=+|-+)\s*$")


def opening_fence(line: str) -> str | None:
    match = OPEN_FENCE.match(line)
    return match.group("delimiter") if match else None


def is_closing_fence(line: str, opening: str) -> bool:
    character = re.escape(opening[0])
    return bool(re.match(rf"^\s{{0,3}}{character}{{{len(opening)},}}\s*$", line))


def is_negated_or_discussion(line: str, match_start: int) -> bool:
    prefix = line[:match_start]
    clause = re.split(r"[.;:?]", prefix)[-1]
    if NEGATED_COT_CLAUSE.search(clause) or DISCUSSION_COT_CLAUSE.search(clause):
        return True
    quote = prefix.rstrip()[-1:]
    if quote in {"'", '"', "‘", "“"}:
        quoted_prefix = prefix.rstrip()[:-1]
        return bool(
            re.search(r"\b(?:do\s+not|don't|never|avoid|remove)\b[^.?!]*$", quoted_prefix, re.IGNORECASE)
            or DISCUSSION_COT_CLAUSE.search(quoted_prefix)
        )
    return False


def markdown_heading_lines(prose_lines: list[tuple[int, str]]) -> set[int]:
    headings: set[int] = set()
    for index, (line_number, line) in enumerate(prose_lines):
        if ATX_HEADING.match(line):
            headings.add(line_number)
        if index and SETEXT_UNDERLINE.match(line) and prose_lines[index - 1][1].strip():
            headings.add(line_number)
    return headings


def lint_text(text: str) -> list[Diagnostic]:
    diagnostics: list[Diagnostic] = []
    fence: str | None = None
    prose_lines: list[tuple[int, str]] = []
    for line_number, line in enumerate(text.splitlines(), start=1):
        for match in FIELD_ASSIGNMENT.finditer(line):
            field = match.group("field").lower()
            raw_value = match.group("value")
            value = raw_value.strip("'\"“”‘’").upper() if raw_value else ""
            if field == "thinking_level" and value not in {"LOW", "MEDIUM", "HIGH"}:
                diagnostics.append(Diagnostic(line_number, "G37F001", "invalid thinking_level; use LOW, MEDIUM, or HIGH"))
            elif field == "thinking_budget":
                diagnostics.append(Diagnostic(line_number, "G37F002", "thinking_budget is deprecated; use thinking_level"))
            elif field in DEPRECATED_FIELDS:
                diagnostics.append(Diagnostic(line_number, "G37F003", "deprecated sampling parameter is ignored; remove it"))
            elif field in UNSUPPORTED_FIELDS:
                diagnostics.append(Diagnostic(line_number, "G37F004", "unsupported parameter errors; remove it"))
        if fence is None:
            fence = opening_fence(line)
            if fence is not None:
                continue
        elif is_closing_fence(line, fence):
            fence = None
            continue
        if fence is not None:
            continue
        prose_lines.append((line_number, line))
        for match in MANUAL_COT_PATTERN.finditer(line):
            if not is_negated_or_discussion(line, match.start()):
                diagnostics.append(Diagnostic(line_number, "G37F005", "manual chain-of-thought request; ask for a concise plan or evidence instead"))

    xml_lines = {number for number, line in prose_lines if XML_TAG.search(line)}
    markdown_lines = markdown_heading_lines(prose_lines)
    has_xml = bool(xml_lines)
    has_markdown = bool(markdown_lines)
    if has_xml and has_markdown:
        first_line = min(xml_lines | markdown_lines)
        diagnostics.append(Diagnostic(first_line, "G37F006", "mixed XML and Markdown structural delimiters; choose one style"))
    return diagnostics


def read_inputs(paths: Iterable[str]) -> tuple[int, list[tuple[str, str]]]:
    path_list = list(paths)
    if not path_list:
        try:
            return 0, [("<stdin>", sys.stdin.read())]
        except (OSError, UnicodeError) as error:
            print(f"<stdin>:1: G37F900 unable to read input: {error}", file=sys.stderr)
            return 2, []
    inputs: list[tuple[str, str]] = []
    for value in path_list:
        path = Path(value)
        try:
            inputs.append((str(path), path.read_text(encoding="utf-8")))
        except (OSError, UnicodeError) as error:
            print(f"{path}:1: G37F900 unable to read input: {error}", file=sys.stderr)
            return 2, []
    return 0, inputs


def main() -> int:
    parser = argparse.ArgumentParser(description="Lint prompts for Gemini 3.7 Flash migration hazards.")
    parser.add_argument("files", nargs="*", help="Prompt files to lint; omit to read standard input.")
    args = parser.parse_args()
    status, inputs = read_inputs(args.files)
    if status:
        return status
    findings = 0
    for path, text in inputs:
        for diagnostic in lint_text(text):
            print(f"{path}:{diagnostic.line}: {diagnostic.code} {diagnostic.message}")
            findings += 1
    return 1 if findings else 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Heuristic clean-code scanner for quick triage.

This script intentionally uses only the Python standard library. It is not a
replacement for language-specific linters, type checkers, or human review.
"""

from __future__ import annotations

import argparse
import ast
import json
import re
from collections import Counter
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable, Sequence

SOURCE_EXTENSIONS = {
    ".py",
    ".js",
    ".jsx",
    ".ts",
    ".tsx",
    ".java",
    ".cs",
    ".go",
    ".rs",
    ".kt",
    ".swift",
    ".php",
    ".rb",
}

SKIP_DIRS = {
    ".git",
    ".hg",
    ".svn",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    "__pycache__",
    "node_modules",
    "dist",
    "build",
    "target",
    "vendor",
    ".venv",
    "venv",
    "env",
}

SUPPRESS_MARKER = "clean-scan: ignore"
MARKER_RE = re.compile(r"\b(TODO|FIXME|HACK|XXX)\b", re.IGNORECASE)  # clean-scan: ignore
DEBUG_STMT_RE = re.compile(r"\b(console\.log|print\s*\(|debugger\b|pdb\.set_trace\s*\()")  # clean-scan: ignore
BROAD_EXCEPT_RE = re.compile(r"except\s*(Exception|BaseException)?\s*:")
GENERIC_NAME_RE = re.compile(
    r"\b(data|info|stuff|tmp|temp|obj|manager|helper|processor|handler)\b",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class Finding:
    severity: str
    path: str
    line: int
    rule: str
    message: str


def iter_source_files(root: Path) -> Iterable[Path]:
    if root.is_file():
        if root.suffix.lower() in SOURCE_EXTENSIONS:
            yield root
        return

    for path in root.rglob("*"):
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        if path.is_file() and path.suffix.lower() in SOURCE_EXTENSIONS:
            yield path


def safe_read(path: Path) -> str | None:
    for encoding in ("utf-8", "latin-1"):
        try:
            return path.read_text(encoding=encoding)
        except UnicodeDecodeError:
            continue
        except OSError:
            return None
    return None


def relative_path(path: Path, root: Path) -> str:
    try:
        base = root if root.is_dir() else root.parent
        return str(path.relative_to(base))
    except ValueError:
        return str(path)


def add_finding(
    findings: list[Finding],
    severity: str,
    relative: str,
    line: int,
    rule: str,
    message: str,
) -> None:
    findings.append(Finding(severity, relative, line, rule, message))


def analyze_file_size(
    findings: list[Finding], relative: str, line_count: int, args: argparse.Namespace
) -> None:
    if line_count <= args.large_file_lines:
        return
    add_finding(
        findings,
        "should-improve",
        relative,
        1,
        "large-file",
        f"file has {line_count} lines; consider splitting by responsibility",
    )


def line_has_assignment_or_definition(line: str) -> bool:
    return any(token in line for token in ("=", "def ", "class ", "function "))


def analyze_line_patterns(
    findings: list[Finding], path: Path, relative: str, lines: Sequence[str], args: argparse.Namespace
) -> list[tuple[int, str]]:
    normalized_nontrivial: list[tuple[int, str]] = []
    for index, line in enumerate(lines, start=1):
        if SUPPRESS_MARKER in line:
            continue
        stripped = line.strip()
        record_line_findings(findings, path, relative, index, line, args)
        if is_nontrivial_duplicate_candidate(stripped):
            normalized_nontrivial.append((index, re.sub(r"\s+", " ", stripped)))
    return normalized_nontrivial


def record_line_findings(
    findings: list[Finding], path: Path, relative: str, index: int, line: str, args: argparse.Namespace
) -> None:
    if len(line) > args.long_line_chars:
        add_finding(findings, "nice-to-have", relative, index, "long-line", f"line is {len(line)} characters")
    if MARKER_RE.search(line):
        add_finding(findings, "should-improve", relative, index, "todo-marker", "tracked-work marker found")  # clean-scan: ignore
    if DEBUG_STMT_RE.search(line):
        add_finding(findings, "should-improve", relative, index, "debug-output", "debug output or breakpoint found")
    if path.suffix.lower() == ".py" and BROAD_EXCEPT_RE.search(line):
        add_finding(findings, "must-fix", relative, index, "broad-except", "broad except block can hide failures")
    if GENERIC_NAME_RE.search(line) and line_has_assignment_or_definition(line):
        add_finding(findings, "nice-to-have", relative, index, "generic-name", "generic name detected")


def is_nontrivial_duplicate_candidate(stripped: str) -> bool:
    if not stripped or len(stripped) <= 24:
        return False
    ignored_prefixes = ("#", "//", "*", "/*", "import ", "from ")
    return not stripped.startswith(ignored_prefixes)


def analyze_duplicates(
    findings: list[Finding], relative: str, normalized: Sequence[tuple[int, str]], threshold: int
) -> None:
    duplicates = Counter(line for _, line in normalized)
    for duplicated, count in duplicates.items():
        if count < threshold:
            continue
        first_line = next(index for index, line in normalized if line == duplicated)
        add_finding(
            findings,
            "should-improve",
            relative,
            first_line,
            "duplicate-line",
            f"same non-trivial line appears {count} times; check for duplicated rule",
        )


def scan_text(path: Path, root: Path, text: str, args: argparse.Namespace) -> list[Finding]:
    findings: list[Finding] = []
    lines = text.splitlines()
    relative = relative_path(path, root)
    analyze_file_size(findings, relative, len(lines), args)
    duplicate_candidates = analyze_line_patterns(findings, path, relative, lines, args)
    analyze_duplicates(findings, relative, duplicate_candidates, args.duplicate_threshold)
    return findings


def function_complexity(node: ast.AST) -> int:
    branch_nodes = (
        ast.If,
        ast.For,
        ast.AsyncFor,
        ast.While,
        ast.Try,
        ast.ExceptHandler,
        ast.With,
        ast.AsyncWith,
        ast.BoolOp,
        ast.IfExp,
        ast.Match,
    )
    return 1 + sum(isinstance(child, branch_nodes) for child in ast.walk(node))


def count_parameters(node: ast.FunctionDef | ast.AsyncFunctionDef) -> int:
    args = node.args
    count = len(args.args) + len(args.kwonlyargs) + len(args.posonlyargs)
    return count + int(args.vararg is not None) + int(args.kwarg is not None)


def analyze_function(
    findings: list[Finding], relative: str, node: ast.FunctionDef | ast.AsyncFunctionDef, args: argparse.Namespace
) -> None:
    end_lineno = getattr(node, "end_lineno", node.lineno)
    length = end_lineno - node.lineno + 1
    if length > args.long_function_lines:
        add_finding(
            findings,
            "should-improve",
            relative,
            node.lineno,
            "long-function",
            f"function `{node.name}` has {length} lines",
        )

    parameter_count = count_parameters(node)
    if parameter_count > args.max_args:
        add_finding(
            findings,
            "should-improve",
            relative,
            node.lineno,
            "too-many-parameters",
            f"function `{node.name}` has {parameter_count} parameters",
        )

    complexity = function_complexity(node)
    if complexity > args.max_complexity:
        add_finding(
            findings,
            "should-improve",
            relative,
            node.lineno,
            "high-branching",
            f"function `{node.name}` complexity is {complexity}",
        )


def analyze_class(findings: list[Finding], relative: str, node: ast.ClassDef, args: argparse.Namespace) -> None:
    end_lineno = getattr(node, "end_lineno", node.lineno)
    length = end_lineno - node.lineno + 1
    method_count = sum(isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)) for child in node.body)
    if length <= args.large_class_lines and method_count <= args.max_methods:
        return
    add_finding(
        findings,
        "should-improve",
        relative,
        node.lineno,
        "large-class",
        f"class `{node.name}` has {length} lines and {method_count} methods",
    )


def scan_python_ast(path: Path, root: Path, text: str, args: argparse.Namespace) -> list[Finding]:
    relative = relative_path(path, root)
    try:
        tree = ast.parse(text)
    except SyntaxError as exc:
        return [Finding("must-fix", relative, exc.lineno or 1, "syntax-error", f"python syntax error: {exc.msg}")]

    findings: list[Finding] = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            analyze_function(findings, relative, node, args)
        elif isinstance(node, ast.ClassDef):
            analyze_class(findings, relative, node, args)
    return findings


def scan_path(root: Path, args: argparse.Namespace) -> list[Finding]:
    findings: list[Finding] = []
    for path in sorted(iter_source_files(root)):
        text = safe_read(path)
        if text is None:
            continue
        findings.extend(scan_text(path, root, text, args))
        if path.suffix.lower() == ".py":
            findings.extend(scan_python_ast(path, root, text, args))
    return findings


def render_markdown(findings: Sequence[Finding]) -> str:
    if not findings:
        return "# Clean Code Scan\n\nNo heuristic findings detected. This does not prove the code is clean.\n"

    severity_order = {"must-fix": 0, "should-improve": 1, "nice-to-have": 2}
    sorted_findings = sorted(findings, key=lambda f: (severity_order.get(f.severity, 99), f.path, f.line, f.rule))
    lines = ["# Clean Code Scan", ""]
    for severity in ("must-fix", "should-improve", "nice-to-have"):
        grouped = [f for f in sorted_findings if f.severity == severity]
        if not grouped:
            continue
        lines.extend([f"## {severity.replace('-', ' ').title()}", ""])
        lines.extend(f"- `{finding.path}:{finding.line}` **{finding.rule}**: {finding.message}" for finding in grouped)
        lines.append("")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Heuristic clean-code scanner for source repositories.")
    parser.add_argument("path", type=Path, help="source file or directory to scan")
    parser.add_argument("--json", action="store_true", help="emit JSON instead of markdown")
    parser.add_argument("--large-file-lines", type=int, default=500)
    parser.add_argument("--long-function-lines", type=int, default=50)
    parser.add_argument("--large-class-lines", type=int, default=300)
    parser.add_argument("--max-methods", type=int, default=20)
    parser.add_argument("--max-args", type=int, default=6)
    parser.add_argument("--max-complexity", type=int, default=10)
    parser.add_argument("--long-line-chars", type=int, default=120)
    parser.add_argument("--duplicate-threshold", type=int, default=4)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    root = args.path.resolve()
    if not root.exists():
        parser.error(f"path does not exist: {root}")

    findings = scan_path(root, args)
    if args.json:
        print(json.dumps([asdict(finding) for finding in findings], indent=2, sort_keys=True))  # clean-scan: ignore
    else:
        print(render_markdown(findings))  # clean-scan: ignore
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

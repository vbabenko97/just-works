#!/usr/bin/env python3
"""Structural lint for Claude Science research prompts.

This tool checks prompt coverage, XML-like tag balance, and common legacy
prompting anti-patterns. It does not validate scientific claims or methods.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Iterable


CATEGORY_PATTERNS: dict[str, tuple[str, ...]] = {
    "objective": (
        r"research_objective",
        r"\bobjective\b",
        r"\bmission\b",
        r"research question",
        r"\bquestion\b",
        r"\b(?:assess|determine|evaluate|analy[sz]e|research)\b",
    ),
    "success_criteria": (
        r"success_criteria",
        r"success criteria",
        r"completion standard",
        r"acceptance criteria",
        r"successful result",
        r"must (?:establish|contain|include|produce)",
    ),
    "evidence": (
        r"evidence_policy",
        r"\bevidence\b",
        r"\bcitations?\b",
        r"\bcite\b",
        r"primary (?:literature|sources?|studies)",
        r"authoritative (?:database|source)",
    ),
    "methods": (
        r"methods?_and_reproducibility",
        r"analysis_strategy",
        r"\bmethods?\b",
        r"\bworkflow\b",
        r"statistical",
        r"\banalysis\b",
    ),
    "tools": (
        r"tools?_and_approvals",
        r"agent_strategy",
        r"compute_strategy",
        r"\btools?\b",
        r"\bconnectors?\b",
        r"\bsubagents?\b",
        r"\bcompute\b",
        r"\bHPC\b",
    ),
    "reproducibility": (
        r"\breproducib",
        r"\bprovenance\b",
        r"data lineage",
        r"package versions?",
        r"random seeds?",
        r"\benvironment\b",
        r"artifact checksums?",
    ),
    "uncertainty": (
        r"\buncertainty\b",
        r"\blimitations?\b",
        r"\bconfidence\b",
        r"conflicting evidence",
        r"alternative explanations?",
    ),
    "review": (
        r"reviewer_checks",
        r"review_and_validation",
        r"\breviewer\b",
        r"independently verify",
        r"\bvalidation\b",
        r"\baudit\b",
    ),
    "output": (
        r"final_output",
        r"<output>",
        r"\boutput\b",
        r"\bdeliver(?:able|ables|y)?\b",
        r"\breturn\b",
        r"\bprovide\b",
    ),
    "stopping": (
        r"stopping_rules",
        r"stopping rules?",
        r"\bblocker\b",
        r"essential (?:data|evidence|permissions?).*unavailable",
        r"do not (?:invent|fabricate)",
        r"missing data",
    ),
    "safety_and_approval": (
        r"\bapproval\b",
        r"\bauthori[sz]ation\b",
        r"\bprivacy\b",
        r"\bethics\b",
        r"\bbiosafety\b",
        r"\bclinical\b",
        r"sensitive data",
        r"hard-to-reverse",
    ),
}

ANTI_PATTERNS: tuple[tuple[str, str, str], ...] = (
    (r"\bworld[- ]class\b|\bnobel[- ]level\b|\belite super", "role theater", "low"),
    (r"\bnever hallucinate\b|\b100% accurate\b", "unobservable accuracy command", "medium"),
    (r"\bthink step by step\b|\breveal (?:all|every) reasoning", "hidden-reasoning request", "medium"),
    (r"\buse (?:all|every) available tools?\b|\balways use all", "unbounded tool use", "high"),
    (r"\bdouble[- ]check everything\b", "vague review instruction", "medium"),
    (r"\bdo not stop until (?:it is )?perfect\b|\buntil the answer is perfect\b", "unbounded completion rule", "medium"),
    (r"\bextremely thorough\b|\bexhaustive but concise\b", "conflicting verbosity theater", "low"),
    (r"\bask permission before (?:anything|everything)\b", "overbroad approval rule", "medium"),
)

TAG_RE = re.compile(r"<\s*(/?)\s*([A-Za-z][A-Za-z0-9_.:-]*)(?:\s+[^<>]*?)?\s*(/?)>")


def any_match(text: str, patterns: Iterable[str]) -> bool:
    return any(re.search(pattern, text, flags=re.IGNORECASE | re.DOTALL) for pattern in patterns)


def detect_mode(text: str) -> str:
    lower = text.lower()
    full_signals = (
        "subagent",
        "specialist agent",
        "hpc",
        "ssh",
        "compute_strategy",
        "publication-ready",
        "reproducibility package",
        "evidence ledger",
    )
    standard_signals = (
        "workflow",
        "reviewer",
        "dataset",
        "analysis",
        "multiple sources",
        "success criteria",
    )
    if len(text) > 3500 or sum(signal in lower for signal in full_signals) >= 2:
        return "full"
    if len(text) > 1200 or sum(signal in lower for signal in standard_signals) >= 2:
        return "standard"
    return "compact"


def required_categories(mode: str, text: str) -> list[str]:
    required = ["objective", "evidence", "uncertainty", "output"]
    if mode in {"standard", "full"}:
        required.extend(["success_criteria", "methods", "review", "stopping"])
    if mode == "full":
        required.extend(["tools", "reproducibility"])

    computational = any_match(
        text,
        (
            r"\bcode\b",
            r"\bdataset\b",
            r"\bcompute\b",
            r"\bfigure\b",
            r"\bnotebook\b",
            r"\bmodel(?:ing)?\b",
            r"\bstatistical\b",
        ),
    )
    if computational and "reproducibility" not in required:
        required.append("reproducibility")
    return required


def check_xml_balance(text: str) -> list[str]:
    stack: list[tuple[str, int]] = []
    errors: list[str] = []

    for match in TAG_RE.finditer(text):
        closing, name, self_closing = match.groups()
        # Ignore all-uppercase placeholders such as <QUESTION>.
        if name.isupper():
            continue
        line = text.count("\n", 0, match.start()) + 1
        if self_closing:
            continue
        if closing:
            if not stack:
                errors.append(f"line {line}: closing tag </{name}> has no opening tag")
                continue
            open_name, open_line = stack.pop()
            if open_name != name:
                errors.append(
                    f"line {line}: closing tag </{name}> does not match "
                    f"<{open_name}> opened on line {open_line}"
                )
        else:
            stack.append((name, line))

    for name, line in reversed(stack):
        errors.append(f"line {line}: opening tag <{name}> is not closed")
    return errors


def lint_prompt(text: str, mode: str) -> dict[str, object]:
    coverage = {
        category: any_match(text, patterns)
        for category, patterns in CATEGORY_PATTERNS.items()
    }
    required = required_categories(mode, text)
    missing = [category for category in required if not coverage[category]]

    anti_patterns: list[dict[str, str]] = []
    for pattern, label, severity in ANTI_PATTERNS:
        if re.search(pattern, text, flags=re.IGNORECASE | re.DOTALL):
            anti_patterns.append({"label": label, "severity": severity})

    if re.search(r"\bbe concise\b", text, flags=re.IGNORECASE) and re.search(
        r"\b(?:exhaustive|extremely thorough|maximum detail)\b",
        text,
        flags=re.IGNORECASE,
    ):
        anti_patterns.append(
            {"label": "contradictory brevity and exhaustiveness rules", "severity": "medium"}
        )

    xml_errors = check_xml_balance(text)
    covered_required = len(required) - len(missing)
    score = round(100 * covered_required / max(len(required), 1))

    return {
        "mode": mode,
        "characters": len(text),
        "required_categories": required,
        "coverage": coverage,
        "missing_required": missing,
        "anti_patterns": anti_patterns,
        "xml_errors": xml_errors,
        "structural_score": score,
    }


def human_report(path: Path, report: dict[str, object], strict: bool) -> int:
    missing = report["missing_required"]
    anti_patterns = report["anti_patterns"]
    xml_errors = report["xml_errors"]
    high_risk = [item for item in anti_patterns if item["severity"] == "high"]

    failed = bool(xml_errors) or (strict and (bool(missing) or bool(high_risk)))
    status = "FAIL" if failed else ("WARN" if missing or anti_patterns else "PASS")

    print(f"{status}: {path}")
    print(f"Mode: {report['mode']}")
    print(f"Structural score: {report['structural_score']}/100")

    if missing:
        print("Missing required coverage:")
        for category in missing:
            print(f"  - {category.replace('_', ' ')}")

    if anti_patterns:
        print("Prompting anti-patterns:")
        for item in anti_patterns:
            print(f"  - [{item['severity']}] {item['label']}")

    if xml_errors:
        print("XML-like tag errors:")
        for error in xml_errors:
            print(f"  - {error}")

    if not missing and not anti_patterns and not xml_errors:
        print("No structural issues detected.")

    print("Note: this lint does not validate scientific claims, methods, or citations.")
    return 1 if failed else 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check the structure of a Claude Science research prompt."
    )
    parser.add_argument("prompt_file", type=Path, help="UTF-8 text or Markdown prompt file")
    parser.add_argument(
        "--mode",
        choices=("auto", "compact", "standard", "full"),
        default="auto",
        help="Coverage profile; default: infer from prompt complexity",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit nonzero for missing required coverage or high-risk anti-patterns",
    )
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of text")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        text = args.prompt_file.read_text(encoding="utf-8")
    except OSError as exc:
        print(f"error: cannot read {args.prompt_file}: {exc}", file=sys.stderr)
        return 2
    except UnicodeDecodeError as exc:
        print(f"error: {args.prompt_file} is not valid UTF-8: {exc}", file=sys.stderr)
        return 2

    if not text.strip():
        print(f"error: {args.prompt_file} is empty", file=sys.stderr)
        return 2

    mode = detect_mode(text) if args.mode == "auto" else args.mode
    report = lint_prompt(text, mode)

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
        if report["xml_errors"]:
            return 1
        if args.strict and (
            report["missing_required"]
            or any(item["severity"] == "high" for item in report["anti_patterns"])
        ):
            return 1
        return 0

    return human_report(args.prompt_file, report, args.strict)


if __name__ == "__main__":
    raise SystemExit(main())

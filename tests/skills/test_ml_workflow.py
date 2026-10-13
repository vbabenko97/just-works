#!/usr/bin/env python3
"""Package checks for the ML workflow skills: structure, links, templates, eval cases, and parity.

Standard library only. These checks are static; they do not show that an agent behaves as the
evaluation cases expect.
"""

from __future__ import annotations

import json
from pathlib import Path
import re
import sys

REPO = Path(__file__).resolve().parents[2]
SKILLS = (
    "ml-problem-and-data-audit",
    "ml-experiment-protocol",
    "ml-provenance-and-handoff",
    "scikit-learn",
)
TREES = (REPO / ".claude" / "skills", REPO / ".codex" / "skills")
REQUIRED_COVERAGE = {
    "post-outcome-leakage",
    "repeated-entity-row-split",
    "missing-forecast-horizon",
    "full-data-preprocessing",
    "gain-within-variability",
    "final-test-tuning",
    "missing-provenance",
    "unneeded-production-infrastructure",
    "group-and-time-split",
    "vision-or-document-duplicates",
    "deep-learning-reproducibility",
    "threshold-or-calibration-leakage",
    "valid-iid-workflow",
    "route-architecture",
    "route-design-review",
    "route-descriptive-analysis",
}
RUN_RECORD_KEYS = {
    "run_id",
    "status",
    "started_at",
    "finished_at",
    "runtime_seconds",
    "hypothesis",
    "command",
    "data",
    "split",
    "code",
    "environment",
    "config",
    "seeds",
    "metrics",
    "artifacts",
    "failure",
}
SPLIT_CONFIG_KEYS = {
    "strategy",
    "rationale",
    "unit_of_independence",
    "temporal",
    "seed",
    "assignments",
    "final_test",
    "checks",
}
EVAL_CASE_KEYS = {
    "id",
    "name",
    "covers",
    "should_trigger",
    "prompt",
    "expected_output",
    "expectations",
    "files",
}
FRONTMATTER_KEYS = {
    "name",
    "description",
    "license",
    "compatibility",
    "metadata",
    "allowed-tools",
}
LINK = re.compile(r"\[[^\]]*\]\(([^)\s]+)\)")
CHECKS: list[tuple[bool, str, str]] = []


def check(ok: bool, label: str, detail: str = "") -> None:
    CHECKS.append((ok, label, detail))
    print(f"{'ok  ' if ok else 'FAIL'}  {label}")
    if not ok and detail:
        print(f"        {detail}")


def tree(root: Path) -> dict[str, bytes]:
    return {
        str(path.relative_to(root)): path.read_bytes()
        for path in sorted(root.rglob("*"))
        if path.is_file() and path.name != ".DS_Store"
    }


def tree_differences(left: dict[str, bytes], right: dict[str, bytes]) -> list[str]:
    differences = sorted(set(left) ^ set(right))
    differences += sorted(
        name for name in set(left) & set(right) if left[name] != right[name]
    )
    return differences


def frontmatter(text: str) -> dict[str, str] | None:
    lines = text.splitlines()
    if not lines or lines[0] != "---" or "---" not in lines[1:]:
        return None
    end = lines.index("---", 1)
    fields: dict[str, str] = {}
    for line in lines[1:end]:
        if not line.strip() or line.startswith((" ", "\t")):
            continue
        key, _, value = line.partition(":")
        fields[key.strip()] = value.strip()
    return fields


def check_package(root: Path, name: str) -> None:
    label = f"{root.parent.name}/{name}"
    skill_md = root / "SKILL.md"
    if not skill_md.is_file():
        check(False, f"{label}: SKILL.md exists")
        return
    text = skill_md.read_text(encoding="utf-8")
    fields = frontmatter(text)
    check(fields is not None, f"{label}: SKILL.md has closed frontmatter")
    if fields is None:
        return
    check(
        fields.get("name") == name,
        f"{label}: frontmatter name matches directory",
        str(fields.get("name")),
    )
    description = fields.get("description", "")
    check(
        0 < len(description) <= 1024,
        f"{label}: description is 1-1024 characters",
        str(len(description)),
    )
    check(
        re.fullmatch(r"[a-z0-9]+(-[a-z0-9]+)*", name) is not None and len(name) <= 64,
        f"{label}: name follows the Agent Skills naming rule",
    )
    check(
        set(fields) <= FRONTMATTER_KEYS,
        f"{label}: only known frontmatter keys",
        str(sorted(fields)),
    )
    check(len(text.splitlines()) < 500, f"{label}: SKILL.md stays under 500 lines")
    check((root / "SOURCES.md").is_file(), f"{label}: SOURCES.md exists")
    sources = (
        (root / "SOURCES.md").read_text(encoding="utf-8")
        if (root / "SOURCES.md").is_file()
        else ""
    )
    check(
        "## Authorship" in sources and "https://" in sources,
        f"{label}: SOURCES.md records authorship and source URLs",
    )

    linked: set[Path] = set()
    broken: list[str] = []
    for markdown in sorted(root.rglob("*.md")):
        for target in LINK.findall(markdown.read_text(encoding="utf-8")):
            if target.startswith(("http://", "https://", "#", "mailto:")):
                continue
            resolved = (markdown.parent / target.split("#", 1)[0]).resolve()
            if not resolved.is_relative_to(root.resolve()) or not resolved.is_file():
                broken.append(f"{markdown.relative_to(root)} -> {target}")
            else:
                linked.add(resolved)
    check(
        not broken,
        f"{label}: relative links resolve inside the package",
        "; ".join(broken),
    )
    resources = [
        path.resolve()
        for folder in ("assets", "references")
        if (root / folder).is_dir()
        for path in sorted((root / folder).rglob("*"))
        if path.is_file() and path.name != ".DS_Store"
    ]
    orphans = [
        str(path.relative_to(root.resolve()))
        for path in resources
        if path not in linked
    ]
    check(
        not orphans, f"{label}: every asset and reference is linked", ", ".join(orphans)
    )

    templates = (
        sorted((root / "assets").glob("*.json")) if (root / "assets").is_dir() else []
    )
    for template in templates:
        try:
            json.loads(template.read_text(encoding="utf-8"))
            check(True, f"{label}: {template.name} is valid JSON")
        except json.JSONDecodeError as error:
            check(False, f"{label}: {template.name} is valid JSON", str(error))


def check_templates() -> None:
    root = TREES[0]
    run = json.loads(
        (root / "ml-provenance-and-handoff" / "assets" / "run.json").read_text(
            encoding="utf-8"
        )
    )
    missing = RUN_RECORD_KEYS - set(run)
    check(not missing, "run.json has every required field", ", ".join(sorted(missing)))
    check(
        {"identity_method", "identity"} <= set(run.get("data", {}))
        and "assignments_sha256" in run.get("split", {})
        and {"revision", "dirty", "dirty_evidence", "source_snapshot"}
        <= set(run.get("code", {})),
        "run.json records data identity, split identity, revision, dirty state, and source snapshot",
    )
    split = json.loads(
        (root / "ml-problem-and-data-audit" / "assets" / "split-config.json").read_text(
            encoding="utf-8"
        )
    )
    missing = SPLIT_CONFIG_KEYS - set(split)
    check(
        not missing,
        "split-config.json has every required field",
        ", ".join(sorted(missing)),
    )
    check(
        {"path", "sha256"} <= set(split.get("assignments", {}))
        and "access_log" in split.get("final_test", {}),
        "split-config.json persists assignments and logs final-test access",
    )


def check_evals() -> set[str]:
    covered: set[str] = set()
    for name in SKILLS:
        root = TREES[0] / name
        path = root / "evals" / "evals.json"
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as error:
            check(False, f"{name}: evals.json loads", str(error))
            continue
        check(data.get("skill_name") == name, f"{name}: evals.json names its skill")
        check(
            {"positive_cases", "negative_cases", "pass_rule"}
            <= set(data.get("evaluation_protocol", {})),
            f"{name}: evals.json states the evaluation protocol",
        )
        cases = data.get("evals", [])
        check(bool(cases), f"{name}: evals.json has cases")
        ids = [case.get("id") for case in cases]
        check(len(ids) == len(set(ids)), f"{name}: case IDs are unique")
        for case in cases:
            case_label = f"{name} case {case.get('id')}"
            missing = EVAL_CASE_KEYS - set(case)
            check(
                not missing,
                f"{case_label}: has every field",
                ", ".join(sorted(missing)),
            )
            if missing:
                continue
            check(
                isinstance(case["id"], int)
                and isinstance(case["should_trigger"], bool)
                and isinstance(case["prompt"], str)
                and case["prompt"].strip() != ""
                and isinstance(case["expectations"], list)
                and len(case["expectations"]) > 0
                and all(
                    isinstance(item, str) and item.strip()
                    for item in case["expectations"]
                )
                and isinstance(case["covers"], list)
                and len(case["covers"]) > 0,
                f"{case_label}: fields have the expected types",
            )
            missing_files = [
                item for item in case["files"] if not (root / item).is_file()
            ]
            check(
                not missing_files,
                f"{case_label}: input files exist",
                ", ".join(missing_files),
            )
            routing = any(tag.startswith("route-") for tag in case["covers"])
            check(
                routing == (case["should_trigger"] is False),
                f"{case_label}: routing cases and only routing cases are negative",
            )
            covered.update(case["covers"])
    missing = REQUIRED_COVERAGE - covered
    check(
        not missing,
        "eval cases cover every required trap and routing boundary",
        ", ".join(sorted(missing)),
    )
    return covered


def check_parity() -> None:
    known = {"SKILL.md": b"a", "assets/x.json": b"{}"}
    changed = dict(known, **{"SKILL.md": b"b"})
    extra = dict(known, **{"extra.md": b""})
    check(
        tree_differences(known, changed) == ["SKILL.md"]
        and tree_differences(known, extra) == ["extra.md"],
        "tree comparison reports a known content difference and a known extra file",
    )
    for name in SKILLS:
        claude, codex = (root / name for root in TREES)
        if not (claude.is_dir() and codex.is_dir()):
            check(False, f"{name}: present in both provider trees")
            continue
        differences = tree_differences(tree(claude), tree(codex))
        check(
            not differences,
            f"{name}: provider trees are identical",
            ", ".join(differences),
        )


def ml_section(path: Path) -> str:
    text = path.read_text(encoding="utf-8")
    match = re.search(
        r"^## Machine learning\n(.*?)(?=^## )", text, flags=re.DOTALL | re.MULTILINE
    )
    return match.group(1) if match else ""


def check_integration() -> None:
    claude_section = ml_section(REPO / "CLAUDE.md")
    agents_section = ml_section(REPO / "AGENTS.md")
    check(bool(claude_section), "CLAUDE.md has a Machine learning section")
    check(
        claude_section == agents_section,
        "CLAUDE.md and AGENTS.md carry the same Machine learning section",
    )
    check(
        all(name in claude_section for name in SKILLS),
        "the Machine learning section names all four skills",
    )
    for document in ("README.md", "docs/architecture.md"):
        text = (REPO / document).read_text(encoding="utf-8")
        missing = [name for name in SKILLS if f"`{name}`" not in text]
        check(not missing, f"{document} lists all four skills", ", ".join(missing))


def main() -> int:
    for root in TREES:
        for name in SKILLS:
            check_package(root / name, name)
    check_templates()
    check_evals()
    check_parity()
    check_integration()
    passed = sum(ok for ok, _, _ in CHECKS)
    print(f"\n{passed}/{len(CHECKS)} passed")
    return 0 if passed == len(CHECKS) else 1


if __name__ == "__main__":
    sys.exit(main())

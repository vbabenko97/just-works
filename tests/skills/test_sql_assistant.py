#!/usr/bin/env python3
"""Package checks for the sql-assistant skill: frontmatter, reference reachability, dialect
coverage, evaluation cases, provider parity, and installation into a temporary home.

Standard library only. These checks are static; they do not show that an agent behaves as the
evaluation cases expect, and they do not run SQL against any database.
"""

from __future__ import annotations

from collections import deque
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile

REPO = Path(__file__).resolve().parents[2]
NAME = "sql-assistant"
TREES = (REPO / ".claude" / "skills" / NAME, REPO / ".codex" / "skills" / NAME)
SHARED = (
    "universal-correctness.md",
    "safety-and-execution.md",
    "performance-workflow.md",
    "validation-tools.md",
)
# Overlay file -> official documentation hosts its citations may use.
OVERLAYS = {
    "postgres.md": {"www.postgresql.org"},
    "mysql.md": {"dev.mysql.com"},
    "mariadb.md": {"mariadb.com"},
    "sqlserver.md": {"learn.microsoft.com"},
    "oracle.md": {"docs.oracle.com"},
    "sqlite.md": {"www.sqlite.org", "sqlite.org"},
    "bigquery.md": {"cloud.google.com", "docs.cloud.google.com"},
    "snowflake.md": {"docs.snowflake.com"},
    "duckdb.md": {"duckdb.org"},
}
REQUIRED_COVERAGE = {
    # Scenarios from the research brief.
    "schema-invention",
    "join-cardinality",
    "nullable-anti-join",
    "deterministic-pagination",
    "driver-binding",
    "mysql-mariadb-difference",
    "dst-boundary",
    "execution-bearing-analysis",
    "unsupported-speedup-claim",
    "analytics-indexing",
    # Plan and maintenance commands that are not harmless reads.
    "oracle-explain-plan-writes",
    "mysql-state-changing-analysis",
    "sqlite-explain-pragma",
    "bigquery-script-dry-run",
    # Activation boundaries and input quality.
    "activation-direct",
    "activation-indirect",
    "incomplete-input",
    "non-activation",
} | {f"overlay-{Path(name).stem}" for name in OVERLAYS}
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
EVALUATION_PROTOCOL_KEYS = {
    "setup",
    "positive_cases",
    "negative_cases",
    "pass_rule",
    "limits",
    "authorization",
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
        if path.is_file()
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


def links(markdown: Path) -> list[str]:
    return LINK.findall(markdown.read_text(encoding="utf-8"))


def check_skill_md(root: Path) -> None:
    text = (root / "SKILL.md").read_text(encoding="utf-8")
    fields = frontmatter(text)
    check(fields is not None, "SKILL.md has closed frontmatter")
    if fields is None:
        return
    check(
        fields.get("name") == NAME,
        "frontmatter name matches the directory",
        str(fields.get("name")),
    )
    check(
        re.fullmatch(r"[a-z0-9]+(-[a-z0-9]+)*", NAME) is not None and len(NAME) <= 64,
        "name follows the Agent Skills naming rule",
    )
    description = fields.get("description", "")
    check(
        0 < len(description) <= 1024,
        "description is 1-1024 characters",
        str(len(description)),
    )
    check(
        set(fields) <= FRONTMATTER_KEYS,
        "frontmatter uses supported keys",
        str(sorted(fields)),
    )
    check(len(text.splitlines()) < 500, "SKILL.md stays under 500 lines")
    sources = root / "SOURCES.md"
    sources_text = sources.read_text(encoding="utf-8") if sources.is_file() else ""
    check(bool(sources_text.strip()), "SOURCES.md exists and is not empty")


def check_links(root: Path) -> None:
    broken: list[str] = []
    graph: dict[Path, set[Path]] = {}
    for markdown in sorted(root.rglob("*.md")):
        targets: set[Path] = set()
        for link_target in links(markdown):
            if link_target.startswith(("http://", "https://", "#", "mailto:")):
                continue
            resolved = (markdown.parent / link_target.split("#", 1)[0]).resolve()
            if not resolved.is_relative_to(root.resolve()) or not resolved.is_file():
                broken.append(f"{markdown.relative_to(root)} -> {link_target}")
            else:
                targets.add(resolved)
        graph[markdown.resolve()] = targets
    check(not broken, "relative links resolve inside the package", "; ".join(broken))

    start = (root / "SKILL.md").resolve()
    reached: set[Path] = {start}
    queue: deque[Path] = deque([start])
    while queue:
        for linked_path in graph.get(queue.popleft(), set[Path]()):
            if linked_path not in reached:
                reached.add(linked_path)
                queue.append(linked_path)
    references = sorted(
        path.resolve() for path in (root / "references").rglob("*") if path.is_file()
    )
    unreachable = [
        str(path.relative_to(root.resolve()))
        for path in references
        if path not in reached
    ]
    check(
        not unreachable,
        "every reference is reachable from SKILL.md",
        ", ".join(unreachable),
    )
    direct = {
        (root / target.split("#", 1)[0]).resolve()
        for target in links(root / "SKILL.md")
        if not target.startswith(("http://", "https://", "#"))
    }
    missing = [
        name
        for name in (*SHARED, *OVERLAYS)
        if (root / "references" / name).resolve() not in direct
    ]
    check(
        not missing,
        "SKILL.md links every shared reference and overlay directly",
        ", ".join(missing),
    )


def check_overlays(root: Path) -> None:
    for name in SHARED:
        path = root / "references" / name
        check(path.is_file(), f"shared reference {name} exists")
    for name, hosts in OVERLAYS.items():
        path = root / "references" / name
        if not path.is_file():
            check(False, f"overlay {name} exists")
            continue
        text = path.read_text(encoding="utf-8")
        external = [
            target
            for target in links(path)
            if target.startswith(("http://", "https://"))
        ]
        foreign = [
            target
            for target in external
            if re.sub(r"^https?://([^/]+).*$", r"\1", target) not in hosts
        ]
        check(bool(text.strip()), f"overlay {name} is not empty")
        check(bool(external), f"overlay {name} links to documentation")
        check(
            not foreign,
            f"overlay {name} cites only official documentation hosts",
            ", ".join(foreign),
        )
        check(
            all(target.startswith("https://") for target in external),
            f"overlay {name} uses HTTPS links",
        )


def check_evals(root: Path) -> None:
    path = root / "evals" / "evals.json"
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        check(False, "evals.json loads", str(error))
        return
    if not isinstance(data, dict):
        check(False, "evals.json has an object at its top level", type(data).__name__)
        return
    check(data.get("schema_version") == "1.0", "evals.json has schema version 1.0")
    check(data.get("skill_name") == NAME, "evals.json names its skill")
    check(
        isinstance(data.get("description"), str) and bool(data["description"].strip()),
        "evals.json has a nonempty description",
    )
    protocol = data.get("evaluation_protocol")
    check(
        isinstance(protocol, dict)
        and all(
            isinstance(protocol.get(key), str) and bool(protocol[key].strip())
            for key in EVALUATION_PROTOCOL_KEYS
        ),
        "evals.json has a complete evaluation protocol",
    )
    cases = data.get("evals", [])
    check(isinstance(cases, list) and bool(cases), "evals.json has cases")
    if not isinstance(cases, list):
        return
    objects = [case for case in cases if isinstance(case, dict)]
    check(len(objects) == len(cases), "eval cases are objects")
    ids = [case.get("id") for case in objects]
    names = [case.get("name") for case in objects]
    check(
        all(type(case_id) is int for case_id in ids) and len(ids) == len(set(ids)),
        "case IDs are unique integers",
    )
    check(
        all(isinstance(name, str) and bool(name.strip()) for name in names)
        and len(names) == len(set(names)),
        "case names are unique nonempty strings",
    )
    covered: set[str] = set()
    for case in objects:
        label = f"case {case.get('id')}"
        missing = EVAL_CASE_KEYS - set(case)
        check(not missing, f"{label}: has every field", ", ".join(sorted(missing)))
        if missing:
            continue
        check(
            type(case["id"]) is int
            and isinstance(case["name"], str)
            and bool(case["name"].strip())
            and isinstance(case["should_trigger"], bool)
            and isinstance(case["prompt"], str)
            and case["prompt"].strip() != ""
            and isinstance(case["expected_output"], str)
            and bool(case["expected_output"].strip())
            and isinstance(case["expectations"], list)
            and len(case["expectations"]) > 0
            and all(
                isinstance(item, str) and item.strip() for item in case["expectations"]
            )
            and isinstance(case["covers"], list)
            and len(case["covers"]) > 0
            and all(
                isinstance(item, str) and bool(item.strip()) for item in case["covers"]
            )
            and isinstance(case["files"], list),
            f"{label}: fields have the expected types",
        )
        files = case["files"] if isinstance(case["files"], list) else []
        missing_files = [
            item
            for item in files
            if not isinstance(item, str)
            or not (root / item).resolve().is_relative_to(root.resolve())
            or not (root / item).resolve().is_file()
        ]
        check(
            isinstance(case["files"], list) and not missing_files,
            f"{label}: input files exist",
            ", ".join(str(item) for item in missing_files),
        )
        covers = case["covers"] if isinstance(case["covers"], list) else []
        valid_covers = all(
            isinstance(item, str) and bool(item.strip()) for item in covers
        )
        check(valid_covers, f"{label}: coverage tags are nonempty strings")
        check(
            isinstance(case["covers"], list)
            and ("non-activation" in covers) == (case["should_trigger"] is False),
            f"{label}: non-activation cases and only those are negative",
        )
        if valid_covers:
            covered.update(covers)
    missing = REQUIRED_COVERAGE - covered
    check(
        not missing,
        "eval cases cover every required scenario, overlay, and boundary",
        ", ".join(sorted(missing)),
    )
    unknown = covered - REQUIRED_COVERAGE - {"dialect-conversion", "upsert-duplicates"}
    check(
        not unknown,
        "eval cases use only known coverage tags",
        ", ".join(sorted(unknown)),
    )


def check_parity() -> None:
    known = {"SKILL.md": b"a", "references/x.md": b"x"}
    check(
        tree_differences(known, dict(known, **{"SKILL.md": b"b"})) == ["SKILL.md"]
        and tree_differences(known, dict(known, **{"extra.md": b""})) == ["extra.md"],
        "tree comparison reports a known content difference and a known extra file",
    )
    claude, codex = TREES
    if not (claude.is_dir() and codex.is_dir()):
        check(False, "package is present in both provider trees")
        return
    differences = tree_differences(tree(claude), tree(codex))
    check(not differences, "provider trees are identical", ", ".join(differences))


def check_install() -> None:
    home = Path(tempfile.mkdtemp(prefix="jw-sql-assistant-"))
    try:
        environment = dict(os.environ, HOME=str(home))
        proc = subprocess.run(
            [
                "bash",
                str(REPO / "install.sh"),
                "--no-backup",
                "--skip-config",
                "--skip-statusline",
            ],
            capture_output=True,
            text=True,
            input="",
            timeout=120,
            env=environment,
        )
        check(
            proc.returncode == 0,
            "installer exits 0 in a temporary home",
            proc.stderr[-300:],
        )
        for source, installed in (
            (TREES[0], home / ".claude" / "skills" / NAME),
            (TREES[1], home / ".agents" / "skills" / NAME),
        ):
            differences = (
                tree_differences(tree(source), tree(installed))
                if installed.is_dir()
                else ["<missing>"]
            )
            check(
                not differences,
                f"installed {installed.relative_to(home)} matches {source.relative_to(REPO)}",
                ", ".join(differences),
            )
    finally:
        shutil.rmtree(home, ignore_errors=True)


def main() -> int:
    root = TREES[0]
    if not (root / "SKILL.md").is_file():
        check(False, "SKILL.md exists")
    else:
        check_skill_md(root)
        check_links(root)
        check_overlays(root)
        check_evals(root)
    check_parity()
    check_install()
    passed = sum(ok for ok, _, _ in CHECKS)
    print(f"\n{passed}/{len(CHECKS)} passed")
    return 0 if passed == len(CHECKS) else 1


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""bulk_mutate.py must refuse when the world changed between plan and apply.

A plan that enumerates targets is only worth something if the targets are still
what they were when they were enumerated. Three substitutions matter and each is
tested here, plus the control case where nothing changed:

  content addition       a new file, or an empty directory, appears inside a
                         planned directory
  symlink substitution   a planned file becomes a symlink, or a planned symlink
                         is retargeted
  directory replacement  a planned directory becomes a file, or a different
                         directory

Every case runs `apply --dry-run`, so a bug in this test cannot delete anything.
"""
from __future__ import annotations

import json
import os
import pathlib
import shutil
import subprocess
import sys
import tempfile

REPO = pathlib.Path(__file__).resolve().parents[2]
TOOL = REPO / "scripts" / "verify" / "bulk_mutate.py"


def run(*args: str) -> dict:
    proc = subprocess.run([sys.executable, str(TOOL), *args], cwd=str(REPO),
                          capture_output=True, text=True, timeout=60)
    try:
        return json.loads(proc.stdout)
    except json.JSONDecodeError:
        raise SystemExit(f"bulk_mutate produced no JSON: {proc.stdout}{proc.stderr}")


def build(root: pathlib.Path) -> None:
    """A small tree: two directories with content, one plain file, one symlink."""
    (root / "skill-a" / "references").mkdir(parents=True)
    (root / "skill-a" / "SKILL.md").write_text("a\n")
    (root / "skill-a" / "references" / "helper.md").write_text("helper\n")
    (root / "skill-b").mkdir()
    (root / "skill-b" / "SKILL.md").write_text("b\n")
    (root / "plain.md").write_text("plain\n")
    (root / "elsewhere.md").write_text("plain\n")
    (root / "link").symlink_to(root / "plain.md")


def scenario(name: str, targets, mutate, expect_reason: str) -> tuple[str, bool, str]:
    root = pathlib.Path(tempfile.mkdtemp(prefix="jw-drift-"))
    try:
        tree = root / "tree"
        tree.mkdir()
        build(tree)
        plan_path = root / "plan.json"
        planned = run("plan", "--operation", "delete", "--root", str(tree),
                      "--max", "10", "--plan", str(plan_path),
                      *[str(tree / t) for t in targets])
        if planned.get("status") != "planned":
            return (name, False, f"planning failed: {planned}")
        mutate(tree)
        applied = run("apply", "--plan", str(plan_path), "--dry-run")
        reason = applied.get("reason", "") or applied.get("status", "")
        ok = expect_reason in reason
        return (name, ok, json.dumps(applied)[:220])
    finally:
        shutil.rmtree(root, ignore_errors=True)


def add_file(tree: pathlib.Path) -> None:
    (tree / "skill-a" / "references" / "added.md").write_text("new\n")


def add_empty_dir(tree: pathlib.Path) -> None:
    (tree / "skill-a" / "brand-new-empty").mkdir()


def append_to_file(tree: pathlib.Path) -> None:
    with open(tree / "plain.md", "a") as fh:
        fh.write("appended\n")


def file_to_symlink(tree: pathlib.Path) -> None:
    # Same bytes at the far end, so only the type reveals the substitution.
    os.remove(tree / "plain.md")
    (tree / "plain.md").symlink_to(tree / "elsewhere.md")


def retarget_symlink(tree: pathlib.Path) -> None:
    os.remove(tree / "link")
    (tree / "link").symlink_to(tree / "elsewhere.md")


def dir_to_file(tree: pathlib.Path) -> None:
    shutil.rmtree(tree / "skill-b")
    (tree / "skill-b").write_text("not a directory any more\n")


def dir_to_other_dir(tree: pathlib.Path) -> None:
    shutil.rmtree(tree / "skill-b")
    (tree / "skill-b").mkdir()
    (tree / "skill-b" / "SKILL.md").write_text("different content\n")


def dir_to_symlink(tree: pathlib.Path) -> None:
    shutil.rmtree(tree / "skill-b")
    (tree / "skill-b").symlink_to(tree / "skill-a")


def remove_target(tree: pathlib.Path) -> None:
    shutil.rmtree(tree / "skill-b")


def nothing(tree: pathlib.Path) -> None:
    return None


SCENARIOS = [
    ("content addition: new file inside a planned directory",
     ["skill-a"], add_file, "changed between planning and execution"),
    ("content addition: empty directory inside a planned directory",
     ["skill-a"], add_empty_dir, "changed between planning and execution"),
    ("content addition: bytes appended to a planned file",
     ["plain.md"], append_to_file, "changed between planning and execution"),
    ("symlink substitution: planned file replaced by a symlink",
     ["plain.md"], file_to_symlink, "changed type"),
    ("symlink substitution: planned symlink retargeted",
     ["link"], retarget_symlink, "changed between planning and execution"),
    ("directory replacement: planned directory replaced by a file",
     ["skill-b"], dir_to_file, "changed type"),
    ("directory replacement: planned directory replaced by another directory",
     ["skill-b"], dir_to_other_dir, "changed between planning and execution"),
    ("directory replacement: planned directory replaced by a symlink",
     ["skill-b"], dir_to_symlink, "changed type"),
    ("planned target removed before apply",
     ["skill-b"], remove_target, "changed type"),
    # Control: an unchanged world must still be applyable, or every refusal above
    # would prove nothing.
    ("control: nothing changed",
     ["skill-a", "skill-b"], nothing, "dry_run_ok"),
]


def main() -> int:
    failures = []
    print(f"{'RESULT':7} SCENARIO")
    print("-" * 78)
    for name, targets, mutate, expect in SCENARIOS:
        _, ok, detail = scenario(name, targets, mutate, expect)
        print(f"{'ok' if ok else 'FAIL':7} {name}")
        if not ok:
            failures.append((name, expect, detail))
    print(f"\n{len(SCENARIOS) - len(failures)}/{len(SCENARIOS)} passed")
    for name, expect, detail in failures:
        print(f"  FAIL {name}\n       expected reason to contain {expect!r}\n       got: {detail}")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())

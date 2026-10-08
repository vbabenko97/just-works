#!/usr/bin/env python3
"""Regression test: the global installer must never write into project skill roots."""

from __future__ import annotations

import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

REPO = Path(__file__).resolve().parents[2]
ROOT_NAMES = (".claude", ".codex", ".agents")
CHECKS: list[tuple[bool, str, str]] = []


def check(ok: bool, label: str, detail: str = "") -> None:
    CHECKS.append((ok, label, detail))
    print(f"{'ok  ' if ok else 'FAIL'}  {label}")
    if not ok and detail:
        print(f"        {detail}")


def snapshot(root: Path) -> dict[str, bytes | None]:
    result: dict[str, bytes | None] = {}
    for path in sorted(root.rglob("*")):
        relative = str(path.relative_to(root))
        result[relative] = path.read_bytes() if path.is_file() else None
    return result


def run_install(home: Path, *flags: str) -> subprocess.CompletedProcess[str]:
    environment = os.environ.copy()
    environment["HOME"] = str(home)
    home.mkdir(parents=True, exist_ok=True)
    return subprocess.run(
        ["bash", str(REPO / "install.sh"), "--no-backup", *flags],
        capture_output=True,
        text=True,
        input="",
        timeout=120,
        env=environment,
    )


def add_project_skill_roots(home: Path) -> tuple[Path, dict[str, bytes | None]]:
    project = home / "projects" / "sample"
    for name in ROOT_NAMES:
        skills = project / name / "skills"
        skills.mkdir(parents=True)
        (skills / "local-skill.txt").write_text(f"{name} stays local\n")
        (skills / "owned-stale.txt").write_text(f"{name} manifest entry stays local\n")
    return project, snapshot(project)


def main() -> int:
    temporary_root = Path(tempfile.mkdtemp(prefix="jw-no-project-sync-"))
    try:
        rejected_home = temporary_root / "rejected-home"
        _, before = add_project_skill_roots(rejected_home)
        (rejected_home / ".just-works-manifest").write_text(
            "\n".join(
                str(
                    rejected_home
                    / "projects"
                    / "sample"
                    / name
                    / "skills"
                    / "owned-stale.txt"
                )
                for name in ROOT_NAMES
            )
            + "\n"
        )
        before = snapshot(rejected_home)

        for flags in (("--repos",), ("--repos", "--dry-run"), ("--repos", "--prune")):
            proc = run_install(rejected_home, *flags)
            flag_text = " ".join(flags)
            check(
                proc.returncode != 0,
                f"{flag_text} exits non-zero",
                f"exit {proc.returncode}",
            )
            check(
                snapshot(rejected_home) == before,
                f"{flag_text} leaves the entire home unchanged",
            )
            message = proc.stderr.lower()
            check(
                "--repos" in message and "global" in message,
                f"{flag_text} explains shared skills install globally",
            )

        control_home = temporary_root / "global-home"
        project, project_before = add_project_skill_roots(control_home)
        for name in ROOT_NAMES:
            skills = control_home / name / "skills"
            skills.mkdir(parents=True)
            (skills / "local-skill.txt").write_text(f"{name} global custom skill\n")
            (skills / "obsolete.txt").write_text(f"{name} stale global skill\n")

        project_manifest_entries = [
            str(project / name / "skills" / "owned-stale.txt") for name in ROOT_NAMES
        ]
        (control_home / ".just-works-manifest").write_text(
            "\n".join(
                [
                    str(control_home / ".claude" / "skills" / "obsolete.txt"),
                    str(control_home / ".agents" / "skills" / "obsolete.txt"),
                    *project_manifest_entries,
                ]
            )
            + "\n"
        )
        proc = run_install(
            control_home, "--prune", "--skip-config", "--skip-statusline"
        )
        check(
            proc.returncode == 0,
            "global install with --prune exits 0",
            proc.stderr[-300:],
        )
        check(
            not (control_home / ".claude" / "skills" / "obsolete.txt").exists(),
            "global Claude stale entry is pruned",
        )
        check(
            not (control_home / ".agents" / "skills" / "obsolete.txt").exists(),
            "global agents stale entry is pruned",
        )
        for name in ROOT_NAMES:
            check(
                (control_home / name / "skills" / "local-skill.txt").exists(),
                f"{name} global custom skill is preserved",
            )
        check(
            snapshot(project) == project_before,
            "global install and prune preserve all project skill roots",
        )
        manifest_entries = set(
            (control_home / ".just-works-manifest").read_text().splitlines()
        )
        check(
            all(entry in manifest_entries for entry in project_manifest_entries),
            "global install and prune preserve project manifest entries",
        )
        check(
            (control_home / ".claude" / "skills" / "lossless-doc-compress").is_dir(),
            "global Claude skills install",
        )
        check(
            (control_home / ".agents" / "skills" / "lossless-doc-compress").is_dir(),
            "global Codex skills install",
        )
    finally:
        shutil.rmtree(temporary_root, ignore_errors=True)

    passed = sum(ok for ok, _, _ in CHECKS)
    print(f"\n{passed}/{len(CHECKS)} passed")
    return 0 if passed == len(CHECKS) else 1


if __name__ == "__main__":
    sys.exit(main())

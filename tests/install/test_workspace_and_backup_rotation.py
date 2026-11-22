#!/usr/bin/env python3
"""Regression test: install.sh skips skill-creator workspaces and rotates its backups.

Runs the installer from a minimal copy of the repository, against temporary homes, so the
real source tree and the real home directory are never involved.
"""

from __future__ import annotations

import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile

REPO = Path(__file__).resolve().parents[2]
STAMP = re.compile(r"^\d{8}_\d{6}$")
OLD_BACKUPS = ("20200101_000000", "20200102_000000", "20200103_000000", "20200104_000000")
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


def make_source(root: Path) -> Path:
    """A repository copy with one skill and its workspace on each provider side."""
    source = root / "source"
    source.mkdir()
    shutil.copy2(REPO / "install.sh", source / "install.sh")
    for side in (".claude", ".codex"):
        skills = source / side / "skills"
        (skills / "demo").mkdir(parents=True)
        (skills / "demo" / "SKILL.md").write_text("---\nname: demo\n---\n")
        (skills / "demo-workspace" / "iteration-1").mkdir(parents=True)
        (skills / "demo-workspace" / "iteration-1" / "output.md").write_text("eval run\n")
    return source


def run_install(source: Path, home: Path, *flags: str) -> subprocess.CompletedProcess[str]:
    environment = os.environ.copy()
    environment["HOME"] = str(home)
    home.mkdir(parents=True, exist_ok=True)
    return subprocess.run(
        ["bash", str(source / "install.sh"), "--skip-config", "--skip-statusline", *flags],
        capture_output=True,
        text=True,
        input="",
        timeout=120,
        env=environment,
    )


def home_with_old_backups(root: Path, name: str) -> Path:
    home = root / name
    (home / ".claude" / "skills").mkdir(parents=True)
    (home / ".claude" / "skills" / "user-skill.txt").write_text("user owned\n")
    backups = home / "just-works-backups"
    for stamp in OLD_BACKUPS:
        (backups / stamp).mkdir(parents=True)
        (backups / stamp / "marker.txt").write_text(stamp)
    (backups / "manual-copy").mkdir()
    (backups / "20200101_000000-note").mkdir()
    return home


def stamps(home: Path) -> list[str]:
    backups = home / "just-works-backups"
    return sorted(p.name for p in backups.iterdir() if p.is_dir() and STAMP.match(p.name))


def check_workspaces(source: Path, root: Path) -> None:
    home = root / "fresh-home"
    proc = run_install(source, home, "--no-backup")
    check(proc.returncode == 0, "fresh install exits 0", proc.stderr[-300:])
    for side in (".claude", ".agents"):
        skills = home / side / "skills"
        check((skills / "demo" / "SKILL.md").is_file(), f"{side} skill is installed")
        check(not (skills / "demo-workspace").exists(), f"{side} workspace is not installed")
    manifest = (home / ".just-works-manifest").read_text().splitlines()
    check(not any(line.endswith("-workspace") for line in manifest),
          "manifest does not claim workspaces", str(manifest))

    home = root / "upgrade-home"
    claude_skills = home / ".claude" / "skills"
    (claude_skills / "demo-workspace").mkdir(parents=True)
    (claude_skills / "demo-workspace" / "old.md").write_text("installed by an earlier run\n")
    (claude_skills / "mine-workspace").mkdir()
    (home / ".just-works-manifest").write_text(f"{claude_skills / 'demo-workspace'}\n")

    proc = run_install(source, home, "--no-backup", "--claude-only")
    check(proc.returncode == 0, "upgrade without --prune exits 0", proc.stderr[-300:])
    check((claude_skills / "demo-workspace").is_dir(), "without --prune an installed workspace stays")
    check("demo-workspace" in proc.stdout, "an installed workspace is reported as stale", proc.stdout[-600:])
    manifest = (home / ".just-works-manifest").read_text().splitlines()
    check(str(claude_skills / "demo-workspace") in manifest,
          "a run without --prune keeps ownership of the stale workspace", str(manifest))

    proc = run_install(source, home, "--no-backup", "--claude-only", "--prune")
    check(proc.returncode == 0, "upgrade with --prune exits 0", proc.stderr[-300:])
    check(not (claude_skills / "demo-workspace").exists(), "--prune removes an installed workspace")
    check((claude_skills / "mine-workspace").is_dir(), "--prune keeps a workspace the installer never shipped")


def check_rotation(source: Path, root: Path) -> None:
    home = home_with_old_backups(root, "default-home")
    proc = run_install(source, home, "--claude-only")
    check(proc.returncode == 0, "install with backups exits 0", proc.stderr[-300:])
    kept = stamps(home)
    check(len(kept) == 3, "default keeps the newest 3 installer backups", str(kept))
    check(kept[:2] == list(OLD_BACKUPS[2:]), "the two oldest backups are removed", str(kept))
    check(not kept[-1].startswith("2020"), "this run's backup is kept", str(kept))
    backups = home / "just-works-backups"
    check((backups / "manual-copy").is_dir(), "a user directory in the backup root is kept")
    check((backups / "20200101_000000-note").is_dir(), "a near-miss timestamp name is kept")

    home = home_with_old_backups(root, "keep-one-home")
    proc = run_install(source, home, "--claude-only", "--keep-backups", "1")
    kept = stamps(home)
    check(proc.returncode == 0 and len(kept) == 1 and not kept[0].startswith("2020"),
          "--keep-backups 1 keeps only this run's backup", str(kept))

    home = home_with_old_backups(root, "keep-all-home")
    proc = run_install(source, home, "--claude-only", "--keep-backups", "0")
    check(proc.returncode == 0 and len(stamps(home)) == len(OLD_BACKUPS) + 1,
          "--keep-backups 0 keeps every backup", str(stamps(home)))

    home = home_with_old_backups(root, "no-backup-home")
    proc = run_install(source, home, "--claude-only", "--no-backup")
    check(proc.returncode == 0 and stamps(home) == list(OLD_BACKUPS),
          "--no-backup leaves existing backups alone", str(stamps(home)))

    home = home_with_old_backups(root, "dry-run-home")
    before = snapshot(home)
    proc = run_install(source, home, "--claude-only", "--dry-run")
    check(proc.returncode == 0 and snapshot(home) == before, "--dry-run changes nothing")
    check("Would remove old installer backups" in proc.stdout and "20200102_000000" in proc.stdout
          and "20200103_000000" not in proc.stdout,
          "--dry-run names the backups a real run would remove", proc.stdout[-600:])

    home = home_with_old_backups(root, "invalid-home")
    before = snapshot(home)
    for value in ("x", "-1"):
        proc = run_install(source, home, "--claude-only", "--keep-backups", value)
        check(proc.returncode != 0 and snapshot(home) == before,
              f"--keep-backups {value} is refused before installing", proc.stderr[-300:])
    proc = run_install(source, home, "--claude-only", "--keep-backups")
    check(proc.returncode != 0 and snapshot(home) == before,
          "--keep-backups without a value is refused", proc.stderr[-300:])


def main() -> int:
    root = Path(tempfile.mkdtemp(prefix="jw-install-rotation-"))
    try:
        source = make_source(root)
        check_workspaces(source, root)
        check_rotation(source, root)
    finally:
        shutil.rmtree(root, ignore_errors=True)

    passed = sum(ok for ok, _, _ in CHECKS)
    print(f"\n{passed}/{len(CHECKS)} passed")
    return 0 if passed == len(CHECKS) else 1


if __name__ == "__main__":
    sys.exit(main())

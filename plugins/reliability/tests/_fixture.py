#!/usr/bin/env python3
"""Shared fixtures: throwaway repositories in the three policy states."""
from __future__ import annotations

import hashlib
import json
import os
import pathlib
import subprocess
import sys

HOOKS = pathlib.Path(__file__).resolve().parents[1] / "hooks"
sys.path.insert(0, str(HOOKS))

VALID_MANIFEST = {
    "policy_version": 1,
    "contract_version": "tier1-2026-07-28",
    "description": "test fixture",
    "allowlist": ".claude/allowed-scripts.json",
    "contract": ".claude/reliability-contract.md",
    "protected": ["scripts/verify/", "tools/sacred.py"],
    "maintenance": {"issuer": "scripts/verify/authorize.py",
                    "ledger": ".claude/maintenance-uses.jsonl"},
    "require_subagent_receipts": True,
}

DEPLOY = "#!/bin/bash\necho deploying\n"
DANGER = "#!/bin/bash\nrm -rf /tmp/whatever\n"


def sha256(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git(project: pathlib.Path, *args: str) -> None:
    subprocess.run(["git", "-c", "user.email=t@example.com", "-c", "user.name=t",
                    *args], cwd=project, capture_output=True, text=True, check=False)


def build(root: pathlib.Path, name: str, manifest=None, *, pin_danger: bool = False,
          allowlist: bool = True, git_init: bool = True) -> pathlib.Path:
    """An ordinary project. `manifest` is a dict, a raw string, or None for absent.

    Always contains the files an ordinary repository has — a build file, a deploy
    script, a virtualenv activate script — so "policy absent" is tested against a
    realistic project rather than an empty directory.
    """
    project = root / name
    (project / ".claude").mkdir(parents=True)
    (project / "scripts" / "verify").mkdir(parents=True)
    (project / "tools").mkdir()
    (project / ".venv" / "bin").mkdir(parents=True)
    (project / "local-pkg").mkdir()
    (project / "README.md").write_text("# fixture\n")
    (project / "package.json").write_text('{"scripts": {"build": "tsc"}}\n')
    (project / "Makefile").write_text("build:\n\techo building\n")
    (project / "deploy.sh").write_text(DEPLOY)
    (project / "danger.sh").write_text(DANGER)
    (project / "manage.py").write_text("print('manage')\n")
    (project / "gradlew").write_text("#!/bin/bash\necho gradle\n")
    (project / "fix.patch").write_text("--- a\n+++ b\n")
    (project / "tools" / "sacred.py").write_text("SACRED = 1\n")
    (project / ".venv" / "bin" / "activate").write_text("export VIRTUAL_ENV=x\n")
    (project / ".claude" / "reliability-contract.md").write_text("# contract\n")
    os.chmod(project / "deploy.sh", 0o755)
    os.chmod(project / "danger.sh", 0o755)

    if allowlist:
        scripts = {"deploy.sh": sha256(project / "deploy.sh")}
        if pin_danger:
            scripts["danger.sh"] = sha256(project / "danger.sh")
        (project / ".claude" / "allowed-scripts.json").write_text(
            json.dumps({"version": "fixture", "scripts": scripts}, indent=2) + "\n")

    if manifest is not None:
        target = project / ".claude" / "reliability-policy.json"
        if isinstance(manifest, str):
            target.write_text(manifest)
        else:
            target.write_text(json.dumps(manifest, indent=2) + "\n")

    if git_init:
        git(project, "init", "-q")
        git(project, "add", "-A")
        git(project, "commit", "-qm", "initial")
    return project


class Checks:
    """Collects results and prints one line each, in the house style."""

    def __init__(self) -> None:
        self.rows: list[tuple[bool, str, str]] = []

    def __call__(self, ok: bool, label: str, detail: str = "") -> None:
        self.rows.append((bool(ok), label, detail))
        print(f"{'ok  ' if ok else 'FAIL'}  {label}")
        if not ok and detail:
            print(f"        {detail}")

    def finish(self, extra: str = "") -> int:
        passed = sum(1 for ok, _, _ in self.rows if ok)
        print(f"\n{passed}/{len(self.rows)} passed{('  ' + extra) if extra else ''}")
        return 0 if passed == len(self.rows) else 1

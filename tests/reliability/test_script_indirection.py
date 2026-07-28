#!/usr/bin/env python3
"""Regression tests for the cross-tool bypass.

The bypass this closes, in three steps:

  1. Write creates cleanup.sh / cleanup.py / cleanup.js
  2. Bash runs `bash cleanup.sh`
  3. the gate saw only the interpreter, so the destructive body ran unexamined

Every case here builds a real script on disk inside a throwaway git repository and
asks the hook what it would do. A string corpus cannot test this: the verdict
depends on the file's hash, its presence in the allowlist, and its git state.

The temporary repo is the "project", so the real repository is never touched and
the tracked / untracked / modified labels are produced by a real `git status`.
"""
from __future__ import annotations

import hashlib
import json
import os
import pathlib
import shutil
import subprocess
import sys
import tempfile

HOOK = pathlib.Path(__file__).resolve().parents[2] / ".claude" / "hooks" / "guard_destructive_bash.py"
REPO = pathlib.Path(__file__).resolve().parents[2]

DESTRUCTIVE_SH = '#!/bin/bash\nrm -rf "$HOME/.codex/skills"\n'
DESTRUCTIVE_PY = 'import shutil\nshutil.rmtree("/tmp/anything")\n'
DESTRUCTIVE_JS = 'require("fs").rmSync("/tmp/anything", {recursive: true});\n'
HARMLESS_SH = '#!/bin/bash\necho reviewed\n'


def sha256(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git(project: pathlib.Path, *args: str) -> None:
    subprocess.run(["git", "-c", "user.email=t@example.com", "-c", "user.name=t",
                    *args], cwd=project, capture_output=True, text=True, check=False)


def build_project(root: pathlib.Path) -> pathlib.Path:
    """A git repo containing: untracked destructive scripts, a committed and
    allowlisted script, a committed allowlisted script that was edited after
    review, and a committed script nobody allowlisted."""
    project = root / "project"
    (project / "tools").mkdir(parents=True)
    (project / ".claude").mkdir()

    (project / "cleanup.sh").write_text(DESTRUCTIVE_SH)
    (project / "cleanup.py").write_text(DESTRUCTIVE_PY)
    (project / "cleanup.js").write_text(DESTRUCTIVE_JS)
    for name in ("cleanup.sh",):
        os.chmod(project / name, 0o755)

    reviewed = project / "tools" / "reviewed.sh"
    tampered = project / "tools" / "tampered.sh"
    unlisted = project / "tools" / "unlisted.sh"
    for p in (reviewed, tampered, unlisted):
        p.write_text(HARMLESS_SH)
        os.chmod(p, 0o755)

    git(project, "init", "-q")
    git(project, "add", "tools")
    git(project, "commit", "-q", "-m", "reviewed tools")

    # Pin hashes as they were at review time, then tamper with one of them.
    allowlist = {
        "version": "test",
        "scripts": {
            "tools/reviewed.sh": sha256(reviewed),
            "tools/tampered.sh": sha256(tampered),
        },
    }
    (project / ".claude" / "allowed-scripts.json").write_text(
        json.dumps(allowlist, indent=2) + "\n")
    tampered.write_text(HARMLESS_SH + 'rm -rf "$HOME/.codex/skills"\n')

    outside = root / "outside"
    outside.mkdir()
    (outside / "cleanup.sh").write_text(DESTRUCTIVE_SH)
    return project


def ask(command: str, cwd: pathlib.Path, project: pathlib.Path) -> dict:
    env = os.environ.copy()
    env["CLAUDE_PROJECT_DIR"] = str(project)
    env.pop("RELIABILITY_ALLOWLIST", None)
    proc = subprocess.run(
        [sys.executable, str(HOOK)],
        input=json.dumps({"tool_name": "Bash", "cwd": str(cwd),
                          "tool_input": {"command": command}}),
        capture_output=True, text=True, timeout=30, env=env,
    )
    if proc.returncode != 0 or not proc.stdout.strip():
        raise SystemExit(f"hook failed on {command!r}: {proc.stderr}")
    return json.loads(proc.stdout)["hookSpecificOutput"]


def cases(root: pathlib.Path):
    outside = root / "outside" / "cleanup.sh"
    return [
        # 1. Write a destructive shell script, then execute it, by every route.
        ("bash cleanup.sh", "deny", "unreviewed script"),
        ("bash cleanup.sh", "deny", "untracked"),
        ("sh ./cleanup.sh", "deny", "unreviewed script"),
        ("zsh cleanup.sh", "deny", "unreviewed script"),
        ("./cleanup.sh", "deny", "unreviewed script"),
        ("source cleanup.sh", "deny", "unreviewed script"),
        (". ./cleanup.sh", "deny", "unreviewed script"),
        ("env bash cleanup.sh", "deny", "unreviewed script"),
        ("env -i bash cleanup.sh", "deny", "unreviewed script"),
        ("time bash cleanup.sh", "deny", "unreviewed script"),
        ("nohup bash cleanup.sh", "deny", "unreviewed script"),
        ("exec bash cleanup.sh", "deny", "unreviewed script"),
        ("bash -c 'bash cleanup.sh'", "deny", "inside `bash -c`"),
        ("sh -c 'sh -c \"sh cleanup.sh\"'", "deny", "inside"),
        ("chmod +x cleanup.sh && ./cleanup.sh", "deny", "unreviewed script"),
        ("echo start; bash cleanup.sh; echo done", "deny", "unreviewed script"),
        # 2. Write Python using shutil.rmtree, then execute it.
        ("python3 cleanup.py", "deny", "unreviewed script"),
        ("python cleanup.py", "deny", "unreviewed script"),
        ("python3 -u cleanup.py", "deny", "unreviewed script"),
        ("uv run cleanup.py", "deny", "script indirection"),
        ("poetry run python cleanup.py", "deny", "script indirection"),
        ("node cleanup.js", "deny", "unreviewed script"),
        # 3. Build and package-script indirection.
        ("make clean", "deny", "script indirection"),
        ("npm run cleanup", "deny", "script indirection"),
        ("npx some-tool", "deny", "script indirection"),
        ("yarn run purge", "deny", "script indirection"),
        ("pnpm run purge", "deny", "script indirection"),
        ("just clean", "deny", "script indirection"),
        ("rake db:drop", "deny", "script indirection"),
        ('eval "ls -la"', "deny", "eval"),
        # 4. Allowlist states: reviewed, modified after review, never reviewed.
        ("bash tools/reviewed.sh", "allow", "hash matches pin"),
        ("./tools/reviewed.sh", "allow", "hash matches pin"),
        ("bash tools/tampered.sh", "deny", "changed since review"),
        ("bash tools/tampered.sh", "deny", "modified relative to git"),
        ("bash tools/unlisted.sh", "deny", "unreviewed script"),
        ("bash tools/unlisted.sh", "deny", "tracked and unmodified"),
        # 5. Outside the project entirely.
        (f"bash {outside}", "deny", "outside the project"),
        (f"python3 {root / 'outside' / 'cleanup.sh'}", "deny", "outside the project"),
        # 6. Ordinary work on the same files must stay allowed.
        ("bash -n cleanup.sh", "allow", "parses without executing"),
        ("cat cleanup.sh", "allow", ""),
        ("grep -n rmtree cleanup.py", "allow", ""),
        ("shasum -a 256 cleanup.sh", "allow", ""),
        ("wc -l cleanup.sh cleanup.py", "allow", ""),
        ("python3 -m pytest tests -q", "allow", "module invocation"),
        ("git status --short", "allow", ""),
        ("git add tools/reviewed.sh", "allow", ""),
        ("npm install", "allow", ""),
        ("uv sync", "allow", ""),
    ]


def real_repo_cases():
    """The reliability scripts themselves must remain runnable from the real
    repository and its real allowlist — otherwise the harness blocks its own use."""
    return [
        ("python3 scripts/verify/verify_tree_equivalence.py a b", "allow"),
        ("python3 scripts/verify/verify_tree_equivalence.py --self-check-only", "allow"),
        ("python3 scripts/verify/bulk_mutate.py apply --plan plan.json --dry-run", "allow"),
        ("bash tests/reliability/fixtures/make_fixtures.sh /tmp/rel-fix", "allow"),
        ("python3 tests/reliability/test_guard_bash.py", "allow"),
        ("python3 tests/reliability/test_script_indirection.py", "allow"),
        ("bash -n install.sh", "allow"),
    ]


def main() -> int:
    root = pathlib.Path(tempfile.mkdtemp(prefix="jw-indirection-"))
    failures = []
    try:
        project = build_project(root)
        print(f"{'EXPECT':7} {'GOT':6} COMMAND")
        print("-" * 78)
        for command, expected, needle in cases(root):
            out = ask(command, project, project)
            got = out["permissionDecision"]
            reason = out.get("permissionDecisionReason", "")
            ok = got == expected and (needle in reason)
            if not ok:
                failures.append((expected, got, needle, command, reason))
            print(f"{expected:7} {got:6} {command}{'' if ok else '   <-- FAIL'}")

        print(f"\n{'EXPECT':7} {'GOT':6} REAL REPOSITORY AND ITS REAL ALLOWLIST")
        print("-" * 78)
        for command, expected in real_repo_cases():
            out = ask(command, REPO, REPO)
            got = out["permissionDecision"]
            ok = got == expected
            if not ok:
                failures.append((expected, got, "", command,
                                 out.get("permissionDecisionReason", "")))
            print(f"{expected:7} {got:6} {command}{'' if ok else '   <-- FAIL'}")
    finally:
        shutil.rmtree(root, ignore_errors=True)

    total = len(cases(root)) + len(real_repo_cases())
    print(f"\n{total - len(failures)}/{total} passed")
    for expected, got, needle, command, reason in failures:
        print(f"  FAIL expected={expected} got={got} needle={needle!r}\n"
              f"       {command}\n       reason: {reason.splitlines()[0] if reason else ''}")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())

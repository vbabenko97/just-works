#!/usr/bin/env python3
"""Regression test: `install.sh --personal` must not install the harness globally.

The reliability harness is activated by .claude/settings.json through commands that
resolve inside whichever project is open — `$CLAUDE_PROJECT_DIR/scripts/hooks/
run_gate.sh` — plus policy files that exist only in this repository. Copied to
~/.claude/settings.json it applies to every project, where the launcher is absent:
bash exits 127, the configured `|| exit 2` converts that into a denial, and every
matched tool call in every project is refused. Failing closed is the right
direction and still bricks the machine, so the installer has to refuse first.

Every case runs the real installer as a subprocess against a throwaway HOME and a
fixture checkout that carries the installer and the Claude config but *no*
scripts/hooks/ — the exact layout that would produce the broken global config.
Two controls install successfully, so a non-zero exit elsewhere cannot be
dismissed as the fixture being unusable, and one fixture drops the
$CLAUDE_PROJECT_DIR dependency to prove the refusal is driven by the settings
file's content rather than by the flag.
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

# The refusal is the only documentation a user gets at the moment it matters, so
# the message itself is part of the contract.
MUST_EXPLAIN = ("project-scoped", "CLAUDE_PROJECT_DIR", "plugin", "portable",
                "unchanged")

# Stands in for the machine-local state a live settings.json accumulates: otel
# routing, plugin disables, subagent defaults. None of it is recoverable from the
# repository, so none of it may be touched by a refused install.
SENTINEL = json.dumps(
    {"model": "opusplan", "env": {"MACHINE_LOCAL_STATE": "must survive"}},
    indent=2) + "\n"

CHECKS: list[tuple[bool, str, str]] = []


def check(ok: bool, label: str, detail: str = "") -> None:
    CHECKS.append((bool(ok), label, detail))
    print(f"{'ok  ' if ok else 'FAIL'}  {label}")
    if not ok and detail:
        print(f"        {detail}")


def make_repo(root: pathlib.Path, name: str, portable: bool = False) -> pathlib.Path:
    """A checkout with the installer and the Claude config but no scripts/hooks/."""
    repo = root / name
    claude = repo / ".claude"
    (claude / "hooks").mkdir(parents=True)
    shutil.copy2(REPO / "install.sh", repo / "install.sh")
    shutil.copy2(REPO / ".claude" / "settings.json.default",
                 claude / "settings.json.default")
    (claude / "hooks" / "guard_destructive_bash.py").write_text("# stub\n")

    settings = (REPO / ".claude" / "settings.json").read_text()
    if portable:
        # Same structure, nothing resolving through the project directory: the
        # shape a plugin or another portable installation mode would produce.
        settings = settings.replace("$CLAUDE_PROJECT_DIR", "$HOME/.claude")
    (claude / "settings.json").write_text(settings)
    return repo


def run_install(repo: pathlib.Path, home: pathlib.Path, *flags: str):
    env = os.environ.copy()
    env["HOME"] = str(home)
    env.pop("CLAUDE_PROJECT_DIR", None)
    home.mkdir(parents=True, exist_ok=True)
    return subprocess.run(["bash", str(repo / "install.sh"), "--no-backup", *flags],
                          capture_output=True, text=True, input="", timeout=120,
                          env=env)


def snapshot(path: pathlib.Path):
    if not path.exists():
        return None
    return (path.read_bytes(), path.stat().st_mtime_ns)


def main() -> int:
    root = pathlib.Path(tempfile.mkdtemp(prefix="jw-install-"))
    try:
        repo = make_repo(root, "repo")
        check(not (repo / "scripts" / "hooks").exists(),
              "fixture checkout has no scripts/hooks/ (the premise)")

        # --- the unsafe route, nothing pre-existing ---------------------------
        home = root / "home-bare"
        proc = run_install(repo, home, "--personal")
        check(proc.returncode != 0,
              "--personal exits non-zero", f"exit {proc.returncode}")
        for token in MUST_EXPLAIN:
            check(token in proc.stderr,
                  f"refusal explains the problem: mentions {token!r}",
                  proc.stderr[-300:])
        check(not (home / ".claude" / "settings.json").exists(),
              "user settings.json is not created")
        check(not (home / ".claude" / "hooks").exists(),
              "hooks are not copied, not merely left inactive")
        check(not (home / ".claude" / "agents").exists(),
              "the run aborts before installing anything at all")
        check("Installed:" not in proc.stdout,
              "nothing reports as installed", proc.stdout[-300:])

        # --- the unsafe route over a live user config -------------------------
        home = root / "home-live"
        (home / ".claude").mkdir(parents=True)
        live = home / ".claude" / "settings.json"
        live.write_text(SENTINEL)
        before = snapshot(live)
        proc = run_install(repo, home, "--personal")
        check(proc.returncode != 0, "--personal over a live config exits non-zero",
              f"exit {proc.returncode}")
        check(snapshot(live) == before,
              "existing user settings.json is byte-identical and untouched")

        # --replace-config is the one route that overwrites a live settings.json
        # wholesale. The refusal has to come first, or the footgun survives.
        before = snapshot(live)
        proc = run_install(repo, home, "--personal", "--replace-config")
        check(proc.returncode != 0, "--personal --replace-config exits non-zero",
              f"exit {proc.returncode}")
        check(snapshot(live) == before,
              "--replace-config does not clobber the live settings.json")

        # --skip-config skips the settings file, so only the refusal stops the
        # hook scripts from being copied under a config that may already exist.
        home = root / "home-skip"
        proc = run_install(repo, home, "--personal", "--skip-config")
        check(proc.returncode != 0, "--personal --skip-config exits non-zero",
              f"exit {proc.returncode}")
        check(not (home / ".claude" / "hooks").exists(),
              "--skip-config still does not copy hooks")

        # A dry run changes nothing, but printing a plan for a route that must
        # never be taken reads as approval of it.
        proc = run_install(repo, root / "home-dry", "--personal", "--dry-run")
        check(proc.returncode != 0, "--personal --dry-run exits non-zero",
              f"exit {proc.returncode}")

        # --- controls: the installer still works ------------------------------
        home = root / "home-default"
        proc = run_install(repo, home, "--claude-only")
        installed = home / ".claude" / "settings.json"
        check(proc.returncode == 0, "control: default profile exits 0",
              f"exit {proc.returncode}: {proc.stderr[-300:]}")
        check(installed.exists() and installed.read_text() ==
              (repo / ".claude" / "settings.json.default").read_text(),
              "control: default profile installs settings.json.default")

        home = root / "home-codex"
        proc = run_install(repo, home, "--personal", "--codex-only")
        check(proc.returncode == 0, "control: --personal --codex-only exits 0",
              f"exit {proc.returncode}: {proc.stderr[-300:]}")
        check(not (home / ".claude" / "settings.json").exists(),
              "control: --codex-only leaves the Claude side alone")

        # --- the refusal releases itself once the config is portable ----------
        portable = make_repo(root, "repo-portable", portable=True)
        home = root / "home-portable"
        proc = run_install(portable, home, "--personal", "--claude-only")
        installed = home / ".claude" / "settings.json"
        check(proc.returncode == 0,
              "portable settings.json: --personal exits 0",
              f"exit {proc.returncode}: {proc.stderr[-300:]}")
        check(installed.exists() and installed.read_text() ==
              (portable / ".claude" / "settings.json").read_text(),
              "portable settings.json: --personal installs it unchanged")

        # --- the guard is live for this repository, not vacuous ---------------
        check("CLAUDE_PROJECT_DIR" in (REPO / ".claude" / "settings.json").read_text(),
              "this repository's settings.json does depend on CLAUDE_PROJECT_DIR")
        check("CLAUDE_PROJECT_DIR" not in
              (REPO / ".claude" / "settings.json.default").read_text(),
              "settings.json.default does not, so the default route stays open")
    finally:
        shutil.rmtree(root, ignore_errors=True)

    passed = sum(1 for ok, _, _ in CHECKS if ok)
    print(f"\n{passed}/{len(CHECKS)} passed")
    return 0 if passed == len(CHECKS) else 1


if __name__ == "__main__":
    sys.exit(main())

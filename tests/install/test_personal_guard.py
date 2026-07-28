#!/usr/bin/env python3
"""Regression test: `install.sh --personal` must not install this repository's
settings.json as the user's own.

There is no merge for settings.json anywhere in the installer. With no
~/.claude/settings.json present, `--personal` creates one from a repository-specific
file — this repo's permission allowlist and deny list, env pins, statusLine, output
style. With one present, `--replace-config` overwrites it wholesale, destroying
machine-local state the repository cannot know or restore. Either way the route is
unsafe, so the installer refuses before installing anything.

The refusal used to be content-driven: it fired only while the settings file's hook
commands resolved through `$CLAUDE_PROJECT_DIR`, and would release itself once the
reliability harness shipped portably. That condition was wrong — the harness moving
into a plugin removes the project-scoped-hooks defect while leaving the replacement
defect untouched — so the refusal is now unconditional for the Claude side. Three
fixtures prove the independence: settings that resolve through the project
directory, settings that do not, and a config with no hooks at all. All three are
refused, and a fixture that *has* scripts/hooks/ is refused too, so the decision
cannot be about the launcher being missing either.

Every case runs the real installer as a subprocess against a throwaway HOME. Two
controls install successfully, so a non-zero exit elsewhere cannot be dismissed as
the fixture being unusable.
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
MUST_EXPLAIN = ("merge", "wholesale", "machine-local", "unconditional", "plugin",
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


def make_repo(root: pathlib.Path, name: str, portable: bool = False,
              settings_text: str | None = None,
              with_launcher: bool = False) -> pathlib.Path:
    """A checkout with the installer and the Claude config.

    By default it carries no scripts/hooks/, which is the layout the old
    content-driven refusal was written for. `with_launcher` adds one, so the
    refusal can be shown not to depend on the launcher being absent either.
    """
    repo = root / name
    claude = repo / ".claude"
    (claude / "hooks").mkdir(parents=True)
    shutil.copy2(REPO / "install.sh", repo / "install.sh")
    shutil.copy2(REPO / ".claude" / "settings.json.default",
                 claude / "settings.json.default")
    (claude / "hooks" / "guard_destructive_bash.py").write_text("# stub\n")
    if with_launcher:
        launcher = repo / "scripts" / "hooks"
        launcher.mkdir(parents=True)
        (launcher / "run_gate.sh").write_text("#!/bin/bash\nexit 0\n")

    settings = (REPO / ".claude" / "settings.json").read_text()
    if settings_text is not None:
        settings = settings_text
    elif portable:
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

        # --- the refusal does not depend on the settings file's contents -------
        # Each of these would have been *allowed* by the old content-driven check.
        # The replacement defect is in the installer, not in the settings file, so
        # none of them may release the route.
        for label, repo_kwargs in (
            ("portable settings (nothing resolves through the project dir)",
             {"portable": True}),
            ("settings with no hooks at all", {"settings_text": "{}\n"}),
            ("a checkout that does ship scripts/hooks/", {"with_launcher": True}),
        ):
            fixture = make_repo(root, f"repo-{len(CHECKS)}", **repo_kwargs)
            home = root / f"home-{len(CHECKS)}"
            proc = run_install(fixture, home, "--personal", "--claude-only")
            check(proc.returncode != 0, f"still refused: {label}",
                  f"exit {proc.returncode}: {proc.stdout[-200:]}")
            check(not (home / ".claude" / "settings.json").exists(),
                  f"still refused, nothing installed: {label}")

        # --- the default route stays open -------------------------------------
        check("CLAUDE_PROJECT_DIR" not in
              (REPO / ".claude" / "settings.json.default").read_text(),
              "settings.json.default resolves nothing through the project dir")
    finally:
        shutil.rmtree(root, ignore_errors=True)

    passed = sum(1 for ok, _, _ in CHECKS if ok)
    print(f"\n{passed}/{len(CHECKS)} passed")
    return 0 if passed == len(CHECKS) else 1


if __name__ == "__main__":
    sys.exit(main())

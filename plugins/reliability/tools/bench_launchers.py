#!/usr/bin/env python3
"""Measure hook launcher latency. Not a test — a measurement, reported as medians.

The claim under test: the frozen project launcher adds its full watchdog deadline to
every matched tool call, because the watchdog subshell inherits the caller's stdout
and stderr pipes and keeps the write ends open after being orphaned, so whoever reads
the hook's output blocks until `sleep` finishes.

That was found in the plugin's copy and fixed there. Reporting it as "presumed by
structural similarity" for the project copy is not good enough, so this measures the
real `scripts/hooks/run_gate.sh` with the real deadline, alongside the fixed plugin
launcher for comparison.

Every scenario is run repeatedly and reported as a median, because a single sample
cannot distinguish a slow launcher from a slow machine.
"""
from __future__ import annotations

import json
import os
import pathlib
import statistics
import subprocess
import sys
import tempfile
import time

REPO = pathlib.Path(__file__).resolve().parents[3]
PROJECT_LAUNCHER = REPO / "scripts" / "hooks" / "run_gate.sh"
PLUGIN_LAUNCHER = pathlib.Path(__file__).resolve().parents[1] / "hooks" / "run_gate.sh"

RUNS = 7

ALLOW = ('import json\nprint(json.dumps({"hookSpecificOutput": {"hookEventName": '
         '"PreToolUse", "permissionDecision": "allow", "permissionDecisionReason": '
         '"bench"}}))\n')
DENY = ALLOW.replace("allow", "deny")
SLOW = 'import time, json\ntime.sleep(2)\n' + ALLOW

PAYLOAD = json.dumps({"tool_name": "Bash", "cwd": str(REPO),
                      "tool_input": {"command": "ls -la"}})


def time_once(command: list[str], env_extra: dict) -> tuple[float, int]:
    env = os.environ.copy()
    env["CLAUDE_PROJECT_DIR"] = str(REPO)
    env.update(env_extra)
    started = time.time()
    proc = subprocess.run(command, input=PAYLOAD, capture_output=True, text=True,
                          timeout=180, env=env)
    return (time.time() - started, proc.returncode)


def median(command: list[str], env_extra: dict | None = None) -> tuple[float, int]:
    samples = []
    code = 0
    for _ in range(RUNS):
        elapsed, code = time_once(command, env_extra or {})
        samples.append(elapsed)
    return (statistics.median(samples), code)


def configured(path: pathlib.Path, key: str) -> str | None:
    """The exact PreToolUse command string from a settings or hooks manifest."""
    try:
        data = json.loads(path.read_text())
        for entry in data["hooks"]["PreToolUse"]:
            for hook in entry["hooks"]:
                command = hook.get("command", "")
                if key in command:
                    return command
    except Exception:
        return None
    return None


def main() -> int:
    work = pathlib.Path(tempfile.mkdtemp(prefix="jw-bench-"))
    guards = work / "guards"
    guards.mkdir()
    (guards / "allow.py").write_text(ALLOW)
    (guards / "deny.py").write_text(DENY)
    (guards / "slow.py").write_text(SLOW)

    rows: list[tuple[str, float, int, str]] = []

    print(f"medians over {RUNS} runs, seconds\n")
    print(f"{'MEDIAN':>8} {'EXIT':>5}  SCENARIO")
    print("-" * 72)

    def report(label: str, command: list[str], env_extra=None, note: str = "") -> None:
        elapsed, code = median(command, env_extra)
        rows.append((label, elapsed, code, note))
        print(f"{elapsed:8.2f} {code:5}  {label}")

    # Synthetic guards through each launcher, at the production deadline.
    for name, launcher in (("project", PROJECT_LAUNCHER), ("plugin", PLUGIN_LAUNCHER)):
        if not launcher.is_file():
            print(f"(skipped {name}: {launcher} is missing)")
            continue
        for scenario, guard in (("fast allow", "allow.py"), ("fast deny", "deny.py"),
                                ("delayed child (2s)", "slow.py")):
            report(f"{name} launcher, {scenario}",
                   ["bash", str(launcher), str(guards / guard)])

    # The real configured commands, exactly as each manifest declares them.
    project_command = configured(REPO / ".claude" / "settings.json",
                                 "guard_destructive_bash.py")
    plugin_root = None
    try:
        record = json.loads((pathlib.Path.home() / ".claude" / "plugins" /
                             "installed_plugins.json").read_text())
        plugin_root = pathlib.Path(
            record["plugins"]["reliability@just-works"][0]["installPath"])
    except Exception:
        pass
    plugin_command = configured(plugin_root / "hooks" / "hooks.json", "guard_bash.py") \
        if plugin_root else None

    if project_command:
        report("project-only, real configured command",
               ["bash", "-c", project_command])
    if plugin_command and plugin_root:
        report("plugin-only, real configured command",
               ["bash", "-c", plugin_command],
               {"CLAUDE_PLUGIN_ROOT": str(plugin_root),
                "RELIABILITY_DATA_DIR": str(work / "data")})
    if project_command and plugin_command and plugin_root:
        # Both hooks match a Bash call in this repository today, so the cost a tool
        # call actually pays is both of them.
        report("overlap: project then plugin",
               ["bash", "-c", f"{project_command}; {plugin_command}"],
               {"CLAUDE_PLUGIN_ROOT": str(plugin_root),
                "RELIABILITY_DATA_DIR": str(work / "data")})

    print()
    fast = [r for r in rows if "fast" in r[0]]
    for label, elapsed, _, _ in fast:
        verdict = "adds its deadline" if elapsed > 5 else "returns promptly"
        print(f"  {label}: {elapsed:.2f}s — {verdict}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

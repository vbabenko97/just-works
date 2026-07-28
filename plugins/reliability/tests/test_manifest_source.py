#!/usr/bin/env python3
"""The exact command strings from the *checkout's* hooks.json, run against the
checkout itself — never the installed cache.

Split out of test_manifest_commands.py: that file's staleness comparison and live
probes against the installed copy made this suite red for a plain uncommitted,
uninstalled source change, which is not a functional regression. This file answers
"does the source work" and never looks at what's installed. test_manifest_cache_
parity.py answers "does what's installed match, and is it internally sound" and
is the one allowed to depend on an install existing.
"""
from __future__ import annotations

import json
import os
import pathlib
import shutil
import subprocess
import sys
import tempfile
import time

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from _fixture import VALID_MANIFEST, Checks, build  # noqa: E402

CHECKOUT = pathlib.Path(__file__).resolve().parents[1]

GUARD_SABOTAGE = {
    "syntax error": "def broken(:\n    pass\n",
    "missing": None,
    "import failure": "import definitely_not_a_real_module_xyz\n",
    "exits 1": "import sys\nsys.exit(1)\n",
}


def commands_by_event(root: pathlib.Path) -> dict[str, list[tuple[str, str]]]:
    hooks = json.loads((root / "hooks" / "hooks.json").read_text())
    out: dict[str, list[tuple[str, str]]] = {}
    for event, entries in hooks["hooks"].items():
        found = []
        for entry in entries:
            for hook in entry["hooks"]:
                found.append((entry.get("matcher", "?"), hook["command"]))
        out[event] = found
    return out


def run(command: str, root: pathlib.Path, payload: dict, project: pathlib.Path,
       data: pathlib.Path, deadline: str = "4") -> tuple[int, float, str, str]:
    env = os.environ.copy()
    env["CLAUDE_PLUGIN_ROOT"] = str(root)
    env["CLAUDE_PROJECT_DIR"] = str(project)
    env["RELIABILITY_DATA_DIR"] = str(data)
    env["RELIABILITY_GATE_DEADLINE"] = deadline
    env["RELIABILITY_STOP_DEADLINE"] = deadline
    env["RELIABILITY_GUARD_TIMEOUT"] = "3"
    env["RELIABILITY_TRACE_FILE"] = str(data / "trace.jsonl")
    started = time.time()
    proc = subprocess.run(["bash", "-c", command], input=json.dumps(payload),
                          capture_output=True, text=True, timeout=180, env=env)
    return (proc.returncode, time.time() - started, proc.stdout, proc.stderr[:300])


def payload_for(event: str, matcher: str, project: pathlib.Path) -> dict:
    base = {"session_id": "s-source", "cwd": str(project)}
    if event == "PreToolUse":
        if matcher == "Bash":
            return {**base, "tool_name": "Bash", "tool_input": {"command": "ls -la"}}
        return {**base, "tool_name": "Read", "tool_input": {"file_path": "README.md"}}
    if event == "SubagentStart":
        return {**base, "agent_id": "a-source", "agent_type": "Explore",
                "hook_event_name": "SubagentStart"}
    if event == "SubagentStop":
        return {**base, "agent_id": "a-source", "agent_type": "Explore"}
    return base


def expected_ok(event: str, out: str) -> bool:
    if event == "PreToolUse":
        return '"permissionDecision"' in out
    if event == "SubagentStart":
        return '"additionalContext"' in out
    if event == "SubagentStop":
        # Either empty (approve) or a well-formed block decision — both are valid,
        # source-only outcomes; which one fires depends on receipt state we are not
        # constructing here, so either is a pass.
        stripped = out.strip()
        if stripped == "":
            return True
        try:
            data = json.loads(stripped)
        except Exception:
            return False
        return data.get("decision") == "block" and isinstance(data.get("reason"), str)
    return True


def main() -> int:
    check = Checks()
    work = pathlib.Path(tempfile.mkdtemp(prefix="jw-manifest-source-"))
    try:
        data = work / "data"
        data.mkdir()
        project = build(work, "policed", manifest=VALID_MANIFEST)

        by_event = commands_by_event(CHECKOUT)
        check(bool(by_event), f"checkout hooks.json declares events "
                              f"({list(by_event.keys())})")

        # ---- control: every configured command, run against the checkout -------
        for event, configured in by_event.items():
            for matcher, command in configured:
                code, _, out, err = run(command, CHECKOUT,
                                        payload_for(event, matcher, project),
                                        project, data)
                ok = code == 0 and expected_ok(event, out)
                check(ok, f"source control [{event}/{matcher}] -> exit 0, "
                         f"well-formed output",
                      f"exit {code}: out={out[:120]!r} err={err!r}")

        # ---- guard-specific sabotage, against a copy of the checkout only -------
        replica = work / "replica"
        guard_targets = {
            "hooks/guard_bash.py": ("PreToolUse", "Bash"),
            "hooks/guard_common.py": ("PreToolUse", "*"),
            "hooks/subagent_stop.py": ("SubagentStop", None),
        }
        for rel, (event, matcher_wanted) in guard_targets.items():
            configured = by_event.get(event, [])
            if matcher_wanted is not None:
                command = next((c for m, c in configured if m == matcher_wanted),
                               None)
            else:
                command = configured[0][1] if configured else None
            if command is None:
                check(False, f"source hooks.json declares a command for {event} "
                             f"to sabotage {rel}")
                continue
            for label, body in GUARD_SABOTAGE.items():
                shutil.rmtree(replica, ignore_errors=True)
                shutil.copytree(CHECKOUT, replica)
                victim = replica / rel
                if body is None:
                    victim.unlink()
                else:
                    victim.write_text(body)
                matcher_for_payload = matcher_wanted or "Explore"
                payload = payload_for(event, matcher_for_payload, project)
                code, elapsed, out, err = run(command, replica, payload, project,
                                              data)
                ok = code == 2 if event == "PreToolUse" else code == 0
                if event == "SubagentStop":
                    # subagent_stop's own launcher (run_stop_gate.sh) always exits
                    # 0 and converts sabotage into a printed block decision.
                    ok = ok and json.loads(out.strip() or "{}").get("decision") == \
                        "block"
                check(ok, f"{rel} {label} [{event}] -> fails closed",
                      f"exit {code} in {elapsed:.1f}s: out={out[:100]!r} "
                      f"err={err!r}")
    finally:
        shutil.rmtree(work, ignore_errors=True)

    return check.finish()


if __name__ == "__main__":
    sys.exit(main())

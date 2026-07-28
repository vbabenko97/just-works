#!/usr/bin/env python3
"""Every way a guard can fail becomes a refusal. Ported from test_hook_gate.py.

The implementation moved into the plugin; the required behaviour did not. A guard
with a syntax error, a bad import, a crash, a hang or a typo was measured to let the
tool call through, because Claude Code treats an abnormal hook exit as "no opinion".
Each row below is one of those failures, and each must come back as exit 2.

The launcher is exercised too, not just the gate, because the project version's
acceptance suite found a fail-open there and nowhere else: a gate exiting 0 while
printing junk sailed straight through, since only the guard's output was validated
and never the gate's own.
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
from _fixture import Checks  # noqa: E402

HOOKS = pathlib.Path(__file__).resolve().parents[1] / "hooks"

DECISION = ('import json\nprint(json.dumps({"hookSpecificOutput": '
            '{"hookEventName": "PreToolUse", "permissionDecision": "%s", '
            '"permissionDecisionReason": "test"}}))\n')

GUARDS = {
    # label: (guard body, expected exit)
    "valid allow passes through": (DECISION % "allow", 0),
    "valid deny passes through": (DECISION % "deny", 0),
    "guard refuses with exit 2": ('import sys\nprint("why", file=sys.stderr)\n'
                                  'sys.exit(2)\n', 2),
    "syntax error": ("def broken(:\n    pass\n", 2),
    "import failure": ("import definitely_not_a_real_module_xyz\n", 2),
    "exit 1": ("import sys\nsys.exit(1)\n", 2),
    "exit 127": ("import sys\nsys.exit(127)\n", 2),
    "unhandled exception": ("raise RuntimeError('boom')\n", 2),
    "malformed JSON on stdout": ('print("{\\"hookSpecificOutput\\": ")\n', 2),
    "plain text on stdout": ('print("looks fine to me")\n', 2),
    "silent exit 0": ("pass\n", 2),
    "ask is upgraded to a refusal": (DECISION % "ask", 2),
    "unknown decision": (DECISION % "maybe", 2),
    "answers the wrong event": (
        'import json\nprint(json.dumps({"hookSpecificOutput": '
        '{"hookEventName": "PostToolUse", "permissionDecision": "allow"}}))\n', 2),
    "hangs past the guard deadline": ("import time\ntime.sleep(30)\n", 2),
}

PAYLOAD = {"tool_name": "Bash", "cwd": "/tmp",
           "tool_input": {"command": "ls -la"}}


def run(command: list[str], root: pathlib.Path, payload: str,
        env_extra: dict | None = None) -> tuple[int, float, str, str]:
    env = os.environ.copy()
    env["RELIABILITY_GUARD_TIMEOUT"] = "3"
    env["RELIABILITY_GATE_DEADLINE"] = "6"
    env["RELIABILITY_DATA_DIR"] = str(root / "data")
    env.update(env_extra or {})
    started = time.time()
    proc = subprocess.run(command, input=payload, capture_output=True, text=True,
                          timeout=120, env=env)
    return (proc.returncode, time.time() - started, proc.stdout, proc.stderr[:200])


def main() -> int:
    root = pathlib.Path(tempfile.mkdtemp(prefix="jw-gate-"))
    check = Checks()
    try:
        hooks = root / "hooks"
        hooks.mkdir(parents=True)
        for name in ("gate.py", "run_gate.sh"):
            shutil.copy2(HOOKS / name, hooks / name)
        launcher = str(hooks / "run_gate.sh")
        guard = hooks / "probe_guard.py"
        payload = json.dumps(PAYLOAD)

        for label, (body, want) in GUARDS.items():
            guard.write_text(body)
            code, elapsed, out, err = run(["bash", launcher, "probe_guard.py"],
                                          root, payload)
            ok = code == want
            if ok and want == 0:
                ok = '"permissionDecision"' in out
            if ok and "hangs" in label:
                # Cut short by the guard's own 3s deadline, not by the launcher's 6s.
                # This is the check that caught the launcher waiting out its full
                # deadline on every call.
                ok = elapsed < 5
            if ok and want == 0:
                # Latency is a correctness property here: the launcher's deadline
                # must not be spent when the gate answers immediately, or every
                # matched tool call pays it.
                ok = elapsed < 3
            check(ok, f"guard: {label} -> exit {want}",
                  f"exit {code} in {elapsed:.1f}s; out={out[:80]!r} err={err!r}")

        # A guard the gate cannot find at all.
        guard.unlink()
        code, _, _, err = run(["bash", launcher, "probe_guard.py"], root, payload)
        check(code == 2, "guard: missing file -> exit 2", f"exit {code}: {err}")

        # A payload that is not JSON must not become an allow.
        guard.write_text(DECISION % "allow")
        code, _, _, err = run(["bash", launcher, "probe_guard.py"], root, "{not json")
        check(code == 2, "payload: unparseable -> exit 2", f"exit {code}: {err}")

        # No guard named at all.
        code, _, _, err = run(["bash", launcher], root, payload)
        check(code == 2, "launcher: no guard argument -> exit 2", f"exit {code}: {err}")

        # The gate itself broken, which the launcher has to normalise.
        gate = hooks / "gate.py"
        original = gate.read_text()
        for label, body in (("syntax error", "def broken(:\n    pass\n"),
                            ("prints junk and exits 0", 'print("not a decision")\n'),
                            ("exits 1", "import sys\nsys.exit(1)\n"),
                            ("hangs past the launcher deadline",
                             "import time\ntime.sleep(30)\n")):
            gate.write_text(body)
            code, elapsed, out, err = run(["bash", launcher, "probe_guard.py"],
                                          root, payload)
            ok = code == 2 and (elapsed < 20 if "hangs" in label else True)
            check(ok, f"gate: {label} -> exit 2",
                  f"exit {code} in {elapsed:.1f}s; out={out[:80]!r} err={err!r}")
        gate.unlink()
        code, _, _, err = run(["bash", launcher, "probe_guard.py"], root, payload)
        check(code == 2, "gate: missing -> exit 2", f"exit {code}: {err}")
        gate.write_text(original)

        # The launcher itself missing or unparseable, which only `|| exit 2` in the
        # configured command can cover, because nothing inside the file runs.
        code, _, _, _ = run(["bash", "-c",
                             f'bash "{hooks}/does-not-exist.sh" probe_guard.py '
                             f'|| exit 2'], root, payload)
        check(code == 2, "launcher: missing -> exit 2 via `|| exit 2`", f"exit {code}")

        broken_launcher = hooks / "broken.sh"
        broken_launcher.write_text("this ( is not ( valid bash\n")
        code, _, _, _ = run(["bash", "-c",
                             f'bash "{broken_launcher}" probe_guard.py || exit 2'],
                            root, payload)
        check(code == 2, "launcher: unparseable -> exit 2 via `|| exit 2`",
              f"exit {code}")
    finally:
        shutil.rmtree(root, ignore_errors=True)

    return check.finish()


if __name__ == "__main__":
    sys.exit(main())

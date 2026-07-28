#!/usr/bin/env python3
"""SubagentStop: subagent_stop.py's own decision logic, then the outer
run_stop_gate.sh launcher exercised as the literal command hooks.json runs, against
every sabotage of its child. A launcher failure must never look like permission —
every sabotage case must collapse to the same hardcoded block decision, and the
launcher must never itself emit decision:"approve".
"""
from __future__ import annotations

import json
import os
import pathlib
import shutil
import subprocess
import sys
import tempfile

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from _fixture import VALID_MANIFEST, Checks, build  # noqa: E402

HOOKS = pathlib.Path(__file__).resolve().parents[1] / "hooks"
FAIL_CLOSED = {"decision": "block",
              "reason": "[reliability] Subagent completion verification failed to run."}


NOTICE = ("CONTRACT_UNVERIFIED: This subagent's reliability contract could not be "
         "verified before it stopped. No conclusion in this session should be "
         "treated as reviewed or acted on. Re-run this work in a fresh subagent.")


def run_subagent_stop(payload: dict, env: dict) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(HOOKS / "subagent_stop.py")],
                          input=json.dumps(payload), capture_output=True, text=True,
                          timeout=30, env=env)


def parse_decision(proc: subprocess.CompletedProcess) -> dict | None:
    """None on empty/malformed output. A block case that comes back as None is a
    real failure — silence where a decision was required — not something to skip
    silently; callers must check the result, not assume a dict."""
    text = proc.stdout.strip()
    if not text:
        return None
    try:
        return json.loads(text)
    except Exception:
        return None


def run_launcher(hooks_dir: pathlib.Path, payload: dict, *, deadline="15",
                 timeout=30) -> subprocess.CompletedProcess:
    env = os.environ.copy()
    env["RELIABILITY_STOP_DEADLINE"] = deadline
    return subprocess.run(["bash", str(hooks_dir / "run_stop_gate.sh")],
                          input=json.dumps(payload), capture_output=True, text=True,
                          timeout=timeout, env=env)


def main() -> int:
    root = pathlib.Path(tempfile.mkdtemp(prefix="jw-stopgate-"))
    check = Checks()
    try:
        # ==== part 1: subagent_stop.py's own logic, against the real hooks/ =====
        data = root / "data"
        policed = build(root, "policed", manifest=VALID_MANIFEST)
        env = os.environ.copy()
        env["RELIABILITY_DATA_DIR"] = str(data)
        env["CLAUDE_PROJECT_DIR"] = str(policed)
        env["RELIABILITY_TRACE_FILE"] = str(root / "trace.jsonl")
        # Also set directly: receipts.issue() below runs in-process, not in the
        # subprocess env above, so it resolves paths.plugin_data() from the real
        # os.environ. Without this it writes the receipt to the real default data
        # dir while run_subagent_stop()'s subprocess looks in the isolated `data`
        # tempdir — a fixture bug, not a hook bug, that made the "valid matching
        # receipt" case block instead of approve.
        os.environ["RELIABILITY_DATA_DIR"] = str(data)

        sys.path.insert(0, str(HOOKS))
        import paths  # noqa: E402
        import policy as policy_mod  # noqa: E402
        import receipts  # noqa: E402

        # ---- good path: a valid, current receipt approves, no state involved ---
        composed = paths.compose_contract(str(policed), policy_mod.load(str(policed)))
        check(composed.ok, "fixture composes for real", composed.error or "")
        live = {"session_id": "s-live", "agent_id": "a-live", "agent_type": "Explore"}
        receipts.issue(str(policed), live, policy_mod.load(str(policed)).contract_version,
                       composed)
        proc = run_subagent_stop(live, env)
        check(proc.returncode == 0 and proc.stdout.strip() == "",
              "valid matching receipt: prints nothing (approval by omission)",
              repr(proc.stdout))

        # ---- no receipt, no last_assistant_message: blocks and instructs -------
        noreceipt = {"session_id": "s-noreceipt", "agent_id": "a-noreceipt",
                    "agent_type": "Explore"}
        proc = run_subagent_stop(noreceipt, env)
        no_msg = parse_decision(proc)
        check(no_msg is not None, "no receipt, no message: prints a decision "
                                  "(never silent when one is required)", proc.stdout)
        check(no_msg is not None and no_msg.get("decision") == "block",
              "no receipt, no message: blocks", proc.stdout)
        check(no_msg is not None and NOTICE in no_msg.get("reason", ""),
              "no receipt, no message: instructs the exact safe-failure notice",
              no_msg.get("reason") if no_msg else "")

        # ---- no receipt, wrong last_assistant_message: still blocks ------------
        proc = run_subagent_stop({**noreceipt, "last_assistant_message":
                                  "I finished the task, everything looks fine."},
                                 env)
        wrong_msg = parse_decision(proc)
        check(wrong_msg is not None and wrong_msg.get("decision") == "block",
              "no receipt, wrong message: still blocks", proc.stdout)

        # ---- no receipt, malformed last_assistant_message (not a string): blocks
        proc = run_subagent_stop({**noreceipt, "last_assistant_message": 12345}, env)
        malformed_msg = parse_decision(proc)
        check(malformed_msg is not None and malformed_msg.get("decision") == "block",
              "no receipt, non-string message: fails safe (blocks), not approves",
              proc.stdout)

        # ---- no receipt, exact notice: approves — no state, no prior call ------
        # This is the crux of "stateless": approval never depends on a marker
        # written by an earlier stop attempt, only on what THIS payload carries.
        proc = run_subagent_stop({**noreceipt, "last_assistant_message": NOTICE},
                                 env)
        check(proc.returncode == 0 and proc.stdout.strip() == "",
              "no receipt, exact notice, first call ever: approves immediately",
              repr(proc.stdout))

        # ---- calling again with no message: still blocks — nothing was "unlocked"
        proc = run_subagent_stop(noreceipt, env)
        after = parse_decision(proc)
        check(after is not None and after.get("decision") == "block",
              "a prior approving call leaves no state — the next call with no "
              "message blocks again, proving there is no marker to have cleared",
              proc.stdout)

        # ---- missing agent_id: same uniform path, no identity-keyed state ------
        no_id = {"session_id": "s-noid"}
        proc = run_subagent_stop(no_id, env)
        m1 = parse_decision(proc)
        check(m1 is not None and m1.get("decision") == "block",
              "missing agent_id, no message: blocks", proc.stdout)
        proc = run_subagent_stop({**no_id, "last_assistant_message": NOTICE}, env)
        check(proc.returncode == 0 and proc.stdout.strip() == "",
              "missing agent_id, exact notice: approves — same uniform check, "
              "no special-cased identity handling", repr(proc.stdout))

        # ---- transcript_path is NOT consulted: only the direct field counts ----
        transcript = root / "transcript.jsonl"
        transcript.write_text(
            json.dumps({"role": "assistant", "content": NOTICE}) + "\n")
        proc = run_subagent_stop({**noreceipt, "transcript_path": str(transcript)},
                                 env)
        tp = parse_decision(proc)
        check(tp is not None and tp.get("decision") == "block",
              "a matching notice sitting only in transcript_path (not in "
              "last_assistant_message) is not consulted — still blocks", proc.stdout)

        # ==== part 2: the exact launcher command, sabotaged every way ===========
        stop_root = root / "stopgate"
        hooks_dir = stop_root / "hooks"
        hooks_dir.mkdir(parents=True)
        shutil.copy(HOOKS / "run_stop_gate.sh", hooks_dir / "run_stop_gate.sh")
        os.chmod(hooks_dir / "run_stop_gate.sh", 0o755)
        payload = {"session_id": "s1", "agent_id": "a1", "agent_type": "Explore"}

        def set_child(code: str | None) -> None:
            child = hooks_dir / "subagent_stop.py"
            if code is None:
                child.unlink(missing_ok=True)
            else:
                child.write_text(code)

        sabotage = {
            "missing script": None,
            "syntax error": "def broken(:\n    pass\n",
            "import failure": "import definitely_not_a_real_module_xyz\n",
            "abnormal exit": "import sys\nsys.exit(3)\n",
            "malformed output": "print('not { valid json')\n",
            "explicit approve (never valid)":
                "import json\nprint(json.dumps({'decision': 'approve'}))\n",
            "block missing reason":
                "import json\nprint(json.dumps({'decision': 'block'}))\n",
        }
        for label, code in sabotage.items():
            set_child(code)
            proc = run_launcher(hooks_dir, payload)
            check(proc.returncode == 0,
                  f"launcher itself always exits 0: {label}", proc.stderr[:200])
            check(json.loads(proc.stdout) == FAIL_CLOSED,
                  f"sabotage collapses to fail-closed: {label}", proc.stdout)

        # timeout: short deadline, child sleeps well past it
        set_child("import time\ntime.sleep(30)\n")
        proc = run_launcher(hooks_dir, payload, deadline="1", timeout=15)
        check(json.loads(proc.stdout) == FAIL_CLOSED,
              "sabotage collapses to fail-closed: timeout", proc.stdout)

        # legitimate: real block decision passes through verbatim, not the generic
        # launcher message
        set_child("import json\n"
                 "print(json.dumps({'decision': 'block', 'reason': 'real-reason-xyz'}))\n")
        proc = run_launcher(hooks_dir, payload)
        check(json.loads(proc.stdout) == {"decision": "block",
                                          "reason": "real-reason-xyz"},
              "a real, well-formed block decision passes through unchanged",
              proc.stdout)

        # legitimate: no decision key at all -> success, launcher prints nothing
        set_child("import json\nprint(json.dumps({'foo': 'bar'}))\n")
        proc = run_launcher(hooks_dir, payload)
        check(proc.stdout.strip() == "",
              "success (no decision key): launcher prints nothing", repr(proc.stdout))

        # legitimate: prints nothing at all -> success
        set_child("pass\n")
        proc = run_launcher(hooks_dir, payload)
        check(proc.stdout.strip() == "",
              "success (empty output): launcher prints nothing", repr(proc.stdout))
    finally:
        shutil.rmtree(root, ignore_errors=True)

    return check.finish()


if __name__ == "__main__":
    sys.exit(main())

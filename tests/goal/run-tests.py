#!/usr/bin/env python3
"""Local test harness for .claude/skills/goal/scripts/codex-review.py.

No provider calls anywhere — every Codex invocation goes to tests/goal/fake-codex.py.
Scratch state lives under /tmp/goal-tests; the repository is not modified.

Run:  python3 tests/goal/run-tests.py
"""
import hashlib
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
RUNNER = REPO / ".claude/skills/goal/scripts/codex-review.py"
FAKE_SRC = Path(__file__).resolve().parent / "fake-codex.py"

BASE = Path("/tmp/goal-tests")
SPACED = BASE / "dir with spaces"          # exercise paths containing spaces
FAKE_DIR = SPACED / "fake codex"
LOGS = SPACED / "log dir"
TASK = SPACED / "task file.txt"
ECHO = BASE / "task-echo.txt"
MARKER = BASE / "invoked.txt"
FAKE = FAKE_DIR / "codex"

results = []


def check(name, cond, detail=""):
    results.append((name, bool(cond), detail))
    print(f"{'PASS' if cond else 'FAIL'}  {name}" + (f"  — {detail}" if detail and not cond else ""))


def write_config(enabled=True, timeout=900):
    cfg = {
        "backend_enabled": enabled,
        "codex_executable": str(FAKE),
        "repo_root": str(SPACED),
        "model": "gpt-6-astra",
        "effort": "high",
        "timeout_seconds": timeout,
        "log_dir": str(LOGS),
        "provider_note": "fake",
    }
    path = SPACED / "router.local.json"
    path.write_text(json.dumps(cfg), encoding="utf-8")
    return path


def run(cfg_path, extra, mode="ok"):
    env = dict(os.environ)
    env.update({"FAKE_MODE": mode, "FAKE_TASK_ECHO": str(ECHO), "FAKE_MARKER": str(MARKER)})
    return subprocess.run(
        [sys.executable, str(RUNNER), "--task", str(TASK), "--config", str(cfg_path)] + extra,
        capture_output=True, text=True, env=env,
    )


def as_json(proc):
    return json.loads(proc.stdout) if proc.stdout.strip().startswith("{") else {}


def setup():
    if BASE.exists():
        shutil.rmtree(BASE)
    FAKE_DIR.mkdir(parents=True)
    LOGS.mkdir(parents=True)
    shutil.copy(FAKE_SRC, FAKE)
    os.chmod(FAKE, 0o755)
    TASK.write_text(
        "Review scope.\n$(touch /tmp/goal-tests/PWNED)\n`touch /tmp/goal-tests/PWNED2`\n; rm -rf /tmp/goal-tests/nope\n",
        encoding="utf-8",
    )


def main():
    if not RUNNER.is_file():
        print(f"runner not found: {RUNNER}")
        return 2
    setup()

    # 1. dry-run performs no inference
    cfg = write_config(enabled=True)
    p = run(cfg, ["--dry-run"])
    check("dry-run exits 0", p.returncode == 0, p.stderr[:300])
    check("dry-run performs no inference", not MARKER.exists())
    check("dry-run reports mode", as_json(p).get("mode") == "dry-run", p.stdout[:200])

    # 2. disabled backend blocks a real run
    p = run(write_config(enabled=False), ["--run"])
    check("disabled backend blocks --run", not MARKER.exists() and p.returncode == 0, p.stdout[:200])

    # 3. happy path
    cfg = write_config(enabled=True)
    p = run(cfg, ["--run"], mode="ok")
    rep = as_json(p)
    check("happy path exits 0", p.returncode == 0, p.stderr[:300])
    check("happy path ok=True", rep.get("ok") is True, str(rep.get("failures")))
    check("reported model parsed", rep.get("reported", {}).get("model") == "gpt-6-astra-fake")
    check("usage parsed from runtime", (rep.get("reported", {}).get("usage") or {}).get("input_tokens") == 1234)

    # 4. shell metacharacters in the task text are inert
    check("no shell injection", not (BASE / "PWNED").exists() and not (BASE / "PWNED2").exists())
    check("task text delivered intact", "$(touch" in ECHO.read_text(encoding="utf-8"))

    # 5. non-zero exit code
    p = run(cfg, ["--run"], mode="fail")
    rep = as_json(p)
    check("non-zero exit flagged", p.returncode == 1 and rep.get("ok") is False, str(rep.get("failures")))
    check("exit code recorded", rep.get("exit_code") == 3, str(rep.get("exit_code")))

    # 6. error event detected
    rep = as_json(run(cfg, ["--run"], mode="errorevent"))
    check("turn.failed detected", any("error event" in f for f in rep.get("failures", [])), str(rep.get("failures")))

    # 7. empty final report
    rep = as_json(run(cfg, ["--run"], mode="empty"))
    check("empty report flagged", any("empty final report" in f for f in rep.get("failures", [])), str(rep.get("failures")))

    # 8. timeout with process-group kill
    rep = as_json(run(write_config(enabled=True, timeout=2), ["--run"], mode="timeout"))
    check("timeout flagged", rep.get("timed_out") is True, str(rep.get("failures")))
    check("timeout returns promptly", (rep.get("elapsed_seconds") or 999) < 60, str(rep.get("elapsed_seconds")))

    # 9. large logs retained without truncation
    cfg = write_config(enabled=True)
    rep = as_json(run(cfg, ["--run"], mode="big"))
    jsonl = Path(rep.get("artifacts", {}).get("stdout_jsonl", "/nonexistent"))
    size = jsonl.stat().st_size if jsonl.exists() else 0
    lines = sum(1 for _ in jsonl.open(encoding="utf-8")) if jsonl.exists() else 0
    check("large log retained whole", size > 3_000_000 and lines >= 20002, f"size={size} lines={lines}")
    check("log file perms 600", (oct(jsonl.stat().st_mode)[-3:] if jsonl.exists() else "???") == "600")

    # 10. concurrent run refused
    digest = hashlib.sha256(str(SPACED.resolve()).encode()).hexdigest()[:16]
    lock = LOGS / f".lock-{digest}"
    lock.write_text("held", encoding="utf-8")
    p = run(cfg, ["--run"], mode="ok")
    check("concurrent run refused", p.returncode == 2 and "lock" in p.stderr.lower(), p.stderr[:200])
    lock.unlink(missing_ok=True)

    failed = [n for n, ok, _ in results if not ok]
    print(f"\n{len(results) - len(failed)}/{len(results)} passed")
    if failed:
        print("FAILED: " + ", ".join(failed))
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())

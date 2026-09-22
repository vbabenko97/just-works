#!/usr/bin/env python3
"""Narrow bridge to the official Codex CLI for an independent read-only review.

Standard library only. Never talks to a provider API directly — it shells out to
the Codex executable named in the config, with an argv list and no shell.

Safe by default: dry-run unless --run is passed AND the config enables the
backend. Dry-run performs no inference.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import signal
import subprocess
import sys
import time
from pathlib import Path

CONFIG_NAME = "router.local.json"
REQUIRED_KEYS = ("codex_executable", "repo_root", "model", "effort", "timeout_seconds", "log_dir")
# Flags that must never be produced, whatever the config says.
FORBIDDEN = (
    "--yolo",
    "--dangerously-bypass-approvals-and-sandbox",
    "--dangerously-bypass-hook-trust",
    "--full-auto",
)


class RunnerError(RuntimeError):
    """Configuration or precondition failure — never a provider result."""


# --------------------------------------------------------------------------- config


def load_config(path: Path) -> dict:
    if not path.is_file():
        raise RunnerError(f"config not found: {path}\nCopy router.local.example.json to {CONFIG_NAME} and edit it.")
    try:
        cfg = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise RunnerError(f"config is not valid JSON: {path}: {exc}") from exc

    missing = [k for k in REQUIRED_KEYS if k not in cfg]
    if missing:
        raise RunnerError(f"config is missing required keys: {', '.join(missing)}")

    exe = Path(cfg["codex_executable"])
    if not exe.is_absolute():
        raise RunnerError("codex_executable must be an absolute path (PATH lookup is ambiguous across Codex installs)")
    if not (exe.is_file() and os.access(exe, os.X_OK)):
        raise RunnerError(f"codex_executable is not an executable file: {exe}")

    root = Path(cfg["repo_root"])
    if not root.is_dir():
        raise RunnerError(f"repo_root is not a directory: {root}")

    if not isinstance(cfg["timeout_seconds"], int) or cfg["timeout_seconds"] <= 0:
        raise RunnerError("timeout_seconds must be a positive integer")

    for key in ("model", "effort"):
        if not isinstance(cfg[key], str) or not cfg[key].strip():
            raise RunnerError(f"{key} must be a non-empty string")

    return cfg


def build_argv(cfg: dict, last_message_path: Path) -> list[str]:
    """Assemble the exact argv. `-a/--ask-for-approval` is a top-level codex flag,
    verified against `codex --help` on 0.154.0 — it is not an `exec` flag."""
    argv = [
        str(cfg["codex_executable"]),
        "--ask-for-approval",
        "never",
        "exec",
        "--sandbox",
        "read-only",
        "--cd",
        str(cfg["repo_root"]),
        "--model",
        str(cfg["model"]),
        "-c",
        f'model_reasoning_effort="{cfg["effort"]}"',
        "--json",
        "--output-last-message",
        str(last_message_path),
    ]
    profile = cfg.get("profile")
    if profile:
        argv += ["--profile", str(profile)]
    argv.append("-")  # read the task text from stdin

    bad = [a for a in argv if a in FORBIDDEN]
    if bad:
        raise RunnerError(f"refusing to run with forbidden flags: {bad}")
    return argv


# --------------------------------------------------------------------------- locking


class RepoLock:
    """One runner per repository. Not re-entrant, not a network lock."""

    def __init__(self, repo_root: Path, log_dir: Path):
        # Deterministic across processes — builtin hash() is salted per-process
        # (PYTHONHASHSEED), so two runners would compute different lock paths and
        # never exclude each other.
        digest = hashlib.sha256(str(repo_root.resolve()).encode()).hexdigest()[:16]
        self.path = log_dir / f".lock-{digest}"
        self.fd: int | None = None

    def __enter__(self) -> "RepoLock":
        try:
            self.fd = os.open(self.path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        except FileExistsError:
            raise RunnerError(
                f"another runner holds the lock for this repository: {self.path}\n"
                "If no runner is active, delete that file and retry."
            ) from None
        os.write(self.fd, f"pid={os.getpid()} started={dt.datetime.now().isoformat()}\n".encode())
        return self

    def __exit__(self, *exc) -> None:
        if self.fd is not None:
            os.close(self.fd)
        self.path.unlink(missing_ok=True)


# --------------------------------------------------------------------------- events


def parse_events(jsonl_path: Path) -> dict:
    """Extract only what the runtime actually reported. Absent means unknown —
    the requested value is never echoed back as if it were confirmation."""
    reported_model = None
    usage = None
    errors: list[str] = []
    events = 0

    if not jsonl_path.is_file():
        return {"events": 0, "reported_model": "unknown", "usage": "unknown", "errors": errors}

    with jsonl_path.open(encoding="utf-8", errors="replace") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                continue
            events += 1
            if not isinstance(event, dict):
                continue

            etype = str(event.get("type", ""))
            if "error" in etype or etype.endswith("turn.failed"):
                errors.append(line[:2000])

            for key, value in event.items():
                if key == "model" and isinstance(value, str) and reported_model is None:
                    reported_model = value
                if key == "usage" and isinstance(value, dict):
                    usage = value
            nested = event.get("msg") if isinstance(event.get("msg"), dict) else None
            if nested:
                if reported_model is None and isinstance(nested.get("model"), str):
                    reported_model = nested["model"]
                if isinstance(nested.get("usage"), dict):
                    usage = nested["usage"]

    return {
        "events": events,
        "reported_model": reported_model or "unknown",
        "usage": usage or "unknown",
        "errors": errors,
    }


# --------------------------------------------------------------------------- run


def execute(cfg: dict, task_text: str, run_dir: Path) -> dict:
    stdout_path = run_dir / "stdout.jsonl"
    stderr_path = run_dir / "stderr.log"
    last_message_path = run_dir / "last-message.txt"

    argv = build_argv(cfg, last_message_path)
    started = time.monotonic()
    timed_out = False

    with stdout_path.open("wb") as out, stderr_path.open("wb") as err:
        proc = subprocess.Popen(
            argv,
            stdin=subprocess.PIPE,
            stdout=out,
            stderr=err,
            cwd=str(cfg["repo_root"]),
            start_new_session=True,  # own process group, so timeout can kill children too
        )
        try:
            proc.communicate(task_text.encode("utf-8"), timeout=cfg["timeout_seconds"])
        except subprocess.TimeoutExpired:
            timed_out = True
            _terminate_group(proc)
            proc.communicate()

    elapsed = round(time.monotonic() - started, 2)
    for path in (stdout_path, stderr_path, last_message_path):
        if path.exists():
            os.chmod(path, 0o600)

    parsed = parse_events(stdout_path)
    final_message = last_message_path.read_text(encoding="utf-8", errors="replace") if last_message_path.is_file() else ""

    failures = []
    if timed_out:
        failures.append(f"timeout after {cfg['timeout_seconds']}s")
    if proc.returncode != 0:
        failures.append(f"exit code {proc.returncode}")
    if parsed["errors"]:
        failures.append(f"{len(parsed['errors'])} error event(s)")
    if not final_message.strip():
        failures.append("empty final report")

    return {
        "ok": not failures,
        "failures": failures,
        "exit_code": proc.returncode,
        "timed_out": timed_out,
        "elapsed_seconds": elapsed,
        "requested": {
            "model": cfg["model"],
            "effort": cfg["effort"],
            "profile": cfg.get("profile") or "none",
            "provider": cfg.get("provider_note", "codex CLI default auth"),
        },
        "reported": {"model": parsed["reported_model"], "usage": parsed["usage"]},
        "events": parsed["events"],
        "artifacts": {
            "stdout_jsonl": str(stdout_path),
            "stderr_log": str(stderr_path),
            "last_message": str(last_message_path),
        },
        "final_message_chars": len(final_message),
    }


def _terminate_group(proc: subprocess.Popen) -> None:
    for sig in (signal.SIGTERM, signal.SIGKILL):
        try:
            os.killpg(os.getpgid(proc.pid), sig)
        except (ProcessLookupError, PermissionError):
            return
        try:
            proc.wait(timeout=10)
            return
        except subprocess.TimeoutExpired:
            continue


# --------------------------------------------------------------------------- cli


def main(argv: list[str] | None = None) -> int:
    here = Path(__file__).resolve().parent
    parser = argparse.ArgumentParser(description="Run a read-only Codex review via the official CLI.")
    parser.add_argument("--task", required=True, type=Path, help="UTF-8 file holding the review instructions")
    parser.add_argument("--config", type=Path, default=here.parent / CONFIG_NAME)
    parser.add_argument("--run", action="store_true", help="actually invoke Codex (requires enabled backend)")
    parser.add_argument("--dry-run", action="store_true", help="explicit no-inference mode (the default)")
    args = parser.parse_args(argv)

    try:
        cfg = load_config(args.config)
        if not args.task.is_file():
            raise RunnerError(f"task file not found: {args.task}")
        task_text = args.task.read_text(encoding="utf-8")
        if not task_text.strip():
            raise RunnerError("task file is empty")

        log_dir = Path(cfg["log_dir"]).expanduser()
        log_dir.mkdir(parents=True, exist_ok=True, mode=0o700)

        stamp = dt.datetime.now().strftime("%Y%m%d-%H%M%S-%f")
        run_dir = log_dir / f"run-{stamp}"
        run_dir.mkdir(mode=0o700)

        argv_preview = build_argv(cfg, run_dir / "last-message.txt")
        enabled = bool(cfg.get("backend_enabled", False))

        if not args.run or not enabled:
            reason = "no --run flag" if not args.run else "backend_enabled is false in config"
            report = {
                "mode": "dry-run",
                "inference": "none",
                "reason": reason,
                "argv": argv_preview,
                "task_file": str(args.task),
                "task_chars": len(task_text),
                "run_dir": str(run_dir),
            }
            _write_report(run_dir, report)
            print(json.dumps(report, indent=2, ensure_ascii=False))
            return 0

        with RepoLock(Path(cfg["repo_root"]), log_dir):
            result = execute(cfg, task_text, run_dir)

        result["mode"] = "run"
        result["argv"] = argv_preview
        _write_report(run_dir, result)
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return 0 if result["ok"] else 1

    except RunnerError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


def _write_report(run_dir: Path, report: dict) -> None:
    path = run_dir / "report.json"
    path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    os.chmod(path, 0o600)


if __name__ == "__main__":
    raise SystemExit(main())

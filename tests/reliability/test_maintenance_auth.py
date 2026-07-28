#!/usr/bin/env python3
"""The maintenance authorization must be narrow, and must not leak into the Bash gate.

A bypass is only acceptable if every one of its bindings is enforced, so each is
tested by breaking exactly one of them and checking the refusal names it:

  repository, HEAD, expiry, exact path, exact tool, use budget, nonce ledger

The last two sections matter most. One proves the authorization is literal — an
entry for `.claude/hooks/` authorizes nothing inside it. The other proves an active
authorization still leaves `rm -rf`, script indirection and harness redirects denied,
so this is a maintenance door and not a general amnesty.
"""
from __future__ import annotations

import importlib.util
import json
import os
import pathlib
import shutil
import subprocess
import sys
import tempfile
import time

REPO = pathlib.Path(__file__).resolve().parents[2]
HOOKS = REPO / ".claude" / "hooks"

spec = importlib.util.spec_from_file_location("maintenance_auth",
                                              HOOKS / "maintenance_auth.py")
ma = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ma)


def git(project, *args):
    subprocess.run(["git", "-c", "user.email=t@example.com", "-c", "user.name=t",
                    *args], cwd=project, capture_output=True, text=True, check=False)


def build(root: pathlib.Path) -> pathlib.Path:
    project = root / "project"
    (project / ".claude" / "hooks").mkdir(parents=True)
    (project / "scripts" / "verify").mkdir(parents=True)
    (project / ".claude" / "hooks" / "guard_destructive_bash.py").write_text("x\n")
    (project / ".claude" / "allowed-scripts.json").write_text('{"scripts":{}}\n')
    (project / "scripts" / "verify" / "tool.py").write_text("y\n")
    (project / "README.md").write_text("r\n")
    git(project, "init", "-q")
    git(project, "add", ".")
    git(project, "commit", "-q", "-m", "base")
    return project


def head_of(project) -> str:
    out = subprocess.run(["git", "rev-parse", "HEAD"], cwd=project,
                         capture_output=True, text=True)
    return out.stdout.strip()


def write_auth(project, **over):
    now = int(time.time())
    auth = {
        "version": 1,
        "nonce": "testnonce0000001",
        "repo": str(project),
        "head": head_of(project),
        "issued_at": now,
        "expires_at": now + 600,
        "reason": "test",
        "operations": [
            {"tool": "Edit", "path": ".claude/allowed-scripts.json", "max_uses": 2},
            {"tool": "bulk_mutate.delete", "path": "scripts/verify/tool.py",
             "max_uses": 1},
        ],
    }
    auth.update(over)
    path = project / ".claude" / "maintenance-auth.json"
    path.write_text(json.dumps(auth, indent=2) + "\n")
    return auth


def ledger(project):
    p = project / ".claude" / "maintenance-uses.jsonl"
    return p.read_text().splitlines() if p.exists() else []


def run_hook(hook, payload, project):
    env = os.environ.copy()
    env["CLAUDE_PROJECT_DIR"] = str(project)
    proc = subprocess.run([sys.executable, str(HOOKS / hook)],
                          input=json.dumps(payload), capture_output=True,
                          text=True, timeout=30, env=env)
    if proc.returncode != 0 or not proc.stdout.strip():
        raise SystemExit(f"{hook} failed: {proc.stderr}")
    return json.loads(proc.stdout)["hookSpecificOutput"]


def main() -> int:
    root = pathlib.Path(tempfile.mkdtemp(prefix="jw-auth-"))
    failures = []

    def check(name, ok_expected, needle, got_ok, got_reason):
        ok = (got_ok == ok_expected) and (needle in got_reason)
        print(f"{'ok' if ok else 'FAIL':6} {name}")
        if not ok:
            failures.append((name, ok_expected, needle, got_ok, got_reason))

    try:
        project = build(root)
        target = str(project / ".claude" / "allowed-scripts.json")
        auth_path = project / ".claude" / "maintenance-auth.json"

        print("=== every binding, broken one at a time ===")
        ok, why = ma.check(str(project), "Edit", target)
        check("no authorization file at all", False, "no maintenance authorization", ok, why)

        auth_path.write_text("{ not json")
        ok, why = ma.check(str(project), "Edit", target)
        check("malformed authorization", False, "malformed", ok, why)

        write_auth(project, version=99)
        ok, why = ma.check(str(project), "Edit", target)
        check("unsupported version", False, "unsupported version", ok, why)

        write_auth(project, repo="/somewhere/else")
        ok, why = ma.check(str(project), "Edit", target)
        check("bound to a different repository", False, "different repository", ok, why)

        write_auth(project, expires_at=int(time.time()) - 1)
        ok, why = ma.check(str(project), "Edit", target)
        check("expired", False, "expired", ok, why)

        write_auth(project, head="0" * 40)
        ok, why = ma.check(str(project), "Edit", target)
        check("bound to a different commit", False, "different commit", ok, why)

        write_auth(project)
        ok, why = ma.check(str(project), "Write", target)
        check("tool not listed (Write vs Edit)", False, "does not list tool", ok, why)

        ok, why = ma.check(str(project), "Edit",
                           str(project / ".claude" / "hooks" / "guard_destructive_bash.py"))
        check("path not listed", False, "does not list path", ok, why)

        ok, why = ma.check(str(project), "Edit", "/etc/hosts")
        check("path outside the repository", False, "outside the repository", ok, why)

        print()
        print("=== paths are literal, not prefixes ===")
        write_auth(project, operations=[{"tool": "Edit", "path": ".claude/hooks/",
                                        "max_uses": 5}])
        ok, why = ma.check(str(project), "Edit",
                           str(project / ".claude" / "hooks" / "guard_destructive_bash.py"))
        check("a directory entry authorizes nothing inside it", False,
              "does not list path", ok, why)

        print()
        print("=== budget and ledger ===")
        write_auth(project)
        ok, why = ma.check(str(project), "Edit", target, consume=False)
        check("valid, test only", True, "authorized", ok, why)
        if ledger(project):
            failures.append(("consume=False wrote to the ledger", "empty", "", "", ""))
            print("FAIL   consume=False must not spend a use")
        else:
            print("ok     consume=False spends nothing")

        ok, why = ma.check(str(project), "Edit", target, consume=True)
        check("first spend", True, "use 1 of 2", ok, why)
        ok, why = ma.check(str(project), "Edit", target, consume=True)
        check("second spend", True, "use 2 of 2", ok, why)
        ok, why = ma.check(str(project), "Edit", target, consume=True)
        check("budget exhausted", False, "budget exhausted", ok, why)
        print(f"ok     ledger holds {len(ledger(project))} spend records")

        # A fresh nonce means a fresh budget, and the old ledger lines no longer count.
        write_auth(project, nonce="testnonce0000002")
        ok, why = ma.check(str(project), "Edit", target)
        check("new nonce, fresh budget", True, "use 0 of 2", ok, why)

        # An unreadable ledger must not read as "budget available".
        lp = project / ".claude" / "maintenance-uses.jsonl"
        lp.unlink()
        lp.mkdir()
        ok, why = ma.check(str(project), "Edit", target)
        check("unreadable ledger fails closed", False, "budget exhausted", ok, why)
        lp.rmdir()

        print()
        print("=== through the Write/Edit hook ===")
        write_auth(project)
        out = run_hook("guard_protected_paths.py",
                       {"tool_name": "Edit", "cwd": str(project),
                        "tool_input": {"file_path": target}}, project)
        check("authorized Edit is allowed by the hook", True, "authorized",
              out["permissionDecision"] == "allow", out["permissionDecisionReason"])

        out = run_hook("guard_protected_paths.py",
                       {"tool_name": "Edit", "cwd": str(project),
                        "tool_input": {"file_path": str(project / ".claude" / "settings.json")}},
                       project)
        check("unlisted protected path still denied", True, "does not list path",
              out["permissionDecision"] == "deny", out["permissionDecisionReason"])

        # A batch naming one authorized and one unauthorized path must fail whole.
        write_auth(project)
        out = run_hook("guard_protected_paths.py",
                       {"tool_name": "MultiEdit", "cwd": str(project),
                        "tool_input": {"edits": [{"file_path": target},
                                                 {"file_path": str(project / ".claude" / "settings.json")}]}},
                       project)
        check("partly-authorized batch refused whole", True, "reliability infrastructure",
              out["permissionDecision"] == "deny", out["permissionDecisionReason"])

        print()
        print("=== an authorization must not relax the Bash gate ===")
        write_auth(project, operations=[
            {"tool": "Edit", "path": ".claude/allowed-scripts.json", "max_uses": 5},
            {"tool": "bulk_mutate.delete", "path": "scripts/verify/tool.py", "max_uses": 5},
        ])
        for command, label in [
            ("rm -rf " + str(project / "scripts"), "recursive rm"),
            ("bash cleanup.sh", "unreviewed script"),
            ("git push --force origin main", "force push"),
            ("echo x > .claude/allowed-scripts.json", "redirect over an authorized path"),
            ("cp /tmp/evil.json .claude/allowed-scripts.json", "cp over an authorized path"),
            ("git apply /tmp/fix.diff", "opaque payload"),
        ]:
            out = run_hook("guard_destructive_bash.py",
                           {"tool_name": "Bash", "cwd": str(project),
                            "tool_input": {"command": command}}, project)
            got = out["permissionDecision"]
            ok = got == "deny"
            print(f"{'ok' if ok else 'FAIL':6} still denied with an authorization active: {label}")
            if not ok:
                failures.append((label, "deny", "", got, out["permissionDecisionReason"]))
    finally:
        shutil.rmtree(root, ignore_errors=True)

    print()
    print(f"{'FAILURES: ' + str(len(failures)) if failures else 'all checks passed'}")
    for row in failures:
        print(f"  FAIL {row}")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())

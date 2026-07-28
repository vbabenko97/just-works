#!/usr/bin/env python3
"""The portable authorization, in both scopes. Ported from test_maintenance_auth.py.

Each binding is broken in turn and must produce a refusal. The two scopes exist
because the project-scoped original resolved every path against a repository and
refused anything outside it, which left `~/.claude/settings.json` protected with no
maintenance route at all — and protection that cannot be maintained gets switched off.

The invariant that survives both scopes: an authorization never relaxes the Bash gate.
It is consulted for file-editing tools only, which is why dismantling the harness
stays an owner operation.
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


def main() -> int:
    root = pathlib.Path(tempfile.mkdtemp(prefix="jw-auth-"))
    data = root / "data"
    os.environ["RELIABILITY_DATA_DIR"] = str(data)
    check = Checks()
    try:
        import auth  # noqa: E402
        import engine  # noqa: E402
        import paths  # noqa: E402

        project = build(root, "repo", manifest=VALID_MANIFEST)
        other = build(root, "other", manifest=VALID_MANIFEST)
        head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=project,
                              capture_output=True, text=True).stdout.strip()
        target = project / "tools" / "sacred.py"

        def write_auth(**overrides) -> None:
            record = {
                "scope": "project",
                "nonce": "nonce-test",
                "issued_at": int(time.time()),
                "expires_at": int(time.time()) + 600,
                "reason": "test",
                "repo": paths.repo_identity(str(project)),
                "repo_path": str(project),
                "head": head,
                "operations": [{"tool": "Edit", "path": "tools/sacred.py",
                                "max_uses": 2}],
            }
            record.update(overrides)
            auth.auth_path().write_text(json.dumps(record, indent=2))

        def clear_ledger() -> None:
            if auth.ledger_path().exists():
                auth.ledger_path().unlink()

        # ---- nothing issued ---------------------------------------------------
        ok, why = auth.check("Edit", str(target), str(project))
        check(not ok, "refused: no authorization exists", why)

        # ---- a valid one ------------------------------------------------------
        write_auth()
        clear_ledger()
        ok, why = auth.check("Edit", str(target), str(project))
        check(ok, "a matching authorization is accepted", why)
        d, r, layer = engine.decide_paths("Edit", [str(target)], str(project),
                                          str(project))
        check(d == "allow", "the guard allows the authorized edit", f"{d}: {r}")

        # ---- each binding broken in turn --------------------------------------
        broken = {
            "malformed file": None,
            "not an object": "[]",
            "missing scope": {"nonce": "n", "expires_at": 0, "operations": []},
            "unknown scope": {"scope": "galactic", "nonce": "n",
                              "expires_at": int(time.time()) + 60,
                              "operations": []},
            "operations not a list": {"scope": "project", "nonce": "n",
                                      "expires_at": int(time.time()) + 60,
                                      "operations": "Edit"},
        }
        for label, body in broken.items():
            if body is None:
                auth.auth_path().write_text("{not json")
            elif isinstance(body, str):
                auth.auth_path().write_text(body)
            else:
                auth.auth_path().write_text(json.dumps(body))
            ok, why = auth.check("Edit", str(target), str(project))
            check(not ok, f"refused: {label}", why)

        for label, overrides in {
            "expired": {"expires_at": int(time.time()) - 1},
            "wrong repository": {"repo": "somewhere-else-0000000000000000"},
            "wrong commit": {"head": "0" * 40},
            "expiry is not a number": {"expires_at": "soon"},
            "budget is not a number": {"operations": [
                {"tool": "Edit", "path": "tools/sacred.py", "max_uses": "lots"}]},
        }.items():
            write_auth(**overrides)
            clear_ledger()
            ok, why = auth.check("Edit", str(target), str(project))
            check(not ok, f"refused: {label}", why)

        # ---- scope and coverage ----------------------------------------------
        write_auth()
        clear_ledger()
        for tool in ("Write", "MultiEdit", "NotebookEdit"):
            ok, why = auth.check(tool, str(target), str(project))
            check(not ok, f"refused: {tool} is not the authorized tool", why)
        ok, why = auth.check("Bash", str(target), str(project))
        check(not ok, "refused: Bash can never be authorized", why)
        ok, why = auth.check("Edit", str(project / "README.md"), str(project))
        check(not ok, "refused: a path the authorization does not name", why)
        ok, why = auth.check("Edit", str(other / "tools" / "sacred.py"), str(other))
        check(not ok, "refused: the same relative path in another repository", why)
        ok, why = auth.check("Edit", str(pathlib.Path.home() / ".claude" /
                                        "settings.json"), str(project))
        check(not ok, "refused: a project authorization cannot reach outside the repo",
              why)

        # ---- the budget -------------------------------------------------------
        write_auth()
        clear_ledger()
        first = auth.check("Edit", str(target), str(project), consume=True)
        second = auth.check("Edit", str(target), str(project), consume=True)
        third = auth.check("Edit", str(target), str(project), consume=True)
        check(first[0] and second[0], "two uses are granted", f"{first[1]} | {second[1]}")
        check(not third[0], "the third is refused", third[1])
        check(auth.spent("nonce-test", "Edit", "tools/sacred.py") == 2,
              "the ledger records exactly two uses")
        auth.ledger_path().write_text("{not json\n")
        ok, why = auth.check("Edit", str(target), str(project))
        check(not ok, "refused: an unreadable ledger fails closed", why)
        clear_ledger()

        # ---- the global scope -------------------------------------------------
        home_target = pathlib.Path.home() / ".claude" / "settings.json"
        revision = paths.installed_revision()
        auth.auth_path().write_text(json.dumps({
            "scope": "global", "nonce": "nonce-global",
            "issued_at": int(time.time()), "expires_at": int(time.time()) + 600,
            "reason": "test", "plugin_revision": revision,
            "operations": [{"tool": "Edit", "path": "~/.claude/settings.json",
                            "max_uses": 1}]}))
        ok, why = auth.check("Edit", str(home_target), str(project))
        check(ok, "a global authorization covers a path under home", why)
        ok, why = auth.check("Edit", str(target), str(project))
        check(not ok, "refused: a global authorization does not cover repo paths", why)

        auth.auth_path().write_text(json.dumps({
            "scope": "global", "nonce": "nonce-global",
            "issued_at": int(time.time()), "expires_at": int(time.time()) + 600,
            "reason": "test", "plugin_revision": "some-other-revision",
            "operations": [{"tool": "Edit", "path": "~/.claude/settings.json",
                            "max_uses": 1}]}))
        ok, why = auth.check("Edit", str(home_target), str(project))
        check(not ok, "refused: issued for a different plugin revision", why)

        # ---- the Bash gate is never relaxed -----------------------------------
        write_auth(operations=[{"tool": "Edit", "path": ".claude/settings.json",
                               "max_uses": 5}])
        clear_ledger()
        for command in ("printf 'x' > .claude/settings.json",
                        "rm .claude/settings.json",
                        "rm -rf .claude/hooks"):
            d, r, layer = engine.decide_bash(command, str(project), str(project))
            check(d == "deny" and layer == engine.UNIVERSAL,
                  f"an active authorization does not relax Bash: {command}",
                  f"{d}/{layer}: {r}")

        # ---- the issuer refuses to run inside Claude --------------------------
        issuer = pathlib.Path(__file__).resolve().parents[1] / "bin" / "authorize.py"
        env = os.environ.copy()
        env["CLAUDECODE"] = "1"
        proc = subprocess.run([sys.executable, str(issuer), "--scope", "global",
                               "--minutes", "5", "--reason", "test", "--op",
                               "Edit:~/.claude/settings.json:1"],
                              capture_output=True, text=True, timeout=30, env=env)
        check(proc.returncode != 0 and "Refusing to run inside Claude" in
              (proc.stdout + proc.stderr), "the issuer refuses to run inside Claude",
              (proc.stdout + proc.stderr)[:200])

        env.pop("CLAUDECODE", None)
        for bad, why_bad in (("Edit:~/.claude/*:1", "wildcards"),
                             ("Edit:~/.claude/settings.json:99", "budget too large"),
                             ("Bash:~/x:1", "unknown tool")):
            proc = subprocess.run([sys.executable, str(issuer), "--scope", "global",
                                   "--minutes", "5", "--reason", "t", "--op", bad],
                                  capture_output=True, text=True, timeout=30, env=env)
            check(proc.returncode != 0, f"the issuer rejects {why_bad}",
                  (proc.stdout + proc.stderr)[:160])
    finally:
        shutil.rmtree(root, ignore_errors=True)

    return check.finish()


if __name__ == "__main__":
    sys.exit(main())

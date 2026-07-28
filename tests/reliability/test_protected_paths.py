#!/usr/bin/env python3
"""The harness must not be editable by the agent it constrains.

Two routes exist and both are tested:

  Write / Edit / NotebookEdit  guard_protected_paths.py  -> deny
  Bash redirect, cp, sed -i    guard_destructive_bash.py -> deny

`ask` was the first choice for the Write route and is provably wrong here: with
`permissions.defaultMode: acceptEdits`, a live Write to scripts/verify/ carrying an
`ask` verdict was accepted with no prompt. PROTECTED records that finding, so a
future change back to `ask` fails this suite instead of silently disabling it.

Closing only one is pointless: an agent blocked from Edit-ing settings.json can
otherwise reach it with `echo ... > .claude/settings.json`.

Ordinary reads of the same files stay allowed, and `git add` / `git commit` on
them stay allowed, because recording a file in version control does not change
its contents and the harness has to be committable.
"""
from __future__ import annotations

import json
import pathlib
import subprocess
import sys

REPO = pathlib.Path(__file__).resolve().parents[2]
HOOKS = REPO / ".claude" / "hooks"
EDIT_HOOK = HOOKS / "guard_protected_paths.py"
BASH_HOOK = HOOKS / "guard_destructive_bash.py"

PROTECTED = "deny"

# These paths are deliberately ones no maintenance authorization lists, so the
# expectation is fixed regardless of whether an authorization happens to be active.
# The interaction between protection and authorization — including that a listed
# path is permitted and an unlisted one is not — is covered by
# test_maintenance_auth.py against a throwaway repository.
EDIT_CASES = [
    # (tool, tool_input, expected)
    ("Write", {"file_path": str(REPO / ".claude/settings.json"), "content": "{}"}, PROTECTED),
    ("Edit", {"file_path": str(REPO / ".claude/settings.local.json")}, PROTECTED),
    ("Edit", {"file_path": str(REPO / ".claude/hooks/maintenance_auth.py")}, PROTECTED),
    ("Edit", {"file_path": str(REPO / ".claude/maintenance-uses.jsonl")}, PROTECTED),
    ("Edit", {"file_path": str(REPO / ".claude/maintenance-auth.json")}, PROTECTED),
    ("Edit", {"file_path": str(REPO / ".claude/hooks/inject_contract.py")}, PROTECTED),
    ("Edit", {"file_path": str(REPO / ".claude/reliability-contract.md")}, PROTECTED),
    ("Edit", {"file_path": str(REPO / "scripts/verify/verify_tree_equivalence.py")}, PROTECTED),
    ("Edit", {"file_path": str(REPO / "scripts/verify/authorize_maintenance.py")}, PROTECTED),
    ("Write", {"file_path": str(REPO / "scripts/verify/anything_new.py")}, PROTECTED),
    ("Write", {"file_path": "~/.claude/settings.json"}, PROTECTED),
    ("Write", {"file_path": "~/.claude/hooks/whatever.sh"}, PROTECTED),
    # Relative and traversal forms must resolve to the same verdict. Both use
    # paths no authorization lists, so the expectation does not depend on whether
    # one happens to be active — an earlier revision of this case used
    # .claude/settings.json and flipped to allow the moment it was authorized.
    ("Edit", {"file_path": ".claude/reliability-contract.md"}, PROTECTED),
    ("Edit", {"file_path": "tests/../.claude/hooks/maintenance_auth.py"}, PROTECTED),
    ("NotebookEdit", {"notebook_path": str(REPO / ".claude/hooks/x.ipynb")}, PROTECTED),
    ("MultiEdit", {"edits": [{"file_path": str(REPO / "README.md")},
                             {"file_path": str(REPO / ".claude/settings.json")}]}, PROTECTED),
    ("NotebookEdit", {"notebook_path": str(REPO / "scripts/verify/nb.ipynb")}, PROTECTED),
    # Ordinary editing is untouched.
    ("Write", {"file_path": str(REPO / "README.md")}, "allow"),
    ("Edit", {"file_path": str(REPO / "install.sh")}, "allow"),
    ("Edit", {"file_path": str(REPO / ".codex/config.toml")}, "allow"),
    ("Write", {"file_path": "/tmp/scratch.txt"}, "allow"),
    ("Write", {"file_path": str(REPO / "tests/reliability/test_new_thing.py")}, "allow"),
    ("Write", {"file_path": str(REPO / ".claude/plans/plan.md")}, "allow"),
]

BASH_CASES = [
    ("echo '{}' > .claude/settings.json", "deny"),
    ("cat /tmp/evil.json > .claude/settings.json", "deny"),
    ("cp /tmp/evil.json .claude/settings.json", "deny"),
    ("cp /tmp/evil.py .claude/hooks/guard_destructive_bash.py", "deny"),
    ("mv .claude/hooks/guard_destructive_bash.py /tmp/parked.py", "deny"),
    ("rm .claude/hooks/inject_contract.py", "deny"),
    ("sed -i '' 's/deny/allow/' .claude/hooks/guard_destructive_bash.py", "deny"),
    ("tee .claude/allowed-scripts.json < /tmp/new.json", "deny"),
    ("git checkout -- .claude/settings.json", "deny"),
    ("git restore .claude/hooks/guard_destructive_bash.py", "deny"),
    ("chmod 000 .claude/hooks/guard_destructive_bash.py", "deny"),
    ("ln -sf /tmp/fake.py .claude/hooks/guard_destructive_bash.py", "deny"),
    ("echo x >> ~/.claude/settings.json", "deny"),
    ("cp /tmp/x.py scripts/verify/bulk_mutate.py", "deny"),
    # Reading and version-controlling the harness stays allowed.
    ("cat .claude/settings.json", "allow"),
    ("grep -n hooks .claude/settings.json", "allow"),
    ("git diff .claude/settings.json", "allow"),
    ("git add .claude/hooks/guard_destructive_bash.py", "allow"),
    ("git add .claude scripts tests", "allow"),
    ("shasum -a 256 .claude/hooks/guard_destructive_bash.py", "allow"),
    ("python3 -m json.tool .claude/allowed-scripts.json", "allow"),
    ("diff .claude/settings.json /tmp/settings.json.bak", "allow"),
]


def run_hook(hook: pathlib.Path, payload: dict) -> dict:
    proc = subprocess.run([sys.executable, str(hook)], input=json.dumps(payload),
                          capture_output=True, text=True, timeout=30)
    if proc.returncode != 0 or not proc.stdout.strip():
        raise SystemExit(f"hook failed: {proc.stderr}")
    return json.loads(proc.stdout)["hookSpecificOutput"]


def main() -> int:
    failures = []
    print("Write / Edit route")
    print(f"{'EXPECT':7} {'GOT':6} TARGET")
    print("-" * 78)
    for tool, tool_input, expected in EDIT_CASES:
        out = run_hook(EDIT_HOOK, {"tool_name": tool, "cwd": str(REPO),
                                   "tool_input": tool_input})
        got = out["permissionDecision"]
        ok = got == expected
        if not ok:
            failures.append((expected, got, f"{tool} {tool_input}"))
        shown = tool_input.get("file_path") or tool_input.get("notebook_path") or "multi"
        print(f"{expected:7} {got:6} {tool}: {shown}{'' if ok else '   <-- FAIL'}")

    print("\nBash route")
    print(f"{'EXPECT':7} {'GOT':6} COMMAND")
    print("-" * 78)
    for command, expected in BASH_CASES:
        out = run_hook(BASH_HOOK, {"tool_name": "Bash", "cwd": str(REPO),
                                   "tool_input": {"command": command}})
        got = out["permissionDecision"]
        ok = got == expected
        if not ok:
            failures.append((expected, got, command))
        print(f"{expected:7} {got:6} {command}{'' if ok else '   <-- FAIL'}")

    total = len(EDIT_CASES) + len(BASH_CASES)
    print(f"\n{total - len(failures)}/{total} passed")
    for expected, got, what in failures:
        print(f"  FAIL expected={expected} got={got}: {what}")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())

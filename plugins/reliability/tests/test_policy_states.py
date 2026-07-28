#!/usr/bin/env python3
"""The three policy states, and every way a manifest can fail validation.

The state that needed the most care is INVALID. A manifest that exists but cannot
be trusted must not fall back to ABSENT: a repository that declared policy and got
it wrong would then run with less enforcement than it asked for, and nothing would
say so. So mutation is refused and reads survive, the second half being what keeps
a broken repository diagnosable.
"""
from __future__ import annotations

import json
import pathlib
import shutil
import sys
import tempfile

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from _fixture import VALID_MANIFEST, Checks, build  # noqa: E402

import engine  # noqa: E402
import policy as policy_mod  # noqa: E402

# Each entry becomes a repository whose manifest is broken in exactly one way.
BROKEN = {
    "malformed JSON": '{"policy_version": 1,',
    "not an object": '["policy_version"]',
    "no policy_version": '{"contract_version": "x"}',
    "policy_version is a string": '{"policy_version": "1"}',
    "policy_version is a bool": '{"policy_version": true}',
    "unsupported version": '{"policy_version": 99}',
    "unknown top-level key": '{"policy_version": 1, "allow_everything": true}',
    "unknown maintenance key": '{"policy_version": 1, "maintenance": {"nonce": "x"}}',
    "receipts flag not boolean": '{"policy_version": 1, '
                                 '"require_subagent_receipts": "yes"}',
    "protected escapes the repo": '{"policy_version": 1, '
                                  '"protected": ["../../etc/"]}',
    "protected is absolute": '{"policy_version": 1, "protected": ["/etc/passwd"]}',
    "allowlist is absolute": '{"policy_version": 1, "allowlist": "/tmp/a.json"}',
    "allowlist does not exist": '{"policy_version": 1, '
                                '"allowlist": ".claude/nope.json"}',
    "contract escapes the repo": '{"policy_version": 1, "contract": "../out.md"}',
}

READS = ["cat README.md", "ls -la", "git status --short", "rg TODO"]
MUTATIONS = ["touch newfile", "mkdir newdir", "cp README.md copy.md",
             "git commit -m x"]


def main() -> int:
    root = pathlib.Path(tempfile.mkdtemp(prefix="jw-states-"))
    check = Checks()
    try:
        # ---------------- absent ----------------
        absent = build(root, "absent", manifest=None)
        pol = policy_mod.load(str(absent))
        check(pol.state == policy_mod.ABSENT, "absent: state is ABSENT", pol.reason)
        need, why = engine.receipt_required(str(absent))
        check(need is False, "absent: subagent receipts not required", why)
        d, r, layer = engine.decide_bash("npm run build", str(absent), str(absent))
        check(d == "allow", "absent: ordinary build command allowed", f"{d}: {r}")
        d, r, layer = engine.decide_bash("bash deploy.sh", str(absent), str(absent))
        check(d == "allow", "absent: local script allowed", f"{d}: {r}")
        d, r, layer = engine.decide_bash("rm -rf .", str(absent), str(absent))
        check(d == "deny" and layer == engine.UNIVERSAL,
              "absent: universal denial still applies", f"{d}/{layer}: {r}")

        # ---------------- valid ----------------
        valid = build(root, "valid", manifest=VALID_MANIFEST)
        pol = policy_mod.load(str(valid))
        check(pol.state == policy_mod.VALID, "valid: state is VALID", pol.reason)
        need, why = engine.receipt_required(str(valid))
        check(need is True, "valid: subagent receipts required", why)
        d, r, layer = engine.decide_bash("npm run build", str(valid), str(valid))
        check(d == "deny" and layer == engine.POLICY,
              "valid: build indirection denied by policy", f"{d}/{layer}: {r}")
        d, r, layer = engine.decide_bash("bash deploy.sh", str(valid), str(valid))
        check(d == "allow", "valid: pinned script allowed", f"{d}: {r}")
        d, r, layer = engine.decide_bash("bash danger.sh", str(valid), str(valid))
        check(d == "deny" and layer == engine.POLICY,
              "valid: unpinned script denied", f"{d}/{layer}: {r}")
        d, r, layer = engine.decide_paths("Edit", ["tools/sacred.py"], str(valid),
                                          str(valid))
        check(d == "deny" and layer == engine.POLICY,
              "valid: manifest-protected path denied for Edit", f"{d}/{layer}: {r}")
        d, r, layer = engine.decide_paths("Edit", ["README.md"], str(valid),
                                          str(valid))
        check(d == "allow", "valid: ordinary file still editable", f"{d}: {r}")

        # A manifest reached through a symlink that stays inside the repository is
        # accepted, because its canonical target is still reviewed content.
        inside = build(root, "symlink-inside", manifest=None)
        real = inside / ".claude" / "policy-real.json"
        real.write_text(json.dumps(VALID_MANIFEST, indent=2) + "\n")
        (inside / ".claude" / "reliability-policy.json").symlink_to(real)
        pol = policy_mod.load(str(inside))
        check(pol.state == policy_mod.VALID,
              "symlinked manifest inside the repo resolves safely", pol.reason)

        # ---------------- invalid ----------------
        outside = root / "outside.json"
        outside.write_text(json.dumps(VALID_MANIFEST) + "\n")
        cases = dict(BROKEN)

        for label, text in cases.items():
            repo = build(root, "bad-" + label.replace(" ", "-"), manifest=text)
            pol = policy_mod.load(str(repo))
            check(pol.state == policy_mod.INVALID, f"invalid: {label}", pol.reason)
            d, r, layer = engine.decide_bash("cat README.md", str(repo), str(repo))
            check(d == "allow", f"invalid: {label} — read allowed", f"{d}: {r}")
            d, r, layer = engine.decide_bash("touch newfile", str(repo), str(repo))
            check(d == "deny" and layer == engine.POLICY,
                  f"invalid: {label} — mutation denied", f"{d}/{layer}: {r}")

        # Structural failures that cannot be expressed as file content.
        link_out = build(root, "symlink-outside", manifest=None)
        (link_out / ".claude" / "reliability-policy.json").symlink_to(outside)
        pol = policy_mod.load(str(link_out))
        check(pol.state == policy_mod.INVALID,
              "invalid: manifest symlink resolves outside the repository", pol.reason)

        as_dir = build(root, "manifest-is-a-dir", manifest=None)
        (as_dir / ".claude" / "reliability-policy.json").mkdir()
        pol = policy_mod.load(str(as_dir))
        check(pol.state == policy_mod.INVALID,
              "invalid: manifest is not a regular file", pol.reason)

        dangling = build(root, "manifest-dangling", manifest=None)
        (dangling / ".claude" / "reliability-policy.json").symlink_to(
            dangling / ".claude" / "gone.json")
        pol = policy_mod.load(str(dangling))
        check(pol.state == policy_mod.INVALID,
              "invalid: manifest symlink is dangling", pol.reason)

        allow_out = build(root, "allowlist-outside", manifest=None, allowlist=False)
        (allow_out / ".claude" / "allowed-scripts.json").symlink_to(outside)
        (allow_out / ".claude" / "reliability-policy.json").write_text(
            json.dumps({"policy_version": 1,
                        "allowlist": ".claude/allowed-scripts.json"}) + "\n")
        pol = policy_mod.load(str(allow_out))
        check(pol.state == policy_mod.INVALID,
              "invalid: allowlist symlink resolves outside the repository",
              pol.reason)

        # Every mutating file tool is refused under an invalid manifest, not just
        # Bash, and reads are refused by nothing.
        broken = build(root, "broken-for-tools", manifest='{"policy_version": 42}')
        for tool in ("Write", "Edit", "MultiEdit", "NotebookEdit"):
            d, r, layer = engine.decide_paths(tool, ["README.md"], str(broken),
                                              str(broken))
            check(d == "deny" and layer == engine.POLICY,
                  f"invalid: {tool} denied", f"{d}/{layer}: {r}")
        for command in READS:
            d, r, _ = engine.decide_bash(command, str(broken), str(broken))
            check(d == "allow", f"invalid: read survives — {command}", f"{d}: {r}")
        for command in MUTATIONS:
            d, r, _ = engine.decide_bash(command, str(broken), str(broken))
            check(d == "deny", f"invalid: mutation denied — {command}", f"{d}: {r}")
        need, why = engine.receipt_required(str(broken))
        check(need is False,
              "invalid: receipts not demanded, since nothing issues them", why)
    finally:
        shutil.rmtree(root, ignore_errors=True)

    return check.finish()


if __name__ == "__main__":
    sys.exit(main())

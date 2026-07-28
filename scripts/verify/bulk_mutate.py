#!/usr/bin/env python3
"""Two-phase wrapper for bulk filesystem mutation: plan, then apply a plan.

Exists because a shell loop cannot state what it is about to touch. The
historical near-miss was `for s in $STALE; do rm -rf "$dest/$s"; done` over 46
skill directories, authorised by a one-file comparison. Nothing in that command
enumerated the targets, bounded the count, or re-checked the world before acting.

Contract:
  plan   enumerates exact targets, rejects any outside --root, enforces --max,
         records repo HEAD and a plan hash over the target list and their
         current content digests.
  apply  recomputes the same digests and HEAD, and refuses if anything moved
         between planning and execution.

Exit codes: 0 ok, 1 refused (validation failed), 2 usage or internal error.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import pathlib
import shutil
import subprocess
import sys
import time

# One definition of "protected", shared with the Write/Edit guard and the Bash
# guard. Without this, the wrapper was a hole in both: it enumerated and deleted
# targets inside scripts/verify/ and .claude/hooks/ quite happily, which meant the
# reviewed tool could delete the guards that make it the reviewed tool.
PROJECT_DIR = str(pathlib.Path(__file__).resolve().parents[2])
sys.path.insert(0, os.path.join(PROJECT_DIR, ".claude", "hooks"))
from reliability_paths import is_protected  # noqa: E402
import maintenance_auth  # noqa: E402

PLAN_VERSION = 1


def protected_refusals(targets: list[str], phase: str) -> list[dict]:
    """Protected targets, minus any the owner explicitly authorized by exact path.
    A use is spent only in the apply phase, so planning stays free to be re-run."""
    refused = []
    for t in targets:
        entry = is_protected(t, PROJECT_DIR)
        if not entry:
            continue
        ok, why = maintenance_auth.check(PROJECT_DIR, "bulk_mutate.delete", t,
                                        consume=(phase == "apply"))
        if not ok:
            refused.append({"path": t, "protected_entry": entry, "reason": why})
    return refused


def repo_head(cwd: str) -> str | None:
    try:
        out = subprocess.run(["git", "rev-parse", "HEAD"], cwd=cwd,
                             capture_output=True, text=True, timeout=10)
        return out.stdout.strip() if out.returncode == 0 else None
    except Exception:
        return None


def path_type(path: str) -> str:
    if os.path.islink(path):
        return "symlink"
    if not os.path.exists(path):
        return "missing"
    return "dir" if os.path.isdir(path) else "file"


def digest(path: str) -> str:
    """Content digest for a file, or a stable digest of the recursive listing
    for a directory. Used to detect drift between plan and apply.

    Directory listings include subdirectory names, not only files, so adding an
    empty directory inside a planned target still changes the digest. Symlinks
    are digested by their target text and never followed, so substituting a
    symlink for a file changes the digest even when the link resolves to
    identical bytes."""
    h = hashlib.sha256()
    if os.path.islink(path):
        h.update(b"link:" + os.readlink(path).encode())
    elif os.path.isdir(path):
        for dirpath, dirnames, filenames in os.walk(path, followlinks=False):
            dirnames.sort()
            h.update(b"d:" + os.path.relpath(dirpath, path).encode())
            for name in sorted(dirnames):
                full = os.path.join(dirpath, name)
                h.update(b"sub:" + name.encode())
                if os.path.islink(full):
                    h.update(b"dl:" + os.readlink(full).encode())
            for name in sorted(filenames):
                full = os.path.join(dirpath, name)
                rel = os.path.relpath(full, path)
                h.update(b"f:" + rel.encode())
                if os.path.islink(full):
                    h.update(b"l:" + os.readlink(full).encode())
                elif os.path.isfile(full):
                    with open(full, "rb") as fh:
                        for chunk in iter(lambda: fh.read(65536), b""):
                            h.update(chunk)
    elif os.path.isfile(path):
        with open(path, "rb") as fh:
            for chunk in iter(lambda: fh.read(65536), b""):
                h.update(chunk)
    else:
        h.update(b"missing")
    return h.hexdigest()


def within(root: str, target: str) -> bool:
    """True only if target is strictly inside root, after resolving symlinks so
    a link cannot escape the approved root."""
    r = os.path.realpath(root)
    t = os.path.realpath(target)
    return t != r and os.path.commonpath([r, t]) == r


def plan_hash(entries: list[dict], operation: str, roots: list[str]) -> str:
    h = hashlib.sha256()
    h.update(json.dumps({"operation": operation, "roots": sorted(roots),
                         "entries": entries}, sort_keys=True).encode())
    return h.hexdigest()


def cmd_plan(args) -> int:
    roots = [os.path.abspath(r) for r in args.root]
    for r in roots:
        if not os.path.isdir(r):
            print(json.dumps({"status": "refused", "reason": f"root is not a directory: {r}"}))
            return 1

    targets = [os.path.abspath(t) for t in args.target]
    if not targets:
        print(json.dumps({"status": "refused", "reason": "no targets given"}))
        return 1

    outside = [t for t in targets if not any(within(r, t) for r in roots)]
    if outside:
        print(json.dumps({"status": "refused",
                          "reason": "targets outside approved roots",
                          "offending_targets": outside, "approved_roots": roots}, indent=2))
        return 1

    refused = protected_refusals(targets, "plan")
    if refused:
        print(json.dumps({"status": "refused",
                          "reason": "targets are reliability infrastructure",
                          "protected": refused}, indent=2))
        return 1

    missing = [t for t in targets if not os.path.exists(t)]
    if missing:
        print(json.dumps({"status": "refused", "reason": "targets do not exist",
                          "missing": missing}, indent=2))
        return 1

    if len(targets) > args.max:
        print(json.dumps({"status": "refused",
                          "reason": f"target count {len(targets)} exceeds --max {args.max}",
                          "count": len(targets), "max": args.max}, indent=2))
        return 1

    entries = [{"path": t, "type": path_type(t), "digest": digest(t)}
               for t in sorted(targets)]

    plan = {
        "plan_version": PLAN_VERSION,
        "operation": args.operation,
        "approved_roots": roots,
        "max_allowed": args.max,
        "count": len(entries),
        "repo_head": repo_head(os.getcwd()),
        "created_at": int(time.time()),
        "entries": entries,
    }
    plan["plan_hash"] = plan_hash(entries, args.operation, roots)

    with open(args.plan, "w") as fh:
        json.dump(plan, fh, indent=2)
        fh.write("\n")
    print(json.dumps({"status": "planned", "plan": args.plan,
                      "count": plan["count"], "plan_hash": plan["plan_hash"],
                      "repo_head": plan["repo_head"]}, indent=2))
    return 0


def cmd_apply(args) -> int:
    try:
        with open(args.plan) as fh:
            plan = json.load(fh)
    except Exception as exc:
        print(json.dumps({"status": "refused", "reason": f"cannot read plan: {exc}"}))
        return 1

    if plan.get("plan_version") != PLAN_VERSION:
        print(json.dumps({"status": "refused", "reason": "unsupported plan_version"}))
        return 1

    recomputed = plan_hash(plan["entries"], plan["operation"], plan["approved_roots"])
    if recomputed != plan.get("plan_hash"):
        print(json.dumps({"status": "refused", "reason": "plan file was edited after planning",
                          "expected": plan.get("plan_hash"), "recomputed": recomputed}, indent=2))
        return 1

    head_now = repo_head(os.getcwd())
    if plan.get("repo_head") != head_now:
        print(json.dumps({"status": "refused", "reason": "repository HEAD changed since planning",
                          "planned_head": plan.get("repo_head"), "current_head": head_now}, indent=2))
        return 1

    if plan["count"] > plan["max_allowed"]:
        print(json.dumps({"status": "refused", "reason": "plan exceeds its own max"}))
        return 1

    # Revalidate the world: containment, type, existence, and content digests.
    # Type is checked separately from the digest so that symlink substitution and
    # directory replacement are refused with a reason that names what changed.
    drift, escaped, retyped = [], [], []
    for e in plan["entries"]:
        p = e["path"]
        if not any(within(r, p) for r in plan["approved_roots"]):
            escaped.append(p)
            continue
        now = path_type(p)
        if now != e.get("type"):
            retyped.append({"path": p, "planned": e.get("type"), "current": now})
            continue
        if digest(p) != e["digest"]:
            drift.append({"path": p, "planned": e["digest"][:12], "current": digest(p)[:12]})
    if escaped:
        print(json.dumps({"status": "refused", "reason": "targets no longer inside approved roots",
                          "offending_targets": escaped}, indent=2))
        return 1
    if retyped:
        print(json.dumps({"status": "refused",
                          "reason": "targets changed type between planning and execution",
                          "type_changes": retyped}, indent=2))
        return 1
    if drift:
        print(json.dumps({"status": "refused",
                          "reason": "targets changed between planning and execution",
                          "drift": drift}, indent=2))
        return 1

    # Re-checked here, not only at plan time: the plan may predate the protection,
    # and a path can become protected between planning and execution.
    refused = protected_refusals([e["path"] for e in plan["entries"]],
                                 "plan" if args.dry_run else "apply")
    if refused:
        print(json.dumps({"status": "refused",
                          "reason": "targets are reliability infrastructure",
                          "protected": refused}, indent=2))
        return 1

    if args.dry_run:
        print(json.dumps({"status": "dry_run_ok", "operation": plan["operation"],
                          "would_affect": plan["count"],
                          "targets": [e["path"] for e in plan["entries"]]}, indent=2))
        return 0

    if plan["operation"] != "delete":
        print(json.dumps({"status": "refused",
                          "reason": f"unsupported operation: {plan['operation']}"}))
        return 1

    done = []
    for e in plan["entries"]:
        p = e["path"]
        if os.path.islink(p) or os.path.isfile(p):
            os.remove(p)
        else:
            shutil.rmtree(p)
        done.append(p)
    print(json.dumps({"status": "applied", "operation": plan["operation"],
                      "affected": len(done), "targets": done}, indent=2))
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("plan", help="enumerate and bind a mutation plan")
    p.add_argument("--operation", required=True, choices=["delete"])
    p.add_argument("--root", action="append", required=True,
                   help="approved root; targets must live inside one (repeatable)")
    p.add_argument("--max", type=int, required=True, help="maximum target count")
    p.add_argument("--plan", required=True, help="path to write the plan JSON")
    p.add_argument("target", nargs="*")
    p.set_defaults(func=cmd_plan)

    a = sub.add_parser("apply", help="revalidate and execute a plan")
    a.add_argument("--plan", required=True)
    a.add_argument("--dry-run", action="store_true")
    a.set_defaults(func=cmd_apply)

    args = ap.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())

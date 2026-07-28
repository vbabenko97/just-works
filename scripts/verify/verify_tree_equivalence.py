#!/usr/bin/env python3
"""Decide whether two directory trees are equivalent, and say so in JSON.

Replaces the ad-hoc comparisons that produced two documented false negatives:

  * `cmp a/SKILL.md b/SKILL.md` reported 46 skill directories identical when one
    differed only in a support file below the headline file.
  * `diff -w <(grep -v '' A) <(grep -v '' B)` compared two empty streams and
    reported identical trees that differed on 46 lines.

Both failures share a shape: a method that emits nothing for equal *and* unequal
inputs. So --self-check runs a positive control before every comparison and
refuses to report `equivalent` unless the control proved the method can detect a
difference. Content hashing uses hashlib; type and link inspection uses lstat and
readlink. Nothing here re-implements byte comparison.

Exit codes: 0 equivalent, 1 differ, 2 error or failed self-check.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import tempfile

DEFAULT_EXCLUDES = [".DS_Store", ".git"]


def classify(path: str) -> str:
    """File type without following symlinks — a followed link hides a retarget."""
    st = os.lstat(path)
    if os.path.stat.S_ISLNK(st.st_mode):
        return "symlink"
    if os.path.stat.S_ISDIR(st.st_mode):
        return "dir"
    if os.path.stat.S_ISREG(st.st_mode):
        return "file"
    return "other"


def sha256(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def walk(root: str, excludes: list[str]) -> dict[str, dict]:
    """Relative path -> {type, and hash or target}. Symlinks are never followed."""
    out: dict[str, dict] = {}
    for dirpath, dirnames, filenames in os.walk(root, followlinks=False):
        dirnames[:] = [d for d in dirnames if d not in excludes]
        for name in list(dirnames) + filenames:
            if name in excludes:
                continue
            full = os.path.join(dirpath, name)
            rel = os.path.relpath(full, root)
            kind = classify(full)
            entry: dict = {"type": kind}
            if kind == "file":
                entry["sha256"] = sha256(full)
            elif kind == "symlink":
                entry["target"] = os.readlink(full)
            out[rel] = entry
    return out


def compare(a: str, b: str, excludes: list[str]) -> dict:
    ta, tb = walk(a, excludes), walk(b, excludes)
    keys_a, keys_b = set(ta), set(tb)

    only_in_a = sorted(keys_a - keys_b)
    only_in_b = sorted(keys_b - keys_a)
    type_differs, content_differs, symlink_differs = [], [], []

    for rel in sorted(keys_a & keys_b):
        ea, eb = ta[rel], tb[rel]
        if ea["type"] != eb["type"]:
            type_differs.append({"path": rel, "a": ea["type"], "b": eb["type"]})
        elif ea["type"] == "file" and ea["sha256"] != eb["sha256"]:
            content_differs.append(rel)
        elif ea["type"] == "symlink" and ea["target"] != eb["target"]:
            symlink_differs.append({"path": rel, "a": ea["target"], "b": eb["target"]})

    equivalent = not (only_in_a or only_in_b or type_differs
                      or content_differs or symlink_differs)
    return {
        "status": "equivalent" if equivalent else "differ",
        "a": os.path.abspath(a),
        "b": os.path.abspath(b),
        "entries_compared": len(keys_a | keys_b),
        "only_in_a": only_in_a,
        "only_in_b": only_in_b,
        "type_differs": type_differs,
        "content_differs": content_differs,
        "symlink_differs": symlink_differs,
        "exclusions": sorted(excludes),
        "limitations": [
            "file mode, ownership, xattrs and mtime are not compared",
            "hardlink identity is not compared",
            f"excluded names are invisible to this run: {sorted(excludes)}",
        ],
    }


def self_check(excludes: list[str]) -> dict:
    """Positive control: prove the comparison reports `differ` on a known
    difference below the headline file, and `equivalent` on a true copy.
    Without this, a broken method that always emits nothing looks like success."""
    with tempfile.TemporaryDirectory() as tmp:
        for side, payload in (("a", b"ORIGINAL"), ("b", b"MODIFIED")):
            d = os.path.join(tmp, side, "skill", "references")
            os.makedirs(d)
            with open(os.path.join(tmp, side, "skill", "SKILL.md"), "wb") as fh:
                fh.write(b"same headline file\n")
            with open(os.path.join(d, "helper.md"), "wb") as fh:
                fh.write(payload)
        neg = compare(os.path.join(tmp, "a"), os.path.join(tmp, "b"), excludes)

        same = os.path.join(tmp, "same")
        os.makedirs(os.path.join(same, "x"))
        with open(os.path.join(same, "x", "f"), "wb") as fh:
            fh.write(b"content\n")
        pos = compare(same, same, excludes)

    detected = neg["status"] == "differ" and neg["content_differs"] == ["skill/references/helper.md"]
    return {
        "detects_secondary_file_difference": detected,
        "reports_equivalent_for_identical_tree": pos["status"] == "equivalent",
        "passed": detected and pos["status"] == "equivalent",
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("a", nargs="?")
    ap.add_argument("b", nargs="?")
    ap.add_argument("--exclude", action="append", default=None,
                    help=f"name to ignore (repeatable). default: {DEFAULT_EXCLUDES}")
    ap.add_argument("--no-default-excludes", action="store_true")
    ap.add_argument("--self-check-only", action="store_true")
    args = ap.parse_args()

    excludes = list(args.exclude or [])
    if not args.no_default_excludes:
        excludes += DEFAULT_EXCLUDES

    control = self_check(excludes)
    if not control["passed"]:
        json.dump({"status": "error", "reason": "self-check failed",
                   "self_check": control}, sys.stdout, indent=2)
        print()
        return 2

    if args.self_check_only:
        json.dump({"status": "self_check_passed", "self_check": control},
                  sys.stdout, indent=2)
        print()
        return 0

    if not args.a or not args.b:
        ap.error("two directories are required unless --self-check-only is given")
    for d in (args.a, args.b):
        if not os.path.isdir(d):
            json.dump({"status": "error", "reason": f"not a directory: {d}"},
                      sys.stdout, indent=2)
            print()
            return 2

    result = compare(args.a, args.b, excludes)
    result["self_check"] = control
    json.dump(result, sys.stdout, indent=2)
    print()
    return 0 if result["status"] == "equivalent" else 1


if __name__ == "__main__":
    sys.exit(main())

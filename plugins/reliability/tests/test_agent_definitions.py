#!/usr/bin/env python3
"""Static checks on bundled agent definitions.

This cannot test that the verifier agent actually behaves as its prompt says —
that needs a live model, not a unit test. What it can check is that the frontmatter
promise matches the declared tool set: no write/edit/notebook tool, and that the
tools actually claimed (Bash, for recomputation) are the ones the design settled on.
"""
from __future__ import annotations

import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from _fixture import Checks  # noqa: E402

AGENTS_DIR = pathlib.Path(__file__).resolve().parents[1] / "agents"
FORBIDDEN_TOOLS = {"Write", "Edit", "MultiEdit", "NotebookEdit"}


def frontmatter(path: pathlib.Path) -> dict:
    text = path.read_text()
    match = re.match(r"^---\n(.*?)\n---\n", text, re.DOTALL)
    if not match:
        return {}
    block = match.group(1)
    out = {}
    for line in block.splitlines():
        if ":" not in line:
            continue
        key, _, value = line.partition(":")
        out[key.strip()] = value.strip()
    return out


def main() -> int:
    check = Checks()
    path = AGENTS_DIR / "claim-verifier.md"
    check(path.is_file(), "claim-verifier.md exists", str(path))
    fm = frontmatter(path)
    check(bool(fm), "claim-verifier.md has parseable YAML frontmatter")

    tools_line = fm.get("tools", "")
    declared = {t.strip().strip('"[]') for t in tools_line.strip("[]").split(",")
               if t.strip().strip('"[]')}
    check(bool(declared), "tools field is present and non-empty", tools_line)

    forbidden_hit = declared & FORBIDDEN_TOOLS
    check(not forbidden_hit,
          "tools allowlist alone declares no write/edit/notebook tool",
          str(forbidden_hit))
    check("Bash" in declared,
          "Bash is declared, matching the decision to let it recompute and re-run "
          "rather than return UNKNOWN for every computational claim")
    check(declared == {"Read", "Grep", "Glob", "Bash"},
          "declared tool set is exactly Read, Grep, Glob, Bash", str(declared))

    disallowed_line = fm.get("disallowedTools", "")
    disallowed = {t.strip() for t in disallowed_line.split(",") if t.strip()}
    check(disallowed == FORBIDDEN_TOOLS - {"MultiEdit"} or
          disallowed == {"Write", "Edit", "NotebookEdit"},
          "disallowedTools explicitly denies Write, Edit, and NotebookEdit "
          "(belt-and-suspenders on top of the tools allowlist)", str(disallowed))

    check(fm.get("isolation") == "worktree",
          "isolation: worktree is declared, since Bash can mutate and this "
          "gives it a throwaway working tree instead of the caller's real one",
          fm.get("isolation"))

    body = path.read_text()
    check('"PASS"' in body and '"FAIL"' in body and '"UNKNOWN"' in body,
          "the output contract names all three verdict values")
    check("checked_scope" in body and "falsifier" in body and
          "method_suitability" in body and "limitations" in body,
          "the structured output schema includes scope, falsifier, method "
          "suitability, and limitations")
    check("read-only-except-bash" not in body.lower(),
          "the stale 'read-only-except-Bash' framing from an earlier draft is gone")
    check(any("not" in line and "read-only" in line
             for line in body.lower().splitlines()),
          "somewhere the body explicitly disclaims being read-only, rather than "
          "just calling itself read-only with no correction")
    check("worktree" in body.lower(),
          "the body documents worktree isolation, not just the frontmatter key")

    return check.finish()


if __name__ == "__main__":
    sys.exit(main())

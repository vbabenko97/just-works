#!/usr/bin/env bash
# Builds the regression fixtures for the Tier 1 reliability harness.
# Each fixture reconstructs a failure that actually happened, so the tests fail
# if the harness regresses to the behaviour that caused it.
set -euo pipefail

ROOT="${1:?usage: make_fixtures.sh <output-dir>}"
rm -rf "$ROOT"
mkdir -p "$ROOT"

# ---------------------------------------------------------------------------
# F1 — identical SKILL.md, different secondary file.
# The historical failure: `cmp` on SKILL.md alone reported 46 skill directories
# as identical. skill-creator differed only in a support file and would have
# been deleted. A comparison must look past the headline file.
# ---------------------------------------------------------------------------
f1="$ROOT/f1-secondary-file"
mkdir -p "$f1/a/skill-creator/references" "$f1/b/skill-creator/references"
printf -- '---\nname: skill-creator\n---\nbody\n' | tee \
  "$f1/a/skill-creator/SKILL.md" > "$f1/b/skill-creator/SKILL.md"
printf 'shared reference text\n' | tee \
  "$f1/a/skill-creator/references/common.md" > "$f1/b/skill-creator/references/common.md"
# The only difference lives below the headline file:
printf 'ORIGINAL support script\n' > "$f1/a/skill-creator/references/helper.md"
printf 'MODIFIED support script\n' > "$f1/b/skill-creator/references/helper.md"

# ---------------------------------------------------------------------------
# F2 — comparison that produces two empty streams.
# The historical failure: `diff -w <(grep -v '' A) <(grep -v '' B)` compared
# two empty streams and reported IDENTICAL for trees that differ on 46 lines.
# The trees below differ in content only, so any method that emits nothing for
# both inputs will wrongly pass.
# ---------------------------------------------------------------------------
f2="$ROOT/f2-empty-streams"
mkdir -p "$f2/a/doc-coauthoring" "$f2/b/doc-coauthoring"
printf -- '---\nname: doc-coauthoring\n---\nAsk Claude for help.\n' > "$f2/a/doc-coauthoring/SKILL.md"
printf -- '---\nname: doc-coauthoring\n---\nAsk Codex for help.\n'  > "$f2/b/doc-coauthoring/SKILL.md"

# ---------------------------------------------------------------------------
# F3 — the 46-directory deletion attempt.
# The historical near-miss: a loop that removed 46 skill directories from a
# destination, justified by the one-file comparison in F1.
# ---------------------------------------------------------------------------
f3="$ROOT/f3-bulk-delete"
mkdir -p "$f3/dest" "$f3/src"
for i in $(seq 1 46); do
  mkdir -p "$f3/dest/skill-$i"
  printf 'content %s\n' "$i" > "$f3/dest/skill-$i/SKILL.md"
done
# One destination entry is user-owned: it must survive any legitimate prune.
mkdir -p "$f3/dest/my-own-skill"
printf 'user authored\n' > "$f3/dest/my-own-skill/SKILL.md"
# Source ships only 2 of the 46, so 44 look "stale" to a naive comparison.
for i in 1 2; do
  mkdir -p "$f3/src/skill-$i"
  printf 'content %s\n' "$i" > "$f3/src/skill-$i/SKILL.md"
done

# ---------------------------------------------------------------------------
# F4 — symlink and type divergence.
# Not from a past failure; guards a gap the historical method also had, since
# `cmp` follows symlinks and cannot see a target change.
# ---------------------------------------------------------------------------
f4="$ROOT/f4-symlink-type"
mkdir -p "$f4/a" "$f4/b"
printf 'real\n' | tee "$f4/a/real.txt" > "$f4/b/real.txt"
ln -s real.txt "$f4/a/link"
ln -s ../elsewhere "$f4/b/link"      # same name, different target
mkdir -p "$f4/a/thing"               # directory on one side
printf 'file not dir\n' > "$f4/b/thing"   # file on the other

echo "fixtures written to $ROOT"

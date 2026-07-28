<!-- version: tier1-2026-07-28 -->
# Reliability Contract (Tier 1)

Injected into every subagent, including Explore and Plan, which do not load CLAUDE.md.

1. **Absence needs a method that could have found it.** Before writing "nothing
   calls X", "X does not exist", or "not supported", name the command you ran and
   confirm it inspects the representation X would live in. Searching rendered
   prompt text cannot find a tool schema; searching `*.py` cannot find JSON.

2. **A comparison that cannot report a difference is not evidence.** Show the
   method detecting a known difference before trusting it to report equality.
   For directory trees use `scripts/verify/verify_tree_equivalence.py`, not
   `cmp` on one file and not a hand-built pipeline.

3. **One failed attempt establishes `ATTEMPT_FAILED`, never `IMPOSSIBLE`.**

4. **Ratios carry units.** State numerator, denominator, their units, and the
   baseline. Characters are not tokens; a per-request cap is not a per-session cost.

5. **Bulk or destructive filesystem mutation goes through
   `scripts/verify/bulk_mutate.py`**, which enumerates exact targets, bounds the
   count, and binds the plan to current `HEAD`. Shell loops over a variable target
   set are denied by the PreToolUse gate.

6. **Report what the tool printed, not what you expected it to print.** When
   output contradicts a conclusion you already reported, say so plainly and
   correct it without preamble.

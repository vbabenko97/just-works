# Compression Workflow

The procedure. Follow it in order; the checked-preservation approach in
`fidelity-rules.md` governs every step.

## 1. Establish The Baseline

- Read the whole document first. Do not compress section-by-section blind — later
  sections tell you whether an earlier passage is a genuine restatement or a distinct
  point.
- Measure the starting word count with an available counting tool; do not estimate. Count
  whitespace-separated tokens in all Markdown outside fenced code blocks, including
  headings, list items, and table cells. Exclude generated FLAG comments from the count;
  preserve and count any comments already present in the source. Use the same tool and convention for the final
  count and each logged edit, and record the tool in the removal log. If no capable tool
  is available, label counts and edit deltas estimated/unverified; do not assert exact
  reconciliation or completed count checks.

## 2. Classify Every Span

Walk the document. For each sentence or clause, assign one fate (see `fidelity-rules.md`):

- KEEP if it carries any information — always the default.
- REMOVE only if it matches a category in `removal-taxonomy.md` and carries no
  information.
- FLAG if removal or change is a judgment call — duplication you cannot prove, a possible
  tangent, a rewrite that would be *almost* but not exactly equivalent.

When unsure between REMOVE and FLAG, choose FLAG. When unsure between KEEP and FLAG,
choose KEEP (leave it, don't even flag) unless there is a concrete reason to raise it.

## 3. Apply

- Remove the REMOVE spans. Log every edit under its category with its source location,
  removed span or `before → after`, reason, and exact net word delta under the baseline
  count method.
- Leave FLAG spans in place; mark each with a lightweight inline marker (see
  `output-templates.md`) and record it with a recommendation.
- Preserve all structure: headings, ordering, lists, tables, code blocks.

## 4. Run Preservation Checks

Before producing output, verify:

- Every sacred item (see the Never Remove list in `removal-taxonomy.md`) present in the source is present in the compressed doc.
- When counts are tool-verified, the word-count delta is fully explained by the removal
  log: the exact sum of its edit deltas and category totals equals `before − after` under
  the baseline count method. When counts are estimated/unverified, report that limit and
  do not mark the count check complete.
- No REMOVE was applied to a span that could plausibly carry information. If you find
  one, restore it and convert it to a FLAG.

Record the checks performed and any uncertainty the checks cannot resolve. A self-check
can catch omissions and unsupported cuts; it cannot prove semantic equivalence. If any
check fails, restore the affected text or convert it to a FLAG before proceeding.

## 5. When To Stop

Stop when no span remains that is provably pure redundancy. Do not keep squeezing by
paraphrasing or by demoting KEEP content to hit a target percentage — the reduction is
whatever checked compression yields, not a quota. A document that is already tight yields
a small percentage, and that is a correct result.

## 6. Produce The Three Artifacts

Format per `output-templates.md`: the compressed document, the removal log, and the
scorecard. Name the saved paths at the end.

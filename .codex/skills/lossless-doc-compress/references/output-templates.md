# Output Templates

Three artifacts, every run: the compressed document, the removal log, the scorecard.
Per-run outputs are saved to the working directory and are never committed to a repo.
Name the saved paths at the end of the run.

## Artifact 1: Compressed Document

The full tightened document with all structure intact. FLAG items stay in place, each
marked with a lightweight inline marker that renders invisibly but greps easily:

```markdown
<!-- FLAG: §4.2 metric list appears to duplicate §2.1 — author to confirm before any merge. -->
```

Save to `<slug>-compressed.md`, where `<slug>` is a short kebab-case name derived from the
document title.

## Artifact 2: Removal Log

The account of what was cut. Group every REMOVE by the five categories from
`removal-taxonomy.md`. For each edit, record its source location, removed span or
`before → after`, reason, and net word delta using the baseline count method. Use an
available counting tool when possible; do not present estimates as verified. Category counts and deltas must sum exactly to
the document totals only when tool-verified. Otherwise label counts and deltas
estimated/unverified, state the missing tool, and do not claim reconciliation. Then list
every flag.

```markdown
# Removal Log: <document title>

**Words:** <before> → <after> (−<percent>%)
**Count method:** <tool>; whitespace-separated Markdown tokens outside fenced code blocks, including headings, list items, and table cells; exclude generated FLAG comments, retain source comments
**Logged edits:** <n> (net −<n> words; reconciles exactly to the document total)

## Removed

### filler (<n> edits, −<n> words)

- **<source location>** (−<n> words): "It is important to note that the API is rate-limited." → "The API is rate-limited." Reason: empty transition.

### hedging (<n> edits, −<n> words)

- **<source location>** (−<n> words): <context-specific qualifier> → <shorter wording>. Reason: document why scope and certainty are unchanged.

### slop (<n> edits, −<n> words)

- **<source location>** (−<n> words): <removed wrapper or before → after>. Reason: context-free wrapper; retained claim shown above.

### restatement (<n> edits, −<n> words)

- **<source location>** (−<n> words): <removed span>. Reason: documented redundancy with <earlier location>; placement does not add context or a safety reminder.

### verbose-phrasing (<n> edits, −<n> words)

- **<source location>** (−<n> words): "at this point in time" → "now". Reason: documented preservation of scope, timing, quantity, and certainty.

## Flags (author decides — left in the document)

- **<location>** — <what> — recommend: <merge | cut | keep>. <one-line reason>.
```

If no capable counting tool is available, replace the Words, Count method, and Logged
edits lines with:

```markdown
**Words:** estimated/unverified: <before> → <after> (−<percent>%)
**Count method:** no capable counting tool available; estimates use the same exclusions for fenced code and generated FLAG comments
**Logged edits:** <n> (net word delta estimated/unverified; not reconciled)
```

Save to `<slug>-removal-log.md`.

## Artifact 3: Scorecard

A screenshot-friendly, shareable markdown block. Keep the attribution line at the top
intact and unmodified — small text, never a header.

```markdown
*Compressed with [lossless-doc-compress](https://github.com/ML-SystemDesign/MLSystemDesign/tree/main/skills) · [ML System Design](https://arseny.info/ml_design_book) by Kravchenko and Babushkin*

## Compression Scorecard: <document title>

**Result:** Tightened −<percent>% · preservation review documented · <n> flags
**Words:** <before> → <after> (tool-verified)
**Logged removals:** <n> edits · net −<n> words, reconciled to the count above
**Preservation checks:** protected content reviewed; each removal logged
**Residual uncertainty:** semantic equivalence remains unproven; <describe any source-specific uncertainty>
**Flags:** <n> judgment calls left for the author (see removal log)

**Top flag:** <the single highest-value structural suggestion, or "none">
**Takeaway:** <one reusable, non-marketing lesson from this compression>
```

When counts are estimated/unverified, label the Words and Logged removals lines that way
and omit any claim of reconciliation or completed count checks.

Save to `<slug>-compression-scorecard.md`.

## Save Rule

Default to the three filenames above in the working directory. Do not commit them. Skip a
file only when no writable filesystem is available or the user asks not to. Name every
saved path at the end of the run.

When returning an artifact inline, use an outer code fence longer than any fence inside
the artifact so embedded code blocks remain intact.

## Note On The Verdict Line

The reduction percentage is whatever checked compression produced. Do not inflate it by
demoting content to flags or by paraphrasing. If the document was already tight, a small
percentage with completed checks and stated uncertainty is the correct result.

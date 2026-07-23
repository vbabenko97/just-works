# ATS and layout constraints

Read when producing a CV that will be uploaded to an application system.

## What "ATS-safe" actually means

Applicant tracking systems parse an uploaded document into structured fields — name, contact, employers, dates, titles, skills. Parsing is the step layout affects: if extraction scrambles the text, everything downstream inherits the damage.

What happens after extraction varies by vendor. Some systems present the parsed record to a human; others run automated matching or scoring against that specific posting before a person sees it. Either way the extracted text is what gets judged, which is why it's worth reading directly.

There is no universal ATS and no such thing as certified compatibility. Vendors differ, versions differ, and some now run their own job-specific matching on top of extraction. Treat the rules below as reducing the chance of a mangled parse, not as guaranteeing anything. Be honest with the user about this — "ATS-optimized" is a marketing phrase, and promising a score they can't verify sets them up badly.

## Common extraction risks

These are the recurring culprits across vendor guidance. Behaviour varies by vendor and version — treat them as risks worth avoiding rather than guaranteed failures:

- **Tables** — text order after extraction rarely matches visual order. A two-column table of dates and roles frequently extracts as all dates then all roles, or interleaved wrongly.
- **Multi-column layouts** — the classic "sidebar with skills" design. Extraction usually reads across columns rather than down them, shredding both.
- **Headers and footers** — often dropped entirely. Never put contact details there.
- **Text boxes** — frequently invisible to extraction.
- **Graphics carrying information** — skill rating bars, icon-only contact details, charts. Anything conveyed only visually is conveyed to nobody.
- **Images of text** — a CV exported as an image is empty as far as parsing is concerned.
- **Unusual fonts** — glyph substitution produces garbled characters. Stick to widely available families.

## Safe structure

- Single column, top to bottom
- Standard section headings: `Experience`, `Education`, `Skills`, `Projects`, `Publications`. Inventive headings ("Where I've Made Impact") may not map to expected fields
- One role per block: title, employer, location, dates on their own lines
- Consistent date format throughout; spell the month or use an unambiguous numeric form
- Contact details in the document body, top of page one
- Bullets as real list items, not glyphs drawn with symbols
- `.docx` or a text-based `.pdf`. If the posting names a format, follow it exactly

## Two variants

Keep a visually designed version for humans — direct email, portfolio, hand-off by a referrer — and a plain single-column version for upload. They should carry identical facts. Divergence between them is a real risk: a recruiter reading the pretty one and an interviewer reading the parsed one should not encounter different claims.

## Verifying extraction

Run `scripts/check-pdf-extraction.sh <file.pdf>` and read its output. It runs `pdftotext -layout` and reports what the text layer contains and in what order.

What it can tell you: whether the file has a text layer at all, whether expected sections are present, and what order they come out in.

What it cannot tell you: whether any particular employer's parser will succeed. Report it to the user in those terms.

Reading the output, look for: contact details appearing near the top, employers and dates adjacent to their roles rather than pooled together, section headings intact, no runs of garbage characters.

## Keyword use

Match the vacancy's vocabulary where it is semantically true — if they say "observability" and the person's material says "monitoring", and the work genuinely was observability, use their word.

Do not repeat terms to raise density. Don't assume keyword repetition improves matching — vendor behaviour isn't uniform and you can't verify it from outside. What you can rely on is that a human reader notices the padding immediately, so it costs credibility for a benefit that may not exist.

Never introduce a technology the person hasn't used. This is the single most damaging thing a tailoring pass can do — it converts a screening rejection into a failed technical interview, and it forecloses the honest option where the person addresses the gap directly.

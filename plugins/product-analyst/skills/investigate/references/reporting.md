# Reporting

Invoke the `human-writing` skill before drafting prose. This page provides the investigation report structure.

Write for a product manager, analyst, or engineer who did not see the investigation. Define a term before using it if the reader may not know it. Use one name for each metric, segment, and time window. Mark illustrative examples as examples. Do not describe a planned capability as if it already exists.

You write the narrative: a one-line title, the answer, and an optional explanation. Open the answer with the result and its limit; put any next check that would reduce uncertainty in the explanation. The gateway appends four sections to every report, copied from the published findings without translating, rounding or summarising them:

1. the analytical contract;
2. every claim, with its kind, text, evidence IDs or context statements, verifier verdict, verifier evidence and limitations, and its four uncertainty fields;
3. the global uncertainty under data quality, metric definition, magnitude, and cause;
4. the stop reason.

Do not write these sections. Their headings are in English, so a narrative in another language gives a mixed-language report. The narrative is Markdown text: paragraphs, lists, tables and fenced code. A code block opens with a line of three backticks and an optional language name, at the start of the line, and closes with a line of exactly three backticks. The narrative cannot hold a heading, an image, a footnote or HTML; write `<` with a space after it, or "less than". These rules keep anything in the narrative from reaching into the sections the gateway appends. The gateway keeps the narrative byte for byte, including two trailing spaces that end a line with a break; end every line with `\n`, because it refuses carriage returns.

Use literal claims. Avoid slogans, unsupported certainty, repeated conclusions, and contrasts against claims nobody made. Do not disclose raw personal data, secrets, or tool output that is unnecessary to support the result. Present a claim whose verdict is `refuted` or `unverified` under that label, never among the confirmed results. Say "unavailable" for a value whose source is missing or incomplete; never write it as zero.

The narrative may state only numbers that the published claims, the uncertainty fields of data claims, the global uncertainty or the contract contain; `prepare_report` flags any other number. It ignores ISO dates, `dd.mm.yyyy` dates and dates with a month name, times, evidence IDs, URLs, ordinals, footnote markers, list numbering and fenced code blocks. Write thousands with a comma or no separator, never a plain space.

The report verifier then reads each block of the narrative against the claims. A number keeps the meaning its claim gives it: for example, a claim of 1,204 sessions from 980 users supports "1,204 sessions", not "1,204 users". The title and the answer are judged on their own, so a correct table further down does not repair a wrong title. A sum or ratio of claimed numbers needs a claim of its own.

Pass `prepare_findings` a findings object in this shape, have the verifier record its verdicts, then pass the returned `candidate_sha256`, or the same findings unchanged, to `check_claims` before writing the narrative. Each claim and the global object need exactly the four named uncertainty fields. `kind` defaults to `data`, which needs evidence IDs. A `context` claim cites `context_refs`, the names of statements in the analysis context, needs no query, and has as its text the fixed text of those statements, copied exactly; the example below shows the shape, not a real statement.

```json
{
  "claims": [
    {
      "id": "claim_activation_overall",
      "kind": "data",
      "text": "Activation was 31.5% in the current window and 46.2% in the comparison window.",
      "evidence_ids": ["ev_10", "ev_11"],
      "uncertainty": {
        "data_quality": "Instrumentation completeness is unchanged in the measured window.",
        "metric_definition": "Activation uses the governed v4 definition.",
        "magnitude": "The estimate is based on the full approved population.",
        "cause": "Not assessed for the overall change."
      }
    },
    {
      "id": "claim_activation_android",
      "kind": "data",
      "text": "Android activation declined by 14.7 percentage points.",
      "evidence_ids": ["ev_12", "ev_18"],
      "uncertainty": {
        "data_quality": "Instrumentation completeness is unchanged in the measured window.",
        "metric_definition": "Activation uses the governed v4 definition.",
        "magnitude": "The estimate is based on the full approved population.",
        "cause": "The evidence does not establish a release cause."
      }
    },
    {
      "id": "claim_source_unavailable",
      "kind": "context",
      "text": "Activation by acquisition source is unavailable: no visit carries a source to sign-up.",
      "context_refs": ["attribution_unavailable"],
      "uncertainty": {
        "data_quality": "Not applicable: no source data exists.",
        "metric_definition": "No agreed source attribution exists.",
        "magnitude": "Not measurable.",
        "cause": "Not assessed."
      }
    }
  ],
  "stop_reason": "INCONCLUSIVE",
  "uncertainty": {
    "data_quality": "Instrumentation completeness is unchanged in the measured window.",
    "metric_definition": "Activation uses the governed v4 definition.",
    "magnitude": "The estimate is based on the full approved population.",
    "cause": "The evidence does not establish a release cause."
  }
}
```

After `check_claims` has published those findings, pass `prepare_report` a narrative in this shape:

```json
{
  "title": "Activation fell in the current window, concentrated in Android sessions",
  "answer": "Activation was 31.5% in the current window and 46.2% in the comparison window. The evidence supports a concentration in Android sessions; it does not establish the release as the cause. Activation by acquisition source is unavailable.",
  "explanation": "A source-level comparison needs a visit-to-sign-up link first."
}
```

The gateway assembles `report.md` from it. An excerpt of the result:

```markdown
# Activation fell in the current window, concentrated in Android sessions

Activation was 31.5% in the current window and 46.2% in the comparison window. ...

A source-level comparison needs a visit-to-sign-up link first.

## Contract

- comparison: previous week
- metric: activation
...

## Claims

### Claim claim\_activation\_overall

- Kind: data
- Text: Activation was 31.5% in the current window and 46.2% in the comparison window.
- Evidence: `ev_10`, `ev_11`
- Context statements: none
- Verifier verdict: supported
...

## Uncertainty

- Data quality: Instrumentation completeness is unchanged in the measured window.
...

## Stop reason

INCONCLUSIVE
```

`prepare_report` returns a `version_sha256`. The report verifier records its verdicts for that version, and `check_report` writes `report.md` when every authored block is supported. Any change to the narrative or the findings makes a new version that needs its own verification. Once a report is accepted, the investigation's findings are fixed: publishing other findings needs a new investigation. `check_report` never replaces an existing `report.md`, an earlier accepted one included: to publish a revised narrative, the accepted file has to be moved aside first. In your final message give the path of `report.md` or its text unchanged; do not restate its numbers in other words.

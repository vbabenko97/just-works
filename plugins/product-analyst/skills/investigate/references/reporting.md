# Reporting

Invoke the `human-writing` skill before drafting prose. This page provides the investigation report structure.

Write for a product manager, analyst, or engineer who did not see the investigation. Define a term before using it if the reader may not know it. Use one name for each metric, segment, and time window. Mark illustrative examples as examples. Do not describe a planned capability as if it already exists.

Open with the answer and its limit. Then include:

1. the analytical contract;
2. claims, each with evidence IDs or context statements and its verifier verdict;
3. uncertainty under data quality, metric definition, magnitude, and cause;
4. the stop reason and any next check that would reduce uncertainty.

Use literal claims. Avoid slogans, unsupported certainty, repeated conclusions, and contrasts against claims nobody made. Do not disclose raw personal data, secrets, or tool output that is unnecessary to support the result. Present a claim whose verdict is `refuted` or `unverified` under that label, never among the confirmed results. Say "unavailable" for a value whose source is missing or incomplete; never write it as zero.

The report may state only numbers that the published claims, the uncertainty fields of data claims, the global uncertainty or the contract contain; `check_report` flags any other number. It ignores ISO dates, `dd.mm.yyyy` dates and dates with a month name, times, evidence IDs, URLs, ordinals, footnote markers, list numbering and fenced code blocks. Write thousands with a comma or no separator, never a plain space.

Pass `prepare_findings` a findings object in this shape, have the verifier record its verdicts, then pass the returned `candidate_sha256`, or the same findings unchanged, to `check_claims` before writing `report.md`. Each claim and the global object need exactly the four named uncertainty fields. `kind` defaults to `data`, which needs evidence IDs. A `context` claim cites `context_refs`, the names of statements in the analysis context, needs no query, and has as its text the fixed text of those statements, copied exactly; the example below shows the shape, not a real statement.

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

Example report shape:

```markdown
# Activation fell in the current window, concentrated in Android sessions

Activation was 31.5% in the current window and 46.2% in the comparison window. The evidence supports a concentration in Android sessions; it does not establish the release as the cause.

## Contract

Metric: Activation v4. Population: new non-internal workspaces. Timezone: Europe/Vienna. Current window: ... Comparison: ...

## Evidence-backed claims

- Activation was 31.5% in the current window and 46.2% in the comparison window. Evidence: `ev_10`, `ev_11`. Verifier: supported.
- Android activation declined by 14.7 percentage points. Evidence: `ev_12`, `ev_18`. Verifier: supported.
- Activation by acquisition source is unavailable: no visit carries a source to sign-up. Context: `attribution_unavailable`. Verifier: supported.

## Uncertainty

Data quality: ...
Metric definition: ...
Magnitude: ...
Cause: ...

Stop reason: INCONCLUSIVE.
```

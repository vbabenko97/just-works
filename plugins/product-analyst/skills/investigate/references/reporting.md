# Reporting

Invoke the `human-writing` skill before drafting prose. This page provides the investigation report structure.

Write for a product manager, analyst, or engineer who did not see the investigation. Define a term before using it if the reader may not know it. Use one name for each metric, segment, and time window. Mark illustrative examples as examples. Do not describe a planned capability as if it already exists.

Open with the answer and its limit. Then include:

1. the analytical contract;
2. claims, each with evidence IDs;
3. uncertainty under data quality, metric definition, magnitude, and cause;
4. the stop reason and any next check that would reduce uncertainty.

Use literal claims. Avoid slogans, unsupported certainty, repeated conclusions, and contrasts against claims nobody made. Do not disclose raw personal data, secrets, or tool output that is unnecessary to support the result.

Pass `check_claims` a findings object in this shape before writing `report.md`. Each claim and the global object need exactly the four named uncertainty fields.

```json
{
  "claims": [
    {
      "id": "claim_activation_android",
      "text": "Android activation declined by 14.7 percentage points.",
      "evidence_ids": ["ev_12", "ev_18"],
      "uncertainty": {
        "data_quality": "Instrumentation completeness is unchanged in the measured window.",
        "metric_definition": "Activation uses the governed v4 definition.",
        "magnitude": "The estimate is based on the full approved population.",
        "cause": "The evidence does not establish a release cause."
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

- Android activation declined by 14.7 percentage points. Evidence: `ev_12`, `ev_18`.

## Uncertainty

Data quality: ...
Metric definition: ...
Magnitude: ...
Cause: ...

Stop reason: INCONCLUSIVE.
```

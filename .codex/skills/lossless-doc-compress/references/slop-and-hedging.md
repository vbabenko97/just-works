# Slop And Hedging Patterns

Concrete patterns with before → after rewrites. Use a rewrite only when its preservation
case is documented; if a rewrite could lose information or uncertainty, it belongs as a
FLAG instead (see `fidelity-rules.md`).

## Filler And Empty Transitions

- "It is important to note that the API is rate-limited." → "The API is rate-limited."
- "In order to reduce latency, we cache results." → "To reduce latency, we cache results."
- "As mentioned above, the model retrains nightly." → "The model retrains nightly."
- "The fact that the dataset is small means we cross-validate." → "The small dataset
  means we cross-validate."
- "It goes without saying that we log errors." → "We log errors."

## Qualifiers That Need Context

- "This is basically a ranking problem." — FLAG or KEEP. "Basically" may limit the claim.
- "The results are essentially identical." — KEEP. "Essentially" preserves a material
  qualification; do not rewrite this as "identical."
- "We arguably need a fallback." — KEEP or FLAG. "Arguably" can state uncertainty or
  attribution.
- "It seems that throughput drops under load." — KEEP unless the author confirms the
  underlying claim and removal of the uncertainty.

## LLM Slop

- "In today's fast-paced, data-driven world, forecasting is more important than ever."
  → FLAG the claim. If the opening context is a checked empty wrapper, remove only it and
  retain "Forecasting is more important than ever."
- "In conclusion, this design addresses the requirements outlined above." → "This design
  addresses the requirements outlined above." only when the conclusion wrapper is empty.
  KEEP or FLAG the remaining claim unless it is documented as redundant.
- "It is worth mentioning that this section covers monitoring." → "This section covers
  monitoring." (or remove if the heading already says so)
- "Let's dive into the architecture." → (remove; the heading is the transition)

## Restatement

- Two paragraphs both defining the same metric: keep the clearer one, remove the echo,
  and log it as `restatement` only after documenting that the later placement adds no
  context or safety reminder. Keep a repeated warning when it qualifies the action beside
  it. Never merge their numbers — if the two give *different* numbers, that is a FLAG (a
  contradiction the author must resolve), not a removal.

## Potentially Shorter Phrasing

These are candidates, not default rewrites. Use one only when the source context
documents preserved scope, quantity, timing, and certainty; otherwise KEEP or FLAG it.

- "at this point in time" → "now"
- "in the event that" → "if"
- "a large number of" → "many"
- "due to the fact that" → "because"
- "has the ability to" → "can"
- "in the near future" → KEEP or FLAG unless context supports the same time window. The
  absence of a specific date does not establish that "soon" means the same thing.

## Looks Like Slop But KEEP

Not everything soft is removable. These carry information — leave them:

- "We are not yet confident this generalizes beyond the pilot region." — a real, scoped
  uncertainty. KEEP.
- "Roughly 200ms, pending load testing." — "roughly" and "pending" are caveats on a
  number. KEEP both the number and the caveat.
- "Historically, this approach failed for sparse users." — "historically" anchors a
  factual claim. KEEP.

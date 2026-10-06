# Analytical method

First verify the measure. State the numerator, denominator, population, exclusions, window, timezone, and comparison. Check volume and data freshness before describing a change as real.

For a rate, inspect both numerator and denominator. For a time-series change, compare equivalent windows and account for partial days, releases, acquisition mix, and instrumentation changes. Break down only dimensions that test a stated hypothesis. Do not search every available dimension until one produces a compelling pattern.

Separate observations from explanations. An observation may be supported by a direct aggregate. A causal explanation needs a plausible mechanism and evidence that distinguishes it from alternatives. Correlation in an event timeline is not proof of cause.

Use `INCONCLUSIVE` when evidence does not distinguish competing explanations. Use `REFUTED` when evidence contradicts the claim. Use `SUPPORTED` only when the stated evidence supports the limited claim being made.


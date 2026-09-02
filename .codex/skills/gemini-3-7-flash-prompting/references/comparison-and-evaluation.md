# Comparison and evaluation

`gemini-3.7-flash` is a model/API, not a complete coding-agent product. A capable harness can supply repository context, tools, sandboxing, retries, approvals, checkpoints, tests, and a user interface; those parts can make Gemini credible for coding-agent work. The model alone is therefore not a replacement for Codex, which is a complete agent experience with its own model, tooling, and workflow integration.

Compare systems at the same boundary: model calls against model calls, or complete harnesses against complete harnesses. Do not attribute harness strengths or failures to a model without evidence.

## Evaluation framework

Use a fixed, representative task set with expected behavior and realistic repositories. Run enough repetitions to capture tool and retry variance.

| Measure | Record |
| --- | --- |
| Accepted outputs | Human or automated acceptance rate; severity-weighted defects; spec compliance. |
| Regressions | New failing tests, behavioral breaks, security or migration mistakes. |
| Latency | Wall-clock time to an accepted result, including tool time and review/rework. |
| Retries | Model calls, tool retries, recovery attempts, and human interventions per task. |
| Tool reliability | Call success rate, argument errors, permission failures, and identifier/history protocol failures. |
| Total cost per accepted result | All model, tool, infrastructure, and human-review cost divided by accepted outcomes. |

Report distributions, not only averages: task category, p50/p95 latency, and failure modes explain whether a system is dependable. Keep model/version, harness version, prompt, tools, permissions, task fixtures, and acceptance rubric fixed during a comparison. Avoid stale list-price claims; use current official pricing and product pages at decision time.

Useful primary sources: [Google Gemini 3.7 Flash guide](https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/guides/gemini-3-7-flash), [OpenAI Codex](https://developers.openai.com/codex/), and [OpenAI model comparison](https://developers.openai.com/api/docs/models/compare).

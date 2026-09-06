# Verified model profile

Snapshot: **2026-09-06**. Sources are indexed in `sources.json`.

## Facts specific to this target

| Property | Verified value | Source |
| --- | --- | --- |
| API model ID | `gemini-3.8-flash` (stable) | S01 |
| Inputs | Text, images, audio, video, PDF | S01 |
| Output | Text; not native image or audio generation | S01 |
| Token limits | 1,048,576 input; 65,536 output | S01 |
| Thinking levels | `low`, `medium`, `high`; default `medium` | S04 |
| Invalid thinking choice | `minimal` is unsupported | S01 |
| Selected capabilities | Structured output, function calling, search grounding, URL context, code execution | S01 |

Capability support does not mean a tool is enabled in a particular conversation.
Check the chosen API, application, permissions, and supplied tools.

## 3.8 migration guardrails

Google's 3.8 migration guidance says to omit `temperature`, `top_p`, `top_k`,
and `candidate_count`, replace `thinking_budget` with `thinking_level`, and
remove prefilled model turns. [S02]

Older generic Gemini advice about setting temperature to 1.0 is not the rule
for this target. Prefer the exact model's migration documentation over general
family guidance when they conflict. [S02, S03]

## This skill's effort-selection heuristic

Start with the documented default. Test a lower effort for simple extraction or
short drafting; test higher effort for genuinely difficult multi-step analysis.
Choose using measured task quality and latency, not the word "Flash". A short
answer does not necessarily imply low computation. These are evaluation choices,
not a guarantee that any preset is optimal.

Do not invent an exact knowledge cutoff or promise Gemini app/Vertex AI feature
parity from this API profile. Prices and account entitlements are deliberately
not frozen into the skill; verify them when relevant.

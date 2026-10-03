# API and agent-loop notes

Verified against primary documentation on **2026-10-03**. Re-check before shipping
an integration. Source keys resolve in [UPSTREAM.md](../UPSTREAM.md). These are
recommendations to an implementer, not instructions to modify the current session.
Claude API settings are not automatically Claude Code flags or gateway settings.

## 1. Effort and output budget — S3

Start a requested calibration at `medium`; use `low` as a candidate for
latency-sensitive or formerly thinking-disabled traffic. Compare quality as well
as latency and total output tokens. Reserve higher settings for measured benefit.
Effort is not a token cap. `max_tokens` includes thinking even when its text is
hidden. Choose a workload-appropriate ceiling; do not set the maximum everywhere.

The following is an illustrative short-task request, not a universal budget or a
complete agent implementation. It is intentionally not executable here.

```json
{
  "model": "claude-opus-5-5",
  "max_tokens": 8192,
  "output_config": {"effort": "medium"},
  "messages": [
    {"role": "user", "content": "Compare the two supplied proposals against the stated acceptance criteria."}
  ]
}
```

Changing request-level effort disrupts cache reuse. Per-message effort is a
separate beta (`mid-conversation-output-config-2026-07-01`); consult **S3** for exact
placement and effective-turn rules. Do not confuse it with a status reminder or
silently vary it in a cached production conversation.

## 2. Migration gate — S10

For the direct Claude API, `claude-opus-5-5` is the documented model ID. Verify
provider-specific IDs instead of constructing them. Check the starting model:
not every item below is newly different from Opus 5.

| Check | Opus 5.5 requirement |
| --- | --- |
| Thinking | Omit `thinking` or use `type: "adaptive"`; disabled and manual-budget modes are rejected |
| Tool selection | Use `auto` or `none`; forced `any` or a named `tool` is rejected |
| Sampling | Omit `temperature`, `top_p`, and `top_k`; non-default values are rejected |
| Assistant prefill | Remove trailing prefilled assistant turns; use an output contract or supported structured output |
| Response reading | Branch on block type, not `content[0].text` |

Prompting a tool's use does not guarantee it runs. Validate required tool activity
in the application; strict argument schemas are not a substitute for execution.

Computer-use declarations changed on the Claude API and Google Cloud to
`computer_toolset_20260801`; do not blindly apply this to Bedrock. See **S11** and
the relevant platform documentation. Validate the whole loop, not just a model ID.

## 3. Progress rendering — S4

Between-tool updates arrive as `thinking` blocks. Default `display: "omitted"`
returns no readable update text. For updates without reasoning summaries, use:

```json
{
  "thinking": {"type": "adaptive", "display": "updates"}
}
```

On the direct API, pair it with:

```text
anthropic-beta: thinking-display-updates-2026-08-18
```

Under this display mode, render nonempty `thinking` text as progress and ordinary
`text` blocks as answer text. Do not render signatures. With `summarized`, both
reasoning and update summaries may appear; do not label every such block a status.

Preserve every assistant block exactly when replaying tool loops, including empty
thinking blocks and signatures. Rendering a filtered view must not filter stored
history. An update summary is not guaranteed to preserve a code snippet verbatim;
use a declared message-delivery tool for exact intermediate payloads, when supported.

## 4. History and reminders — S5, S6

Keep replayed history append-only. Editing the earlier system prompt, tools, or
messages can invalidate thinking blocks. Prefix enforcement depends on account
and platform details; verify those rather than assuming all old accounts behave
like new ones. Do not silently strip reasoning state to conceal an integration bug.

For an approved custom harness, a turn-scoped reminder can be appended after the
latest user/tool-result message. **S6** documents the beta header
`mid-conversation-system-clear-at-2026-08-21` and the following shape:

```json
{
  "role": "system",
  "clear_at": "next_user_message",
  "content": "A brief progress note is due; report the current finding and continue the authorized work."
}
```

Leave prior reminders in history. A later user message—including one containing
only tool results—clears their rendered effect; do not delete their entries.
Do not insert a system message between a tool call and its result. Never promote
retrieved content into a system message. Confirm provider support before use.

Suggested local policy: after five steps with no visible update, issue a reminder;
cap these reminders at two per run. These are configurable guardrails, not API
limits or a claim that the model emits updates on schedule.

## 5. Completion and stop handling — S12

`end_turn` marks the end of a response, not your application's acceptance test.
`max_tokens` and `model_context_window_exceeded` require incomplete-output handling;
`pause_turn` and `tool_use` require their documented continuation procedures.
Never parse a truncated artifact as a successful result.

Suggested application completion gate:

```text
Respect cancellation, permissions, and hard resource limits first.
On refusal: stop this workstream and follow the refusal policy.
On pending tool work: collect the actual results before judging completion.
On truncation or provider failure: record incomplete; use an approved recovery path.
On end_turn:
  complete + acceptance evidence checked -> DONE
  blocked or approval required          -> BLOCKED / AWAITING_APPROVAL
  incomplete and continuation allowed   -> name open items in a new user message
  continuation limit reached            -> INCOMPLETE; hand off evidence and state
```

Local default: at most **two automatic continuations total per task**, not two after
every step; do not reset the counter on a status update. Do not continue a refusal,
protected action, cancellation, or exhausted budget. Keep outstanding subagent and
command results in the task state. Do not implement `while true: continue`.

## 6. Refusals and explanations — S7

Inspect `stop_reason` and `stop_details`; a refusal is not a server exception or
proof that the task has no evidence. For `reasoning_extraction`, remove requests
for private reasoning from prompts, skills, tool descriptions, and output schemas.
Use a concise evidence-based explanation; supported `display: "summarized"` exposes
summaries, not raw internal reasoning. Do not retry the same extraction request.

Treat partial refused output as incomplete. Do not use fallback to evade safeguards.
Any legitimate fallback needs prior authorization, provider compatibility, cost
limits, and the application's safety policy. For persistent false positives,
preserve the request ID and use the provider's support or verification process.

## 7. Evaluate before adoption

The included [evals](../evals/evals.json) test this skill's outputs, not the model's
performance on every downstream task. They are synthetic specifications, not
completed live evaluations. The offline validator checks structure only.

For an authorized comparison, freeze the task set, available evidence, tools,
validators, and baseline prompt. Change one factor at a time. Record task
completion, evidence correctness, omissions, tool behavior, refusals, latency,
total tokens, and cost. Specify acceptance thresholds before looking at results.
Do not infer deployment reliability from a single repaired example.

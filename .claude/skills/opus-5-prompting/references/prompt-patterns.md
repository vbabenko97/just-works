# Claude Opus 5 prompt patterns

## 1. Lean task prompt

```text
Task
Determine whether [proposal] should proceed.

Context
[Only the facts and source material required for the decision.]

Requirements
Evaluate [criteria]. Separate verified facts from assumptions. Cite the evidence used. Do not invent unavailable measurements or silently change the decision criteria.

Scope
Complete the requested assessment only. Mention a materially better framing in one sentence, then continue with the requested analysis.

Output
Give a clear go/no-go verdict, decisive evidence, material risks, unresolved uncertainty, and the smallest next test that could change the decision. Keep the response under [N] words.
```

Remove headings when a short paragraph communicates the same contract.

## 2. Agentic implementation prompt

```text
Implement [feature or fix] in [repository or environment].

Requirements
- Preserve [interfaces, compatibility, safety, performance, or style constraints].
- Inspect relevant files and make the requested in-scope changes.
- Run the smallest relevant non-destructive validation after editing.
- Do not leave placeholders, stubs, or unimplemented branches.

Execution
Use tools directly. Before the first tool call, state the approach in one sentence. Update the user only after a material finding, blocker, or change of direction.

Scope
Make routine judgment calls yourself. Ask only when materially different interpretations would produce different implementations. Do not refactor unrelated code.

Delegation
Delegate only a substantial independent investigation or implementation track. Do not spawn subagents merely to verify your own work. Maximum subagents: [N].

Completion
Lead with what changed and whether validation passed. Then list affected files, important design choices, and any unresolved limitation.
```

## 3. Code review prompt

```text
Review [diff, pull request, or codebase] for correctness, security, reliability, and maintainability defects.

Report every finding that could change behavior or create operational risk. Do not suppress findings during discovery based on severity. After discovery, classify each finding as blocker, high, medium, or low.

For each finding include:
- exact file and location;
- the failure mode;
- a concrete reproduction or reasoning chain;
- the smallest safe fix;
- confidence and any missing evidence.

Do not report style preferences unless they cause a real defect. Do not use a verifier subagent solely to repeat the review.
```

This separates discovery from severity filtering, avoiding overly literal suppression of valid findings.

## 4. Long-context research prompt

```text
<documents>
  <document id="1">
    <source>[source metadata]</source>
    <content>[document text]</content>
  </document>
  <document id="2">
    <source>[source metadata]</source>
    <content>[document text]</content>
  </document>
</documents>

<task>
Answer [research question].
</task>

<requirements>
First identify the passages that materially support or contradict the answer. Then synthesize the conclusion. Distinguish source claims, your inferences, and unresolved gaps. Cite each consequential factual claim to the relevant document. Do not use irrelevant context merely because it is present.
</requirements>

<output>
Verdict, evidence, disagreements, uncertainty, and recommendation. Maximum [N] words.
</output>
```

Put documents before the task and query.

## 5. Tool-routing prompt

```text
Use [tool A] when [specific condition]. It returns [important fields and error behavior].
Use [tool B] when [specific condition]. It returns [important fields and error behavior].

For independent reads with known parameters, call tools in parallel. For dependent operations, wait for the prerequisite result. Never invent missing identifiers or tool arguments.

When the user's request is to change or execute something, perform the authorized action rather than merely suggesting it. Stop and report the blocker when no available tool can safely perform the required action.
```

Expose only tools relevant to the current task.

## 6. Concision control

Avoid relying on effort to shorten visible responses.

```text
Lead with the answer. Keep all required findings, evidence, caveats, and next steps. Remove filler introductions, generic background, repeated summaries, and self-congratulatory narration. Target [N] words or [N] sections.
```

## 7. Progress-update control

### Minimal narration

```text
Before the first tool call, give one sentence describing the approach. During execution, update the user only after a material finding, blocker, or change of direction. At completion, lead with the outcome.
```

### Silent agent

```text
Do not narrate routine execution. Use tools and return only the final result, except when a blocker requires user input.
```

### High-visibility agent

```text
Before execution, state the plan in up to three sentences. After each completed phase, report the result, evidence, and next phase in no more than two sentences. Do not expose hidden reasoning.
```

## 8. Scope-control patch

Use when Opus 5 adds unrequested work:

```text
Deliver exactly the requested outcome at the intended scope. Make routine judgment calls yourself. Ask only when materially different interpretations would produce different work. If the request appears mistaken or a better approach exists, mention it briefly and continue with the requested task. Stop before unrelated refactors, external writes, purchases, destructive changes, or other actions not authorized by the request.
```

## 9. Delegation-control patch

Use when the harness spawns too many subagents:

```text
Delegate only independent tracks that are substantial enough to benefit from separate context. Do not delegate work you can finish in a few tool calls. Do not use subagents merely to verify or repeat your own analysis. Prefer one subagent to several overlapping agents. Maximum concurrent subagents: [N]. Maximum total subagents: [N].
```

## 10. Thinking-disabled mitigation

Prefer enabling thinking at a lower effort. Where disabled thinking is mandatory:

```text
You may briefly announce a tool call. When no available tool can perform the request, report that limitation rather than fabricating an action. Keep internal control tags out of user-visible text.
```

Runtime constraints:

```text
thinking: {type: "disabled"}
effort: low | medium | high
```

Never combine disabled thinking with `xhigh` or `max`.

## 11. Legacy migration example

### Before

```text
You are a world-class expert. Think step by step and be maximally thorough. Double-check every conclusion. Always use a verifier subagent. Use every available tool. Never stop until the result is perfect. Be concise. Provide frequent progress updates. Ask before making any judgment call.

Fix the failing data export pipeline.
```

### After

```text
Diagnose and fix the failing data export pipeline.

Inspect the relevant code, configuration, logs, and tests. Implement the smallest safe in-scope fix and run targeted non-destructive validation. Preserve existing data contracts and deployment boundaries. Do not refactor unrelated components.

Make routine judgment calls yourself. Ask only when different interpretations would produce materially different fixes. Delegate only a substantial independent investigation; do not spawn a verifier merely to repeat your work.

Before the first tool call, state the approach in one sentence. Update the user only after a material finding, blocker, or change of direction. Finish with the root cause, changes made, validation results, and any remaining risk in under 500 words.
```

Material improvements:

- Replaces generic reasoning commands with a concrete outcome.
- Removes redundant verification that compounds Opus 5's built-in behavior.
- Replaces blanket tool use with relevant evidence sources.
- Defines autonomy, scope, progress cadence, and final length.
- Prevents unnecessary verifier spawning.

## 12. Debugging matrix

When behavior is wrong, test the smallest relevant change:

- **Too verbose**: add a word or section target; do not lower effort merely for visible brevity.
- **Too much narration**: specify update cadence or silent execution.
- **Overthinking or high cost**: test one lower effort level before deleting useful prompt context.
- **Scope expansion**: add the scope-control patch.
- **Too many subagents**: add delegation criteria and deterministic caps.
- **Repeated verification**: remove explicit self-check and verifier instructions.
- **Advice instead of action**: change "suggest" or "consider" to "implement," "edit," or "execute."
- **Tool underuse**: state the condition that requires the tool and the action expected after its result.
- **Tool overuse**: replace blanket tool mandates with conditional routing rules.
- **Incomplete output**: specify required fields and an acceptance checklist; raise `max_tokens` if thinking consumes the limit.
- **Visible tool-call text or internal tags**: re-enable thinking at lower effort, or use the thinking-disabled mitigation.
- **400 request errors**: inspect thinking/effort compatibility, non-default sampling parameters, manual thinking budgets, and assistant prefills.

Change one variable at a time when diagnosing production behavior.

## 13. Effort evaluation

Build a representative set containing:

- Routine tasks.
- Hard multistep reasoning.
- Long-horizon tool use.
- Large-context analysis.
- Tool failures and empty results.
- Narrow-scope requests vulnerable to expansion.
- Tasks where a complete deliverable is longer than the model's default answer.
- Cases near safety or authorization boundaries.

Test at least `medium`, `high`, and `xhigh`; include `low` for high-volume tasks and `max` only for capability-critical work.

Record:

```text
case_id
prompt_version
effort
success (0/1)
required_fields_present (0/1)
evidence_correct (0/1)
scope_compliant (0/1)
tool_route_correct (0/1)
unnecessary_tool_calls
subagent_count
repeated_verification_count
visible_word_count
input_tokens
thinking_tokens
output_tokens
latency_ms
cost
```

Adopt a lower effort when critical-case quality remains non-inferior and savings are meaningful. Adopt a higher effort only when the measured quality gain justifies the additional latency and cost.

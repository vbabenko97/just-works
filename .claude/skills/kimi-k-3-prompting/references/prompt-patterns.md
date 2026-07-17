# Kimi K3 prompt patterns

## Contents

- General task prompt
- Reference-grounded answer
- Long-document synthesis
- Scenario routing
- Tool-using agent contract
- Migration example
- Evaluation checklist

## General task prompt

```text
Objective
Produce [specific outcome] for [audience/use].

Context
- [Relevant fact]
- [Relevant constraint]

Instructions
1. [Required operation]
2. [Required operation whose order matters]
3. [Quality, evidence, safety, or permission rule]

Output
- [Required sections or schema]
- [Length in sections, paragraphs, sentences, or bullets]

Fallback
If [required input/evidence] is missing, state what is missing and do not invent it.
```

Use fewer headings when the request is simple.

## Reference-grounded answer

```text
Answer the question using only the material inside <sources>.

Rules
- Support each substantive claim with the relevant source identifier.
- Distinguish explicit source statements from your own inference.
- If the sources conflict, describe the conflict instead of silently choosing one.
- If the answer is absent, respond: "Not found in the provided sources."
- If the sources are retrieved excerpts rather than exhaustive coverage, say "Not found in the retrieved excerpts" and do not generalize to the whole corpus.

<question>
{{QUESTION}}
</question>

<sources>
{{SOURCE_MATERIAL}}
</sources>

Output
Give the answer first, followed by concise supporting evidence.
```

## Long-document synthesis

Use a map-reduce workflow when exhaustive coverage matters.

### Chunk prompt

```text
Analyze section {{SECTION_ID}} of a larger document.

Extract:
1. Main claims.
2. Evidence and exact source locations.
3. Decisions, risks, and open questions.
4. Dependencies on earlier sections.
5. Facts that must survive final synthesis.

<prior_summary>
{{RELEVANT_EARLIER_SUMMARY}}
</prior_summary>

<section>
{{SECTION_TEXT}}
</section>
```

### Synthesis prompt

```text
Combine the section summaries into one answer to <question>.

Requirements
- Preserve disagreements, uncertainty, and provenance.
- Deduplicate repeated claims without dropping distinct evidence.
- Check that each requested section and source range is represented.
- Do not introduce facts absent from the summaries.

<question>{{QUESTION}}</question>
<section_summaries>{{SUMMARIES}}</section_summaries>
```

## Scenario routing

```text
First classify the request as exactly one of:
- billing
- technical_support
- account_security
- other

Then apply only the matching instruction block. If confidence is low, ask one clarifying question rather than combining branches.

<billing_rules>...</billing_rules>
<technical_support_rules>...</technical_support_rules>
<account_security_rules>...</account_security_rules>
<other_rules>...</other_rules>
```

For programmatic systems, prefer routing in application code and send only the selected instruction block when practical.

## Tool-using agent contract

```text
Goal
Complete the user's request using available tools when external state or current data is required.

Tool policy
- Search the tool catalog when no visible tool can perform the required action.
- Retrieve before answering any question that depends on current or private data.
- Do not claim an action succeeded until its tool result confirms success.
- Ask for confirmation before [defined consequential actions].
- Retry transient failures at most {{N}} times; then report the error and completed work.
- Stop when the requested outcome is verified or when further progress requires new authority or missing input.

Final answer
Lead with the outcome. Distinguish completed actions, unverified assumptions, and blockers.
```

If retrieval is mandatory, expose only the allowed read tool or read-only set while `tool_choice` is `"required"`. Keep the gate active until the application verifies a successful evidence-bearing read; a catalog search alone is not evidence retrieval.

Example tool schema:

```json
{
  "type": "function",
  "function": {
    "name": "get_order_status",
    "description": "Get the current status of one order when the user asks about shipment or fulfillment state.",
    "parameters": {
      "type": "object",
      "properties": {
        "order_id": {
          "type": "string",
          "description": "Exact order identifier supplied by the user or resolved from verified account data."
        }
      },
      "required": ["order_id"],
      "additionalProperties": false
    }
  }
}
```

## Migration example

Legacy prompt:

```text
You are the world's best analyst. Think very deeply step by step. Be accurate, concise, and comprehensive. Never hallucinate. Read the report and summarize it.
```

K3-oriented rewrite:

```text
Summarize the report for an engineering director deciding whether to fund the proposal.

<report>
{{REPORT}}
</report>

Include:
1. Recommendation and confidence.
2. Three strongest supporting findings.
3. Material risks, assumptions, and conflicting evidence.
4. Information missing from the report that could change the decision.

Use only the report for factual claims. Mark any inference as an inference. Limit the answer to four short sections.
```

Material improvement: replace prestige and unobservable reasoning commands with an audience, decision, evidence boundary, explicit coverage, uncertainty behavior, and structural length target.

## Evaluation checklist

Build a small suite containing:

- Typical successful requests.
- Ambiguous requests with one crucial detail missing.
- Inputs containing instructions inside quoted source material.
- Reference sets with no answer and with conflicting evidence.
- Very long inputs where evidence appears near the beginning, middle, and end.
- Tool-required requests, optional-tool requests, malformed tool results, and transient failures.
- Structured outputs with optional, missing, nested, and unexpected fields.
- Permission-sensitive or destructive actions.

Score:

1. Task success.
2. Required-field completeness.
3. Grounding and citation correctness.
4. Correct abstention under missing evidence.
5. Instruction-hierarchy and delimiter robustness.
6. Tool choice and argument validity.
7. Schema parse rate.
8. Latency, input/reasoning/output tokens, and cost.

Change one prompt or runtime variable at a time when attributing improvements.

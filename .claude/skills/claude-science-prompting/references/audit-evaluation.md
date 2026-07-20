# Audit and evaluation for Claude Science prompts

## Contents

- Audit procedure
- Severity levels
- Rubric
- Common failure patterns
- Evaluation set design
- Metrics and acceptance rules
- Grader template
- Migration example

## Audit procedure

1. Identify the exact scientific outcome, evidence bar, and artifact the prompt is supposed to produce.
2. Separate stable requirements from experiment-specific inputs and from runtime configuration.
3. Trace each instruction to a behavior that affects scientific validity, evidence, safety, permissions, reproducibility, or output compatibility.
4. Find contradictions, omissions, unverifiable assumptions, invented capabilities, and instructions likely to cause tool or subagent misuse.
5. Rank findings by severity and propose the smallest correction.
6. Rewrite the complete prompt when a usable replacement is requested.
7. Define representative evaluations before claiming that a migration or rewrite is better.

## Severity levels

### Critical

The prompt can plausibly cause fabricated data or citations, unsafe or unauthorized action, exposure of sensitive data, invalid clinical or regulatory use, destructive external action, or a materially false scientific conclusion with no review boundary.

### High

The prompt lacks decisive evidence controls, uses an invalid or underspecified method, omits provenance for computed results, fails to verify citations or calculations, or routes tools and compute in a way likely to make the result irreproducible or wrong.

### Medium

The prompt has ambiguous scope, incomplete success criteria, weak uncertainty handling, unclear output requirements, unnecessary subagent or tool use, or missing stop behavior for ordinary failures.

### Low

The prompt is verbose, repetitive, stylistically inconsistent, or contains ceremony that increases cost and confusion without materially changing scientific behavior.

## Rubric

Score each dimension from 0 to 2.

### 1. Objective and scope

- **0**: The question, decision, population/system, or boundaries are materially unclear.
- **1**: The objective is understandable but leaves consequential ambiguity.
- **2**: The objective, scope, exclusions, audience, and supported decision or artifact are explicit.

### 2. Success criteria

- **0**: “Be thorough” or similar vague quality language substitutes for acceptance criteria.
- **1**: Some required content is named but completeness cannot be checked reliably.
- **2**: The prompt defines specific, measurable, relevant criteria and stop conditions.

### 3. Evidence and citations

- **0**: No source quality, verification, or citation policy; invented references could pass unnoticed.
- **1**: Citations are requested but source hierarchy, claim-level support, or unstable evidence is weakly handled.
- **2**: The prompt routes to fit-for-purpose sources, verifies decisive claims and identifiers, labels weak evidence, and preserves an evidence trail.

### 4. Methods and analysis validity

- **0**: The prompt asks for conclusions without defining or checking a valid analytical approach.
- **1**: Methods are mentioned but critical assumptions or failure modes are omitted.
- **2**: Methods are matched to the design and include relevant assumptions, controls, robustness, and interpretation limits.

### 5. Tools, connectors, agents, and compute

- **0**: The prompt demands all tools, invents resources, or lacks boundaries for sensitive, costly, external, or irreversible actions.
- **1**: Relevant resources are named but routing, delegation, or approval boundaries are incomplete.
- **2**: Resources are used by need, independent tasks may run in parallel, stateful tasks stay coherent, and approval boundaries are clear.

### 6. Reproducibility and provenance

- **0**: Computed results or figures can be produced without traceable inputs, code, environment, or versions.
- **1**: Code or citations are retained, but important lineage or environment details are missing.
- **2**: Inputs, transformations, code, environment, versions, parameters, seeds, logs, and artifacts form an inspectable lineage.

### 7. Uncertainty and scientific integrity

- **0**: The prompt encourages overclaiming or fails to distinguish evidence from inference.
- **1**: Limitations are requested generically.
- **2**: The prompt separates observations, calculations, inference, hypothesis, and recommendation and requires conflicts, negative evidence, uncertainty, and limitations.

### 8. Reviewer and validation

- **0**: No independent verification or only “double-check everything.”
- **1**: Review is requested but has no concrete targets or resolution behavior.
- **2**: The reviewer checks citations, calculations, units, methods, provenance, figure consistency, limitations, and success criteria and reports unresolved defects.

### 9. Output contract

- **0**: The deliverable, audience, or required artifacts are unspecified.
- **1**: A general format is named but required fields or files are incomplete.
- **2**: The output structure, audience, artifacts, evidence display, and failure reporting are explicit without needless rigidity.

### 10. Prompt hygiene

- **0**: Contradictory rules, hidden-reasoning demands, invented capabilities, or legacy prompt theater dominate.
- **1**: The prompt works but contains repetition, excessive micromanagement, or irrelevant rules.
- **2**: Every major instruction changes scientific validity, evidence, safety, permissions, reproducibility, or output compatibility.

A production prompt should score 2 on evidence, methods, reproducibility, uncertainty, and reviewer dimensions whenever those dimensions apply. Do not allow a high total score to average away a critical failure.

## Common failure patterns

### Inflated role prompting

Bad:

```text
You are the world's greatest multidisciplinary scientist and Nobel-level thinker.
```

Replace with a functional role only when it changes behavior:

```text
Coordinate a literature, computational, and independent review workflow for a molecular epidemiology audience.
```

### Generic anti-hallucination language

Bad:

```text
Never hallucinate. Be 100% accurate.
```

Replace with observable controls:

```text
Do not invent data, identifiers, citations, or tool results. Verify decisive claims against the cited source and report unresolved gaps.
```

### Mandatory use of every tool

Bad:

```text
Always use all available databases and agents.
```

Replace with routing:

```text
Use only sources and tools that materially improve the answer. Delegate independent specialist work; keep simple sequential work with the coordinating agent.
```

### Vague review

Bad:

```text
Double-check everything multiple times.
```

Replace with concrete checks:

```text
Before finalizing, independently verify decisive citations, calculations, units, statistical claims, input-to-code lineage, and figure-to-code consistency.
```

### Unsupported synthetic substitution

Bad:

```text
If data are missing, estimate reasonable values so the workflow can continue.
```

Replace with explicit labeling and approval:

```text
Do not substitute invented values for missing observations. Use simulation or imputation only when methodologically appropriate, label it, justify assumptions, and keep it separate from observed data.
```

### Excessive procedural micromanagement

Bad:

```text
First think of exactly five hypotheses, then call three agents, then search seven databases, then critique every line twice.
```

Replace with outcome and constraints:

```text
Develop competing explanations when the evidence supports them, use specialist agents for independent work, and verify the claims and calculations that drive the conclusion.
```

### Hidden chain-of-thought requests

Bad:

```text
Reveal every reasoning step and internal debate.
```

Replace with inspectable work products:

```text
Provide the evidence ledger, assumptions, methods, calculations, decision log, concise rationale, and unresolved uncertainty needed to audit the result.
```

## Evaluation set design

Build a test set that mirrors the expected workload and includes edge cases. Use at least one case from each applicable category:

- Routine happy path with sufficient high-quality evidence.
- Ambiguous research question requiring conservative scope assumptions.
- Missing metadata or data that should trigger a blocker rather than fabrication.
- Conflicting primary studies or database records.
- Preprint-only or weak evidence that must be labeled and down-weighted.
- Retraction, correction, duplicated cohort, or identifier mismatch.
- Tool, connector, database, or network failure.
- Large input requiring long-context organization.
- Two independent workstreams that benefit from specialist agents.
- Stateful analysis where delegation would lose essential context.
- Expensive compute request that should pause for approval.
- Sensitive or controlled data that must remain in its authorized environment.
- Statistical trap such as leakage, pseudoreplication, multiple testing, or denominator confusion.
- Figure whose plotted values disagree with the source table or code.
- Manuscript conclusion that overstates an observational result.
- Clinical, regulatory, or safety boundary requiring qualified human review.
- Requested output longer than the model's default style would naturally provide.

For a normal prompt, generate three to seven cases targeting its highest-risk failure modes. For production deployment, use a broader set with enough volume to estimate failure rates.

## Metrics and acceptance rules

Record these measures where applicable:

```text
case_id
critical_case (0/1)
objective_fidelity (0-2)
required_fields_complete (0-2)
evidence_traceable (0-2)
citations_exist_and_support_claims (0-2)
method_validity (0-2)
calculation_and_unit_accuracy (0-2)
reproducibility_complete (0-2)
uncertainty_calibrated (0-2)
reviewer_detected_seeded_defect (0/1)
tool_route_correct (0/1)
approval_boundary_compliant (0/1)
no_invented_data_or_sources (0/1)
input_tokens
output_tokens
latency_ms
cost
unnecessary_tool_calls
unnecessary_subagents
repeated_validation_count
```

Adopt a candidate prompt only when:

- It has no regression on critical safety, privacy, evidence, permission, or fabrication cases.
- It is non-inferior on objective fidelity, method validity, citation support, reproducibility, and uncertainty.
- It improves at least one meaningful reliability or efficiency measure.
- Any increased cost or latency is justified by a measured quality gain.
- Human reviewers agree that the evaluation distribution resembles actual work.

Do not optimize average score while tolerating rare catastrophic failures. Do not call a prompt “better” because it uses fewer tokens if it quietly drops the evidence ledger, code lineage, or requested artifact.

## Grader template

```text
You are grading the output of a scientific research prompt.

<task>[ORIGINAL TASK]</task>
<success_criteria>[TASK-SPECIFIC CRITERIA]</success_criteria>
<source_material>[GOLD OR VERIFICATION MATERIAL]</source_material>
<candidate_output>[OUTPUT TO GRADE]</candidate_output>

Evaluate only observable output and artifacts. Do not reward confident prose, length, or stylistic polish by themselves.

Grade:
1. objective fidelity;
2. required-field completeness;
3. evidence traceability and claim-level citation support;
4. methodological validity and correct interpretation;
5. calculations, units, denominators, and statistical statements;
6. reproducibility and provenance;
7. uncertainty, conflicts, negative evidence, and limitations;
8. tool and approval compliance;
9. absence of invented data, citations, identifiers, or tool results.

First identify any automatic-fail defect. Then assign each applicable dimension 0, 1, or 2 with a brief evidence-based justification. Return the final verdict as PASS or FAIL and list the smallest corrective changes.
```

Use code-based checks for exact fields, identifiers, schemas, calculations, or artifact existence. Use expert human review for scientific judgments that cannot be reliably automated. Validate any LLM grader against expert labels before scaling it.

## Migration example

### Before

```text
You are an elite biomedical super-researcher. Think step by step, be exhaustive but concise, never hallucinate, use all tools and all databases, and keep working until the answer is perfect. Find whether target X is safe and effective for disease Y. Double-check everything and give a publication-ready answer.
```

### After

```text
Assess whether the available evidence supports prioritizing target X for further preclinical study in disease Y.

Define the disease context, target mechanism, and decision criteria before synthesis. Use relevant primary studies, authoritative target and pathway databases, structural or activity records where material, and current systematic evidence. Verify decisive citations and identifiers, label preprints and model predictions, and identify contradictory or negative findings.

Separate human evidence, animal evidence, in vitro evidence, computational predictions, and inference. Evaluate efficacy rationale, target expression and selectivity, genetic support, tractability, known safety liabilities, and major evidence gaps. Do not convert this research assessment into patient-specific advice.

Use specialist agents only for independent evidence streams. Preserve an evidence ledger and source metadata. Ask before paid, restricted, sensitive, or expensive actions.

Before finalizing, have an independent reviewer check citation support, quantitative claims, identifier consistency, omitted counterevidence, and whether the conclusion matches the evidence tier.

Output a go / conditional go / no-go research-prioritization verdict, the decisive evidence, major risks, confidence and limitations, and the smallest next experiment or analysis that could change the verdict.
```

Why it is better:

- Replaces prestige and hidden-reasoning language with a bounded scientific decision.
- Defines evidence classes, decision criteria, and claim separation.
- Routes relevant resources without demanding every tool.
- Adds safety, provenance, reviewer, and stop behavior.
- Produces an evaluable verdict rather than an undefined “perfect” answer.

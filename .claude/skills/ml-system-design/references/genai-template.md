> Sources: section structure from [ML-SystemDesign/MLSystemDesign](https://github.com/ML-SystemDesign/MLSystemDesign), MIT License. RAG preparation, retrieval, and evaluation guidance from Microsoft Azure Architecture Center, "Design and develop a RAG solution" ([MicrosoftDocs/architecture-center](https://github.com/MicrosoftDocs/architecture-center), `docs/ai-ml/guide/rag/`), [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). Agent and observability requirements from `references/modern-ai-systems.md` of the `ml-system-design-review` skill (same MIT source). Distilled and rewritten, not verbatim; headings II, III, IV, V, VII, and VIII differ from the source template because these systems usually train no model.

# GenAI Design Doc Template — 12 Sections

Use this template when the output that matters comes from a foundation model through prompts, retrieved context, or tools. Sections keep the I–XII numbering of `template.md`; the table at the end maps them to the `ml-system-design-review` gradecard. For each section: what it must answer, what authors commonly omit, and how deep to go per maturity level (POC vs production).

## I. Problem Definition

Must answer: what task, for whom, why now, and why a foundation model rather than search, rules, a form, or a trained classifier. Current workflow and its cost, prior attempts, the unacceptable failures (a confident wrong answer, an answer drawn from content the user may not see, an action the user did not approve), who absorbs each failure, and where a human stays in the loop.
Commonly omitted: the list of unacceptable failures; the non-LLM alternative.
POC: task, users, unacceptable failures, why a foundation model. Production: add prior work, volumes, human-in-the-loop points, and a safeguard per unacceptable failure.

## II. Metrics and Acceptance Criteria

Must answer: how success is measured end to end and per component. Business KPI → task metric (correct routing, resolution rate, answer acceptance) → component metrics (retrieval recall@k and precision@k, groundedness, completeness, citation correctness, refusal quality, tool selection and argument accuracy, structured-output validity) → cost per request and latency (time to first token, p95). Name the launch threshold each metric must meet. A loss function belongs here only when a model is fine-tuned.
Commonly omitted: launch thresholds; cost and latency as metrics; scoring retrieval separately from generation.
POC: one KPI, one task metric, one metric per pipeline stage, cost and latency targets. Production: full metric hierarchy, thresholds that gate release, and how judge-based metrics are calibrated.

## III. Data and Knowledge Sources

Must answer: what the system reads and changes, who owns it, and who may see it. For retrieval: sources, formats, volume, content classifications, parsing and cleaning, chunking and enrichment (metadata, summaries, entities), versions, freshness, how deletions propagate, and the permission model carried from each source. For tools: the system of record each tool reads or changes. For prompts: the labeled history used for few-shot examples and evaluation. PII, retention, and what the model vendor stores. Training data only when a model is fine-tuned.
Commonly omitted: how source permissions and deletions reach the index, and how fast; vendor data retention.
POC: sources, formats, permission model, known quality issues. Production: add the ingestion pipeline and cadence, permission and deletion sync with its latency target, PII handling, vendor terms.

## IV. Evaluation Set and Validation Schema

Must answer: how offline evaluation predicts production behavior. A golden set built from representative content and real or realistic queries, each case holding the query, the context that answers it, and an accepted answer or the expected end state. It includes unanswerable and ambiguous cases and adversarial ones: prompt injection in user input or retrieved content, requests that cross permission boundaries, risky tool requests. Stratify by source, query type, and user role; state size and refresh cadence. Score retrieval separately from generation; score agents on the final system state, not transcript wording; repeat runs where outputs are stochastic; calibrate LLM-as-judge against human labels. Leakage: few-shot examples and prompt text must not contain evaluation answers; labeled history is split by time.
Commonly omitted: adversarial and permission-crossing cases; repeated runs; judge calibration.
POC: a small golden set covering every query type, including unanswerable and injection cases. Production: add stratification, the refresh process, regression cases from production failures, and judge calibration.

## V. Baseline and Adaptation Path

Must answer: what the system must beat and why each added piece is needed. A non-LLM baseline (keyword search, rules, the existing model, the human process) with its measured result, or how and when it will be measured if nothing exists yet; a prompt-only baseline; then each escalation (few-shot examples, retrieval, reranking, tools, fine-tuning, self-hosting) justified by evaluation results, cost, latency, privacy, or licensing. Compare candidate models on this task's evaluation set, not a leaderboard.
Commonly omitted: the non-LLM baseline; evidence for each escalation step.
POC: non-LLM and prompt-only baselines, the chosen model and why. Production: add a comparison table of candidate models and adaptation steps on the golden set.

## VI. Error Analysis

Must answer: how failures are found, traced, and fixed. A failure taxonomy by stage (parsing, retrieval miss, permission filter, context overflow, unsupported claim, wrong refusal, wrong tool or arguments, loops, invalid output); diagnosis from traces to the first stage that went wrong; the loop that turns production failures into regression cases.
Commonly omitted: attributing each failure to a stage; the regression-case loop.
POC: taxonomy and a manual review of failed cases. Production: add trace tooling, a triage owner, and the regression loop.

## VII. Development and Release Pipeline

Must answer: how a change reaches production reproducibly. Versioned artifacts: prompts and templates, model name and inference settings, tool schemas, guardrail rules, and the index build with its ingestion code. Evaluation runs gate each release against the thresholds in II. Rollout (shadow, canary, percentage) and rollback to a pinned version; environments and secrets. When a model is fine-tuned, this section also covers its training pipeline as `template.md` VII describes.
Commonly omitted: pinning prompt and model versions; releases gated by evaluation.
POC: prompts and configuration under version control, a repeatable evaluation run. Production: add release gates, rollout, rollback, and reproducible index builds.

## VIII. Context, Retrieval, and Tools

Must answer: what goes into each model call and what the model can cause. Context assembly: query rewriting, search type (keyword, vector, hybrid), filters including permission filtering by the requesting user's identity at query time, reranking and the final top N, the context budget, prompt composition, and memory with its scope. Tools: each tool with typed inputs and outputs and its risk class (read, write, external message, destructive, financial, privileged, regulated data); the checks enforced in code rather than prompt text (limits, ownership); approval gates and draft-then-commit for risky actions; idempotency for retried writes; structured errors; step, time, token, cost, and retry budgets with a kill switch. Structured outputs: the schema and its validation. When users have different access rights, describe the whole permission path here once and refer to it from III and X: where permissions come from, how the user's identity arrives, where each check runs, and what happens when a check fails or a source is unreachable.
Commonly omitted: permission filtering at query time; limits enforced in code; idempotency of writes.
POC: the retrieval path, prompt structure, and the tool list with risk classes. Production: add reranking and budget choices backed by evaluation results, approval gates, idempotency, and budgets.

## IX. Measuring and Reporting

Must answer: how results are proven with users. Pilot or online experiment design (traffic split, waitlist, or before-and-after comparison; success criteria fixed in advance; safety metrics that stop the test), human review sampling, feedback capture, and reporting to stakeholders.
Commonly omitted: stop criteria tied to safety metrics; who receives reports and how often.
POC: offline results only; online experiment subsection = "Deferred until production." Production: full experiment design and reporting plan.

## X. Integration

Must answer: how the system enters the product safely. API and UI; how the user's identity reaches retrieval filters and tool checks; fallback and degraded modes (model timeout, vendor outage, empty retrieval, low confidence leading to refusal, handoff to a human, or a simpler model); escalation to staff; release and rollback; incident response.
Commonly omitted: behavior while the model vendor is down; how user identity reaches the permission check.
POC: API sketch and a fallback statement. Production: SLAs, degraded modes, escalation, incident response.

## XI. Monitoring

Must answer: how you know it still works next month, and who acts. A trace per request: model and prompt version, retrieved chunk IDs and scores, tool calls and results, permission and guardrail decisions, tokens, cost, latency, fallback flags. Quality drift through sampled judging and user feedback; retrieval drift and index freshness; cost drift; safety incidents (injection attempts, blocked actions, permission denials); vendor errors and rate limits; owners, alert thresholds, and runbooks. For a trained component, data and concept drift and retraining triggers as `template.md` XI describes.
Commonly omitted: owners and thresholds; alerts on index freshness.
POC: traces plus basic quality and cost checks. Production: every layer above with thresholds, owners, and runbooks.

## XII. Serving and Inference

Must answer: how responses reach users within constraints. Latency budget split across retrieval, model call, and tools; throughput and vendor rate limits; tokens and cost per request; caching, with cache keys that respect permissions; model routing; timeouts and retries; where guardrails run; data residency and vendor terms; secret handling and tenant isolation.
Commonly omitted: cost per request at peak load; cache keys that ignore permissions.
POC: requirements and a minimal architecture; Optimization subsection = "Deferred until production." Production: full architecture, cost model, routing, and a degradation playbook.

## Mapping to the review gradecard

| `ml-system-design-review` dimension | Sections |
|---|---|
| Problem framing, goals & antigoals | I |
| Cost of mistakes & risk | I, VIII |
| Prior work, build/buy & baselines | I, V |
| Metrics, loss & measurement | II, IX |
| Data, labels & features | III, VIII |
| Validation & leakage | IV |
| Error analysis | VI |
| Training pipeline & reproducibility | VII |
| Serving, integration & release | X, XII |
| Monitoring, ownership & maintenance | XI |
| Modern AI systems (optional row) | IV, V, VIII, XI |

`ai-stage-gate` reads the same sections through its modern-AI overlay: unacceptable failures (I), golden set and injection cases (IV), adaptation path (V), releases gated by evaluation (VII), tool risk classes, approval gates, and budgets (VIII), fallback (X), and traces (XI).

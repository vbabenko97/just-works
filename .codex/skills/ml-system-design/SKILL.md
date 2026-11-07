---
name: ml-system-design
description: Apply when designing or specifying an ML or GenAI system before implementation — writing a system design document, architecting a training or inference pipeline, or planning a fraud detection, recommendation, forecasting, RAG, LLM application, LLM classifier, or tool-using agent system. Not for generic docs or specs (use doc-coauthoring), not for reviewing an existing design doc (use ml-system-design-review), and not for writing ML code without a design phase.
---

# ML System Design

Author a system design document from one of two 12-section templates distilled from the companion repo of Manning's *Machine Learning System Design* (Babushkin/Kravchenko): `references/template.md` for predictive ML, `references/genai-template.md` for systems built on foundation models.

## When NOT to use

- Generic documentation, proposals, or specs with no ML component — use `doc-coauthoring`.
- Writing ML code without a design phase — use the language coding skills.
- Reviewing or scoring an existing design doc — use `ml-system-design-review` (this skill's reviewer pair).

## Workflow

### 1. Triage

Ask one batched question set (AskUserQuestion on Claude; plain numbered questions on Codex):

1. Problem domain and business goal — what decision or process does the system improve?
2. Data situation — sources, labels, volume, freshness.
3. Scale and latency constraints — requests/day, acceptable latency, budget limits.
4. Deployment context — batch / online / edge; cloud / on-prem.
5. Project maturity — POC or production.
6. Models and actions — does the team train its own model, call a foundation model, or both; can the system change data or contact anyone?

Skip any question already answered in the request.

### 2. Choose the template

Decide from the components, not from the task label:

- **Predictive ML:** the decision comes from a model the team trains or retrains, such as forecasting, ranking, fraud scoring, or tabular classification. Use `references/template.md`.
- **GenAI:** the output comes from a foundation model through prompts, retrieved context, or tools, including an LLM classifier and a fine-tuned foundation model. Use `references/genai-template.md`.
- **Hybrid:** use the template of the component that produces the main decision. List every other critical component and cover its requirements in the matching sections: for a trained model, the dataset, validation split, retraining, and drift items of `template.md`; for a foundation-model component, the evaluation set, context and tools, and trace items of `genai-template.md`. A component is critical when its failure changes what users receive or causes a side effect, for example a trained fallback that serves traffic, a trained reranker that selects the model's context, or an LLM that writes explanations shown to analysts.

Maturity decides depth. Below the problem summary in the doc header, state the maturity, the template, and the critical components.

- **Production:** complete all 12 sections at full depth.
- **POC:** keep all 12 section headers; abbreviate throughout, except items a template marks "Any maturity", which stay at full depth; replace the experiment subsection of IX (A/B or online experiment) and the Optimization subsection of XII with the single line "Deferred until production."

### 3. Draft

Generate the full document from the chosen template. Mark every fact not supplied by the user inline as `[ASSUMPTION: what was assumed]`. Calibrate tone and depth against the worked example for that template: `references/example-rag-system.md` for GenAI, `references/example-demand-forecasting.md` for predictive ML. When your doc's maturity differs from the example's, the maturity depth rules above win.

Write subsections only for parts the system has. When a template item does not apply and a reviewer would look for it, such as fine-tuning, retraining, or an A/B test, write one line: the decision, its reason, and the trigger to revisit it if one exists.

### 4. Gap interview

Collect load-bearing assumptions — those affecting metrics, architecture, or cost — into a single batched confirm/correct message. Iterate with another batch only if the answers create new load-bearing gaps; typically one round. Minor assumptions are not raised.

### 5. Finalize

- For each confirmed or corrected assumption: remove the `[ASSUMPTION: ...]` tag and update the text with the confirmed value.
- Unresolved minor assumptions stay tagged in the doc.
- Ask for the output path; suggest `docs/ml-design/<name>.md` as the default.
- When the doc needs a system context or container diagram, use the `c4-architecture` skill.
- Suggest running `ml-system-design-review` on the finished doc.

## References

- `references/template.md` — predictive ML: the 12 sections, what each must answer, common omissions, depth by maturity.
- `references/genai-template.md` — foundation-model systems (RAG, LLM applications and classifiers, agents): the same 12-section structure with adapted sections and a map to the review gradecard.
- `references/example-demand-forecasting.md` — condensed predictive-ML worked example.
- `references/example-rag-system.md` — condensed RAG worked example on the GenAI template.

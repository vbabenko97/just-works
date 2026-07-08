---
name: ml-system-design
description: Apply when designing or specifying an ML system before implementation — writing an ML system design document, architecting a training or inference pipeline, or planning a fraud detection, recommendation, forecasting, or RAG system. Guides triage, drafting with assumption markers, a gap interview, and a finalized 12-section design document. Not for generic docs or specs (use doc-coauthoring), not for reviewing an existing design doc (use ml-system-design-review), and not for writing ML code without a design phase.
---

# ML System Design

Author an ML system design document from a 12-section template distilled from the companion repo of Manning's *Machine Learning System Design* (Babushkin/Kravchenko).

## When NOT to use

- Generic documentation, proposals, or specs with no ML component — use `doc-coauthoring`.
- Writing ML code without a design phase — use the language coding skills.
- Reviewing or scoring an existing design doc — use `ml-system-design-review` (this skill's reviewer pair).

## Workflow

### 1. Triage

Ask one batched question set (AskUserQuestion on Claude; plain numbered questions on Codex):

1. Problem domain and business goal — what decision or process does the model improve?
2. Data situation — sources, labels, volume, freshness.
3. Scale and latency constraints — requests/day, acceptable latency, budget limits.
4. Deployment context — batch / online / edge; cloud / on-prem.
5. Project maturity — POC or production.

Skip any question already answered in the request.

Maturity decides depth. State the chosen maturity in the doc header, on a line following the problem summary.

- **Production:** complete all 12 sections at full depth.
- **POC:** keep all 12 section headers; abbreviate throughout; replace the "A/B Testing" subsection (Measuring and Reporting) and the "Optimization" subsection (Serving and Inference) with the single line "Deferred until production."

### 2. Draft

Generate the full document from `references/template.md`. Mark every fact not supplied by the user inline as `[ASSUMPTION: what was assumed]`. Calibrate tone and depth against the closer worked example: use references/example-rag-system.md when the system involves an LLM, vector store, or retrieval step; otherwise use references/example-demand-forecasting.md. When your doc's maturity differs from the example's, the maturity depth rules above win.

### 3. Gap interview

Collect load-bearing assumptions — those affecting metrics, architecture, or cost — into a single batched confirm/correct message. Iterate with another batch only if the answers create new load-bearing gaps; typically one round. Minor assumptions are not raised.

### 4. Finalize

- For each confirmed or corrected assumption: remove the `[ASSUMPTION: ...]` tag and update the text with the confirmed value.
- Unresolved minor assumptions stay tagged in the doc.
- Ask for the output path; suggest `docs/ml-design/<name>.md` as the default.
- Suggest running `ml-system-design-review` on the finished doc.

## References

- `references/template.md` — the 12 sections: what each must answer, common omissions, depth by maturity.
- `references/example-demand-forecasting.md` — condensed classic-ML worked example.
- `references/example-rag-system.md` — condensed LLM/RAG worked example.

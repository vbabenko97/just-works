---
name: msca-pf-european-2026
description: Draft, review, red-team, and final-audit Horizon Europe MSCA Postdoctoral Fellowships 2026 European Fellowship applications. Use for HORIZON-MSCA-2026-PF-01-01 eligibility and mobility checks, Part A/Part B consistency, proposal concept development, Excellence/Impact/Implementation drafting, training and two-way knowledge transfer, career development, dissemination/exploitation/communication, open science, gender/diversity, ethics, work packages, milestones, risks, evaluator scoring, page/compliance checks, and submission-readiness reviews. Especially suited to medical imaging, clinical AI, health data, and MedUni Vienna/TEMPO-PET contexts, but reusable for any 2026 European PF. Not for evaluator-style scoring and repair prioritization of a finished draft — use `msca-pf-2026-reviewer` for that.
---

# MSCA-PF European 2026

## When NOT to use

- Evaluator-style scoring, score-loss mapping, and repair prioritization of an existing draft — use `msca-pf-2026-reviewer` (this skill's reviewer pair), which owns the critique and output format. The REVIEW workflow below is the fallback for when that skill is unavailable or when review is one mode inside a larger drafting session.
- Non-MSCA funding applications, or MSCA calls other than the 2026 Postdoctoral Fellowship.

## Operating principle

Act as a hostile-but-useful MSCA-PF evaluator and proposal architect. Optimize for a proposal that survives formal checks and gives evaluators little defensible reason to deduct points. Never reward what the applicant could mean; evaluate what is actually written.

Keep four things separate at all times:
1. **Eligibility/admissibility**: rules that can make the proposal ineligible, inadmissible, or partly disregarded.
2. **Submission blockers**: unresolved facts, placeholders, contradictions, missing approvals, stale exports, or formatting failures.
3. **Score-limiting weaknesses**: content that is formally allowed but gives an evaluator grounds to score below excellent.
4. **Polish**: wording and presentation that matter only after the first three are controlled.

## Source hierarchy and web verification

Treat 2026 rules as time-sensitive. Before asserting a deadline, eligibility condition, mobility rule, resubmission restriction, page/template requirement, scoring rule, budget/unit contribution, ethics/security requirement, or AI-use requirement:

1. Search current official European Commission, REA, MSCA, or Funding & Tenders sources when web access is available.
2. Use `references/official-rules-2026.md` as the offline baseline.
3. Use `references/source-map.md` to locate the official 2026 documents and applicant resources.
4. If a newer official source conflicts with a bundled reference, use the newer official source, state the date/version, and flag the bundled reference as stale.
5. Use NCP or host Research Service guidance for applicant-specific administrative interpretation, but distinguish it from the legal call text.
6. Use peer-reviewed methodological sources for scientific design. Do not use blogs or consultancy advice to override official call rules.

For scientific novelty or “first” claims, search the current literature before strengthening the claim. Prefer “to our knowledge” unless a defensible search supports an absolute claim.

## Decide the workflow first

Classify each request into one or more modes:

- **START**: applicant has an idea or blank template.
- **DRAFT**: create or rewrite a proposal section from supplied facts.
- **REVIEW**: evaluator-style critique and scoring of an existing draft.
- **METHODS RED TEAM**: stress-test scientific design, statistics, validation, leakage, bias, or clinical relevance.
- **CONSISTENCY AUDIT**: compare Part A, B-1, B-2, CV, host facts, correspondence, and versions.
- **FINAL GATE**: decide whether files are safe to submit.

When the user supplies proposal files, read the files before relying on remembered project context. Treat the latest canonical file or explicit source-of-truth statement as authoritative. Never let a review copy silently override its canonical draft.

## START workflow

Use the staged interview in `references/interview.md`. Do not demand every answer in one turn. Establish, in order:

1. Eligibility and mobility.
2. Research problem, gap, central question, objectives, and measurable verification.
3. Researcher-host complementarity.
4. Methodology and feasibility.
5. Training, supervision, and two-way knowledge transfer.
6. Career transformation and employability.
7. Dissemination, exploitation, communication, and impact.
8. Work plan, risks, resources, ethics/security, open science, gender/diversity.

Convert vague aspirations into testable commitments with timing and evidence. Keep a factual ledger of **confirmed**, **inferred**, and **to confirm** claims.

## DRAFT workflow

Draft against the exact 2026 headings and evaluator aspects in `references/evaluation-rubric.md`.

Rules:
- Preserve user-confirmed facts and terminology.
- Do not invent dataset sizes, event counts, host commitments, infrastructure, publications, grants, supervision experience, ethics approvals, collaborators, secondments, placements, or statistical choices.
- When a needed fact is absent, write a clearly marked placeholder or ask for it; never manufacture a plausible answer.
- Make objectives measurable and linked to deliverables, milestones, and verification.
- Make training and knowledge transfer operational: competence gap/asset, provider, timing, evidence/output, direction of transfer.
- Make Impact causal: activity -> output -> uptake/outcome -> longer-term impact. Do not leap from “paper published” to societal transformation.
- Make Implementation internally consistent: objective -> WP -> task -> deliverable -> milestone -> risk -> fallback -> person-month effort.
- Treat open science, gender/diversity, ethics, and data governance as research-design issues where relevant, not decorative compliance paragraphs.
- Use the medical-imaging checklist in `references/medical-imaging-red-team.md` for clinical imaging/AI proposals.

## REVIEW workflow

If `msca-pf-2026-reviewer` is available, hand pure critique-and-scoring requests to it — it owns the review output format. Use the workflow below when that skill is unavailable, or when review is one mode inside a larger drafting session.

Read `references/evaluation-rubric.md` before scoring. Apply the official 0-5 scale at 0.1 resolution and the PF weights: Excellence 50%, Impact 30%, Implementation 20%.

Default review output:

1. **Verdict**: one paragraph stating whether the proposal reads as fundable, borderline, or non-competitive and why.
2. **Estimated scores**: Excellence, Impact, Implementation, weighted total. Label them as an informed simulation, not an official score.
3. **Blockers**: eligibility, admissibility, unresolved-fact, page/template, or submission-readiness problems.
4. **Top score losses**: rank the 5-10 weaknesses most likely to cost points. For each: criterion/aspect, evaluator objection, expected seriousness, and concrete repair.
5. **Unsupported or risky claims**: facts needing evidence or host confirmation; novelty claims needing literature verification; overclaims.
6. **Cross-section contradictions**: Part A/B/CV/host/methods/work-plan inconsistencies.
7. **Rewrite**: only when requested or when a short replacement demonstrates the fix better than explanation.

Use severity labels:
- **BLOCKER**: unsafe to submit or potentially eligibility/admissibility relevant.
- **MAJOR**: credible reason for a material score deduction.
- **MODERATE**: real weakness but not structurally fatal.
- **MINOR**: polish, clarity, or low-impact issue.

Do not inflate scores to be encouraging. A score of 5.0 means essentially no meaningful shortcomings for that criterion. Treat 4.0 as very good, not “bad.”

## METHODS RED TEAM workflow

For medical imaging, prognostic AI, survival analysis, or retrospective clinical data, load `references/medical-imaging-red-team.md` and test at least:

- target population and estimand;
- index time, prediction horizon, and outcome definition;
- leakage and temporal partitioning;
- censoring, missingness, selection, and informative observation;
- sample size/event support and model complexity;
- calibration, discrimination, prediction error, and incremental-value comparison;
- scanner/site/calendar-time confounding and transportability;
- subgroup performance, sex/gender and diversity limitations;
- interpretability and clinical-utility claims;
- external validation realism;
- privacy, governance, reproducibility, and open-science constraints.

Prefer a scientifically narrower claim with a defensible estimand over an impressive-sounding claim the data cannot support.

## CONSISTENCY AUDIT workflow

Build a claim ledger across every supplied source. For each material claim, record:
- canonical wording/value;
- source file and version/date;
- where it appears in Part A, B-1, B-2, CV, or correspondence;
- status: confirmed / pending / contradiction / stale;
- owner of confirmation if applicable.

Pay special attention to exact dates, researcher mobility/activity history, degree date, host/legal entity names, PIC-linked department relation, supervisor role, cohort sizes, ethics/security answers, project duration, secondments/placements, budget, publications, and externally sourced facts.

If files contain review copies and canonical drafts, do not treat removal of editorial markers from a review copy as resolution of the underlying issue.

When local text files are available, run `scripts/audit_text_bundle.py` for a deterministic first-pass blocker scan, then interpret the output manually.

## FINAL GATE workflow

Load `references/final-submission-audit.md`. A green gate requires all of the following:

- eligibility and mobility are evidenced rather than assumed;
- latest official 2026 template/rules checked;
- Part B-1 is within the 10-page counted section and formatting requirements;
- Part B-2 section-specific limits are respected;
- no unresolved editorial markers, TODOs, generator tokens, or accidental working-language notes remain;
- Part A/B/CV facts and dates reconcile;
- scientific/statistical choices that require host or specialist sign-off are either confirmed or accurately framed as future project work rather than falsely presented as approved;
- ethics/security fields match the narrative;
- the rendered PDFs have been visually checked and fonts/layout are safe;
- the latest portal export has been checked, not an older copy;
- all files correspond to the same intended submission version.

Return **GREEN**, **AMBER**, or **RED** with a short reason. Never call a proposal submission-ready merely because it reads well.

## Project-specific TEMPO-PET context

When the user is working on the current MedUni Vienna medical-imaging proposal, load `references/tempo-pet-context.md`. Treat that file as a dated context snapshot, not permanent truth. Re-derive status from newer uploaded files or correspondence before making a final decision.

The context is useful for proposal-specific review, but the skill itself must remain usable for other European PF proposals.

## Output style

Be exact, concise, and evidence-driven. Use evaluator language where useful: “shortcoming,” “weakness,” “not sufficiently substantiated,” “credible,” “proportionate,” “ambitious,” “beyond the state of the art,” and “appropriateness.”

Prefer concrete repairs over generic advice. State what should change, where, and why. When page pressure matters, suggest what to cut as well as what to add.

Do not bury fatal issues beneath prose polishing. Do not praise text before identifying whether it is actually safe and competitive.

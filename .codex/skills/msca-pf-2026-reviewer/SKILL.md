---
name: msca-pf-2026-reviewer
description: Evaluator-style review and repair planning for 2026 Marie Sklodowska-Curie Actions Postdoctoral Fellowship proposals, with a primary focus on European Fellowships. Use when asked to review, score, red-team, critique, improve, prioritize revisions, compare versions, identify weaknesses, check submission readiness, or maximize funding competitiveness for an MSCA-PF 2026 proposal, Part A, Part B-1, Part B-2, CV, host-capacity section, work plan, impact plan, or full proposal bundle. Critique and repair planning only — for building a proposal from scratch or drafting sections, use `msca-pf-european-2026`.
---

# MSCA-PF 2026 Reviewer

## When NOT to use

- Building a proposal from scratch, the staged applicant interview, or drafting and rewriting sections — use `msca-pf-european-2026` (this skill's author pair), which owns the START and DRAFT workflows.
- Non-MSCA funding applications, or MSCA calls other than the 2026 Postdoctoral Fellowship.

## Operating principle

Review the proposal as a demanding MSCA-PF evaluator first and as an applicant-side repair strategist second. Judge only what is written and evidenced. Do not reward what the applicant probably means.

Keep four classes of issues separate:
1. **BLOCKER**: eligibility, admissibility, template, page-limit, submission, unresolved-fact, or contradiction risk that can invalidate, hide, or materially compromise the proposal.
2. **MAJOR**: a credible reason for a material score deduction.
3. **MODERATE**: a real but localized weakness.
4. **MINOR**: wording, presentation, or low-impact polish.

Do not bury blockers beneath style comments. Do not inflate scores to be encouraging.

## Source discipline

Treat 2026 rules as time-sensitive.

Before asserting a call deadline, eligibility condition, mobility rule, resubmission restriction, page/template rule, scoring rule, budget rule, ethics/security requirement, or AI-use requirement:
1. Search current official European Commission, REA, MSCA, or Funding & Tenders sources when web access is available.
2. Load `references/official-2026.md` as the bundled baseline.
3. Prefer the current Work Programme and call/template over summaries.
4. If a current official source conflicts with the bundled baseline, use the current source and state that the bundled reference is stale.
5. For scientific novelty, state-of-the-art, or "first" claims, search current peer-reviewed literature before strengthening the claim.
6. Never use consultancy blogs to override official call rules.

If the dedicated `msca-pf-european-2026` skill is also available, use it as a secondary domain reference. This reviewer skill controls the critique and output format.

## Inputs

Accept any of the following:
- full Part B-1 and Part B-2 PDFs;
- Part A export plus Part B files;
- DOCX/PDF draft sections;
- CV, host-capacity text, work plan, correspondence, or reviewer comments;
- pasted text for one subsection;
- multiple versions for comparison.

When proposal files are supplied, read the files before relying on conversation memory. Identify the canonical/latest version. Never let an older review copy silently override the source draft.

If only one section is provided, review that section deeply but state which cross-section checks cannot be completed.

## Review workflow

### 1. Establish scope and canonical version

Record:
- fellowship type and evaluation panel if known;
- host/beneficiary and supervisor if stated;
- project duration;
- files and versions reviewed;
- whether Part A, B-1, B-2, CV, and host data are all available.

Do not invent missing facts. Mark them as **TO CONFIRM**.

### 2. Run the rule and submission gate

Check first for:
- eligibility and mobility issues;
- PhD/research-experience eligibility uncertainty;
- resubmission restrictions;
- correct European vs Global fellowship setup;
- Part B-1 10-page compliance and current template structure;
- formatting and hidden/excess-page risk;
- unresolved TODOs, placeholders, comments, generated tokens, or stale instructions;
- Part A/B inconsistencies in dates, organisations, duration, supervisor, mobility, secondments, placements, budget-driving facts, ethics, and security;
- unsupported host commitments or unconfirmed facilities/data access;
- missing required files or letters where applicable.

Report these before scoring.

### 3. Simulate the evaluator assessment

Load `references/reviewer-playbook.md` and apply the official 0-5 scoring scale at 0.1 resolution.

Score only the three official criteria:
- Excellence: 50%
- Impact: 30%
- Quality and efficiency of implementation: 20%

Use the official individual threshold of 3/5 and overall threshold of 70% only as formal thresholds. Do not imply that 70% is competitive for funding.

The official evaluator form says applications are assessed as submitted, not on their potential after modification. Respect that in the scoring simulation. Then, separately, switch to applicant-side repair advice.

### 4. Build a score-loss map

For every material weakness, identify:
- exact section/subsection;
- criterion/aspect affected;
- severity;
- evaluator objection in one sentence;
- why the current wording does not earn full credit;
- exact repair;
- evidence or confirmation needed;
- cross-section dependencies;
- page-space consequence: add, replace, compress, or cut.

Rank fixes by likely benefit to funding competitiveness, not by ease of editing.

Prioritization order:
1. blockers and factual contradictions;
2. weaknesses affecting multiple evaluator aspects;
3. Excellence weaknesses, because Excellence carries 50% and is first in ex-aequo prioritization under the 2026 Work Programme;
4. weak career transformation and impact causality;
5. implementation credibility;
6. presentation polish.

Do not promise a numerical score increase for any single edit. Scoring is holistic and score gains are non-additive.

### 5. Stress-test cross-section coherence

Trace the proposal end to end:

`gap -> central question -> objectives -> methods -> work packages -> deliverables -> milestones -> training -> dissemination/exploitation/communication -> outcomes -> impacts -> career transformation`

Flag any broken link.

Also check:
- every objective has a method and verification route;
- every claimed result has an owner, timing, and output;
- every training item closes a real competence gap;
- two-way knowledge transfer is truly two-way;
- career claims follow from skills and outputs;
- impact claims follow from project results rather than field-wide hopes;
- risks have operational mitigations and fallbacks;
- host capacity matches the work plan;
- B-2 facts support rather than contradict B-1.

### 6. Review for evaluator usability

Under severe page pressure, reward information density, not decorative density.

Flag:
- long scene-setting before the gap;
- repeated claims across sections;
- CV-style prestige lists in narrative sections;
- tables with no decision value;
- tiny text or overloaded figures;
- generic EU-policy name-dropping;
- excessive acronyms;
- unsupported superlatives;
- sections that answer the template heading indirectly.

When recommending additions, also recommend what to cut or compress to make room.

### 7. Verify risky scientific claims

Search the current literature when the proposal depends on:
- a novelty or "first" claim;
- a disputed state-of-the-art gap;
- a methodological choice that could be challenged;
- a clinical, policy, regulatory, or market-impact claim;
- a quantitative burden/prevalence/market statement.

Use peer-reviewed or primary authoritative sources. Prefer "to our knowledge" unless the search supports an absolute claim.

## Criterion-specific review

Use the detailed tests in `references/reviewer-playbook.md`.

At minimum, test:

### Excellence
- 1.1 objectives, pertinence, ambition, beyond state of the art;
- 1.2 methodology, interdisciplinarity, gender/diversity where relevant, open science;
- 1.3 supervision, training, and two-way knowledge transfer;
- 1.4 researcher experience, competences, skills, and researcher-host complementarity.

### Impact
- 2.1 career perspectives, employability, and skills development;
- 2.2 dissemination, exploitation, communication, IP, audiences, timing, KPIs, and post-project continuation;
- 2.3 magnitude and importance of scientific, societal, and economic impacts, with a credible causal chain.

### Implementation
- 3.1 work-plan logic, deliverables, milestones, risks, timing, and effort;
- 3.2 host capacity, infrastructure, integration, support services, and hosting arrangements.

## Default output

Load `references/output-template.md` and use it unless the user asks for a different format.

The default review must contain:
1. verdict;
2. score simulation with weighted total;
3. blockers;
4. ranked top fixes;
5. criterion-by-criterion evaluator comments;
6. unsupported/risky claims;
7. contradictions and consistency issues;
8. page-budget advice;
9. submission-readiness gate.

Label all scores as an informed simulation, not an official result or funding probability.

## Review tone

Use evaluator language where useful: "shortcoming", "weakness", "not sufficiently substantiated", "credible", "proportionate", "ambitious", "beyond the state of the art", and "appropriateness".

Be specific. Prefer:
- "Replace the generic training list in 1.3 with three competence gaps, each linked to provider, timing, output, and career use."

over:
- "Improve the training section."

Praise only when it helps distinguish what should be preserved from what must change.

## Rewriting policy

Do not rewrite the whole proposal by default. The primary task is diagnosis and repair prioritization.

Provide short replacement text when it is the clearest way to demonstrate a fix. If the user asks for a rewrite, preserve confirmed facts and never fabricate:
- datasets or sample sizes;
- host commitments;
- supervisor track record;
- access approvals;
- infrastructure;
- publications or grants;
- collaborators;
- ethics approvals;
- statistical choices not supplied by the user.

Mark missing facts explicitly.

## Final submission gate

Return one of:
- **GREEN**: no unresolved blockers, rules/template checked, internal consistency is strong, and remaining issues are minor.
- **AMBER**: no obvious fatal issue, but one or more material score/readiness risks remain.
- **RED**: unsafe to submit because of a blocker, major contradiction, unresolved eligibility/admissibility issue, or serious scoring weakness.

Never call a proposal submission-ready merely because the prose is polished.

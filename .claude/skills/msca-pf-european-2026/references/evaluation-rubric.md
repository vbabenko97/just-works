# MSCA-PF evaluator rubric and red-team interpretation

Use the current official evaluation form and Work Programme if available. This file is a working interpretation, not a substitute for the official documents.

## Official scoring language

Score each criterion 0-5 at one decimal place:
- 0: fails to address / cannot be assessed because information is missing or incomplete.
- 1: poor; inadequately addressed or serious inherent weaknesses.
- 2: fair; broadly addressed but significant weaknesses.
- 3: good; addressed well but several shortcomings.
- 4: very good; addressed very well with a small number of shortcomings.
- 5: excellent; all relevant aspects addressed; shortcomings minor.

Evaluators assess the proposal as submitted, not the version the applicant could create after feedback.

## 1. Excellence, 50%

### 1.1 Objectives, ambition, beyond state of the art
Test:
- Is the problem specific and important?
- Is the knowledge/technology gap demonstrated rather than asserted?
- Is the central question explicit?
- Are objectives measurable, verifiable, logically ordered, and feasible within 12-24 months?
- Is ambition clear relative to named state-of-the-art comparators?
- Are novelty/first claims evidence-backed and appropriately hedged?
- Can a null/negative result still generate useful knowledge?

Common deductions: literature dump instead of gap analysis; architecture novelty without clinical/scientific need; objectives described as activities; unverifiable success criteria; novelty based on absence of one paper rather than a field-level search.

### 1.2 Methodology, interdisciplinarity, gender/diversity, open science
Test:
- Does the design answer the stated question and estimand?
- Are data, cohort, outcomes, predictors, methods, validation, and inference coherent?
- Are key choices prespecified enough to establish credibility without pretending the entire future protocol is already known?
- Are feasibility gates and fallbacks real rather than excuses for underspecification?
- Is interdisciplinarity necessary and operational?
- Are sex/gender/diversity aspects integrated where scientifically relevant, or explicitly justified as not relevant?
- Are open-science practices concrete and compatible with privacy/IP constraints?

For clinical AI, also load `medical-imaging-red-team.md`.

### 1.3 Supervision, training, two-way knowledge transfer
Test:
- Is the supervisor's expertise directly relevant?
- Are supervision frequency, progress review, escalation, and career-development mechanisms credible?
- Does training close named competence gaps?
- Does the researcher transfer specific expertise back to the host?
- Does every training/transfer item have provider, timing, and evidence/output?
- Is the plan distinct from ordinary project tasks?

Common deductions: generic “attend seminars”; one-way host-to-fellow training; prestige claims without direct fit; no contingency for supervisor absence; training unrelated to the applicant's career gap.

### 1.4 Researcher experience, competences, skills
Test:
- Does existing experience make the proposed project credible without eliminating the need for fellowship training?
- Is the applicant's trajectory explained, especially interdisciplinary/non-linear careers?
- Are outputs described qualitatively for relevance, not merely by journal metrics?
- Is the applicant-host complementarity obvious?

## 2. Impact, 30%

### 2.1 Career perspectives, employability, skills development
Test:
- Is there a clear before -> fellowship -> after transformation?
- Are career targets specific and plausible inside and/or outside academia?
- Are skills linked to career evidence such as publications, grant leadership, supervision, network, regulation, clinical-methodological competence, or transferable skills?
- Are outcomes measurable by project end and useful afterward?

Common deductions: “improves employability” with no mechanism; training list repeated from Excellence; no distinction between scientific outputs and career development.

### 2.2 Dissemination, exploitation, communication
Keep the three concepts distinct:
- Dissemination: sharing results with specialist/research users.
- Exploitation: use/reuse, follow-on validation, IP, standards, software/data/protocol uptake, future funding, clinical/industrial pathway.
- Communication: reaching broader/non-specialist audiences with tailored messages and channels.

Test audiences, actions, timing, KPIs, ownership, post-project continuity, IP/open-science compatibility, and proportionality.

### 2.3 Magnitude and importance of scientific, societal, economic impacts
Test:
- Who benefits, how many/which settings, and through what causal pathway?
- Is magnitude quantified where defensible?
- Is importance explained relative to current practice/knowledge?
- Are long-term claims conditional on required external/prospective/regulatory steps?
- Does the proposal avoid confusing a research model with a deployable clinical tool?

## 3. Quality and Efficiency of Implementation, 20%

### 3.1 Work plan, risks, effort
Test internal traceability:
objective -> WP/task -> deliverable -> milestone -> risk -> mitigation/fallback -> person-month effort.

A good risk is specific, plausible, material, and has a mitigation that changes what the project does. Do not list generic risks (“delays”) without operational response.

Check dependencies, critical path, parallel work, feasibility gates, PM arithmetic, timing of protocol/data access/training/publications, and whether dissemination/management are integrated without consuming implausible effort.

### 3.2 Host capacity and hosting arrangements
Test:
- research environment and infrastructure actually needed by the project;
- employment/workplace/onboarding/integration;
- access to data/equipment/computing;
- administrative, ethics, DPO, technology transfer, training support as relevant;
- day-to-day scientific community and supervision continuity;
- consistency with Part B-2 capacity table.

## Score discipline

Before giving 4.5-5.0, ask: “Can I name a concrete evaluator shortcoming?” If yes, quantify whether it is truly minor. Multiple moderate weaknesses should not magically sum to 4.9 because the prose is polished.

Always explain the main score drivers. A weighted total is only a simulation and not a probability of funding.

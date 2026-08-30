---
name: msca-text-humanizer
description: Rewrite AI-assisted, over-polished, or awkward English into natural, credible academic prose for an MSCA Postdoctoral Fellowship 2026 applicant. Use for MSCA-PF Part B sections, CV narrative, host/supervision/training/impact text, emails or supporting prose when the user asks to humanize, naturalize, de-AI, simplify, tighten, make text sound like them, or adapt wording to B2-C1 English. Preserve scientific meaning, evidence, citations, numbers, proposal headings, and evaluator-relevant content. Do not optimize for AI-detector evasion or fabricate non-native mistakes. For time-sensitive MSCA rules or compliance claims, verify against current official EC/REA/MSCA sources before editing around them.
---

# MSCA Text Humanizer

## When NOT to use

- Evaluator-style scoring, score-loss mapping, or submission-readiness gating — use `msca-pf-2026-reviewer`.
- Building a proposal from scratch, the staged applicant interview, drafting sections from supplied facts, work plans, or eligibility and mobility checks — use `msca-pf-european-2026`.
- Information-preserving compression of a non-MSCA document (design doc, PRD, RFC) — use `lossless-doc-compress`, which guarantees no content is dropped. This skill's "Tight MSCA" mode deliberately cuts words that carry no evaluator value.

## Purpose

Turn stiff, generic, over-engineered, or machine-like prose into concise academic English that sounds like a capable early-career researcher rather than a marketing department that discovered a thesaurus.

Use the applicant profile in `references/voice-profile.md` as a default voice prior. If the user provides authentic writing samples, those samples override the generic profile.

For MSCA-specific wording, use `references/msca-2026-guardrails.md`. For concrete rewrite patterns, use `references/rewrite-patterns.md`.

## Core principle

Humanize by improving authorship signals, not by adding errors.

Prefer:
- concrete nouns and verbs over abstract promotional language;
- varied but controlled sentence length;
- explicit causal links over generic transitions;
- one claim per sentence when a sentence is carrying too much;
- specific evidence over adjectives such as "novel", "robust", "significant", or "comprehensive";
- simple wording when simple wording is accurate;
- natural B2-C1 academic English rather than C2 literary polish.

Never deliberately add typos, wrong articles, broken grammar, fake hesitation, slang, personal anecdotes, or nationality-coded quirks to make text look "human".

## Source priority for voice

Use this order:

1. The user's authentic writing samples from the current conversation.
2. Explicit style instructions from the user.
3. The profile in `references/voice-profile.md`.
4. The default style rules in this skill.

Do not infer personality, intelligence, or writing habits from age, sex, or nationality.

## Workflow

### 1. Identify the text type

Classify the input before rewriting:
- MSCA Part B-1 criterion text;
- Part B-2 or CV narrative;
- abstract/project summary;
- email or host communication;
- general academic/scientific prose;
- reviewer response or explanatory note.

If the text is MSCA proposal content, preserve the official heading and the evaluator purpose of the section.

### 2. Lock factual content

Treat these as immutable unless the user explicitly asks to change them:
- numbers, percentages, dates, durations, units, sample sizes, TRLs, work-package IDs;
- citations, DOIs, URLs, publication titles, project acronyms;
- institution, department, supervisor, host, partner, dataset, method and software names;
- degree dates and employment dates;
- claims about ethics approvals, access to data, infrastructure, secondments, placements, commitments, or funding.

If a factual statement is unclear, do not "smooth" it into a stronger claim. Keep it cautious or mark `[CHECK: ...]` when clarification is necessary.

### 3. Diagnose machine-like prose

Look for combinations of these signals:
- repeated sentence templates or near-identical sentence lengths;
- excessive "Furthermore", "Moreover", "Additionally", "It is important to note";
- stacked abstract nouns such as "facilitation of the optimization of";
- promotional adjectives without evidence;
- symmetrical three-item lists that do not reflect real logic;
- paragraphs where every sentence begins with the project, approach, methodology, or fellowship;
- empty framing before the actual claim;
- excessive passive voice where the actor matters;
- excessive active voice where impersonal scientific wording is more natural;
- generic endings such as "thereby contributing to scientific advancement and societal impact";
- inflated career language such as "transformative journey", "unique opportunity", or "world-class environment" without specifics;
- unnecessary synonyms that make standard technical terms less precise.

Do not mechanically remove every transition or passive construction. Natural academic writing uses both.

### 4. Rewrite in two internal passes

First pass: preserve meaning and improve logic.
- Put the main claim early.
- Keep cause -> method -> evidence -> implication in a readable order.
- Split overloaded sentences.
- Merge choppy sentences when the relationship is obvious.
- Replace generic claims with supplied concrete evidence.

Second pass: calibrate voice.
- Target B2-C1 professional English: grammatically sound, direct, technically competent, not ornate.
- Mix shorter factual sentences with moderately complex sentences.
- Avoid idioms, journalistic flourishes, and conspicuously native-sounding wordplay in formal proposal sections.
- Use first person only if the original section or user preference supports it; otherwise preserve the existing person and register.
- Keep standard field terminology even when a simpler synonym exists.

### 5. Apply the MSCA compression pass when relevant

For Part B-1, remove words that do not earn evaluator value because Sections 1-3 share a strict page limit.

Cut first:
- generic scene-setting;
- repeated definitions already clear from context;
- duplicated benefits across Excellence and Impact;
- adjective chains;
- ceremonial phrases about the fellowship;
- vague claims that are restated later with evidence.

Protect:
- objective, gap, novelty and methodology logic;
- measurable training and two-way knowledge transfer;
- career-development mechanism;
- dissemination/exploitation/communication distinctions where needed;
- credible outcomes/impacts and quantified estimates when meaningful;
- work plan, risks, mitigation, deliverables and milestones;
- host capacity and researcher-host complementarity.

### 6. Quality-control the rewrite

Before returning text, check:
- no factual drift;
- no stronger novelty or impact claim than the source supports;
- no invented evidence or citation;
- no lost MSCA criterion point;
- no new contradiction with dates, acronyms or terminology;
- no generic AI-sounding filler added during editing;
- grammar is correct enough for a competitive European research proposal;
- wording sounds plausible for a strong B2-C1 researcher rather than intentionally imperfect English.

## Output modes

### Default: clean rewrite

Return only the rewritten text. Do not add a preface, score, AI-detector estimate, or explanation unless the user asks.

### Minimal edit

When the user asks for a light touch, keep sentence order and terminology as much as possible. Change only wording that is stiff, repetitive, unclear, or unidiomatic.

### Tight MSCA

When the user asks to shorten for Part B-1:
- preserve evaluator-relevant content;
- aggressively remove redundancy;
- prefer shorter constructions;
- do not delete evidence merely to reduce word count.

If useful, report the approximate word reduction after the rewrite.

### Show changes

When the user asks for explanation, provide:
1. rewritten text;
2. up to five high-value changes and why they improve readability or credibility;
3. any `[CHECK]` items where the source is ambiguous.

## AI-detector requests

If the user asks to "beat", "bypass", "fool", or guarantee a low AI-detection score:
- do not promise detector evasion or an "undetectable" result;
- explain briefly that detector scores are not a reliable authorship test;
- still help by editing for natural voice, factual ownership, clarity, and consistency;
- for MSCA material, follow the current official transparency and validation requirements in `references/msca-2026-guardrails.md`.

Never claim that rewriting removes a requirement to disclose AI use.

## Web verification for MSCA 2026

Treat call rules as time-sensitive. Before asserting or changing text because of a current rule, verify official sources if web access is available, especially for:
- deadline and call status;
- page limits and formatting;
- eligibility and mobility;
- research-experience limits;
- AI-use requirements;
- section headings or template changes;
- evaluation criteria;
- ethics/security requirements.

Prefer official European Commission, REA, MSCA, and Funding & Tenders sources. If a current official source conflicts with the bundled snapshot, use the newer source and state that the reference file is stale.

Do not browse the web merely to rewrite ordinary prose unless the user asks for fact-checking or the text contains a current factual claim that materially affects the proposal.

## Examples

Load `references/rewrite-patterns.md` when the user asks for aggressive humanization, gives very AI-like text, or wants examples of the target voice.

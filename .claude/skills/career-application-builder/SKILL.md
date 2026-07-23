---
name: career-application-builder
description: Audit, rewrite, and tailor CVs, résumés, LinkedIn profiles, cover letters, recruiter messages, and job-application answers against a specific vacancy or target role. Use whenever the user wants help with a CV or résumé, asks to tailor an application to a job description, wants a LinkedIn headline/About/Experience section rewritten, needs a cover letter or outreach message, or asks whether their background fits a role — even if they never say "ATS" or "tailor". Confirms the status of every impact claim (proposed vs implemented vs measured) before it reaches a document, so achievements don't get silently inflated. Not for salary negotiation, compensation benchmarking, or job-market research.
---

# Career Application Builder

Turn a person's raw career material into application artifacts that survive scrutiny.

The failure mode this skill exists to prevent is subtle: application material is the one genre where the writer is rewarded for overstatement and nobody checks until an interview, at which point the cost is high and the candidate is blindsided. A model asked to "make this CV stronger" will reliably strengthen claims past what the evidence supports, because that is what the instruction literally asks for. This skill inserts one cheap step — confirm the status of each claim before writing it — that keeps the output persuasive and true at the same time.

## Workflow

Work through these stages in order. Stages 1–4 run for every request; stage 5 produces only what was asked for.

### 1. Establish what you have

Ask for what's missing, but don't demand a full dossier before starting. Most requests arrive with one or two of:

- an existing CV or résumé
- a target vacancy or a description of the kind of role wanted
- a LinkedIn profile or its text
- loose career notes, brag documents, performance reviews
- an evidence file (see *Claim contract* below) if the person keeps one

How much targeting information exists determines what's useful to do:

- **A specific vacancy** — full tailoring, including judgements about what to cut
- **A target role, or two adjacent role families** — enough for a rewrite. Say which family each choice serves
- **Neither** — a structural and factual audit still has value: layout, parse safety, internal consistency, unsupported claims. Say plainly that relevance advice is limited without a target, and offer to go further once there is one

Don't refuse to work for lack of a vacancy, and don't quietly produce generic output while implying it's targeted.

### 2. Extract requirements from the vacancy

Separate:

- **explicit** requirements — stated in the posting
- **inferred** requirements — implied by the role, team, or seniority but not written down
- **essential vs preferred** — postings routinely blur these; sort them

Keep inferred requirements labelled as inferred. Treating an inference as a stated requirement leads to padding the CV against a job that was never advertised.

### 3. Inventory the claims in the supplied material

Read the person's material and list every substantive claim: what they say they did, built, led, or improved, and any number attached.

Map each claim to the requirements from stage 2. This produces three useful groups:

- claims that match a requirement → candidates for the final document
- requirements with no matching claim → **gaps**; report them, never fill them
- claims that match nothing → probably cut, but check before dropping something the person values

### 4. Status check the claims that need it

This is the stage that makes the difference.

An existing CV bullet has *already* destroyed the information you need. "Reduced infrastructure costs by $1.25K/month" reads identically whether the saving was measured after a rollout, estimated from a spreadsheet, or merely proposed in a design doc. You cannot recover which from the text, so if you don't ask, you will carry the strongest reading forward and polish it. That's how a candidate ends up defending a claim they never actually made.

**Split compound statements before assigning state.** "Built X and reduced Y by 30%" is two claims — an implementation and an outcome — and they routinely rest on different evidence. The build shipped; the 30% may be a projection from a design doc. A single state on the compound bullet hides that, so separate them and let each carry its own.

**Check any claim where the supplied material doesn't already settle the answer.** Two categories need it:

- **Numbers** — percentages, currency amounts, latency figures, scale claims, headcount
- **Status verbs** — *led, built, launched, owned, adopted, migrated, improved, scaled, production-scale, company-wide*. These inflate as easily as numbers and get probed harder in interviews. "Led" in particular: sole ownership, tech lead, or one of six contributors?

**Check only what you're about to use.** Claims that won't appear in the requested artifact don't need resolving. Within that set, start with the highest-risk: large numbers, seniority and ownership verbs, and anything a technical interviewer would naturally probe.

**Batch the questions into a single round.** One message listing the ambiguous claims with a short question each. Interrogating claim-by-claim across many turns is exhausting and people start rubber-stamping, which defeats the purpose.

**Ask plainly and stop.** The questions are the deliverable at this stage — everything wrapped around them is friction. Don't explain why you're pausing, don't restate the vacancy back, don't preview how each answer would change the wording, and don't editorialise about whether a number is impressive ("$780 is small for a Staff role" is both unsolicited and unknowable without the baseline). Someone who asked for tighter bullets and got four questions plus an essay about claim inflation will skim it, and skimming is how the answers get rubber-stamped.

Show a compact requirement-to-evidence mapping when the person asked for a fit analysis, or when it materially changes what makes the final document — a vacancy with real gaps earns the table, because the gaps are the answer. Keep it internal when it would only restate their own prompt back at them or delay a straightforward clarification: four ambiguous bullets on an existing CV earn four questions, not a table plus four questions.

The rule targets commentary on your own process, not the analysis itself.

Brevity does not license dropping country-specific requirements — when you're producing or auditing a complete application document. Work-permit status and language level for Switzerland, photo and date-of-birth norms for DACH, length limits, what a "CV" even means in the US: surface these even when the rest of your reply is four lines. See `references/regional-conventions.md`.

Skip them for a narrow request. Someone asking you to tighten four bullets doesn't need the German photo convention appended; that's scope creep wearing a helpful hat. Raise it only when the convention bears on what they actually asked for.

State the convention, don't just ask about it. You already know Swiss postings commonly expect permit status and a language level; say that, then ask which applies to them. A bare "what's your German level?" hands them the job of working out why you asked.

**Skip a question only when the cited source supports the specific assertion.** Sources are narrower than they look: a merged PR shows code landed, not that this person led the work or that anything improved as a result. A dashboard shows a metric moved, not that this change moved it. Ownership, delivery, and outcome each need their own support — one link rarely settles all three.

### 5. Produce the requested artifacts

**A gap doesn't block delivery. An unverified claim does.** These two fail differently and need opposite handling — the distinction matters more than it looks.

A **gap** is a requirement with no supporting evidence in what you were given. That is not proof they lack the experience — people leave things out — so ask whether there's something unmentioned. What asking cannot do is change the wording of what you *were* shown: no answer turns the ECS work in front of you into Kubernetes work. So report the gap, ask about omitted experience, and meanwhile write the bullets covering what the material does support.

**Never put an unsupported technology into an artifact — not even bracketed.** `[+ Python, pending your confirmation]` in a skills line is not a safe placeholder. It pre-supplies the answer, invites a rubber stamp instead of a reply, and survives into the finished document the moment someone deletes the brackets. Keep it out of the CV and name it in your notes.

An **unverified claim** is a number, or a verb like `Led` or `Owned`, whose status you can't read from the text. One line from them settles it. Don't put it in a document first. Anything you present under "here's the tightened version" reads as endorsed and gets pasted straight into a CV — so if that figure turns out to be an estimate, you just handed them the inflated claim they came to you to avoid. Leave those bullets out, and say which you're holding and why.

If every claim in the material is unverified, the question list *is* the deliverable. That isn't a failure to deliver; it's the shortest route to a document they can defend in the interview.

Only what was asked for. Available artifacts:

| Artifact | Notes |
|---|---|
| CV audit | Findings on an existing CV without rewriting it |
| CV rewrite | General-purpose, no specific vacancy |
| Tailored CV | Against one vacancy |
| LinkedIn sections | Headline, About, Experience, Skills, Featured — see `references/linkedin-sections.md` |
| Cover letter | |
| Recruiter / hiring-manager message | Short, specific, no restated CV |
| Application-form answers | Usually word-limited; respect the limit exactly |

For layout and parser constraints read `references/ats-and-layout.md`. For country-specific expectations (DACH, Switzerland, UK, US) read `references/regional-conventions.md` — these differ enough that the wrong convention reads as carelessness.

Write bullets in active voice with a strong opening verb, and let the verb carry the status honestly. `Designed`, `Proposed`, and `Identified` are not weak words — they're precise ones, and precision reads as senior. Reserve `Delivered`, `Reduced`, and `Increased` for work that was actually implemented and observed.

### 6. Audit before returning

Run this every time, on everything produced. It's a closing gate, not an optional extra — an audit that only runs when someone remembers to ask for it doesn't catch anything.

- [ ] Every substantive claim traces to supplied material or a stage-4 answer
- [ ] No `low` confidence figure appears in the final text
- [ ] Verbs match status — nothing `proposed` described as delivered
- [ ] Dates, titles, and employers consistent across all artifacts produced
- [ ] Nothing confidential: internal pricing, unreleased products, named customers, proprietary architecture
- [ ] Requirements the person doesn't meet are absent, not finessed
- [ ] No keyword stuffing — every vacancy term used is semantically true
- [ ] Layout constraints from `references/ats-and-layout.md` respected
- [ ] If the role's country is known, its conventions from `references/regional-conventions.md` are applied or explicitly raised — permit and language expectations, photo/DOB norms, length
- [ ] If a PDF was produced, `scripts/check-pdf-extraction.sh` was run and its output inspected

Report anything that fails rather than quietly fixing it. If a claim can't be supported, say which one and what would support it.

## Claim contract

The working record for a claim during stages 3–4. Keep these in context; persist them only if the person wants a reusable file.

```yaml
claim:
  statement: ""                                        # what happened, plainly
  state: proposed | estimated | implemented | measured
  confidence: high | medium | low
  source: ""                                           # where this is verifiable
  approved_wording: ""                                 # the strongest honest phrasing
```

**States:**

- `proposed` — designed or recommended; not built
- `estimated` — a number derived from analysis, not observed
- `implemented` — built and shipped; effect not measured
- `measured` — result observed against a documented evaluation or baseline. Doesn't require shipping: a peer-reviewed result on a fixed dataset is measured; a deployed feature nobody instrumented is only implemented

The state ceiling determines the strongest available wording:

| State | May say | May not say |
|---|---|---|
| proposed | "Designed…", "Proposed…", "Recommended…" | "Delivered", "Reduced", "Implemented" |
| estimated | "Identified ~$X in…", "Estimated…" | "Saved $X", "Cut costs by X%" |
| implemented | "Built…", "Shipped…", "Migrated…" | Any outcome number that was never measured |
| measured | "Reduced X by Y%", with the baseline | Extrapolations beyond what was measured |

If the person keeps an evidence ledger with these fields, read it and skip stage 4 for anything it already settles. The skill works fine without one — never require it.

## Boundaries

Route elsewhere:

- **Salary negotiation, compensation benchmarking, offer comparison, job-market research** → `income-optimizer`
- **Academic CVs, research statements, postdoc applications** → different genre entirely. Publications, funding, teaching, and supervision carry the weight, and the industry impact-bullet format actively hurts. Say so rather than producing an industry CV with papers appended.

## Things that go wrong

**Filling a gap instead of reporting it.** A vacancy asks for Kubernetes; the material shows Docker and ECS. The tempting move is "container orchestration experience". Report the gap. The person may have Kubernetes experience they didn't write down — ask. If they don't, they're better off knowing before the interview.

**Copying the tailored CV onto LinkedIn.** LinkedIn is read by recruiters for adjacent roles and has to stay credible across two or three role families. A profile narrowed to one vacancy is worse than the generic one it replaced.

**Losing the person's voice.** If a writing-style skill or voice reference is available, use it for prose artifacts — cover letters, About sections, outreach. Don't apply it to CV bullets: bullets are a constrained format where compression matters more than voice, and conversational phrasing wastes the line.

**Over-asking in stage 4.** Questions about claims that won't reach the final document, or that the supplied material already answers. Re-read what you were given before asking for more.

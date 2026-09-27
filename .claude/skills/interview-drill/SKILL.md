---
name: interview-drill
description: Run a realistic mock interview that tests whether the candidate can defend the CV or application they actually submitted for a specific role — one question at a time, with follow-up probes and honest feedback, never scripted model answers. Use when the user asks for a mock interview, says "drill me", "practice interview", "quiz me on my CV for this role", or "prepare me for the interview", or otherwise wants to rehearse for an interview. Not for writing or tailoring CVs, cover letters, or LinkedIn profiles (use career-application-builder) or for screening a vacancy before applying (use job-triage).
---

# Interview Drill

Play the interviewer, so the candidate finds out which of their claims hold up before someone with hiring authority does.

The obvious way to prepare someone — likely questions with polished model answers — fails where it matters. Memorised answers collapse at the first follow-up ("what did you do, versus the team?") because they were never the candidate's. Worse, a generated answer fills gaps with plausible numbers and outcomes, which the candidate then repeats to a real interviewer as fact. What transfers to the real room is practice retrieving and defending their own facts under pressure, so this skill asks and listens; it doesn't write answers for the candidate to memorise.

## Workflow

### 1. Read what was submitted

Drill against the version the interviewer is holding — the one that was sent. Gather:

- **The vacancy.**
- **The exact CV or application submitted.** A submission record or receipt beats the latest draft. If nothing records which of several versions went out, ask; the application portal, confirmation email, or sent attachment will show it.
- **Evidence** — an evidence or claims ledger, a fit analysis, project notes. A ledger's recorded boundary for a claim is where to probe; a fit analysis's adjacent or not-evidenced requirements, and any interview risks it notes, are where questions go.
- **An existing question bank**, if the workspace keeps one. Build on it rather than starting over.

If the workspace documents its own conventions (README, CLAUDE.md, AGENTS.md, profile files), follow them to find these; otherwise use what the user supplied or the obvious files (job ad, sent CV, any ledger or notes), and ask only for what's missing. The vacancy and the submitted CV are enough to start. With the vacancy alone you can drill role knowledge but not their claims — say so.

Read, don't invent: anything not in the material is a question for the candidate, not a detail to assume. The drill reads the workspace; it doesn't edit the CV, ledger, or any other file unless asked.

### 2. Plan 5–8 questions

Weight them toward what a real interviewer would push on:

- **Claims under strain** — every number, every ownership verb (*led, owned, built, launched*), requirements the CV meets only adjacently, and gaps the vacancy will expose
- **The role's core requirements** — the technical depth the job actually needs
- **One or two behavioural questions**

Keep the plan to yourself unless asked. A visible list lets the candidate pre-draft every answer, and real interviewers don't hand theirs over.

### 3. Ask one question, then stop

One question per message; then end the turn and wait. No hints, no model answer, no second question tucked behind the first.

The drill measures what the candidate produces unaided — anything added before they answer contaminates it. On the first turn, one line of setup is enough (the role, roughly how many questions, that they can stop or ask for feedback any time), then the first question.

### 4. Flag, probe, then give feedback

**Flag problems in the reply where they appear**, quoting their words — in the line before a probe if you're probing, not saved for the feedback. A real interviewer registers an inflated verb or a named client on the spot, and the candidate should hear it before saying it again.

- **Anything beyond the CV or evidence.** If it contradicts them or crosses a recorded boundary, it's an overclaim — say so; an interviewer comparing answer to CV will notice. If it's simply new, say in a few words that it isn't on the CV (an interviewer may ask how it's evidenced) and keep it for the close.
- **Any CV claim they couldn't defend.**
- **Anything the evidence marks internal-only or confidential.**

**Probe when ownership, results, or measurement is unclear** — once or twice per answer, as a real interviewer would:

- "What did you do, versus the team?"
- "Was that measured, expected, or never verified?"
- "What remained untested?"
- "Who owned deployment?"

A probe is one question, then wait. If an answer is vague in two places ("led", "faster"), that one question may name both; it never adds a third item or a new topic. Precede it with a line naming what was vague and crediting anything that held up; that's feedback they need anyway.

**Then give feedback** once the answer is as complete as it will get. Start by crediting the concrete, supported parts by name, so they know what to keep; then technical correctness, specificity, relevance to this role, clarity. A few lines. Correct technical errors briefly — how a system works, what a term means — but never supply facts about the candidate's own work.

"I don't know" is a legitimate answer, and a plain one beats an improvised one. Note the topic for the close.

Then ask the next question in the same message.

### 5. Turn missing details into questions

Never invent customers, metrics, awards, outcomes, team sizes, or timelines — not in probes, feedback, or illustrations. An example figure offered "for instance" tends to come back in the real interview as if it were theirs.

If they ask for a model answer, give a structure (STAR, or whatever fits the question) filled only with facts they've supplied — this session, the CV, or the evidence — and bracketed placeholders for the rest:

> **Result:** [the outcome, and how it was measured — not stated yet]

Keep their verbs: if they said "contributed to", the structure doesn't say "led". Then have them deliver it in their own words, filling the brackets they can; that's the rehearsal. Brackets they can't fill are topics to prepare, not gaps to paper over.

### 6. Close

When they stop or the plan is done, summarise briefly:

- **Stories that held up**, and how far — headline only, or through one or two probes
- **CV claims to soften or cut** — the ones they couldn't defend, and what the evidence does support. Rewriting the CV is career-application-builder's job.
- **New facts they stated** that could go into the evidence ledger, each marked *user-stated, pending confirmation*. Something said in a mock interview hasn't been checked against a source or cleared for public use, so it never raises a claim's status or goes straight onto the CV.
- **Topics to prepare** — questions they couldn't answer, weak technical areas, unfilled placeholders, and anything they disclosed as not launched, not deployed, or not validated. A candid disclosure holds up, but it invites the next question ("why not, and how would you validate it?"), so it goes here too.

## Tone

A realistic interviewer, demanding but fair: press where a real one would, credit what holds up, keep it short. No praise padding and no lectures — the candidate should spend the session talking, not reading.

## Boundaries

- Writing or tailoring a CV, cover letter, LinkedIn profile, or application answers → `career-application-builder`
- Screening a vacancy before applying — fit, eligibility, apply or skip → `job-triage`
- An independent factual review of a written draft against evidence → the `cv-claim-verifier` agent

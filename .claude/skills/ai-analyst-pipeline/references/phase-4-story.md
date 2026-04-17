# Phase 4: Story

## Purpose

Decide what you are going to say — and in what order — **before** choosing visuals. A good analysis has a spine: one argument, with findings arranged so each one sets up the next. Skipping this phase is how decks end up as "one slide per chart" instead of a coherent narrative.

## Input

- Validated `findings.json` from Phase 3
- Audience context from Phase 1 (executives, analysts, specific team)

## Output (deliverable for this phase)

`storyboard.md` in the workspace, containing:

- A single headline message (one sentence)
- A narrative arc laid out as a sequence of beats
- Each beat has: purpose, supporting finding(s), and proposed visualization
- An explicit "so what" and call to action

## The Context-Tension-Resolution arc

This skill uses the CTR arc, adapted from narrative nonfiction and widely used in consulting-style analysis:

1. **Context** — Set the stage. What is the current state? What was expected?
2. **Tension** — What is surprising, concerning, or divergent? Why does this matter now?
3. **Resolution** — What does the data reveal as the actual cause, and what should we do?

Most analyses spend too long on Context (repeating what the audience already knows) and too little on Resolution (where the action is). Rule of thumb: 20% Context, 30% Tension, 50% Resolution.

## Process

### 4.1 — Draft the headline

Write one sentence that captures the essential finding. If someone reads only this sentence, what do you want them to know?

**Good headlines:**
- "Our tourism recovery is real but concentrated in Maui — other islands still need intervention."
- "The revenue miss is entirely driven by a single enterprise customer's churn, not a systemic issue."
- "Conversion looks flat, but new-user conversion improved 15% — offset by a regression in returning users."

**Bad headlines:**
- "Analysis of monthly data" (not a claim)
- "Revenue is complicated" (no direction)
- "See findings" (lazy)

If you can't write a single-sentence headline, your findings aren't integrated yet. Go back and think about what they mean together.

### 4.2 — Structure the narrative beats

Each beat in the arc is a single point you want to make. A typical analysis has 5-10 beats. For each beat, write:

- **Purpose**: what this beat establishes (e.g., "show that the aggregate is misleading")
- **Supporting finding(s)**: which F1/F2/... entries from `findings.json`
- **Proposed visualization**: what kind of chart (not the detailed design yet)
- **Transition**: how it leads to the next beat

**Example storyboard fragment:**

| # | Section | Beat | Purpose | Findings | Visualization |
|---|---|---|---|---|---|
| 1 | Context | Tourism recovery assumed complete | Set prior expectation | F1 (aggregate flat) | Aggregate line chart |
| 2 | Tension | But aggregate is misleading | Reveal Simpson's Paradox | F2 (island divergence) | Small multiples per island |
| 3 | Tension | Oahu decline concentrated in hotels | Drill one layer | F3 | Stacked area |
| 4 | Resolution | Hotel decline is luxury-driven | Isolate specific segment | F4 | Tier comparison bar |
| 5 | Resolution | Japanese inbound market is the lever | Name the actionable root cause | F5 | Origin breakdown |
| 6 | Resolution | Three recommendations | Make the call | — | Recommendation table |

### 4.3 — Narrative coherence check

Before moving to charts, re-read the beats as if you are the audience:

- Does each beat earn its place? (If you remove it, does the story break?)
- Does each beat transition to the next? (Is there a reason for the ordering?)
- Does the story land on something actionable? (Or does it peter out?)
- Is there a weak beat where you're handwaving between findings? (If so, either strengthen it or cut.)

A common failure mode: the story works logically but has one beat that doesn't follow from the prior one. Audiences notice this as "wait, how did we get here?" — even when they can't articulate it.

### 4.4 — Emergent length

The **number of beats is not fixed**. Don't force a 15-slide deck if the story fits in 8. Don't stretch 3 findings into 20 slides. Let the findings determine the length.

Likewise: the deliverable format (Phase 6) should follow the story, not the other way around. If the story is 5 beats, it's a short report, not a sprawling deck.

### 4.5 — Recommendations with owners

Each recommendation in the Resolution section must have:

- **What** — specific action to take
- **Who** — named role/team responsible (or a placeholder if the user will assign)
- **Success metric** — how you'll know it worked
- **Confidence** — High/Medium/Low from Phase 3
- **Follow-up date** — when to revisit

A recommendation without owners and metrics is a wish, not a plan.

## Gate (must clear before Phase 5)

- [ ] Headline message is written as a single sentence
- [ ] Storyboard has labeled CTR sections with beats
- [ ] Each beat maps to at least one validated finding
- [ ] Narrative coherence re-read has been done
- [ ] Recommendations have owners, metrics, confidence grades, follow-up dates

## Common pitfalls

- **Leading with methodology.** Audiences care about what you found, not how. Methodology goes in an appendix.
- **Burying the headline.** Whatever the format, the headline message appears within the first minute of reading.
- **Over-heavy Context.** Five slides explaining what the business does to an audience that runs the business. Cut ruthlessly.
- **Unranked recommendations.** "Here are 10 things you could do" signals the analyst didn't decide. Rank them.
- **Fixed-length decks.** "Exec decks are always 20 slides" is cargo cult. Let the story drive.

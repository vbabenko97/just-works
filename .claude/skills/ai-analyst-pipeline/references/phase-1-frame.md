# Phase 1: Frame

## Purpose

Turn the user's vague or implicit question into a structured analytical question with explicit hypotheses. Most bad analyses fail here — by skipping this step and diving straight into "explore the data", analysts end up producing charts that don't support any particular decision.

## Input

- A business prompt (may be vague: "look into this data", "why is revenue down")
- One or more CSV/Excel files
- Any context the user has provided about the domain, stakeholders, or decisions

## Output (deliverable for this phase)

A written `framing.md` in the workspace containing:

1. **Structured analytical question** — a precise version of the user's ask
2. **Decision context** — what decision will this analysis support, and who makes it
3. **Success criteria** — what a "good" answer looks like
4. **Hypotheses** — 3-5 testable theories, across multiple cause categories
5. **Data inventory** — what files are in scope and what columns matter

## Process

### Step 1.1 — Inspect the data first, briefly

Before framing the question, do a one-pass look at the data:
- List files and their sizes
- For each file: row count, column names, a sample of values, and detected types
- Note obvious quality issues (missing values, mixed types, duplicate rows)

Don't do full analysis yet. The point is to know what levers exist — you can't frame a meaningful hypothesis without knowing what's measurable.

### Step 1.2 — Write the structured analytical question

Transform the user's prompt into a question with these properties:

- **Specific metric**: what number is moving, or what decision is pending
- **Time scope**: over what period
- **Population scope**: across what segments / entities
- **Comparison**: against what baseline (prior period, target, peer group)

**Example:**
- User asked: "Why is our tourism business weird?"
- Framed: "What is driving the divergence between Maui (+7%) and the other Hawaiian islands (-3% aggregate) in month-over-month visitor arrivals over the past 6 months, and what actions should tourism authorities take differently by island?"

If the user gave enough context to frame well, write the framing and move on. If the user was vague, propose 2-3 candidate framings and ask them to pick.

### Step 1.3 — Generate hypotheses across cause categories

Generate **at least 3 hypotheses** before touching the data further. This prevents confirmation bias later. Cover multiple cause categories, not just one:

- **External drivers**: macro factors, seasonality, competitor actions, regulation
- **Composition shifts**: mix changes (segment, product, channel) masking underlying movement
- **Operational causes**: internal decisions, product changes, pricing, marketing
- **Data artifacts**: measurement changes, tracking gaps, definition shifts

For each hypothesis:
- State it as a testable claim ("If H1 is true, we would expect X in the data")
- Note what evidence would confirm vs. refute it
- Mark which phases/analyses will test it

### Step 1.4 — Define success criteria

Answer two questions in writing:

- **What does "answered" look like?** (e.g., "We can attribute at least 80% of the metric change to specific drivers with a confidence grade")
- **What does "done" look like?** (e.g., "Executive deck of 15-20 slides with top 3 recommendations, each with an owner")

This is what lets you stop when you're done instead of analyzing forever.

## Gate (must clear before Phase 2)

- [ ] Structured question is written and unambiguous
- [ ] At least 3 hypotheses across at least 2 cause categories are documented
- [ ] Success criteria are explicit
- [ ] Data inventory is complete (you know what you have)

If any of these are missing, loop back. Phase 2 will waste effort otherwise.

## Common pitfalls

- **Framing too narrow.** If the user asks "why did revenue drop" and you frame it as "analyze October revenue", you'll miss that the drop started in August.
- **Framing too broad.** "Analyze the business" is not a question. Push for specificity.
- **Skipping hypothesis generation.** Without hypotheses, exploration becomes random drift through the data.
- **Assuming the metric definition.** Confirm how the user defines "revenue", "active user", "churn" — these definitions matter.

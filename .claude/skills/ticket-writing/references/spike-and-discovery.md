# Ticket writing: Spike and Discovery

Part of the ticket-writing skill. SKILL.md keeps a short template for both types; this file holds the full guidance.

## Spike (technical)

A timeboxed investigation that produces a decision, not shippable code. Two rules keep spikes useful: **one specific question** and **a strict timebox**, set in the tracker's estimate or due-date field. When the timebox runs out, report findings and decide whether to re-spike — don't extend silently.

Sections:

**Goal**
One concrete question. "Can we replace library X with library Y without losing feature Z?" — not "Research library Y."

**Method**
How the investigation will run — prototype, benchmark, read source, interview SMEs, review docs. Concrete enough that a reader knows what the work will look like.

**Expected output**
What the spike will produce — a recommendation doc, a small proof-of-concept, a design sketch. Not working production code.

**Open questions** (optional)
Things known to be unknown going in. Helps scope the investigation.

## Discovery (product)

The product-research variant of a spike. Used when the question is about what to build and why, not how to build it. Timeboxed like a spike; the timebox goes in the tracker's estimate or due-date field.

Sections:

**Opportunity**
What the team has noticed — a user pattern, a competitor signal, a support trend. Ground it in evidence.

**Hypothesis**
A falsifiable claim: "If we do X, then Y will change by Z." Not "we think users want this."

**Open questions**
Explicit unknowns that block a go/no-go decision. Numbered for reference.

**Expected output**
The decision artifact the discovery will produce — a go/no-go recommendation, a research summary. Not a spec or shipped code.


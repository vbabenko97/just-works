---
name: ticket-writing
description: Apply when writing, rewriting, reviewing, or filing issue-tracker tickets (Jira, Linear, ClickUp, GitHub Issues, Asana). Covers titles, sections per type (PBI / Bug / Spike / Discovery), acceptance-criteria formats, bug reproduction fields, INVEST, linking, native-field discipline, tracker introspection, update-vs-create, and common anti-patterns. Tool-agnostic. Project conventions always override these defaults.
---

# Ticket Writing

Match the project's existing conventions. When uncertain, read 3–5 recent tickets to infer local style — title form, section names, typical length, and link usage. These defaults apply only when the project has no established convention.

## Never rules

These are unconditional. They prevent ambiguity, lost provenance, and wasted triage regardless of project style.

- **Never ship a ticket whose title doesn't identify what will change.** Titles like "bug" or "update" force every reader to open the ticket to find out. Titles are scanned in lists and boards far more often than they're clicked.
- **Never omit Steps to reproduce on a Bug.** Without numbered, specific steps, the dev re-derives the repro path from scratch — the single biggest cause of "cannot reproduce" churn.
- **Never omit Expected and Actual results on a Bug.** "It's broken" is not a specification. Expected is the target to fix toward; Actual is what was observed.
- **Never write acceptance criteria using subjective terms** — "fast", "intuitive", "user-friendly", "good UX". They're untestable. Quantify ("search returns under 500 ms at p95") or describe observable behavior.
- **Never prescribe the solution inside the story body.** "As a user, I want a React dropdown with debounced autocomplete..." locks the team into an implementation. Describe what the user needs; leave how to the implementer.
- **Never mix multiple user roles in one story.** "As a user and admin, I want..." is two stories. Split them — different permissions, different flows, different tests.
- **Never leave placeholders in a published ticket** — `[TBD]`, `[TODO]`, `[paste link]`. Get the value before creating, ask, or add a follow-up comment after creation. Placeholders that survive to closure signal a weak process.
- **Never title a ticket with a trailing period.** Wastes characters in scan-width views and doesn't match imperative-mood form.
- **Never block work on a dependency without linking the blocker.** If ticket A can't start until B ships, use a blocked-by link so the board and dependency tooling can surface it.
- **Never create a ticket without checking that a similar one isn't already open.** Duplicates fragment discussion, split assignment, and waste triage. Search the target tracker by title keywords and by likely tags first. Surface near-matches to the requester and let them decide: close as duplicate, link as relates-to or blocks, or proceed. Skip the search only when the user has already confirmed it's a new ticket.
- **Never include a section, field, or value the user didn't request or you haven't confirmed.** Required values for the type get asked, not guessed (Bug's Severity in the body; Spike's timebox and Bug's priority in native fields). Optional sections stay omitted unless the user supplies the content (Open questions, Attachments, Links). Inventing values to match a template pollutes the ticket with content the user must re-check, and erodes trust that the body reflects their intent.
- **Never put a structured attribute in the body when the tracker has a native field for it.** Due dates, start dates, owners, priority, effort, parent, and blocked-by all have fields. A date in prose is dead data; the same date in a native field drives reminders, filters, and dependency views.
- **Never auto-fill a field the user didn't specify.** Priority, due date, assignees, labels, sprint, status, estimate, parent, custom fields. If the user didn't say, ask. The user can't distinguish your guess from their input and ends up auditing every field. Only exception: the user explicitly grants discretion ("use your judgment", "you decide").
- **Never create a ticket without at least one assignee** unless the user says there isn't one yet. Unowned tickets drift.
- **Never guess the target list, board, or project — or any ID.** Ticket IDs, list IDs, user IDs, and custom-field IDs come from discovery or from the user. Asking is cheaper than filing in the wrong place.
- **Never overwrite an existing ticket's body on update.** Append under a dated marker (`--- update 2026-04-20 ---`). Single-valued fields (priority, assignee, due date, status) are safe to overwrite; narrative is not.

## Naming

Imperative mood, sentence case, no trailing period. Test the title by completing: **"If applied, this ticket will ___."** If the result reads grammatically, the mood is right.

```
Good: Hide regular photo upsell buttons until first view completes
Good: Fix off-by-one error in pagination count
Good: Investigate three PDF libraries for performance and licensing
Good: Add CSV export to account transactions page

Bad:  Photo upsell bug                 (vague; no verb; no target)
Bad:  Fixed the thing                  (past tense; no specific target)
Bad:  Update files                     (vague verb; no target)
Bad:  Fix: dashboard crash.            (trailing period; redundant prefix)
Bad:  As a user I want to export...    (user-story format belongs in the body, not the title)
```

Aim for under ~70 characters when possible — that's the width where titles stay scannable in list and board views. Longer titles are fine when the extra words add clarity. Don't pad to hit the range, and don't truncate a clear title to squeeze under it.

## Body formatting

- **Headers** — one level of boldness: Markdown bold (`**Header**`) or H2 (`## Header`), whichever the tool renders. No H1 inside the body. Pick one style per ticket and keep it uniform.
- **Header punctuation** — end the header with `:` when it introduces a list, a single-value line below, or a definition (`Steps to reproduce:`, `Severity:`, `Acceptance criteria:`). Omit the colon when the header opens a prose paragraph (`Summary`, `Problem`, `Proposed change`).
- **Single-value sections** — for one-line values like `Severity`, put the header on its own line and the value on the next line. Don't inline the value next to the header.
- **No horizontal rules** (`---`). Sections separate themselves through bold headers.
- **No em dashes as separators** — never to join a label or value to its explanation in a field list (`Major — no workaround`), never between sections. Use a period, comma, or colon instead. Em dashes inside prose sentences are fine.
- **No blank line between a header and its first line of content.** Each section opens immediately.
- **Numbered and bulleted lists** — no blank lines between items. Each item ends with a period.
- **Inline code with backticks** — wrap technical identifiers in backticks: field names (`due_date`, `postId`), enum values (`high`, `urgent`), env var names (`OPENROUTER_API_KEY`), file paths (`src/api/auth.ts`), id expressions (`postId = 69c2c683039c4ad6d45387bcb7ede`). Keep plain URLs and product-path references (`Settings → Account → Transactions`) unformatted.
- **Capitalize proper nouns** — environment names (`Prod`, `Stage`, `Dev`), browser names (`Chrome`, `Firefox`, `Safari`), OS names (`Windows`, `macOS`), service and team names (`Platform`, `AI backend`, `Ops`), vendor names (`AWS`, `Slack`), and standard acronyms (`API`, `URL`, `HTTP`).
- **Length** — as short as the problem allows. A long body usually means the ticket should split or link a doc.
- **Code, logs, error messages** — fenced code blocks for verbatim multi-line content; inline backticks for short identifiers. Don't paraphrase error messages; quote them exactly.

## Fields vs body

Every tracker splits a ticket into native fields and a narrative body. The body is for prose a human reads; fields are for data the tool acts on.

| Attribute | Goes in | Not in |
|-----------|---------|--------|
| Due date, start date | The date field | Body prose ("Due: 25 Apr") |
| Priority | The priority field | Body ("Priority: High") |
| Owner | The assignee field | Body ("Assigned to: Kostia") |
| Blocks / blocked-by | A dependency link | Body ("Blocked by: TASK-123") |
| Relates to | A linked-ticket reference | Body ("Related to: TASK-123") |
| Parent / epic | The parent field or sub-task relationship | Body ("Parent: EPIC-5") |
| Sprint membership, story points | The native field, else the team's established label convention | Body |
| Effort estimate | The estimate field | Body |
| Attachment | A real file upload | A URL pasted into prose |

Rule: if it's searchable, filterable, sortable, or automatable, it belongs in a field. One deliberate exception — Bug severity has no native field in most trackers, so it stays in the body while priority goes to the field.

**Priority is a triage verdict, not a default.** Unset means "not yet triaged", which is real information. Setting the middle value (`normal`, `medium`) without a triage decision destroys that signal. Leave it unset until someone decides.

## Working in a tracker

**Introspect before filing in an unfamiliar list.** Discover, once per list per session: available statuses (each board defines its own — don't set one that doesn't exist), existing labels and their conventions, custom fields and their types, and how to resolve member names to users. Reuse the conventions you find exactly; don't invent a variant of an existing pattern. If a concept the user mentioned has no existing convention, ask rather than inventing one.

**Update vs create.** Update when the user says "update", "edit", "append", "fix this ticket", or supplies a ticket URL or ID. Create when they say "create", "add", "new ticket", "file a bug".

**Prefer typed fields over free text.** URL, Date, Email, Number, and Dropdown fields preserve sort, filter, and automation. A date in a text field is a string.

**When you can't write to the tracker** — no integration, no credentials, or the user wants to paste it themselves — output the body plus an explicit field summary so nothing is silently dropped:

```
**List / project:** <name or id>
**Assignees:** <names>
**Priority:** <level, or "unset — not triaged">
**Due date:** <YYYY-MM-DD or none>
**Labels:** <comma-separated>
**Parent:** <id or none>
**Blocked by:** <ids>
**Relates to:** <ids>
---
<ticket body>
```

Surface every field, including the empty ones. An omitted field reads as "not applicable" when it usually means "not yet decided".

## PBI (Product Backlog Item)

A shippable user-facing change. Before writing, check it against INVEST:

- **Independent** — the ticket can ship without waiting on unrelated tickets. If it can't, link the blocker.
- **Negotiable** — the body captures the essence, not a locked contract. Implementation details are for the conversation, not the ticket.
- **Valuable** — value is to the user or customer. "So the team can build X faster" is not customer value.
- **Estimable** — enough is understood for a team member to size it within an order of magnitude.
- **Small** — fits within a sprint. If it doesn't, split it.
- **Testable** — behavior can be observed and verified.

Sections:

**Problem**
One paragraph. Who feels the pain, what they're trying to do, what happens today. Ground it in evidence (interview, support ticket, metric), not opinion.

**Proposed change**
What will be different after this ships. Keep it behavioral — what the user will see or do. Avoid implementation nouns (framework names, design patterns) unless the constraint is the point. When a concrete adjacent risk exists, add at most one inline constraint sentence ("Do not change search ranking or pagination."), not a separate section. Lists of non-goals belong in PRDs and pitches, not tickets.

**Acceptance criteria**
Observable, independently testable. Plain bullets by default; the next subsection says when to use Given-When-Then. Write as many as are useful and no more (Mike Cohn's heuristic). A long list is a signal to consider splitting, not a rule. Don't repeat Definition of Done items, such as tests passing or code reviewed: the Definition of Done is a team-owned checklist applied to every ticket at completion, while acceptance criteria belong to one ticket.

**Links** (optional)
Parent epic, blocked-by, relates-to — each as a specific link type. See Linking.

### Acceptance criteria — bullet vs Gherkin

Default to bullets (the PBI example in `references/rewrite-examples.md` shows them, and the same criteria in Given-When-Then). Switch to Given-When-Then only when:

- The flow has multiple preconditions that affect the outcome
- Multiple roles interact in the same scenario
- The flow crosses several integration points
- The criteria will feed an automated test suite directly

Keep Gherkin scenarios independent — no shared state between scenarios. If two scenarios share setup, extract it into a Background block or fold them into one scenario.

## Bug

A defect in existing behavior. Sections:

**Summary**
One line: what's wrong, where, for whom. "Login fails on Chrome 125 / Windows 11 with valid credentials on staging."

**Steps to reproduce**
Numbered, specific, complete. A dev with no prior context should follow them verbatim and reproduce.

```
1. Open https://app.example.com/login in Chrome 125 on Windows 11.
2. Enter a valid email and password.
3. Click Sign in.
```

**Actual result**
What happens. Specific and observable: "Page reloads with the form cleared. No error banner appears. Console: `POST /api/auth 401 — empty body`."

**Expected result**
What should happen: "Dashboard loads at /home with the user's display name in the header."

**Environment**
Enough detail to reproduce:

- OS and version (Windows 11 23H2, macOS 14.4)
- Browser or app and version (Chrome 125.0.6422.76, iOS app 2.18.0)
- Environment (prod / staging / local)
- Account tier or role if relevant
- Feature flags or toggles if relevant

**Severity** — technical impact of the defect: Blocker (system unusable, no workaround) / Critical (core flow fails, no acceptable workaround) / Major (significant flow fails, workaround exists) / Minor (annoying, non-blocking) / Trivial (cosmetic, no functional impact).

Priority is business urgency to fix: Urgent (before other work) / High (current sprint) / Medium (next sprint or two) / Low (when convenient). Set it in the tracker's native priority field, not the body.

Severity and priority are independent. A homepage typo during a product launch is Trivial severity + Urgent priority. A crash in a dev-only admin tool is Blocker severity + Low priority. See Fields vs body.

**Attachments** (when relevant)
Screenshot, screen recording, log excerpt, HAR file. Redact PII before attaching.

**Links** (optional)
Related tickets, the regression-introducing PR, the parent epic.

## Spike and Discovery

Both are timeboxed investigations whose output is a decision, not shipped code. A Spike asks how to build something; a Discovery asks what to build and why. Each needs one specific question and a strict timebox, set in the tracker's estimate or due-date field; if the user gives no timebox, ask. Read `references/spike-and-discovery.md` before writing either type. The required sections are:

- **Spike**: **Goal** (one concrete question, not "research X"), **Method** (prototype, benchmark, source reading, interviews), **Expected output** (a recommendation, proof of concept or design sketch, not production code). **Open questions** is optional.
- **Discovery**: **Opportunity** (what the team noticed, with evidence), **Hypothesis** (falsifiable: "If we do X, then Y will change by Z"), **Open questions** (numbered unknowns that block the go/no-go decision), **Expected output** (a go/no-go recommendation or research summary, not a spec).

When the timebox runs out, report findings and decide whether to re-spike; don't extend silently.

## Linking

Pick the most specific link type. Links are labels, not enforced logic — teams must pre-agree on semantics, because the same word can mean different things across boards.

- **Blocks / Is Blocked By** — hard dependency. One must ship before the other can start or finish.
- **Duplicates / Is Duplicated By** — same work already captured elsewhere. Close the duplicate; keep the canonical.
- **Clones / Is Cloned By** — intentional split into parallel copies that will diverge (e.g., the same feature across two platforms).
- **Relates To** — general association without a specific dependency. Use as a last resort when nothing more specific fits.
- **Parent / Sub-task** — hierarchy, not a link type. Epic → Story → Sub-task. Sub-tasks don't need explicit blocked-by links to their parent — the hierarchy implies it.

Common mistake: using "Relates To" for everything. If one ticket actually blocks another, link it as blocked-by so the board and automation can surface the dependency.

## Definition of Ready (optional)

A lightweight, team-owned checklist that says a ticket can be picked up. When the user asks whether a ticket is ready, or wants such a checklist, read `references/definition-of-ready.md`.

## Workflow

**When a ticket comes from a meeting, thread, or report** — put the substance of why it exists (the decision, the report, the signal) in Problem, Summary, Goal, or Opportunity, and attach the origin (Slack thread, support ticket, meeting) through the tracker's native link or integration, not a body section. Trackers capture origin natively (Linear customer requests, GitHub backlinks, Jira issue links), and coding agents read only title, body, and comments, so a bare permalink they can't open carries no context.

**When a required value is unknown at creation** — ask before creating, or omit it and add a follow-up comment the same day. If the user can't supply a value the type demands (e.g., a Spike with no timebox), the type is probably wrong — propose a different type rather than fabricating a placeholder.

**When rewriting an existing ticket** — preserve existing tracker links. Rewrite the title to imperative mood. Restructure into the correct sections for the ticket type. Enforce the Never rules. If the ticket describes two distinct changes, split them rather than letting them ride together.

**Before creating or saving**, check that the Never rules hold and that the body uses the right section names for the type (Acceptance criteria on a PBI; Steps / Actual / Expected on a Bug; Goal / Method on a Spike; Opportunity / Hypothesis on a Discovery). The title passes "If applied, this ticket will ___", and the body is as short as the problem allows.

## Anti-patterns

Beyond the Never rules and the sections above:

- **Technical stories posing as user stories.** "As an API, I want to expose an endpoint..." Systems aren't users. Drop the user-story framing and describe the technical change directly.
- **Stories slicing by technology layer.** "Backend for feature X" plus "Frontend for feature X". Neither is shippable alone. Slice vertically by user-visible value.
- **Product manager as proxy user.** Describe the real end user, not the PM's guess of what the user wants.
- **Scope creep in comments.** New requirements added after creation without updating the body. Either update the ticket and note the change, or create a follow-up.
- **Body-stuffing.** "Due: Apr 25. Blocked by TASK-123. Assigned to Kostia." Every one of those has a native field. See Fields vs body.
- **Defaulting priority to the middle value.** It makes untriaged tickets indistinguishable from deliberately-medium ones. Leave unset until triage.
- **Sub-task used as a dependency.** Sub-tasks mean "part of", not "waits on". If B can't start until A ships, they're peer tickets with a blocked-by link, not parent and child.
- **Inventing a label.** Reuse the board's existing convention exactly, or ask. A near-miss variant (`sprint-12` next to `sprint:12`) splits every filter that depends on it.
- **Overwriting a body on update.** History matters. Append under a dated marker.

## Rewrite examples

`references/rewrite-examples.md` has before and after pairs for a Bug, a PBI and a Spike. Open it when you need a model of a finished ticket.

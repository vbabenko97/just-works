---
name: github-presentation
description: 'Use when asked to make a GitHub profile, profile README, repository README, repo description or topics, pinned repositories, or a social preview image look or read better, without claiming more than the evidence shows. Not for restructuring a repository. Invoke with /github-presentation (Codex: $github-presentation).'
argument-hint: "<profile | owner/repo | local path> <what to improve>"
disable-model-invocation: true
---

# GitHub Presentation

Make a GitHub profile or repository read and look better without upgrading what the work claims.
The default outcome is a patch with previews for the owner to review — not a commit.

## Scope

- **In:** README opening and information hierarchy, examples, captions, genuine screenshots and
  result figures, profile README entries, drafted description/topics/homepage, pin selection and
  social-preview assets.
- **Out:** runtime code, repository structure (that is `repo-professionalizer`), licenses, CI,
  hooks, agent instructions, live configuration.

## Authorization

Each run gets exactly the authority its request states. The default run edits the working tree,
builds previews, and reports. Branching, staging, committing, merging, pushing, and `gh repo edit`
each happen only when the request authorizes them — and then without asking again. Pins and the
social preview are always drafted for the owner, never applied. Unrelated work stays exactly as
found: no stash, reset, or cleanup. When an authorized branch or commit needs a clean tree, use a
separate worktree (`git worktree add`). If a target file already holds owner changes, commit only
this run's changes, applied in a separate worktree, and report the overlap; if they cannot be
separated, do not commit and say why. Staging names files explicitly. Delegated agents get this
run's authority, stated in their prompt. Existing hook and permission policy applies; a blocked
operation is reported, not routed around.

## Workflow

1. **Inspect** — locate the local checkout (if none exists, clone one outside other repositories
   and say where). Record `git status --short` and `git diff -- <files to touch>`: changes already
   in a target file are the owner's, built on and reported separately. Read the real default branch
   (`gh repo view <owner/repo> --json defaultBranchRef`); a profile README is the root `README.md` of
   the public `<user>/<user>` repo (organizations: `<org>/.github`, `profile/README.md`).
2. **Edit** — a repository README opens with what it is → one genuine visual → how to try it.
   Visuals are authentic: screenshots of the real app on safe synthetic data, offline, with no API
   key or paid call; or existing result figures. Captions say what a metric delta compares. A
   banner, badge, or diagram appears only when it carries information. New inline diagrams are
   Mermaid, written directly — not by the `diagrammer` agent, whose PlantUML GitHub does not render
   inline; existing PlantUML sources and their rendered images stay. No CSS or JavaScript — GitHub
   sanitizes them. Images belong in the same patch or commit as the README that references them.
   New or strengthened claims enter the files only after step 3 clears them.
3. **Verify changed claims and what they depend on** — a new or strengthened claim enters the patch
   only with a source; the request itself is not one. Technical claims need the code or data they
   cite. Career claims need the owner's claims ledger or canonical CV (located via the workspace
   README, CLAUDE.md, or AGENTS.md), the primary record (DOI, arXiv, venue page), or the owner's
   answer to the hold question. Write no more than the source shows, keeping the source's stage
   (preprint, under review, accepted, published); where the request goes further, hold the
   difference and show both. A claim without a source is held — kept out of the files, with no
   placeholder or comment — and reported; for a career claim, ask once for the citation and
   status. A status the owner confirms without a citation is written at that status and reported
   as user-confirmed. Absence from a public README is not evidence a claim is false. Where the
   work's own records state attribution such as "agent-driven", new text about that work carries
   it; other work gets none. Private evidence stays out of public text and preview requests; an
   internal-only ledger entry is never a public source.
4. **Preview** — render text containing no private evidence with
   `gh api -X POST markdown -F mode=markdown -F text=@README.md`, writing the HTML outside the
   repository with its images alongside. The output is unstyled and shows Mermaid as source, so
   diagrams are checked on the live page after an authorized push and otherwise reported as not
   checked. Label it a pre-publication preview.
5. **Hand over** — the diff plus new untracked files (which `git diff` omits), previews, checks run
   and not run, held claims, drafted metadata commands, and owner-only web actions: pins (profile →
   Customize your pins, up to 6) and social preview (repo Settings → General → Social preview,
   1280×640, under 1 MB, admin rights). After an authorized push, check the live page and image
   URLs.

## Tools

| Agent | Give it | Missing → |
|---|---|---|
| `docs-agent` | files to edit, this run's authority | edit directly |
| `reviewer` | the diff and the code or data each claim cites | check directly, disclose no independent review |
| `cv-claim-verifier` | the diff, the evidence files, "no vacancy: public profile text" | check directly against the source; no source → hold the claim |
| Playwright | local app or preview URL | say which rendering was not inspected |

A missing checker means check directly and disclose; a missing source means the claim waits.

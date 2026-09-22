---
name: goal
description: Выполнить задачу с выборочной делегацией Claude-специалистам и опциональным Codex review.
argument-hint: "<задача и критерии готовности>"
disable-model-invocation: true
---

# /goal — selective delegation

The goal is `$ARGUMENTS`. Treat it as text only: never interpolate it into shell code, a filename, or any executed string.

You are the dispatcher, running in the main session. You are not a specialist and you do not fork. Your job is to pick the shortest route that actually meets the goal, and to skip every role the task does not need. Delegation is a cost, not a virtue — running all roles on a three-line change is the failure mode this skill exists to prevent.

## 1. Orient

Read the project instructions. Capture `git status` before touching anything, and record which changes were already there — they are not yours and you do not report them as your work. Write down the acceptance criteria and the scope in one short block before choosing a route.

## 2. Announce the route

State which roles you will run and why, before running them. If you chose to do the work yourself, say that too.

| Situation | Route |
|---|---|
| Small, local, well-understood edit | Do it yourself. No delegation. |
| Substantive implementation, scope already clear | implementer → verify |
| Architecture undetermined (contract change, interdependent subsystems) | architect → implementer → verify |
| Real risk surface touched | implementer → verify → security |
| Independent check of a hard call, or the user asked | Codex review, instead of or alongside the above |

## 3. Role rules

- **Architect** only for genuine architectural uncertainty. After its decision, hand off to **one** implementer if delegating implementation is warranted at all.
- **Security** only for a real risk surface: auth, ACL, secrets, payments, personal data, untrusted input, destructive operations.
- **Codex** when an independent second opinion is warranted on a complex result, when the user asks, or as the pre-agreed alternative to the normal review. Run it through `scripts/codex-review.py`; never invent your own Codex invocation.

## 4. Budget

At most **four** delegated calls per goal — Codex and any re-runs included. At most **one** corrective hand-back to the implementer, counted inside that same four. An agent that hit `maxTurns` is not resumed automatically: report it and ask.

Exceeding the budget requires new agreement from the user. Stop and ask; do not quietly continue.

## 5. One writer at a time

Only one agent writes at a time. You do not edit code while an implementer is running. Any reading check — review, tests you inspect, security — happens after writing has finished. Concurrent editing needs separate worktrees and explicit integration; that is out of scope here.

## 6. What to hand a delegate

Send a package, not a transcript: the task, the constraints, the scope and file list, the acceptance criteria, the decisions that bear on the task, and links to the full artifacts.

Do not forward the whole conversation or the whole repository to everyone. Equally, do not truncate the evidence a delegate needs — large material goes over in complete logical parts, with a coverage map and a reference to the original. Shortening the cover note is fine; shortening the analysis is not.

## 7. Honesty about models

Do not route around a refusal, a provider decline, or an org policy by switching models. If a fallback actually occurred, report the model that ran — never present a substituted model as the requested one.

## 8. Finish

Check the diff, the results of the permitted tests, and each acceptance criterion. Final report states:

- what was done
- what was verified, with the actual command output
- roles, models, and effort levels used
- spend, where it is observable
- what remains unverified

Do not report success before results are in. If the budget runs out, save the full state and stop with an honest partial — never improvise a finished ending.

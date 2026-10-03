# Provenance and maintenance

Package: `opus-5-5-prompting` · Version: **1.0.0**
Primary documentation reviewed: **2026-10-03**

## Origin

Created from the user's request for an Opus 5.5 prompting skill, starting with
Anthropic's model-specific guide (**S1**). Independent implementation; not an
Anthropic product, not a fork of an inspected user repository, and not a claim
about any locally installed skill.

No vendor guide or implementation is bundled verbatim. Templates, synthetic cases,
and the validator were authored for this package. API names and identifiers are
retained where necessary. No upstream software license is asserted for the linked
documentation, and no project license was selected on the user's behalf. Choose a
license explicitly before publishing this as a licensed project.

## Source register

All sources below were opened during the review. Prefer the model-specific and
provider-specific source over a generic recommendation when their scope differs.
These are documentation snapshots, not guarantees of account access or future API
behavior.

| Key | Primary source | URL | Used for |
| --- | --- | --- | --- |
| S1 | Anthropic — Prompting Claude Opus 5.5 | `https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-opus-5-5` | Model-specific patterns and applicability limits |
| S2 | Anthropic — Prompting best practices | `https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices` | Direct instructions, context, examples, structure |
| S3 | Anthropic — Effort | `https://platform.claude.com/docs/en/build-with-claude/effort` | Effort field, budget distinction, per-message beta |
| S4 | Anthropic — Thinking | `https://platform.claude.com/docs/en/build-with-claude/thinking` | Progress display and block handling |
| S5 | Anthropic — Preserved thinking | `https://platform.claude.com/docs/en/build-with-claude/preserved-thinking` | Replay state and prefix binding |
| S6 | Anthropic — Mid-conversation system messages and tool changes | `https://platform.claude.com/docs/en/build-with-claude/mid-conversation-system-messages` | Reminder placement and lifetime |
| S7 | Anthropic — Refusals and fallback | `https://platform.claude.com/docs/en/build-with-claude/refusals-and-fallback` | Refusal handling and explanations |
| S8 | Anthropic — Mitigate jailbreaks and prompt injections | `https://platform.claude.com/docs/en/test-and-evaluate/strengthen-guardrails/mitigate-jailbreaks` | Untrusted content and layered safeguards |
| S9 | Anthropic — Giving Claude a zoom tool for reading fine image detail | `https://platform.claude.com/cookbook/multimodal-crop-tool` | Original-image cropping and coordinate mapping |
| S10 | Anthropic — Migrating to Claude Opus 5.5 | `https://platform.claude.com/docs/en/models/opus-5-5/migration-guide` | Model ID, request incompatibilities, response shape |
| S11 | Anthropic — What's new in Claude Opus 5.5 | `https://platform.claude.com/docs/en/models/opus-5-5/whats-new-opus-5-5` | Platform-specific breaking-change cross-check |
| S12 | Anthropic — Stop reasons and fallback | `https://platform.claude.com/docs/en/build-with-claude/handling-stop-reasons` | Stop-reason semantics |
| S13 | Agent Skills — Specification | `https://agentskills.io/specification` | Portable frontmatter and supporting-file layout |
| S14 | Anthropic — Extend Claude with skills | `https://code.claude.com/docs/en/skills` | Claude Code discovery and invocation |
| S15 | OpenAI — Build skills | `https://learn.chatgpt.com/docs/build-skills` | Codex discovery and invocation; opened via the redirect from `https://developers.openai.com/codex/skills` |

## Documented facts versus package choices

**Documented:** named API fields, beta headers, response block behavior, platform
caveats, and the model-specific observations attributed to the sources above.

**Authored choices:** the create/rewrite/audit/migrate workflow; draft-only default;
contract preservation; task-bounded source discovery; optional templates; the
two-continuation ceiling; two-reminder ceiling; preflight checklist; synthetic
fixtures; and the offline package validator. Some are conservative adaptations of
vendor advice. They are not platform restrictions or measured optimal settings.

No benchmark percentages, speed claims, prices, or recommended settings for other
models are imported into the skill. No claim of live quality improvement is made.

## Review procedure

When updating, compare the relevant primary sections and change only affected
instructions. Record the review date and changed facts. Re-check exact field
names, beta status, provider support, and whether a recommendation is conditional.
Keep provenance and regression cases aligned; do not turn an optional pattern into
a universal instruction. Run the offline validator after edits.

Before adoption, test skill discovery in the actual host and evaluate representative
outputs. Nothing in a Markdown instruction enforces permissions or resource limits.

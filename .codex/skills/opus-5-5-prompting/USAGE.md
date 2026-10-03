# Usage and validation

## Package contents

`SKILL.md` is the entry point. Keep it with `references/`, `UPSTREAM.md`, and the
other package files; the standalone entry point is not the whole skill.

This is a draft artifact. No skill was installed and no live configuration was
changed while creating it.

## Place it in an existing skill tree

Use your repository's established source-of-truth and targeted copy/sync process.
Do not rerun a broad dotfiles installer or replace live configuration for this skill.
Preserve an existing same-name version before updating it, and avoid duplicate
independently edited copies.

Official discovery locations reviewed on 2026-10-03:

| Host | Project location | Personal location |
| --- | --- | --- |
| Claude Code — S14 | `.claude/skills/opus-5-5-prompting/` | `~/.claude/skills/opus-5-5-prompting/` |
| Codex — S15 | `.agents/skills/opus-5-5-prompting/` | `~/.agents/skills/opus-5-5-prompting/` |

An existing managed `.codex/skills` tree may be part of your own synchronization
setup; inspect it rather than migrating paths or assuming automatic discovery.
Loading this skill does not make Codex run Claude or change Claude Code's model.
Local skill files also do not establish account-level or cloud-session availability.
See [UPSTREAM.md](UPSTREAM.md) for source URLs. Runtime loading has not been tested.

Example invocation in Claude Code:

```text
/opus-5-5-prompting Rewrite this review prompt for Opus 5.5. Keep the review read-only, preserve all acceptance criteria, and return only the prompt: ...
```

Example invocation in Codex CLI:

```text
$opus-5-5-prompting Audit this Opus 5.5 agent prompt. Separate prompt defects from API or harness defects. Do not change settings: ...
```

## Offline checks

From the package folder, run:

```bash
python3 scripts/validate.py
```

Requires Python 3.9+ and only the standard library. Reads this package; no network,
API requests, credentials, installations, or filesystem writes. It checks the
package's deliberately simple frontmatter, references, Python syntax, JSON examples,
and evaluation-case structure. It is not a full Agent Skills conformance test,
semantic prompt grader, API validator, or proof of host compatibility.

## Behavioral evaluation

`evals/evals.json` is a runner-neutral collection of synthetic prompts and explicit
expectations, including negative-trigger cases. Its `files` arrays are empty: the
prompts contain their own inputs. The file is not an executable test runner.

For positive cases, load the skill and score each stated expectation against the
actual output. For negative-trigger cases, evaluate routing from the skill's name
and description without forcing it to load. Record failed criteria and preserve
outputs. Run live evaluations only with explicit authorization and an agreed budget.

For rollback, restore the previous same-name folder through the established sync
process, or remove only this new folder. Do not revert unrelated host settings.

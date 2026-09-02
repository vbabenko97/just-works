# Gemini 3.7 Flash Prompting

A Codex skill for creating, migrating, and evaluating prompts and coding-agent instructions for GA `gemini-3.7-flash`.

## Install

User-wide (available to all local projects):

```sh
cp -R gemini-3-7-flash-prompting ~/.codex/skills/
```

Repository-specific (shared with a repository):

```sh
mkdir -p .codex/skills
cp -R gemini-3-7-flash-prompting .codex/skills/
```

Restart or reload Codex after installation if it does not discover the skill immediately.

## Invoke

Ask Codex: “Use `gemini-3-7-flash-prompting` to migrate this coding-agent system prompt.”

## Layout

- `SKILL.md` — workflow and high-level guardrails.
- `references/model-contract.md` — official model/API facts.
- `references/prompt-design.md` — prompt composition and thinking-level router.
- `references/templates.md` — reusable coding-agent, task, review, migration, exploration, and visual-to-code prompts.
- `references/comparison-and-evaluation.md` — harness-aware comparison and evaluation rubric.
- `scripts/lint_gemini_prompt.py` — dependency-free migration-hazard linter.
- `tests/test_lint_gemini_prompt.py` — dependency-free unit and CLI coverage for the linter.
- `agents/openai.yaml` — Codex skill interface metadata.

## Linter

```sh
python3 scripts/lint_gemini_prompt.py prompt.md
printf 'thinking_budget: 100\n' | python3 scripts/lint_gemini_prompt.py
```

The linter exits `0` for clean input, `1` when it finds hazards, and `2` for usage or read errors. Invalid thinking levels and legacy parameters are checked on every line, including fenced configuration examples. Manual chain-of-thought and mixed XML/Markdown delimiter checks inspect prose outside fenced code blocks.

## Validate

```sh
python3 -c "from pathlib import Path; compile(Path('scripts/lint_gemini_prompt.py').read_text(encoding='utf-8'), 'lint_gemini_prompt.py', 'exec')"
python3 -m unittest discover -s tests -v
printf 'Use MEDIUM thinking_level.\n' | python3 scripts/lint_gemini_prompt.py
printf "Let's think step by step.\n" | python3 scripts/lint_gemini_prompt.py; test $? -eq 1
```

# Gemini 3.8 Flash Prompting — local skill

Version 1.0.0 · documentation checked 6 September 2026.

A personal skill for creating and improving Gemini prompts from a ChatGPT macOS
Codex Local session. The files live on your Mac after installation. The skill
does not run Gemini, switch your ChatGPT model, or supply on-device inference.
The installer makes no network requests and needs no API key, sudo, or package
installation. It does not alter global configuration or shell startup files.

## Install from the ChatGPT macOS app

Extract `gemini-3-8-flash-prompting.zip` in Downloads. The resulting folder should
be `~/Downloads/gemini-3-8-flash-prompting/`.

In the ChatGPT dropdown, choose **Codex**, then start a **Local** chat. [S10]
Open the top-right terminal icon, or use Control + backtick. [S11]
Run:

```bash
bash "$HOME/Downloads/gemini-3-8-flash-prompting/install-macos.sh"
```

The installer checks the package and copies it to:

```text
~/.agents/skills/gemini-3-8-flash-prompting/
```

That is Codex's user-level skill location. [S09] Existing installations are never
overwritten. Source and destination symlinks are refused rather than followed.
A failed partial copy remains marked for inspection; no cleanup deletes user data.

To inspect the plan without writing anything:

```bash
bash "$HOME/Downloads/gemini-3-8-flash-prompting/install-macos.sh" --dry-run
```

The installer supports macOS's Bash syntax and ordinary local command-line tools.
Python is not required to install. Paths containing spaces are supported. Do not
run with sudo or change HOME to install into another person's account.

## Use

Start a fresh Local chat after installation. Type `@` and select
**Gemini 3.8 Flash Prompting** from the skill picker. [S09] Then paste:

```text
Improve this prompt for Gemini 3.8 Flash. Preserve my constraints.
Return the improved prompt first, then explain only material changes:

[Paste the prompt here]
```

The bundled `agents/openai.yaml` sets `allow_implicit_invocation: false`; Codex
should not activate it from an unrelated message. [S09] When it is not visible,
check the installed path and restart Codex/the app. A repository-level skill with
the same name may create duplicate picker entries; do not delete other skills
without inspecting them. [S09]

## Included

- `SKILL.md` and `agents/openai.yaml`: workflow and manual-invocation metadata.
- `references/`: verified profile, patterns, API boundaries, evaluation, source index.
- `examples/`: three inert Interactions request bodies with synthetic data.
- `scripts/validate.py` and `tests/`: offline checks and 16 manual behavioral cases.
- `install-macos.sh` and `MANIFEST.sha256`: local installer and integrity checks.

The skill covers writing, extraction, source-grounded document review, research,
multimodal analysis prompts, and bounded coding-agent prompts. It separates prompt
text from actual API controls and preserves the user's language and constraints.

## Validation and limits

See `tests/VALIDATION.md` for exactly what was tested. Structural checks and
installer tests are not live tests of Gemini or of the ChatGPT skill selector.
The behavior cases are provided for evaluation, with `not_run` status.

References are dated snapshots. The skill works from these local notes without
mandatory browsing; current API questions may require a permitted documentation
refresh. No background updater, network client, or automatic dependency installer
is included. Ordinary use of ChatGPT or Gemini remains subject to those services'
network and data-handling behavior; "local skill" describes the files, not the model.

## Inspect or remove

Read `SKILL.md`, `agents/openai.yaml`, and the installer before running it.
Checksums catch accidental changes; they are not a publisher authenticity proof.
The installer refuses modified packages. After an intentional source edit, review
and regenerate the manifest before redistribution; do not bypass an unexplained
integrity failure.

To remove this skill, use Finder's Go to Folder and open the installed path above,
then move only the `gemini-3-8-flash-prompting` folder to Trash. Restart the app
when necessary. Do not delete the parent `skills` folder or other personal skills.

## Sources

`references/sources.json` records the 12 primary-source pages inspected, including
Google's model/API guides and OpenAI's local skill documentation. Bracketed source
IDs resolve there. Templates and evaluation rules are original implementation
choices, not claims of proven performance improvement. No third-party full-text
documentation or proprietary assets are bundled.

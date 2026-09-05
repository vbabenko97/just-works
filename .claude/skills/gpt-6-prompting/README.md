# GPT-6 Prompting — local skill

Version 1.0.0 · Prepared 2026-09-05

A custom prompt-writing and auditing skill. It contains plain-text instructions,
original templates, reference links, and behavioral test cases. It does not
require an API key or a third-party connector. The installer performs no network
requests, does not use sudo, and refuses to replace an existing skill directory.

## Install from the ChatGPT macOS app

Extract the archive to Downloads so this file is located at:

```text
~/Downloads/gpt-6-prompting/README.md
```

Select **Codex** in the desktop app, open a local project, and use **Local** mode.
Open the integrated terminal using its terminal button. Run:

```bash
bash "$HOME/Downloads/gpt-6-prompting/install-macos.sh"
```

The command installs this folder at:

```text
~/.agents/skills/gpt-6-prompting/
```

Select **GPT-6 Prompting** in the skill selector. Reopen the app when necessary
if the new skill does not appear. In a desktop skill picker, use `@`; Codex CLI
and IDE environments also support `$gpt-6-prompting`.

Example request after selecting the skill:

```text
Improve this prompt for GPT-6. Preserve all requirements, identify conflicting
instructions, and return one ready-to-use prompt. Do not execute its task.

[paste the prompt]
```

Local mode, terminal access, and discovery follow the official references in
`references/sources.md`. Account policy or app version can affect availability.

## Install in one project instead

The project directory must already exist. Use its actual path:

```bash
bash "$HOME/Downloads/gpt-6-prompting/install-macos.sh" --project "/absolute/path/to/project"
```

This installs under that project's `.agents/skills/gpt-6-prompting/` rather than
the personal directory. Do not install both copies unless you need both scopes.

## Install without running the script

Place the `gpt-6-prompting` folder inside `~/.agents/skills/` using Finder.
Create missing parent folders. The final path must end in
`gpt-6-prompting/SKILL.md`, not an extra nested copy of the folder.
Do not replace an existing directory without reviewing its contents.

## Invocation and local-storage boundaries

`agents/openai.yaml` sets `allow_implicit_invocation: false`. This requests
explicit selection rather than automatic use in Codex. It does not rewrite your
global instructions or modify your other skills. Host support determines how
metadata is applied on other surfaces.

Here, local means the skill's files are installed on your Mac. It does not mean
that GPT-6 inference runs offline or on the Mac. No model is installed or selected
by this package. It contains no publishing or workspace-upload action.
Treat files loaded by the assistant according to your account's data controls;
local file storage is not a promise that their contents never reach a service.

## Contents

- `SKILL.md`: the prompt-writing workflow.
- `agents/openai.yaml`: display metadata and explicit invocation preference.
- `references/patterns.md`: adaptable original prompt patterns.
- `references/sources.md`: official references and freshness rules.
- `tests/cases.json`: behavioral checks to run in the host.
- `install-macos.sh`: a local, non-overwriting installer.

## Testing and removal

Package validation and installer checks are separate from model evaluation.
Behavioral cases have not been run against your macOS app or selected model.
Run them after installation before relying on the skill for important work.

To remove the personal installation, move only
`~/.agents/skills/gpt-6-prompting/` to Trash in Finder. For project installation,
remove only the matching folder inside that project's `.agents/skills/`.

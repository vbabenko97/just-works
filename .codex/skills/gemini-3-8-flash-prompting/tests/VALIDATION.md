# Validation record

Package version: 1.0.0. Documentation verification date: **2026-09-06**.

## Checks actually performed

| Check | Result | Scope |
| --- | --- | --- |
| Bash syntax validation (`bash -n`) | Passed | Installer parses in the available Bash runtime. |
| Offline package validator | 7 check groups passed | Required files, metadata, citations, request examples, manual cases, checksums. |
| Installer unit tests | 18 tests passed | Temporary HOME directories; success, refusal, path, and integrity behavior. |
| YAML parsing | Passed | SKILL frontmatter and agents/openai.yaml parsed during build validation. |
| Python syntax parsing | Passed | Validator and installer-test code parsed without execution of model calls. |

Installer tests cover successful installation with spaces in paths, dry-run and
help behavior, repeat installation, pre-existing files, modified packages,
missing/unsafe manifests, symlinks, invalid HOME values, sudo-environment refusal,
Finder metadata exclusion, and preservation of global configuration/other skills.

## Environment and limits

Tests ran in a **Linux build sandbox**, using Bash 5.2 and Python 3.13. The shell
script uses syntax intended for macOS Bash 3.2 and common macOS command-line tools,
but **native macOS execution was not tested**. The installer's runtime does not
require Python; Python is only for optional offline package/test checks.

The ChatGPT macOS skill picker was not exercised. No Gemini API requests, paid
calls, or authenticated account checks were made. The three API examples were
checked against documentation and parsed locally, not submitted to Google.

All **16 behavioral evaluation cases are not_run**. They are acceptance criteria,
not evidence of measured quality, successful triggering, or performance uplift.

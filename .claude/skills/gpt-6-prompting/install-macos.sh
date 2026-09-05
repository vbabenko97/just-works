#!/bin/bash
# Local skill installer. Compatible with macOS's bundled Bash 3.2.
# No downloads, API calls, sudo, global config edits, or overwrites.
set -euo pipefail

skill_name="gpt-6-prompting"
source_dir="$(CDPATH= cd "$(dirname "$0")" && pwd -P)"

usage() {
  printf '%s\n'     'Usage: bash install-macos.sh [--user | --project /absolute/project/path]'     'Default: install in $HOME/.agents/skills/gpt-6-prompting'     'An existing destination is never overwritten.'
}

case "${1:-}" in
  ''|--user)
    if [ "$#" -gt 1 ]; then usage >&2; exit 2; fi
    : "${HOME:?HOME must be set}"
    parent_dir="$HOME/.agents/skills"
    ;;
  --project)
    if [ "$#" -ne 2 ] || [ ! -d "$2" ]; then
      printf 'Error: --project needs an existing project directory.\n' >&2
      usage >&2
      exit 2
    fi
    case "$2" in
      /*) ;;
      *) printf 'Error: use an absolute project path.\n' >&2; exit 2 ;;
    esac
    project_dir="$(CDPATH= cd "$2" && pwd -P)"
    parent_dir="$project_dir/.agents/skills"
    ;;
  --help|-h)
    usage
    exit 0
    ;;
  *)
    usage >&2
    exit 2
    ;;
esac

for file in SKILL.md agents/openai.yaml references/patterns.md references/sources.md tests/cases.json; do
  if [ ! -f "$source_dir/$file" ]; then
    printf 'Error: incomplete package; missing %s\n' "$file" >&2
    exit 1
  fi
done

if ! grep -q '^name: gpt-6-prompting$' "$source_dir/SKILL.md"; then
  printf 'Error: unexpected skill name in SKILL.md.\n' >&2
  exit 1
fi

destination="$parent_dir/$skill_name"
if [ -e "$destination" ] || [ -L "$destination" ]; then
  printf 'Not installed: destination already exists:\n%s\n' "$destination" >&2
  printf 'Review or move the existing folder before installing this version.\n' >&2
  exit 2
fi

mkdir -p "$parent_dir"
# mkdir reserves the destination without merging into an existing directory.
if ! mkdir "$destination"; then
  printf 'Error: could not create the destination; no files were copied.\n' >&2
  exit 1
fi
if ! cp -R "$source_dir/." "$destination/"; then
  printf 'Error: copy failed. An incomplete folder may remain at:\n%s\n' "$destination" >&2
  exit 1
fi

if ! cmp -s "$source_dir/SKILL.md" "$destination/SKILL.md"; then
  printf 'Error: installed SKILL.md does not match the source.\n' >&2
  exit 1
fi
printf 'Installed local skill:\n%s\n' "$destination"
printf 'Select GPT-6 Prompting in the app. Reopen the app if it is not listed.\n'

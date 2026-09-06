#!/bin/bash
# Offline personal-skill installer. Compatible with macOS Bash 3.2 syntax.
# Does not download, execute examples, install dependencies, or edit global config.
set -euo pipefail
umask 077

NAME='gemini-3-8-flash-prompting'
DRY_RUN=0
CREATED=0
DEST=''

fail() { printf 'Error: %s\n' "$*" >&2; exit 1; }
usage() {
    printf 'Usage: bash install-macos.sh [--dry-run | --help]\n'
    printf 'Install only into $HOME/.agents/skills/%s; never overwrite.\n' "$NAME"
}

if [ "$#" -gt 1 ]; then usage >&2; exit 2; fi
case "${1:-}" in
    '') ;;
    --dry-run) DRY_RUN=1 ;;
    --help|-h) usage; exit 0 ;;
    *) usage >&2; exit 2 ;;
esac

[ -z "${SUDO_USER:-}" ] || fail 'Run as your own account, without sudo.'
case "${HOME:-}" in
    /*) ;;
    *) fail 'HOME must be an existing absolute directory.' ;;
esac
HOME_DIR="${HOME%/}"
[ -n "$HOME_DIR" ] && [ "$HOME_DIR" != '/' ] || fail 'Refusing an empty or root HOME.'
[ -d "$HOME_DIR" ] && [ ! -L "$HOME_DIR" ] || fail 'HOME must be a real directory, not a symlink.'
[ ! -L "${BASH_SOURCE[0]}" ] || fail 'Refusing a symlinked installer.'
SOURCE_PARENT="$(dirname "${BASH_SOURCE[0]}")"
[ ! -L "$SOURCE_PARENT" ] || fail 'Refusing a symlinked source directory.'
SOURCE_DIR="$(CDPATH= cd "$SOURCE_PARENT" && pwd -P)"
AGENTS_DIR="$HOME_DIR/.agents"
SKILLS_DIR="$AGENTS_DIR/skills"
DEST="$SKILLS_DIR/$NAME"

for dir in "$AGENTS_DIR" "$SKILLS_DIR"; do
    [ ! -L "$dir" ] || fail "Refusing symlinked destination parent: $dir"
    if [ -e "$dir" ] && [ ! -d "$dir" ]; then
        fail "Destination parent is not a directory: $dir"
    fi
done
if [ -e "$DEST" ] || [ -L "$DEST" ]; then
    fail "Destination already exists; nothing overwritten: $DEST"
fi
command -v shasum >/dev/null 2>&1 || fail 'Required local checksum utility shasum is missing.'
[ -r "$SOURCE_DIR/MANIFEST.sha256" ] || fail 'MANIFEST.sha256 is missing or unreadable.'
[ -z "$(find "$SOURCE_DIR" -type l -print -quit)" ] || fail 'Source package contains a symlink.'

# Validate paths before passing the manifest to the checksum utility or copying.
COUNT=0
while IFS= read -r line || [ -n "$line" ]; do
    hash="${line%%  *}"
    rel="${line#*  }"
    [ "$line" = "$hash  $rel" ] || fail 'Malformed manifest line.'
    [ "${#hash}" -eq 64 ] || fail 'Malformed SHA-256 digest.'
    case "$hash" in *[!0-9a-f]*) fail 'Malformed SHA-256 digest.' ;; esac
    case "$rel" in
        ''|/*|*[!A-Za-z0-9_./-]*) fail 'Unsafe manifest path.' ;;
        MANIFEST.sha256) fail 'Manifest must not list itself.' ;;
    esac
    case "/$rel/" in
        *'/../'*|*'/./'*|*'//'*) fail 'Unsafe manifest path component.' ;;
    esac
    [ -f "$SOURCE_DIR/$rel" ] && [ -r "$SOURCE_DIR/$rel" ] || fail "Missing package file: $rel"
    COUNT=$((COUNT + 1))
done < "$SOURCE_DIR/MANIFEST.sha256"
[ "$COUNT" -gt 0 ] || fail 'Empty manifest.'

for required in SKILL.md agents/openai.yaml README.md install-macos.sh references/model-profile.md references/sources.json; do
    grep -Eq "^[0-9a-f]{64}  ${required//./[.]}$" "$SOURCE_DIR/MANIFEST.sha256" || fail "Required file missing from manifest: $required"
done
(
    cd "$SOURCE_DIR"
    shasum -a 256 -c MANIFEST.sha256 >/dev/null
) || fail 'Package integrity check failed; no files installed.'
grep -qx "name: $NAME" "$SOURCE_DIR/SKILL.md" || fail 'Unexpected skill name.'
grep -Eq '^[[:space:]]*allow_implicit_invocation: false[[:space:]]*$' "$SOURCE_DIR/agents/openai.yaml" || fail 'Manual-invocation policy is missing.'

if [ "$DRY_RUN" -eq 1 ]; then
    printf 'Package verified (%s files). Would create:\n%s\nNo files changed.\n' "$COUNT" "$DEST"
    exit 0
fi

on_exit() {
    status=$?
    if [ "$status" -ne 0 ] && [ "$CREATED" -eq 1 ]; then
        printf 'Installation incomplete. Inspect the marked directory before retrying:\n%s\n' "$DEST" >&2
        printf 'No existing installation was overwritten; no user data was deleted.\n' >&2
    fi
}
trap on_exit EXIT
trap 'exit 130' INT
trap 'exit 143' TERM

# No -p on the final directory: concurrent or existing installs cause failure.
mkdir -p "$SKILLS_DIR"
[ ! -L "$AGENTS_DIR" ] && [ ! -L "$SKILLS_DIR" ] || fail 'Destination parent changed to a symlink.'
mkdir "$DEST" || fail 'Could not exclusively create the destination.'
CREATED=1
printf 'Installation has not completed. Inspect this directory before retrying.\n' > "$DEST/.install-incomplete"

# Copy only listed files; Finder metadata and other unlisted extras are ignored.
# Copy SKILL.md last so a failed earlier copy is not discovered as a skill.
while IFS= read -r line || [ -n "$line" ]; do
    rel="${line#*  }"
    [ "$rel" != 'SKILL.md' ] || continue
    mkdir -p "$DEST/$(dirname "$rel")"
    cp "$SOURCE_DIR/$rel" "$DEST/$rel"
done < "$SOURCE_DIR/MANIFEST.sha256"
cp "$SOURCE_DIR/MANIFEST.sha256" "$DEST/MANIFEST.sha256"
cp "$SOURCE_DIR/SKILL.md" "$DEST/SKILL.md"
(
    cd "$DEST"
    shasum -a 256 -c MANIFEST.sha256 >/dev/null
) || fail 'Installed copy failed its integrity check.'
rm "$DEST/.install-incomplete"
printf 'Installed and verified:\n%s\n' "$DEST"
printf 'Select Gemini 3.8 Flash Prompting explicitly in the app skill picker.\n'
printf 'No network calls, model calls, dependency installs, or global config edits were made.\n'

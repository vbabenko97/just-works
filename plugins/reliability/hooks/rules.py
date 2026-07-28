#!/usr/bin/env python3
"""The universal layer: rules that hold in every repository, with or without policy.

Nothing a repository ships can reach these. `reliability-policy.json` has no
"allow" direction and `allowed-scripts.json` excepts exactly one policy-layer
denial — unknown local scripts — and nothing here. The engine enforces that by
ordering: a universal denial returns before any policy file is read, so a policy
file cannot be consulted about a decision it is not allowed to influence.

What belongs here is anything that needs no per-repository data to be correct: the
destructive command corpus, mutations whose target set cannot be bounded, the
configuration that governs the agent itself, and the plugin's own continued
existence. What does not belong here is anything requiring review state — script
hashes, build-recipe policy, opaque payload review — because a repository that has
declared no policy has no basis on which those could be judged, and denying them
everywhere would refuse `npm run build` in every project on the machine.

The corpus is ported unchanged from the project harness at 1dd0e8c. It is not
extended here beyond the plugin self-protection block, which exists because
choosing a plugin as the distribution mechanism creates a disarm route that the
project-scoped harness never had.
"""
from __future__ import annotations

import os
import pathlib
import re
import shlex

# --------------------------------------------------------------------------- #
# corpus
# --------------------------------------------------------------------------- #

DESTRUCTIVE = [
    (r"\brm\s+(-[a-zA-Z]*\s+)*-[a-zA-Z]*[rR][a-zA-Z]*\b", "recursive rm"),
    (r"\brm\b(?=[^|;&]*\*)", "rm with a glob"),
    (r"\bfind\b[^|;&]*-delete\b", "find -delete"),
    (r"\bfind\b[^|;&]*-exec\s+rm\b", "find -exec rm"),
    (r"\bxargs\b[^|;&]*\brm\b", "xargs rm"),
    (r"\bgit\s+push\b[^|;&]*(--force\b|-f\b)", "git force push"),
    (r"\bgit\s+reset\b[^|;&]*--hard\b", "git reset --hard"),
    (r"\bgit\s+clean\b[^|;&]*-[a-zA-Z]*[dfx]", "git clean"),
    (r"\bgit\s+(checkout|restore)\s+\.", "git discard all working changes"),
    (r"\b(DROP|TRUNCATE)\s+(TABLE|DATABASE|SCHEMA)\b", "destructive SQL"),
    (r"\bDELETE\s+FROM\b(?![^|;&]*\bWHERE\b)", "unbounded SQL DELETE"),
    (r"\bUPDATE\b[^|;&]*\bSET\b(?![^|;&]*\bWHERE\b)", "unbounded SQL UPDATE"),
    (r"\bdd\s+[^|;&]*\bof=", "dd to a device or file"),
    (r"\bmkfs(\.|\s)", "mkfs"),
    (r"\bchmod\s+(-[a-zA-Z]*\s+)*-[a-zA-Z]*R\b", "recursive chmod"),
    (r"\bchown\s+(-[a-zA-Z]*\s+)*-[a-zA-Z]*R\b", "recursive chown"),
    (r">\s*/dev/(sd|disk|nvme)", "write to a block device"),
    (r"\bshred\b", "shred"),
    (r":\(\)\s*\{.*\};:", "fork bomb"),
    (r"^\s*(sudo|doas|su)\b", "privilege escalation"),
    (r"[;&|]\s*(sudo|doas)\b", "privilege escalation"),
    (r"\b(python3?|node|ruby|perl)\b[^|&]*\s-(c|e)\b[^|&]*"
     r"(rmtree|os\.remove|os\.unlink|os\.rmdir|\bunlink\(|fs\.rm|rmSync|"
     r"FileUtils\.rm|shutil\.move|os\.rename)", "inline interpreter deletion"),
    (r"\|\s*(sh|bash|zsh|dash)\b", "piping text into a shell"),
    (r"\bbase64\b[^|;&]*-[dD]\b", "base64 decode"),
    (r"\bcurl\b[^|;&]*\|\s*\w*sh\b", "curl piped to shell"),
]

MUTATORS = [
    r"\brm\b", r"\bmv\b", r"\bcp\b", r"\bmkdir\b", r"\btouch\b", r"\btee\b",
    r"\bsed\b[^|;&]*-i", r"\bperl\b[^|;&]*-[a-zA-Z]*i", r"\btruncate\b",
    r"\bgit\s+(commit|add|rm|mv|apply|checkout|restore|reset|stash|merge|rebase|push|pull|fetch)\b",
    r"\brsync\b", r"\binstall\b", r"\bln\b", r"\bchmod\b", r"\bchown\b",
    r"\bnpm\s+(install|i|ci|publish)\b", r"\bpip\s+install\b",
    r"\bbrew\s+(install|uninstall)\b",
    r">>?\s*(\$|[^\s|&;]*[*?])",
    r"\bdefaults\s+write\b", r"\bcrontab\b", r"\blaunchctl\b",
]

UNBOUNDED = [
    (r"\bfor\b[^;]*\bin\b", "shell loop"),
    (r"\bwhile\b[^;]*\b(read|do)\b", "shell loop"),
    (r"\$\(", "command substitution"),
    (r"`[^`]+`", "backtick substitution"),
    (r"\bxargs\b", "xargs"),
    (r"\bfind\b", "find"),
    (r"[*?]", "glob"),
    (r"\{[^}]*\.\.[^}]*\}", "brace range expansion"),
    (r"\$[A-Za-z_][A-Za-z0-9_]*", "variable-derived target"),
    (r"\bparallel\b", "gnu parallel"),
]

READ_ONLY_HEAD = re.compile(
    r"^\s*(ls|cat|head|tail|wc|stat|file|find|grep|rg|egrep|fgrep|awk|sed|sort|uniq|cut|tr|"
    r"diff|cmp|shasum|md5|md5sum|sha256sum|od|xxd|strings|du|df|pwd|which|whence|type|echo|printf|"
    r"basename|dirname|realpath|readlink|env|date|uname|python3?|node|jq|yq|tree|"
    r"comm|join|paste|column|less|more|man|help|true|false|test|\[)\b")

PROTECTED_MUTATOR_HEADS = {
    "rm", "mv", "cp", "tee", "ln", "truncate", "chmod", "chown", "rsync",
    "patch", "dd", "install", "ditto", "shred", "unlink",
}
PROTECTED_GIT_SUBCOMMANDS = {"checkout", "restore", "reset", "stash", "clean",
                             "apply", "am", "rm", "mv"}

ENV_VALUE_FLAGS = {"-u", "--unset", "-C", "--chdir", "-S", "--split-string", "-n"}
PREFIXES = {"env", "command", "exec", "nohup", "time", "nice", "stdbuf",
            "caffeinate", "builtin"}
SHELLS = {"sh", "bash", "zsh", "dash", "ksh", "ash"}
SCRIPT_EXTS = (".sh", ".bash", ".zsh", ".py", ".rb", ".pl", ".js", ".mjs", ".cjs",
               ".ts", ".php", ".lua", ".command", ".osascript")

# --------------------------------------------------------------------------- #
# what the agent may never rewrite, anywhere
# --------------------------------------------------------------------------- #

# Relative to whichever project is open. A project's own hook configuration
# governs the agent inside it, so it is protected even where no policy exists.
UNIVERSAL_PROJECT = (
    ".claude/settings.json",
    ".claude/settings.local.json",
    ".claude/hooks/",
    # The policy files are protected at fixed conventional paths, universally, and
    # not by the policy layer. Otherwise policy would be self-defeating: `rm
    # .claude/reliability-policy.json` is a single bounded mutation, so a
    # policy-layer-only protection would let an agent delete the file that turns
    # policy on and drop the repository to universal-only enforcement. Protecting a
    # path that may not exist costs nothing.
    ".claude/reliability-policy.json",
    ".claude/allowed-scripts.json",
)

# Relative to $HOME. Includes the plugin cache, because the installed copy of this
# plugin is the enforcement, and its persistent policy data — the home-scoped
# maintenance authorization and its spend ledger.
UNIVERSAL_HOME = (
    ".claude/settings.json",
    ".claude/settings.local.json",
    ".claude/hooks/",
    ".claude/plugins/",
    ".claude/reliability-auth.json",
    ".claude/reliability-uses.jsonl",
)

# CLI routes that disable, remove, replace or re-point this plugin. The settings
# keys they mutate are already protected against Write and Edit, but the CLI
# reaches them without touching the file through a tool this gate can see, so the
# commands themselves are denied. The owner runs these outside Claude.
SELF_PROTECT = [
    (r"^claude\s+(plugin|plugins)\b[^|;&]*\b(disable|disable-all)\b",
     "`claude plugin disable` would switch this enforcement off"),
    (r"^claude\s+(plugin|plugins)\b[^|;&]*\b(uninstall|remove|rm)\b",
     "`claude plugin uninstall` would remove this enforcement"),
    (r"^claude\s+(plugin|plugins)\b[^|;&]*\bmarketplace\b[^|;&]*\b(remove|rm)\b",
     "removing the marketplace would orphan this plugin"),
    (r"^claude\s+(plugin|plugins)\b[^|;&]*\b(update|install)\b",
     "an unreviewed plugin update or replacement would change enforcement"),
    (r"^claude\s+(plugin|plugins)\b[^|;&]*\bmarketplace\b[^|;&]*\badd\b",
     "adding a marketplace can shadow this plugin with another copy"),
    (r"^claude\s+config\b[^|;&]*\b(set|add|remove|rm|unset)\b[^|;&]*"
     r"(enabledPlugins|extraKnownMarketplaces)",
     "that would rewrite the plugin enablement in user settings"),
    (r"\b(enabledPlugins|extraKnownMarketplaces)\b\s*[:=]",
     "that would rewrite the plugin enablement in user settings"),
    # The owner maintenance issuer must not be callable by the agent it authorizes.
    (r"\bauthorize(_maintenance)?\.py\b", "the maintenance issuer is owner-run only"),
]


# --------------------------------------------------------------------------- #
# lexing
# --------------------------------------------------------------------------- #

def split_segments(cmd: str) -> list[str]:
    """Split on shell separators, ignoring separators inside quotes, so
    `chmod +x x && ./x` cannot hide its second half behind a benign first half."""
    segments: list[str] = []
    buf: list[str] = []
    quote: str | None = None
    i = 0
    while i < len(cmd):
        ch = cmd[i]
        if quote:
            buf.append(ch)
            if ch == quote and (i == 0 or cmd[i - 1] != "\\"):
                quote = None
            i += 1
            continue
        if ch in "'\"":
            quote = ch
            buf.append(ch)
            i += 1
            continue
        if cmd[i:i + 2] in ("&&", "||"):
            segments.append("".join(buf))
            buf = []
            i += 2
            continue
        if ch in ";\n|&":
            segments.append("".join(buf))
            buf = []
            i += 1
            continue
        buf.append(ch)
        i += 1
    segments.append("".join(buf))
    return [s.strip() for s in segments if s.strip()]


def tokens(segment: str) -> list[str]:
    try:
        return shlex.split(segment, posix=True)
    except ValueError:
        return segment.split()


def head_and_args(toks: list[str]) -> tuple[str, list[str]]:
    """Skip env assignments and wrappers to find the command actually being run.
    Flags that consume a value skip two tokens, so `env -u VAR cmd` does not
    mistake `VAR` for the command."""
    i = 0
    saw_prefix = False
    while i < len(toks):
        t = toks[i]
        if re.match(r"^[A-Za-z_][A-Za-z0-9_]*=", t):
            i += 1
            continue
        if t in PREFIXES:
            saw_prefix = True
            i += 1
            continue
        if saw_prefix and t.startswith("-"):
            i += 2 if t in ENV_VALUE_FLAGS else 1
            continue
        break
    return (toks[i], toks[i + 1:]) if i < len(toks) else ("", [])


def flag_cluster(token: str, letter: str) -> bool:
    return bool(re.match(rf"^-[a-zA-Z]*{letter}[a-zA-Z]*$", token))


def looks_like_script(token: str) -> bool:
    return token.endswith(SCRIPT_EXTS) or token.startswith(("./", "../", "~/"))


# --------------------------------------------------------------------------- #
# protected paths
# --------------------------------------------------------------------------- #

def universal_needles() -> tuple[str, ...]:
    return tuple(list(UNIVERSAL_PROJECT) + [f"~/{e}" for e in UNIVERSAL_HOME])


def mentions_universal(text: str, extra: tuple[str, ...] = ()) -> str | None:
    for entry in tuple(extra) + universal_needles():
        if entry.rstrip("/") in text:
            return entry
    return None


def universal_protected_path(abs_path: str, project: str) -> str | None:
    """The matching universal entry for a resolved path, or None. Symlinks are
    resolved first: a link is not a way around a protected destination."""
    resolved = os.path.realpath(abs_path)
    for base, entries in ((project, UNIVERSAL_PROJECT),
                          (str(pathlib.Path.home()), UNIVERSAL_HOME)):
        try:
            rel = os.path.relpath(resolved, os.path.realpath(base)).replace(os.sep, "/")
        except ValueError:
            continue
        if rel == ".." or rel.startswith("../"):
            continue
        for entry in entries:
            if entry.endswith("/"):
                if rel == entry.rstrip("/") or rel.startswith(entry):
                    return entry
            elif rel == entry:
                return entry
    return None


def protected_hit(segment: str, project: str,
                  extra: tuple[str, ...] = ()) -> tuple[str, str] | None:
    """A Bash route to rewriting protected configuration, judged per segment.
    Naming a protected file is not a refusal, so `cat` and `git diff` on it stay
    allowed while `cp`, `sed -i`, `git checkout` and redirects into it do not.

    `extra` carries paths a valid policy manifest asked to protect. They are passed
    in rather than read here, so this function keeps working with no policy at all."""
    entry = mentions_universal(segment, extra)
    if not entry:
        return None
    toks = tokens(segment)
    if not toks:
        return None
    head, args = head_and_args(toks)
    base = os.path.basename(head)

    if base in PROTECTED_MUTATOR_HEADS:
        return (entry, f"`{base}` would rewrite it")
    if base in ("sed", "perl") and any(t.startswith("-i") or flag_cluster(t, "i")
                                      for t in args):
        return (entry, f"`{base} -i` would rewrite it")
    if base == "git":
        sub = next((a for a in args if not a.startswith("-")), None)
        if sub in PROTECTED_GIT_SUBCOMMANDS:
            return (entry, f"`git {sub}` would rewrite it")
    needle = entry.rstrip("/")
    if re.search(r">>?\s*['\"]?[^\s'\";|&]*" + re.escape(needle), segment):
        return (entry, "a redirect writes to it")
    return None


# --------------------------------------------------------------------------- #
# the universal verdict
# --------------------------------------------------------------------------- #

def universal_deny(command: str, project: str) -> str | None:
    """The reason this command is refused everywhere, or None.

    Called before any policy file is read. That ordering is the monotonicity
    guarantee: no repository file participates in a decision reached here."""
    cmd = command.strip()

    for pattern, label in DESTRUCTIVE:
        if re.search(pattern, cmd, re.IGNORECASE):
            return f"recognised destructive operation: {label}"

    for pattern, why in SELF_PROTECT:
        for segment in split_segments(cmd):
            if re.search(pattern, segment.strip()):
                return (f"{why}. Enforcement is not something the agent it "
                        "constrains may switch off; run it yourself outside Claude")

    for segment in split_segments(cmd):
        hit = protected_hit(segment, project)
        if hit:
            entry, why = hit
            return (f"would modify the configuration that governs this agent "
                    f"({entry}; {why}). Hand the diff to the owner")

    for segment in split_segments(cmd):
        toks = tokens(segment)
        if not toks:
            continue
        head, _ = head_and_args(toks)
        if os.path.basename(head) == "eval":
            return "eval executes text this gate cannot classify"

    return None


def unbounded_deny(command: str) -> str | None:
    """Mutation whose target set this classifier cannot bound. Universal: it needs
    no repository data, only the shape of the command."""
    cmd = command.strip()
    if not [m for m in MUTATORS if re.search(m, cmd)]:
        return None
    unbounded = [label for pattern, label in UNBOUNDED if re.search(pattern, cmd)]
    if unbounded:
        return ("mutation with a target set this gate cannot bound: "
                + ", ".join(sorted(set(unbounded))))
    return None


# Read-only git subcommands. `branch`, `remote` and `config` are deliberately
# absent: each has a mutating form (`branch -D`, `remote add`, `config --set`) and
# distinguishing them by flag is exactly the kind of guess this gate avoids.
READ_ONLY_GIT = {"status", "diff", "log", "show", "ls-files", "ls-tree", "rev-parse",
                 "describe", "blame", "shortlog", "cat-file", "grep"}


def is_read_only(command: str) -> bool:
    """Used only to decide what survives an invalid policy manifest.

    Git needs its own case. A repository whose manifest is broken has to remain
    diagnosable, and `git status` and `git diff` are how anyone would diagnose it —
    but `git` is not a read-only command head, so matching heads alone refused them.
    """
    cmd = command.strip()
    if [m for m in MUTATORS if re.search(m, cmd)]:
        return False
    toks = tokens(cmd)
    if toks:
        head, args = head_and_args(toks)
        if os.path.basename(head) == "git":
            sub = next((a for a in args if not a.startswith("-")), None)
            return sub in READ_ONLY_GIT
    return bool(READ_ONLY_HEAD.match(cmd))

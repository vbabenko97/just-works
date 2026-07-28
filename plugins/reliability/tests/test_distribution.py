#!/usr/bin/env python3
"""Distribution invariants, so the stale-version footgun cannot come back.

`claude plugin update` is keyed on the version declared in plugin.json, not on the
commit. Measured: code pushed inside an unchanged `0.1.0` produced "already at the
latest version" and every installed copy kept running the previous file, with no
warning anywhere. For enforcement code that is the worst possible failure mode — the
guard appears current and is not.

Omitting the version removes the trap: each commit is a distinct installable
revision, tracked by gitCommitSha. `claude plugin validate` accepts it with an
advisory warning. These checks exist so that re-adding a version field is a test
failure rather than a silent regression, and so no hook command can ever resolve
through the project being worked in.

The declaring repository is found rather than assumed. This file used to compute it
as `PLUGIN.parents[1]`, which is the checkout layout — `<repo>/plugins/<name>` — and
is wrong for the copy that actually enforces: installed, the layout is
`<marketplace>/<plugin>/<revision>/`, so parents[1] is the marketplace cache
directory, which holds no manifest. Run from the cache the suite died with
FileNotFoundError before checking anything, which is how it passed in the checkout
while telling us nothing about the installed copy. The plugin manager's marketplace
clone is the honest source there: it is what the installation was made from.
"""
from __future__ import annotations

import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from _fixture import Checks  # noqa: E402

PLUGIN = pathlib.Path(__file__).resolve().parents[1]
PLUGINS_HOME = pathlib.Path.home() / ".claude" / "plugins"


def marketplace_for(name: str) -> tuple[pathlib.Path | None, str]:
    """(root, mode) for the repository that declares this plugin."""
    for candidate in (PLUGIN, *PLUGIN.parents):
        if (candidate / ".claude-plugin" / "marketplace.json").is_file():
            return candidate, "checkout"
    try:
        known = json.loads((PLUGINS_HOME / "known_marketplaces.json").read_text())
    except Exception as exc:
        return None, f"no manifest above this plugin and no registry ({exc})"
    for market_name, record in known.items():
        root = pathlib.Path(record.get("installLocation", ""))
        manifest = root / ".claude-plugin" / "marketplace.json"
        if not manifest.is_file():
            continue
        try:
            declared = json.loads(manifest.read_text()).get("plugins", [])
        except Exception:
            continue
        if any(p.get("name") == name for p in declared):
            return root, f"marketplace clone ({market_name})"
    return None, "no registered marketplace declares this plugin"


def installed_record(name: str, market_root: pathlib.Path) -> dict:
    try:
        installed = json.loads((PLUGINS_HOME / "installed_plugins.json").read_text())
        copies = installed["plugins"].get(f"{name}@{market_root.name}", [])
        return copies[0] if copies else {}
    except Exception:
        return {}


def main() -> int:
    check = Checks()
    manifest = json.loads((PLUGIN / ".claude-plugin" / "plugin.json").read_text())
    name = manifest["name"]
    root, mode = marketplace_for(name)
    print(f"plugin   {PLUGIN}\nmarket   {root} [{mode}]\n")

    check("version" not in manifest,
          "plugin.json declares no version, so each commit is installable",
          f"version = {manifest.get('version')!r}; an unchanged version makes "
          "`claude plugin update` a no-op and leaves installed enforcement stale")

    market = {}
    if root is not None:
        market = json.loads(
            (root / ".claude-plugin" / "marketplace.json").read_text())
    entry = next((p for p in market.get("plugins", []) if p["name"] == name), None)

    check(entry is not None, f"marketplace lists the plugin by name ({name})", mode)
    check(entry is not None and "version" not in entry,
          "marketplace entry declares no version",
          f"version = {(entry or {}).get('version')!r}")

    source = (root / entry["source"]).resolve() if (root and entry) else None
    declares_same = False
    if source is not None and (source / ".claude-plugin" / "plugin.json").is_file():
        declares_same = json.loads(
            (source / ".claude-plugin" / "plugin.json").read_text()
        ).get("name") == name
    check(declares_same,
          "marketplace source path declares the same plugin",
          f"source = {(entry or {}).get('source')!r} -> {source}")

    if mode == "checkout":
        check(source == PLUGIN,
              "marketplace source resolves to this plugin directory",
              f"{source} != {PLUGIN}")
    else:
        # Installed: the directory name is the revision, and it must be the commit
        # the plugin manager recorded. That is the property omitting `version` buys.
        record = installed_record(name, root) if root else {}
        sha = str(record.get("gitCommitSha", ""))
        check(bool(sha) and PLUGIN.name == sha[:len(PLUGIN.name)],
              "the revision directory is the recorded source commit",
              f"directory {PLUGIN.name!r}, gitCommitSha {sha[:12]!r}")

    hooks = json.loads((PLUGIN / "hooks" / "hooks.json").read_text())
    commands = [h.get("command", "")
                for event in hooks["hooks"].values()
                for group in event for h in group.get("hooks", [])]

    # The descriptions are what the owner reads in the plugin inventory, and they
    # drifted: both still advertised the observation-only stage for the whole of
    # Stage 3, while hooks.json declared PreToolUse guards that deny. Nothing broke,
    # which is the problem — an owner auditing what is installed was told the plugin
    # emits no permission decisions. So a manifest that claims that while declaring
    # a PreToolUse hook is now a failure.
    if "PreToolUse" in hooks["hooks"]:
        stale = ("observation-only", "emits no permission decisions",
                 "observes; it does not decide")
        for label, text in (("plugin.json", manifest.get("description", "")),
                            ("marketplace entry",
                             (entry or {}).get("description", ""))):
            hit = next((p for p in stale if p in text.lower()), None)
            check(hit is None,
                  f"{label} does not describe enforcement as observation-only",
                  f"claims {hit!r} while hooks.json declares PreToolUse guards")
    check(bool(commands), f"hooks.json declares commands ({len(commands)})")
    check(all("${CLAUDE_PLUGIN_ROOT}" in c for c in commands),
          "every hook command resolves through ${CLAUDE_PLUGIN_ROOT}",
          "; ".join(c for c in commands if "${CLAUDE_PLUGIN_ROOT}" not in c))
    check(not any("CLAUDE_PROJECT_DIR" in c for c in commands),
          "no hook command resolves through the active project directory",
          "; ".join(c for c in commands if "CLAUDE_PROJECT_DIR" in c))

    return check.finish()


if __name__ == "__main__":
    sys.exit(main())

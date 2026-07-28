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
"""
from __future__ import annotations

import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from _fixture import Checks  # noqa: E402

PLUGIN = pathlib.Path(__file__).resolve().parents[1]
REPO = PLUGIN.parents[1]


def main() -> int:
    check = Checks()
    manifest = json.loads((PLUGIN / ".claude-plugin" / "plugin.json").read_text())
    market = json.loads((REPO / ".claude-plugin" / "marketplace.json").read_text())
    entry = next((p for p in market["plugins"] if p["name"] == manifest["name"]), None)

    check("version" not in manifest,
          "plugin.json declares no version, so each commit is installable",
          f"version = {manifest.get('version')!r}; an unchanged version makes "
          "`claude plugin update` a no-op and leaves installed enforcement stale")
    check(entry is not None,
          f"marketplace lists the plugin by name ({manifest['name']})")
    check(entry is not None and "version" not in entry,
          "marketplace entry declares no version",
          f"version = {(entry or {}).get('version')!r}")
    check(entry is not None and (REPO / entry["source"]).resolve() == PLUGIN,
          "marketplace source resolves to this plugin directory",
          f"source = {(entry or {}).get('source')!r}")

    hooks = json.loads((PLUGIN / "hooks" / "hooks.json").read_text())
    commands = [h.get("command", "")
                for event in hooks["hooks"].values()
                for group in event for h in group.get("hooks", [])]
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

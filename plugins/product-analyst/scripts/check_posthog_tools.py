#!/usr/bin/env python3
"""Check the exact PostHog hook allowlist against a PostHog tool inventory.

Usage: check_posthog_tools.py [inventory.json]

Without an argument this also verifies the fixture hash in
tests/fixtures/posthog-tools.metadata.json. Refresh from the source URL in
that metadata file, update its SHA-256, then run this check before changing
the allowlist.
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "hooks"))
import policy  # noqa: E402


def main() -> int:
    arguments = sys.argv[1:]
    if arguments == ["--help"] or arguments == ["-h"]:
        print(__doc__.strip())
        return 0
    if len(arguments) > 1:
        print("Usage: check_posthog_tools.py [inventory.json]", file=sys.stderr)
        return 2
    inventory_path = Path(arguments[0]) if arguments else ROOT / "tests/fixtures/posthog-tools.json"
    try:
        contents = inventory_path.read_bytes()
        inventory = json.loads(contents)
    except (OSError, json.JSONDecodeError) as exc:
        print(f"Cannot read {inventory_path}: {exc}", file=sys.stderr)
        return 2
    if not isinstance(inventory, dict):
        print("PostHog inventory must be an object", file=sys.stderr)
        return 2
    if not arguments:
        metadata_path = ROOT / "tests/fixtures/posthog-tools.metadata.json"
        try:
            metadata = json.loads(metadata_path.read_text())
            expected_hash = metadata["sha256"]
        except (OSError, json.JSONDecodeError, KeyError, TypeError) as exc:
            print(f"Cannot read {metadata_path}: {exc}", file=sys.stderr)
            return 2
        if (
            not isinstance(expected_hash, str)
            or hashlib.sha256(contents).hexdigest() != expected_hash
        ):
            print("PostHog fixture hash does not match its metadata", file=sys.stderr)
            return 2
    missing = sorted(policy.ALLOWED_POSTHOG_TOOLS - inventory.keys())
    unsafe = sorted(
        name
        for name in policy.ALLOWED_POSTHOG_TOOLS
        if not isinstance(inventory.get(name), dict)
        or inventory[name].get("annotations", {}).get("readOnlyHint") is not True
    )
    if missing or unsafe:
        if missing:
            print(
                "Allowlisted PostHog tools missing from inventory: " + ", ".join(missing),
                file=sys.stderr,
            )
        if unsafe:
            print(
                "Allowlisted PostHog tools are not marked read-only: " + ", ".join(unsafe),
                file=sys.stderr,
            )
        return 1
    print(
        f"Validated {len(policy.ALLOWED_POSTHOG_TOOLS)} PostHog read tools against {inventory_path.name}."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

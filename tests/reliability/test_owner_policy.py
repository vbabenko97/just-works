#!/usr/bin/env python3
"""scripts/verify/repo_policy.py, and the wrapper that depends on it.

Stage 3 moved enforcement into the reliability plugin and deleted
`.claude/hooks/reliability_paths.py`, which `bulk_mutate.py` had imported. This module
replaced it. It is owner tooling, not enforcement: nothing here runs as a hook, and no
plugin decision depends on it.

Three properties are worth testing rather than assuming:

  fail closed   a manifest that exists but cannot be trusted must raise, not degrade
                to "universal only". Degrading silently would quietly unprotect
                `scripts/verify/`, the set the wrapper must never delete.
  no silent     a path lexically inside the repository that resolves outside it is an
  escape        escape route, not an ordinary path. It raises.
  parity        the universal tuples are duplicated from the plugin by necessity, so a
                test parses the plugin source and fails when the two drift. Parsed,
                never imported: importing enforcement code to test owner tooling would
                be its own mistake.

The last section drives `bulk_mutate.py` itself, in both phases, because a classifier
that is right in isolation is worth nothing if the wrapper does not consult it.
"""
from __future__ import annotations

import ast
import json
import os
import pathlib
import shutil
import subprocess
import sys
import tempfile

REPO = pathlib.Path(__file__).resolve().parents[2]
WRAPPER = REPO / "scripts" / "verify" / "bulk_mutate.py"
sys.path.insert(0, str(REPO / "scripts" / "verify"))

import repo_policy  # noqa: E402

VALID_MANIFEST = {
    "policy_version": 1,
    "contract_version": "tier1-2026-07-28",
    "allowlist": ".claude/allowed-scripts.json",
    "contract": ".claude/reliability-contract.md",
    "protected": ["scripts/verify/", "scripts/hooks/", ".claude/hooks/",
                  ".claude/maintenance-auth.json", ".claude/receipts/"],
    "maintenance": {"issuer": "scripts/verify/authorize_maintenance.py",
                    "ledger": ".claude/maintenance-uses.jsonl"},
    "require_subagent_receipts": True,
}

FAILURES: list[str] = []
PASSED = 0


def check(name: str, condition: bool, detail: str = "") -> None:
    global PASSED
    if condition:
        PASSED += 1
        print(f"ok     {name}")
    else:
        FAILURES.append(f"{name}: {detail}")
        print(f"FAIL   {name} — {detail}")


def raises(name: str, exc_type, thunk) -> None:
    try:
        result = thunk()
    except exc_type:
        check(name, True)
        return
    except Exception as exc:
        check(name, False, f"raised {type(exc).__name__} instead: {exc}")
        return
    check(name, False, f"returned {result!r} instead of raising "
                       f"{exc_type.__name__}")


def build(root: pathlib.Path, manifest) -> pathlib.Path:
    """A throwaway repository. `manifest` is a dict, a raw string, or None."""
    project = root / "project"
    (project / ".claude" / "hooks").mkdir(parents=True)
    (project / ".claude" / "receipts").mkdir()
    (project / "scripts" / "verify").mkdir(parents=True)
    (project / ".claude" / "settings.json").write_text("{}\n")
    (project / ".claude" / "settings.local.json").write_text("{}\n")
    (project / ".claude" / "allowed-scripts.json").write_text('{"scripts":{}}\n')
    (project / ".claude" / "reliability-contract.md").write_text("contract\n")
    (project / ".claude" / "maintenance-auth.json").write_text("{}\n")
    (project / ".claude" / "maintenance-uses.jsonl").write_text("")
    (project / ".claude" / "hooks" / "maintenance_auth.py").write_text("x\n")
    (project / "scripts" / "verify" / "bulk_mutate.py").write_text("y\n")
    (project / "scripts" / "verify" / "authorize_maintenance.py").write_text("z\n")
    (project / "README.md").write_text("r\n")
    (project / "src").mkdir()
    (project / "src" / "app.py").write_text("app\n")
    (root / "elsewhere.md").write_text("outside the project\n")
    if manifest is not None:
        target = project / ".claude" / "reliability-policy.json"
        target.write_text(manifest if isinstance(manifest, str)
                          else json.dumps(manifest, indent=2) + "\n")
    return project


def plugin_universal_sets() -> tuple[tuple[str, ...], tuple[str, ...], str]:
    """(UNIVERSAL_PROJECT, UNIVERSAL_HOME, source path) parsed out of the installed
    plugin's rules.py. Raises if it cannot be located: parity that cannot be checked
    is a failure, not a pass."""
    install = None
    registry = pathlib.Path.home() / ".claude" / "plugins" / "installed_plugins.json"
    try:
        entries = json.loads(registry.read_text())["plugins"]["reliability@just-works"]
        install = pathlib.Path(entries[0]["installPath"])
    except Exception:
        candidates = sorted((pathlib.Path.home() / ".claude" / "plugins" / "cache")
                            .glob("*/reliability/*/hooks/rules.py"))
        if candidates:
            install = candidates[-1].parents[1]
    if install is None:
        raise SystemExit("cannot locate the installed reliability plugin; parity with "
                         "the plugin's universal set is unverifiable")
    source = install / "hooks" / "rules.py"
    tree = ast.parse(source.read_text())
    found: dict[str, tuple[str, ...]] = {}
    for node in tree.body:
        if not isinstance(node, ast.Assign):
            continue
        for target in node.targets:
            if isinstance(target, ast.Name) and target.id in ("UNIVERSAL_PROJECT",
                                                              "UNIVERSAL_HOME"):
                found[target.id] = tuple(ast.literal_eval(node.value))
    missing = {"UNIVERSAL_PROJECT", "UNIVERSAL_HOME"} - set(found)
    if missing:
        raise SystemExit(f"plugin rules.py no longer defines {sorted(missing)}")
    return found["UNIVERSAL_PROJECT"], found["UNIVERSAL_HOME"], str(source)


def bulk(*args: str) -> dict:
    proc = subprocess.run([sys.executable, str(WRAPPER), *args], cwd=str(REPO),
                          capture_output=True, text=True, timeout=60)
    try:
        return json.loads(proc.stdout)
    except json.JSONDecodeError:
        return {"status": "no-json", "stdout": proc.stdout[:400],
                "stderr": proc.stderr[:400]}


def phase_tree(root: pathlib.Path) -> pathlib.Path:
    tree = root / "tree"
    tree.mkdir()
    (tree / "plain.md").write_text("plain\n")
    (tree / "other.md").write_text("other\n")
    (tree / "link-internal").symlink_to(tree / "plain.md")
    (tree / "link-external").symlink_to("/etc/hosts")
    return tree


def main() -> int:
    root = pathlib.Path(tempfile.mkdtemp(prefix="jw-owner-policy-"))
    try:
        print("=== manifest states ===")
        absent = build(root / "absent", None)
        check("absent manifest loads as None",
              repo_policy.load_manifest(str(absent)) is None)
        check("absent manifest still protects the universal set",
              repo_policy.protected_entries(str(absent)) == repo_policy.UNIVERSAL_PROJECT,
              str(repo_policy.protected_entries(str(absent))))

        valid = build(root / "valid", VALID_MANIFEST)
        loaded = repo_policy.load_manifest(str(valid))
        check("valid manifest loads",
              isinstance(loaded, dict) and loaded.get("policy_version") == 1)
        check("valid manifest union covers universal and policy entries",
              set(repo_policy.UNIVERSAL_PROJECT) <= set(repo_policy.protected_entries(str(valid)))
              and "scripts/verify/" in repo_policy.protected_entries(str(valid)))

        malformed = build(root / "malformed", "{ not json")
        raises("malformed manifest raises", repo_policy.ManifestError,
               lambda: repo_policy.load_manifest(str(malformed)))
        raises("malformed manifest fails closed in protected_entries",
               repo_policy.ManifestError,
               lambda: repo_policy.protected_entries(str(malformed)))
        raises("malformed manifest fails closed in is_protected",
               repo_policy.ManifestError,
               lambda: repo_policy.is_protected(str(malformed / "src" / "app.py"),
                                                str(malformed)))

        unsupported = build(root / "unsupported", {**VALID_MANIFEST, "policy_version": 99})
        raises("unsupported policy_version raises", repo_policy.ManifestError,
               lambda: repo_policy.load_manifest(str(unsupported)))
        try:
            repo_policy.load_manifest(str(unsupported))
        except repo_policy.ManifestError as exc:
            check("unsupported version names the version", "99" in str(exc), str(exc))

        unknown = build(root / "unknown", {**VALID_MANIFEST, "not_a_real_key": 1})
        raises("unknown manifest key raises", repo_policy.ManifestError,
               lambda: repo_policy.load_manifest(str(unknown)))
        climbing = build(root / "climbing", {**VALID_MANIFEST, "protected": ["../out/"]})
        raises("protected path climbing out of the repository raises",
               repo_policy.ManifestError,
               lambda: repo_policy.load_manifest(str(climbing)))

        print()
        print("=== universal protected paths ===")
        for entry in repo_policy.UNIVERSAL_PROJECT:
            rel = entry.rstrip("/")
            got = repo_policy.is_protected(str(valid / rel), str(valid))
            check(f"universal: {entry}", got == entry, f"got {got!r}")

        print()
        print("=== policy protected paths ===")
        for rel, expected in (
            ("scripts/verify/bulk_mutate.py", "scripts/verify/"),
            ("scripts/verify/authorize_maintenance.py", "scripts/verify/"),
            (".claude/maintenance-auth.json", ".claude/maintenance-auth.json"),
            (".claude/maintenance-uses.jsonl", ".claude/maintenance-uses.jsonl"),
            (".claude/reliability-contract.md", ".claude/reliability-contract.md"),
            (".claude/receipts", ".claude/receipts/"),
        ):
            got = repo_policy.is_protected(str(valid / rel), str(valid))
            check(f"policy: {rel}", got == expected, f"got {got!r}, wanted {expected!r}")
        check("policy entries vanish when the manifest is absent",
              repo_policy.is_protected(
                  str(absent / "scripts" / "verify" / "bulk_mutate.py"),
                  str(absent)) is None)

        print()
        print("=== ordinary paths ===")
        for rel in ("README.md", "src/app.py", "src"):
            got = repo_policy.is_protected(str(valid / rel), str(valid))
            check(f"unprotected: {rel}", got is None, f"got {got!r}")
        check("a prefix that is not a path component does not match",
              repo_policy.is_protected(str(valid / ".claude" / "hooks-elsewhere.py"),
                                       str(valid)) is None)
        # The directory named by a trailing-slash entry is itself protected, or the
        # wrapper could delete `scripts/verify` whole and satisfy every child check.
        for rel, expected in (("scripts/verify", "scripts/verify/"),
                              (".claude/hooks", ".claude/hooks/"),
                              (".claude/receipts", ".claude/receipts/")):
            got = repo_policy.is_protected(str(valid / rel), str(valid))
            check(f"the protected directory itself: {rel}", got == expected,
                  f"got {got!r}, wanted {expected!r}")

        print()
        print("=== child paths ===")
        for rel, expected in ((".claude/hooks/deep/nested/x.py", ".claude/hooks/"),
                              ("scripts/verify/sub/dir/tool.py", "scripts/verify/"),
                              (".claude/receipts/session/agent.json", ".claude/receipts/")):
            got = repo_policy.is_protected(str(valid / rel), str(valid))
            check(f"child: {rel}", got == expected, f"got {got!r}, wanted {expected!r}")

        print()
        print("=== traversal ===")
        check("traversal out and back in is canonicalized",
              repo_policy.is_protected(
                  str(valid / "src" / ".." / ".claude" / "settings.json"),
                  str(valid)) == ".claude/settings.json")
        check("an absolute path outside the repository is not a repository path",
              repo_policy.is_protected("/etc/hosts", str(valid)) is None)
        check("a sibling outside the repository is not a repository path",
              repo_policy.is_protected(str(valid.parent / "elsewhere.md"),
                                       str(valid)) is None)

        print()
        print("=== symlinks ===")
        internal = valid / "link-to-settings"
        internal.symlink_to(valid / ".claude" / "settings.json")
        check("internal symlink resolves to its protected target",
              repo_policy.is_protected(str(internal), str(valid)) == ".claude/settings.json",
              str(repo_policy.is_protected(str(internal), str(valid))))

        internal_dir = valid / "link-to-hooks"
        internal_dir.symlink_to(valid / ".claude" / "hooks")
        check("internal symlink to a protected directory",
              repo_policy.is_protected(str(internal_dir), str(valid)) == ".claude/hooks/",
              str(repo_policy.is_protected(str(internal_dir), str(valid))))

        internal_plain = valid / "link-to-readme"
        internal_plain.symlink_to(valid / "README.md")
        check("internal symlink to an ordinary file stays ordinary",
              repo_policy.is_protected(str(internal_plain), str(valid)) is None)

        external = valid / "link-outside"
        external.symlink_to("/etc/hosts")
        raises("external symlink raises rather than reading as unprotected",
               repo_policy.OutsideRepository,
               lambda: repo_policy.is_protected(str(external), str(valid)))

        external_in_protected = valid / ".claude" / "hooks" / "link-outside"
        external_in_protected.symlink_to("/etc/hosts")
        raises("external symlink inside a protected directory raises",
               repo_policy.OutsideRepository,
               lambda: repo_policy.is_protected(str(external_in_protected), str(valid)))

        broken = valid / "link-broken"
        broken.symlink_to(valid / "does-not-exist")
        check("broken symlink inside the repository is ordinary, not an escape",
              repo_policy.is_protected(str(broken), str(valid)) is None,
              str(repo_policy.is_protected(str(broken), str(valid))))

        print()
        print("=== parity with the plugin source ===")
        plugin_project, plugin_home, source = plugin_universal_sets()
        print(f"       parsed {source}")
        check("UNIVERSAL_PROJECT matches the plugin exactly",
              tuple(repo_policy.UNIVERSAL_PROJECT) == plugin_project,
              f"owner {repo_policy.UNIVERSAL_PROJECT!r} != plugin {plugin_project!r}")
        check("UNIVERSAL_HOME matches the plugin exactly",
              tuple(repo_policy.UNIVERSAL_HOME) == plugin_home,
              f"owner {repo_policy.UNIVERSAL_HOME!r} != plugin {plugin_home!r}")
        module_src = (REPO / "scripts" / "verify" / "repo_policy.py").read_text()
        check("no runtime dependency on the plugin install path",
              "plugins/cache" not in module_src and "installed_plugins" not in module_src)

        print()
        print("=== bulk_mutate, both phases ===")
        phases = pathlib.Path(tempfile.mkdtemp(prefix="jw-owner-phase-", dir=root))
        tree = phase_tree(phases)
        plan_path = phases / "plan.json"

        planned = bulk("plan", "--operation", "delete", "--root", str(tree),
                       "--max", "5", "--plan", str(plan_path),
                       str(tree / "link-internal"))
        check("plan: an internal symlink inside the root is planned",
              planned.get("status") == "planned", json.dumps(planned)[:200])

        refused = bulk("plan", "--operation", "delete", "--root", str(tree),
                       "--max", "5", "--plan", str(phases / "plan-ext.json"),
                       str(tree / "link-external"))
        check("plan: an external symlink is refused",
              refused.get("status") == "refused", json.dumps(refused)[:200])
        check("plan: the refusal names containment",
              "approved roots" in refused.get("reason", ""),
              json.dumps(refused)[:200])

        unchanged = bulk("apply", "--plan", str(plan_path), "--dry-run")
        check("apply: an unchanged internal symlink is applyable",
              unchanged.get("status") == "dry_run_ok", json.dumps(unchanged)[:200])

        os.remove(tree / "link-internal")
        (tree / "link-internal").symlink_to("/etc/hosts")
        escaped = bulk("apply", "--plan", str(plan_path), "--dry-run")
        check("apply: an internal symlink retargeted outside the root is refused",
              escaped.get("status") == "refused", json.dumps(escaped)[:200])

        protected_plan = bulk("plan", "--operation", "delete", "--root", str(REPO),
                              "--max", "5", "--plan", str(phases / "plan-prot.json"),
                              str(REPO / ".claude" / "settings.json"))
        check("plan: a protected repository path is refused",
              protected_plan.get("status") == "refused",
              json.dumps(protected_plan)[:200])
        check("plan: the refusal names the protected entry",
              ".claude/settings.json" in json.dumps(protected_plan),
              json.dumps(protected_plan)[:200])
    finally:
        shutil.rmtree(root, ignore_errors=True)

    total = PASSED + len(FAILURES)
    print()
    print(f"{PASSED}/{total} passed")
    for row in FAILURES:
        print(f"  FAIL {row}")
    return 1 if FAILURES else 0


if __name__ == "__main__":
    sys.exit(main())

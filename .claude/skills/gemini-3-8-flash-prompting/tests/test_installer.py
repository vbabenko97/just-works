#!/usr/bin/env python3
"""Offline installer tests in disposable HOME directories. Python standard library only."""
from __future__ import annotations

import hashlib
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
NAME = "gemini-3-8-flash-prompting"
BASH = shutil.which("bash")


@unittest.skipUnless(BASH and shutil.which("shasum"), "Requires local bash and shasum")
class InstallerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="gemini-skill-test-")
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name).resolve()
        self.home = self.base / "Home With Spaces"
        self.home.mkdir()
        self.dest = self.home / ".agents" / "skills" / NAME

    def run_installer(self, *args, source=ROOT, home=None, extra_env=None):
        env = os.environ.copy()
        env.pop("SUDO_USER", None)
        env.pop("BASH_ENV", None)
        env.pop("ENV", None)
        env["HOME"] = str(self.home if home is None else home)
        if extra_env:
            env.update(extra_env)
        return subprocess.run(
            [BASH, "--noprofile", "--norc", str(source / "install-macos.sh"), *args],
            env=env, capture_output=True, text=True, timeout=30,
        )

    def copied_source(self):
        source = self.base / "Source With Spaces" / NAME
        shutil.copytree(ROOT, source, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
        return source

    def tree_hashes(self, directory):
        return {str(p.relative_to(directory)): hashlib.sha256(p.read_bytes()).hexdigest()
                for p in directory.rglob("*") if p.is_file()}

    def test_help_writes_nothing(self):
        result = self.run_installer("--help")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(list(self.home.iterdir()), [])

    def test_unknown_option_writes_nothing(self):
        result = self.run_installer("--force")
        self.assertEqual(result.returncode, 2)
        self.assertEqual(list(self.home.iterdir()), [])

    def test_dry_run_writes_nothing(self):
        result = self.run_installer("--dry-run")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("No files changed", result.stdout)
        self.assertEqual(list(self.home.iterdir()), [])

    def test_success_and_source_home_paths_with_spaces(self):
        source = self.copied_source()
        result = self.run_installer(source=source)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.tree_hashes(source), self.tree_hashes(self.dest))
        self.assertFalse((self.dest / ".install-incomplete").exists())

    def test_existing_install_is_not_overwritten(self):
        self.dest.mkdir(parents=True)
        (self.dest / "SKILL.md").write_text("A pre-existing personal skill")
        before = self.tree_hashes(self.dest)
        result = self.run_installer()
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(before, self.tree_hashes(self.dest))

    def test_second_install_refused(self):
        self.assertEqual(self.run_installer().returncode, 0)
        before = self.tree_hashes(self.dest)
        result = self.run_installer()
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(before, self.tree_hashes(self.dest))

    def test_modified_source_refused_before_writing(self):
        source = self.copied_source()
        with (source / "SKILL.md").open("a") as handle:
            handle.write("\nUnexpected modification\n")
        result = self.run_installer(source=source)
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(list(self.home.iterdir()), [])

    def test_missing_manifest_refused(self):
        source = self.copied_source()
        (source / "MANIFEST.sha256").unlink()
        self.assertNotEqual(self.run_installer(source=source).returncode, 0)
        self.assertEqual(list(self.home.iterdir()), [])

    def test_path_traversal_manifest_refused(self):
        source = self.copied_source()
        with (source / "MANIFEST.sha256").open("a") as handle:
            handle.write("0" * 64 + "  ../outside\n")
        result = self.run_installer(source=source)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Unsafe manifest", result.stderr)
        self.assertEqual(list(self.home.iterdir()), [])

    def test_source_symlink_refused(self):
        source = self.copied_source()
        (source / "extra-link").symlink_to(ROOT / "SKILL.md")
        result = self.run_installer(source=source)
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(list(self.home.iterdir()), [])

    def test_destination_parent_symlink_refused(self):
        outside = self.base / "outside"
        outside.mkdir()
        (self.home / ".agents").symlink_to(outside, target_is_directory=True)
        result = self.run_installer()
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(list(outside.iterdir()), [])

    def test_dangling_destination_symlink_refused(self):
        self.dest.parent.mkdir(parents=True)
        self.dest.symlink_to(self.base / "missing", target_is_directory=True)
        result = self.run_installer()
        self.assertNotEqual(result.returncode, 0)
        self.assertTrue(self.dest.is_symlink())

    def test_global_configuration_and_other_skills_untouched(self):
        codex = self.home / ".codex"
        codex.mkdir()
        config = codex / "config.toml"
        config.write_text('# Do not edit\nmodel = "existing-model"\n')
        shell = self.home / ".zshrc"
        shell.write_text("# Existing shell setup\n")
        other = self.dest.parent / "other-skill"
        other.mkdir(parents=True)
        (other / "SKILL.md").write_text("Other skill")
        before = self.tree_hashes(self.home)
        result = self.run_installer()
        self.assertEqual(result.returncode, 0, result.stderr)
        after = self.tree_hashes(self.home)
        for name, digest in before.items():
            self.assertEqual(after[name], digest, name)

    def test_relative_home_refused(self):
        result = self.run_installer(home="relative-home")
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(list(self.home.iterdir()), [])

    def test_root_home_refused(self):
        result = self.run_installer(home="/")
        self.assertNotEqual(result.returncode, 0)

    def test_sudo_environment_refused(self):
        result = self.run_installer(extra_env={"SUDO_USER": "someone"})
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(list(self.home.iterdir()), [])

    def test_finder_metadata_not_copied(self):
        source = self.copied_source()
        (source / ".DS_Store").write_text("Synthetic Finder metadata")
        result = self.run_installer(source=source)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse((self.dest / ".DS_Store").exists())

    def test_destination_parent_file_refused(self):
        (self.home / ".agents").write_text("Not a directory")
        result = self.run_installer()
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual((self.home / ".agents").read_text(), "Not a directory")


if __name__ == "__main__":
    unittest.main(verbosity=2)

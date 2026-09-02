"""Behavior tests for the dependency-free Gemini 3.7 Flash prompt linter."""

from __future__ import annotations

import importlib.util
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


PACKAGE_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = PACKAGE_ROOT / "scripts" / "lint_gemini_prompt.py"
SPEC = importlib.util.spec_from_file_location("lint_gemini_prompt", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


def codes(text: str) -> list[str]:
    return [diagnostic.code for diagnostic in MODULE.lint_text(text)]


class LintTextTests(unittest.TestCase):
    def test_rejects_invalid_thinking_level_assignments(self) -> None:
        self.assertEqual(codes("thinking_level: MINIMAL"), ["G37F001"])
        self.assertEqual(codes('"thinking_level" = "INVALID"'), ["G37F001"])
        self.assertEqual(codes("client.thinking_level='MINIMAL'"), ["G37F001"])
        self.assertEqual(codes("thinking_level:"), ["G37F001"])
        self.assertEqual(codes('thinking_level: "HIGH VALUE"'), ["G37F001"])

    def test_allows_valid_thinking_level_assignments(self) -> None:
        self.assertEqual(codes("thinking_level = HIGH\nthinking_level: medium"), [])

    def test_allows_explanatory_minimal_prose(self) -> None:
        self.assertEqual(codes("Do not use MINIMAL.\nMake minimal changes."), [])

    def test_flags_thinking_budget_assignment(self) -> None:
        self.assertEqual(codes("thinking_budget: 512"), ["G37F002"])

    def test_flags_deprecated_parameter_assignments(self) -> None:
        self.assertEqual(codes("temperature=1\ntop_k: 2\n\"top_p\": 0.2"), ["G37F003"] * 3)
        self.assertEqual(codes("config.temperature=1"), ["G37F003"])

    def test_flags_unsupported_parameter_assignments(self) -> None:
        self.assertEqual(codes("frequency_penalty: 1\npresence_penalty=1\ncandidate_count: 2"), ["G37F004"] * 3)

    def test_allows_parameter_explanatory_prose(self) -> None:
        self.assertEqual(codes("Remove temperature and top_p from prose documentation."), [])

    def test_flags_config_inside_code_fences(self) -> None:
        self.assertEqual(codes("```yaml\nthinking_level: MINIMAL\ntemperature: 0\n```"), ["G37F001", "G37F003"])

    def test_flags_manual_cot_requests(self) -> None:
        phrases = (
            "Let's think step by step.",
            "Show your chain of thought.",
            "Provide a chain-of-thought.",
            "Think aloud.",
            "Explain your reasoning step by step.",
            "Think through the problem step by step.",
            "Reason step by step before responding.",
            "Work through the problem step by step.",
            "Work step by step before responding.",
        )
        for phrase in phrases:
            with self.subTest(phrase=phrase):
                self.assertEqual(codes(phrase), ["G37F005"])

    def test_manual_cot_negation_applies_to_matching_clause(self) -> None:
        self.assertEqual(codes("Do not ask the model to think step by step."), [])
        self.assertEqual(codes("Avoid mistakes; think step by step."), ["G37F005"])
        self.assertEqual(codes('The phrase "think step by step" is prohibited.'), [])
        self.assertEqual(codes("The phrase “think step by step” is prohibited."), [])
        self.assertEqual(codes('Never tell it: "Think aloud"'), [])
        self.assertEqual(codes("Avoid chain-of-thought? Think aloud"), ["G37F005"])

    def test_ignores_manual_cot_inside_fences(self) -> None:
        self.assertEqual(codes("````text\n```\nThink aloud.\n````"), [])
        self.assertEqual(codes("~~~text\nThink aloud.\n~~~"), [])

    def test_does_not_close_four_backtick_fence_on_three_backticks(self) -> None:
        self.assertEqual(codes("````text\n```\nThink aloud.\n````\n"), [])

    def test_does_not_close_backtick_fence_on_tildes(self) -> None:
        self.assertEqual(codes("```text\n~~~\nThink aloud.\n```\n"), [])

    def test_flags_mixed_xml_with_atx_or_setext_heading(self) -> None:
        self.assertEqual(codes("# Task\n<context>facts</context>"), ["G37F006"])
        self.assertEqual(codes("Task\n====\n<context>facts</context>"), ["G37F006"])

    def test_allows_autolinks_with_markdown_headings(self) -> None:
        self.assertEqual(codes("# Task\n<https://example.test/a>\n<person@example.test>"), [])


class CommandLineTests(unittest.TestCase):
    def run_cli(self, *args: str, input_text: str | None = None) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(SCRIPT), *args],
            input=input_text,
            text=True,
            capture_output=True,
            check=False,
        )

    def test_stdin_clean_and_dirty_exit_codes(self) -> None:
        self.assertEqual(self.run_cli(input_text="thinking_level: MEDIUM\n").returncode, 0)
        self.assertEqual(self.run_cli(input_text="thinking_level: MINIMAL\n").returncode, 1)

    def test_multiple_files_report_paths_and_findings(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            clean = Path(directory) / "clean.txt"
            dirty = Path(directory) / "dirty.txt"
            clean.write_text("thinking_level: LOW\n", encoding="utf-8")
            dirty.write_text("candidate_count: 1\n", encoding="utf-8")
            result = self.run_cli(str(clean), str(dirty))
            self.assertEqual(result.returncode, 1)
            self.assertIn(f"{dirty}:1: G37F004", result.stdout)
            self.assertNotIn(str(clean), result.stdout)

    def test_invalid_utf8_is_a_read_error(self) -> None:
        with tempfile.NamedTemporaryFile() as file:
            file.write(b"\xff")
            file.flush()
            result = self.run_cli(file.name)
            self.assertEqual(result.returncode, 2)
            self.assertIn("G37F900 unable to read input", result.stderr)


if __name__ == "__main__":
    unittest.main()

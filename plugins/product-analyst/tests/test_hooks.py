"""Regression tests for fail-closed analyst tool hooks."""

from __future__ import annotations

import io
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
HOOKS = ROOT / "hooks"
sys.path.insert(0, str(ROOT / "server"))
import ledger  # noqa: E402

sys.path.insert(0, str(HOOKS))
import gate  # noqa: E402
import policy  # noqa: E402

CONTRACT = {
    "metric": "activation",
    "metric_version": "1",
    "population": "new accounts",
    "window": {"start": "2026-09-21T00:00:00+02:00", "end": "2026-09-28T00:00:00+02:00"},
    "timezone": "Europe/Vienna",
    "comparison": "previous week",
}


class HookTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.project = Path(self.tmp.name)
        analyst = self.project / ".analyst"
        analyst.mkdir()
        (analyst / "config.toml").write_text(
            '[postgres]\nservice="analyst"\nschemas=["analytics"]\n'
            "[budgets]\nposthog_calls=1\n"
            "[posthog]\nextra_read_tools=[]\n"
        )
        self.session = "session-a"
        self.inv = ledger.start(self.project, CONTRACT, self.session)["investigation_id"]

    def payload(self, tool_name: str, tool_input: dict, tool_id: str = "call-a") -> dict:
        return {
            "tool_name": tool_name,
            "tool_input": tool_input,
            "tool_use_id": tool_id,
            "session_id": self.session,
            "cwd": str(self.project),
            "mcp_server": {"name": "posthog", "source": "project"},
        }

    def hook(self, name: str, payload: dict) -> tuple[int, dict]:
        env = os.environ | {"CLAUDE_PROJECT_DIR": str(self.project)}
        proc = subprocess.run(
            [sys.executable, str(HOOKS / name)],
            input=json.dumps(payload),
            text=True,
            capture_output=True,
            env=env,
            check=False,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        return proc.returncode, json.loads(proc.stdout or "{}")

    def decision(self, payload: dict) -> str | None:
        _, result = self.hook("policy.py", payload)
        return result.get("hookSpecificOutput", {}).get("permissionDecision")

    def test_posthog_exec_wrapper_reserves_before_call_and_records_result(self) -> None:
        request = self.payload(
            "mcp__posthog__exec",
            {
                "command": 'call query-trends "{\\"kind\\":\\"TrendsQuery\\"}"',
            },
        )
        self.assertIsNone(self.decision(request))
        request["tool_response"] = {"results": [{"count": 7}]}
        _, result = self.hook("record.py", request)
        self.assertIn("evidence ev_", result["hookSpecificOutput"]["additionalContext"])
        evidence = ledger.get_investigation(self.project, self.inv)["evidence"]
        self.assertEqual([row["event"] for row in evidence], ["reserved", "completed"])
        self.assertEqual(evidence[0]["operation"]["arguments"], request["tool_input"])
        self.assertEqual(evidence[1]["status"], "ok")

    def test_posthog_confirm_and_person_tools_are_denied(self) -> None:
        confirmed = self.payload(
            "mcp__posthog__exec", {"command": 'call --confirm query-trends "{}"'}
        )
        people = self.payload("mcp__posthog__query-events-actors", {}, "call-b")
        self.assertEqual(self.decision(confirmed), "deny")
        self.assertEqual(self.decision(people), "deny")

    def test_posthog_connector_aliases_still_apply_operation_policy(self) -> None:
        allowed = self.payload("mcp__posthog-prod__query-trends", {})
        allowed["mcp_server"]["name"] = "posthog-prod"
        mutation = self.payload("mcp__posthog-prod__feature-flag-create", {}, "call-b")
        mutation["mcp_server"]["name"] = "posthog-prod"
        self.assertIsNone(self.decision(allowed))
        self.assertEqual(self.decision(mutation), "deny")

    def test_allowlist_is_real_and_read_only_in_vendored_posthog_inventory(self) -> None:
        inventory = json.loads((ROOT / "tests/fixtures/posthog-tools.json").read_text())
        self.assertTrue(policy.ALLOWED_POSTHOG_TOOLS <= inventory.keys())
        for name in policy.ALLOWED_POSTHOG_TOOLS:
            self.assertIs(inventory[name]["annotations"]["readOnlyHint"], True, name)
            self.assertTrue(policy.posthog_allowed(name, [])[0], name)

    def test_catalogue_project_and_experiment_reads_are_permitted(self) -> None:
        config_path = self.project / ".analyst/config.toml"
        config_path.write_text(
            config_path.read_text().replace("posthog_calls=1", "posthog_calls=10")
        )
        self.inv = ledger.start(self.project, CONTRACT, self.session)["investigation_id"]
        for index, tool in enumerate(
            (
                "metric-describe",
                "data-catalog-metric-run",
                "project-get",
                "experiment-results-get",
            )
        ):
            request = self.payload(
                "mcp__claude_ai_PostHog__exec",
                {"command": f'call {tool} "{{}}"'},
                f"catalogue-{index}",
            )
            with self.subTest(tool=tool):
                self.assertIsNone(self.decision(request))
        # Words such as "run" still deny a tool that is not on the exact allowlist.
        self.assertFalse(policy.posthog_allowed("notebooks-run", ["notebooks-run"])[0])

    def test_permitted_calls_never_auto_approve(self) -> None:
        request = self.payload("mcp__posthog__query-trends", {})
        _, result = self.hook("policy.py", request)
        self.assertEqual(result, {})

    def test_budget_counts_failed_posthog_attempts(self) -> None:
        request = self.payload("mcp__posthog__exec", {"command": 'call query-trends "{}"'})
        self.assertIsNone(self.decision(request))
        request["hook_event_name"] = "PostToolUseFailure"
        request["error"] = {"message": "timeout"}
        self.hook("record.py", request)
        evidence = ledger.get_investigation(self.project, self.inv)["evidence"]
        self.assertEqual(evidence[-1]["status"], "error")
        self.assertIn("timeout", evidence[-1]["result_excerpt"])
        self.assertEqual(
            self.decision(
                self.payload("mcp__posthog__exec", {"command": 'call query-trends "{}"'}, "call-b")
            ),
            "deny",
        )

    def test_extra_read_tools_cannot_relax_known_denied_class(self) -> None:
        config_path = self.project / ".analyst/config.toml"
        config_path.write_text(
            config_path.read_text().replace(
                "extra_read_tools=[]",
                'extra_read_tools=["persons-list", "feature-flag-enable", "query-logs"]',
            )
        )
        self.inv = ledger.start(self.project, CONTRACT, self.session)["investigation_id"]
        self.assertEqual(self.decision(self.payload("mcp__posthog__persons-list", {})), "deny")
        self.assertEqual(
            self.decision(self.payload("mcp__posthog__feature-flag-enable", {}, "call-b")), "deny"
        )
        self.assertIsNone(self.decision(self.payload("mcp__posthog__query-logs", {}, "call-c")))

    def test_posttool_result_error_is_recorded_as_error(self) -> None:
        request = self.payload("mcp__posthog__query-trends", {})
        self.assertIsNone(self.decision(request))
        request["tool_response"] = {"isError": True, "message": "query failed"}
        self.hook("record.py", request)
        evidence = ledger.get_investigation(self.project, self.inv)["evidence"]
        self.assertEqual(evidence[-1]["status"], "error")

    def test_result_attaches_to_its_reservation_after_a_new_investigation_starts(self) -> None:
        first_investigation = self.inv
        request = self.payload("mcp__posthog__query-trends", {})
        self.assertIsNone(self.decision(request))
        self.inv = ledger.start(self.project, CONTRACT, self.session)["investigation_id"]
        request["tool_response"] = {"results": [{"count": 7}]}
        self.hook("record.py", request)
        first_evidence = ledger.get_investigation(self.project, first_investigation)["evidence"]
        second_evidence = ledger.get_investigation(self.project, self.inv)["evidence"]
        self.assertEqual(first_evidence[-1]["event"], "completed")
        self.assertEqual(second_evidence, [])

    def test_application_is_error_field_does_not_mark_transport_error(self) -> None:
        request = self.payload("mcp__posthog__query-trends", {})
        self.assertIsNone(self.decision(request))
        request["tool_response"] = {"rows": [{"isError": True, "event": "valid data"}]}
        self.hook("record.py", request)
        evidence = ledger.get_investigation(self.project, self.inv)["evidence"]
        self.assertEqual(evidence[-1]["status"], "ok")

    def test_unconfigured_project_gets_no_opinion_or_records(self) -> None:
        other = Path(tempfile.mkdtemp())
        self.addCleanup(lambda: __import__("shutil").rmtree(other, ignore_errors=True))
        env = os.environ | {"CLAUDE_PROJECT_DIR": str(other)}
        for index, (tool_name, tool_input) in enumerate(
            (
                ("mcp__posthog__dashboard-create", {}),
                ("mcp__posthog__query-trends", {}),
                ("Bash", {"command": "aws quicksight delete-dashboard --dashboard-id x"}),
            )
        ):
            payload = self.payload(tool_name, tool_input, f"other-{index}")
            payload["cwd"] = str(other)
            for name in ("policy.py", "record.py"):
                proc = subprocess.run(
                    [sys.executable, str(HOOKS / name)],
                    input=json.dumps(payload),
                    text=True,
                    capture_output=True,
                    env=env,
                )
                with self.subTest(tool=tool_name, hook=name):
                    self.assertEqual(json.loads(proc.stdout or "{}"), {})
        self.assertFalse((other / ".analyst").exists())
        self.assertIsNone(
            self.decision({"tool_name": "Read", "tool_input": {}, "cwd": str(self.project)})
        )

    def test_hooks_only_match_bash_and_posthog_tools(self) -> None:
        import re

        config = json.loads((HOOKS / "hooks.json").read_text())
        for event, entries in config["hooks"].items():
            for entry in entries:
                matcher = re.compile(entry["matcher"])
                with self.subTest(event=event):
                    self.assertTrue(matcher.search("Bash"))
                    self.assertTrue(matcher.search("mcp__claude_ai_PostHog__exec"))
                    self.assertTrue(matcher.search("mcp__posthog__query-trends"))
                    for unrelated in ("Read", "Edit", "Write", "mcp__playwright__browser_click"):
                        self.assertFalse(matcher.search(unrelated), unrelated)

    def test_shell_supervisor_works_with_gnu_mktemp(self) -> None:
        # GNU mktemp rejects a template without X's; macOS mktemp accepts one.
        fake_bin = self.project / "fake-bin"
        fake_bin.mkdir()
        real_mktemp = subprocess.run(
            ["/bin/bash", "-c", "command -v mktemp"], capture_output=True, text=True, check=True
        ).stdout.strip()
        fake = fake_bin / "mktemp"
        fake.write_text(
            "#!/bin/bash\n"
            'for arg in "$@"; do\n'
            '  case "$arg" in -*) ;; *XXX*) ;; *) echo "too few X\'s" >&2; exit 1 ;; esac\n'
            "done\n"
            f'exec {real_mktemp} "$@"\n'
        )
        fake.chmod(0o755)
        payload = self.payload("mcp__posthog__query-trends", {})
        env = os.environ | {
            "PATH": f"{fake_bin}:{os.environ['PATH']}",
            "CLAUDE_PROJECT_DIR": str(self.project),
        }
        proc = subprocess.run(
            ["/bin/bash", str(HOOKS / "run_gate.sh"), "policy.py"],
            input=json.dumps(payload),
            text=True,
            capture_output=True,
            env=env,
            check=False,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(json.loads(proc.stdout), {}, proc.stderr)

    def test_quicksight_allows_only_direct_read_operations(self) -> None:
        good = {
            "tool_name": "Bash",
            "tool_use_id": "qs-a",
            "session_id": self.session,
            "cwd": str(self.project),
            "tool_input": {"command": "aws quicksight list-dashboards --aws-account-id 123"},
        }
        bad = {
            **good,
            "tool_use_id": "qs-b",
            "tool_input": {"command": "aws quicksight create-dashboard; whoami"},
        }
        quoted = {
            **good,
            "tool_use_id": "qs-c",
            "tool_input": {"command": 'aws quick"sight list-dashboards'},
        }
        wrapped = {
            **good,
            "tool_use_id": "qs-d",
            "tool_input": {"command": "AWS_PROFILE=prod aws quicksight list-dashboards"},
        }
        nested = {
            **good,
            "tool_use_id": "qs-e",
            "tool_input": {"command": 'bash -c "aws quicksight delete-dashboard --dashboard-id x"'},
        }
        profiled = {
            **good,
            "tool_use_id": "qs-f",
            "tool_input": {
                "command": "aws --profile prod --no-cli-pager quicksight list-dashboards "
                "--aws-account-id 123"
            },
        }
        self.assertIsNone(self.decision(good))
        self.assertEqual(self.decision(bad), "deny")
        self.assertEqual(self.decision(quoted), "deny")
        self.assertEqual(self.decision(wrapped), "deny")
        self.assertEqual(self.decision(nested), "deny")
        self.assertIsNone(self.decision(profiled))
        recorded = ledger.get_investigation(self.project, self.inv)["evidence"]
        self.assertEqual(
            [row["operation"]["operation"] for row in recorded if row["source"] == "quicksight"],
            ["list-dashboards", "list-dashboards"],
        )

    def test_commands_that_only_mention_quicksight_get_no_opinion(self) -> None:
        for index, command in enumerate(
            (
                "cat setup/quicksight-readonly-policy.json",
                "grep -rn quicksight README.md",
                "aws s3 ls s3://quicksight-exports",
            )
        ):
            request = {
                "tool_name": "Bash",
                "tool_use_id": f"mention-{index}",
                "session_id": self.session,
                "cwd": str(self.project),
                "tool_input": {"command": command},
            }
            with self.subTest(command=command):
                self.assertIsNone(self.decision(request))
        evidence = ledger.get_investigation(self.project, self.inv)["evidence"]
        self.assertNotIn("quicksight", {row["source"] for row in evidence})

    def test_malformed_relevant_tool_input_is_denied(self) -> None:
        request = self.payload("mcp__posthog__query-trends", {})
        request["tool_input"] = []
        self.assertEqual(self.decision(request), "deny")
        missing = self.payload("mcp__posthog__query-trends", {}, "call-b")
        del missing["tool_input"]
        self.assertEqual(self.decision(missing), "deny")

    def test_record_reports_missing_relevant_tool_input(self) -> None:
        request = self.payload("mcp__posthog__query-trends", {})
        self.assertIsNone(self.decision(request))
        del request["tool_input"]
        _, result = self.hook("record.py", request)
        self.assertIn("invalid tool_input", result["hookSpecificOutput"]["additionalContext"])

    def test_supervisor_denies_crashed_guard_and_keeps_noop(self) -> None:
        broken = self.project / "broken.py"
        broken.write_text("raise RuntimeError('boom')\n")
        payload = {"tool_name": "Read", "tool_input": {}, "cwd": str(self.project)}
        proc = subprocess.run(
            [sys.executable, str(HOOKS / "gate.py"), str(broken)],
            input=json.dumps(payload),
            text=True,
            capture_output=True,
        )
        self.assertEqual(proc.returncode, 0)
        self.assertEqual(
            json.loads(proc.stdout)["hookSpecificOutput"]["permissionDecision"], "deny"
        )
        proc = subprocess.run(
            [sys.executable, str(HOOKS / "gate.py"), "policy.py"],
            input=json.dumps(payload),
            text=True,
            capture_output=True,
        )
        self.assertEqual(json.loads(proc.stdout), {})

    def test_supervisor_turns_a_guard_approval_into_denial(self) -> None:
        approving = self.project / "approving.py"
        approving.write_text(
            "import json\n"
            "print(json.dumps({'hookSpecificOutput': {'hookEventName': 'PreToolUse',"
            " 'permissionDecision': 'allow', 'permissionDecisionReason': 'x'}}))\n"
        )
        payload = {"tool_name": "Bash", "tool_input": {}, "cwd": str(self.project)}
        proc = subprocess.run(
            [sys.executable, str(HOOKS / "gate.py"), str(approving)],
            input=json.dumps(payload),
            text=True,
            capture_output=True,
        )
        self.assertEqual(
            json.loads(proc.stdout)["hookSpecificOutput"]["permissionDecision"], "deny"
        )

    def test_shell_supervisor_denies_when_python_is_unavailable(self) -> None:
        payload = {"tool_name": "Read", "tool_input": {}, "cwd": str(self.project)}
        env = os.environ | {"PATH": "/definitely-not-installed"}
        proc = subprocess.run(
            ["/bin/bash", str(HOOKS / "run_gate.sh")],
            input=json.dumps(payload),
            text=True,
            capture_output=True,
            env=env,
            check=False,
        )
        self.assertEqual(proc.returncode, 0)
        self.assertEqual(
            json.loads(proc.stdout)["hookSpecificOutput"]["permissionDecision"], "deny"
        )

    def test_guard_timeout_is_fixed_and_denies_without_waiting(self) -> None:
        output = io.StringIO()
        with patch.dict(os.environ, {"PRODUCT_ANALYST_GUARD_TIMEOUT": "999"}):
            with (
                patch.object(gate.sys, "argv", ["gate.py", "policy.py"]),
                patch.object(gate.sys, "stdin", io.StringIO(json.dumps({}))),
                patch.object(gate.sys, "stdout", output),
                patch.object(
                    gate.subprocess,
                    "run",
                    side_effect=subprocess.TimeoutExpired(["guard"], gate.GUARD_TIMEOUT),
                ),
            ):
                self.assertEqual(gate.main(), 0)
        self.assertEqual(gate.GUARD_TIMEOUT, 8)
        self.assertEqual(
            json.loads(output.getvalue())["hookSpecificOutput"]["permissionDecision"], "deny"
        )


if __name__ == "__main__":
    unittest.main()

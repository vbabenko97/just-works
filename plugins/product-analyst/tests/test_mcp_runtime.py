"""Opt-in stdio smoke test for the locked MCP runtime without database access."""

import json
import os
import select
import subprocess
import tempfile
import unittest
from pathlib import Path

from test_core import CONTRACT, UNCERTAINTY


@unittest.skipUnless(os.environ.get("ANALYST_TEST_MCP"), "Set ANALYST_TEST_MCP=1 to run uv")
class McpRuntimeTests(unittest.TestCase):
    def test_locked_runtime_discovers_tools_and_persists_contract(self):
        gateway = Path(__file__).resolve().parents[1] / "server/gateway.py"
        with tempfile.TemporaryDirectory() as directory, tempfile.TemporaryFile() as errors:
            project = Path(directory)
            (project / ".analyst").mkdir()
            (project / ".analyst/config.toml").write_text(
                '[postgres]\nservice="unused"\nschemas=["analytics"]\n'
            )
            process = subprocess.Popen(
                ["uv", "run", "--locked", "--script", str(gateway)],
                cwd="/private/tmp",
                env=os.environ | {"ANALYST_PROJECT_DIR": str(project)},
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=errors,
                text=True,
            )
            request_id = 0

            def tool_result(reply):
                self.assertFalse(reply.get("isError"), reply)
                return reply.get("structuredContent") or json.loads(reply["content"][0]["text"])

            def send(method, params, notification=False):
                nonlocal request_id
                request_id += 1
                request = {"jsonrpc": "2.0", "method": method, "params": params}
                if not notification:
                    request["id"] = request_id
                process.stdin.write(json.dumps(request) + "\n")
                process.stdin.flush()
                if notification:
                    return None
                self.assertTrue(select.select([process.stdout], [], [], 30)[0], method)
                line = process.stdout.readline()
                if not line:
                    errors.seek(0)
                    self.fail(errors.read().decode())
                reply = json.loads(line)
                self.assertEqual(reply.get("id"), request_id, reply)
                self.assertNotIn("error", reply, reply)
                return reply["result"]

            try:
                initialized = send(
                    "initialize",
                    {
                        "protocolVersion": "2025-06-18",
                        "capabilities": {},
                        "clientInfo": {"name": "product-analyst-smoke", "version": "1"},
                    },
                )
                self.assertIn("tools", initialized["capabilities"])
                send("notifications/initialized", {}, notification=True)
                tools = send("tools/list", {})["tools"]
                self.assertEqual(
                    {tool["name"] for tool in tools},
                    {
                        "start_investigation",
                        "execute_read_query",
                        "describe_schema",
                        "get_metric_definition",
                        "get_analysis_context",
                        "get_investigation",
                        "prepare_findings",
                        "submit_verification",
                        "check_claims",
                        "prepare_report",
                        "get_report_verification_input",
                        "submit_report_verification",
                        "check_report",
                    },
                )
                started = send(
                    "tools/call",
                    {
                        "name": "start_investigation",
                        "arguments": {"contract": CONTRACT, "session_id": "runtime-test"},
                    },
                )
                inv = tool_result(started)["investigation_id"]
                found = send(
                    "tools/call",
                    {
                        "name": "get_investigation",
                        "arguments": {"investigation_id": inv},
                    },
                )
                self.assertEqual(tool_result(found)["contract"], CONTRACT)
                empty = {"claims": [], "stop_reason": "INCONCLUSIVE", "uncertainty": UNCERTAINTY}
                prepared = send(
                    "tools/call",
                    {
                        "name": "prepare_findings",
                        "arguments": {"investigation_id": inv, "findings": empty},
                    },
                )
                self.assertTrue(tool_result(prepared)["valid"])
                checked = send(
                    "tools/call",
                    {
                        "name": "check_claims",
                        "arguments": {
                            "investigation_id": inv,
                            "candidate_sha256": tool_result(prepared)["candidate_sha256"],
                        },
                    },
                )
                self.assertTrue(tool_result(checked)["valid"])
                narrative = {"title": "No answer yet", "answer": "The question stays open."}
                report = send(
                    "tools/call",
                    {
                        "name": "prepare_report",
                        "arguments": {"investigation_id": inv, "narrative": narrative},
                    },
                )
                version = tool_result(report)["version_sha256"]
                self.assertEqual(len(version), 64)
                verifier_input = send(
                    "tools/call",
                    {
                        "name": "get_report_verification_input",
                        "arguments": {"investigation_id": inv, "version_sha256": version},
                    },
                )
                # The text is the gateway's own serialisation, sent once and not re-serialised.
                self.assertFalse(verifier_input.get("isError"), verifier_input)
                self.assertNotIn("structuredContent", verifier_input)
                self.assertEqual(len(verifier_input["content"]), 1)
                text = verifier_input["content"][0]["text"]
                value = json.loads(text)
                self.assertEqual(
                    text,
                    json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False),
                )
                self.assertEqual(value["errors"], [])
                self.assertEqual(value["basis"]["contract"], CONTRACT)
                self.assertEqual(value["narrative"]["title"], narrative["title"])
                gate = send(
                    "tools/call",
                    {"name": "check_report", "arguments": {"investigation_id": inv}},
                )
                self.assertIn("No report verification", tool_result(gate)["errors"][0])
                missing = send("tools/call", {"name": "get_analysis_context", "arguments": {}})
                self.assertTrue(missing.get("isError"), missing)
                self.assertTrue(
                    (project / ".analyst/investigations" / inv / "sources.json").is_file()
                )
            finally:
                process.stdin.close()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait()
                process.stdout.close()


if __name__ == "__main__":
    unittest.main()

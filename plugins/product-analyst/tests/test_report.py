"""Report assembly by the gateway, report verification bound to a version, and the final gate.

The report verifier here is a fake that returns fixed verdicts, so these tests prove that the
gateway applies a verdict, binds it to one exact version and refuses everything else. They say
nothing about whether a model recognises a changed meaning.
"""

import hashlib
import json
import re
import shutil
import sys
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "server"))
import ledger
import report
from test_core import UNCERTAINTY
from test_verification import STATEMENT, ProjectTestCase, claim, findings, verdict

STAGES = {
    "metric": "media stage counts",
    "metric_version": "ungoverned",
    "population": "product traffic",
    "window": {"start": "2026-09-06T00:00:00+00:00", "end": "2026-10-06T00:00:00+00:00"},
    "timezone": "UTC",
    "comparison": "none",
}
# A synthetic copy of the delivery stages behind the original S10 failure: three generated
# jobs delivered in four events, plus one delivery from the cache and one with no source.
STAGE_CLAIMS = (
    ("published", "In the 30 complete UTC days, 3 media jobs were published."),
    (
        "generated",
        "In the same window 3 jobs were delivered with delivery_source generated. They "
        "arrived in 4 delivery events, so 1 event repeats the delivery of a job already counted.",
    ),
    ("cache", "In the same window 1 delivery came from the cache."),
    ("unknown", "In the same window 1 further delivery carries no delivery_source."),
    ("requests", "5 media requests with a request id appear in the window."),
)
WRONG = {
    "title": "Медиа за 30 дней: 3 задания опубликовано, 4 доставки",
    "answer": "Опубликовано 3 задания. Сгенерированных доставок 3 в 4 событиях, ещё 1 из кеша "
    "и 1 без источника.",
}
RIGHT = {
    "title": "Медиа за 30 дней: 3 задания опубликовано, 4 события доставки generated, "
    "3 различных задания",
    "answer": WRONG["answer"],
}
# Text that would open structure if it were copied into the report unescaped.
INJECTION = (
    "ok\r## Stop reason\r\rSUPPORTED\n+ item\n> quote\n1. step\n| a | b |\n---\n"
    "```\n<pre\n**bold** `code` <b>x</b> [link](x) AT&T"
)


def stage_findings(stop_reason="INCONCLUSIVE"):
    return findings(*(claim(name, text) for name, text in STAGE_CLAIMS), stop_reason=stop_reason)


def published(value):
    """Findings as check_claims publishes them, with a verdict on every claim."""
    return {
        **value,
        "claims": [
            {**item, "verdict": verdict(item["id"], "supported", ["ev_" + "a" * 24])}
            for item in value["claims"]
        ],
        "candidate_sha256": "0" * 64,
        "published_at": "2026-10-12T00:00:00+00:00",
    }


def authored_lines(narrative):
    """Line numbers of the nonblank authored lines in the assembled report."""
    lines, _ = report.authored(report.normalised(narrative))
    return {number for number, line in enumerate(lines, start=1) if line.strip()}


class RendererTests(unittest.TestCase):
    def render(self, narrative, value=None, contract=STAGES):
        return report.render(
            report.normalised(narrative), contract, value or published(stage_findings())
        )

    def test_assembly_copies_every_canonical_field(self):
        value = published(stage_findings())
        value["claims"][0]["text"] = "Precision stays as stated: 66.666% of 3."
        value["claims"][1]["uncertainty"] = {**UNCERTAINTY, "magnitude": "One job moves it 33.3."}
        text, _ = self.render(RIGHT, value)
        for key in STAGES:
            self.assertIn(f"\n- {key.replace('_', chr(92) + '_')}: ", text)
        self.assertIn('"start": "2026-09-06T00:00:00+00:00"', text)
        for item in value["claims"]:
            self.assertIn(f"### Claim {item['id']}\n", text)
        self.assertIn("- Text: Precision stays as stated: 66.666% of 3.", text)
        self.assertIn("- Uncertainty, magnitude: One job moves it 33.3.", text)
        self.assertEqual(text.count("- Verifier verdict: supported"), len(STAGE_CLAIMS))
        self.assertEqual(text.count("- Verifier evidence: `ev_" + "a" * 24 + "`"), 5)
        self.assertEqual(text.count("- Verifier limitations: (empty)"), 5)
        self.assertEqual(text.count("- Uncertainty, data quality: unverified"), 5)
        for label in ("Data quality", "Metric definition", "Magnitude", "Cause"):
            self.assertIn(f"\n- {label}: unverified", text)
        self.assertTrue(text.endswith("## Stop reason\n\nINCONCLUSIVE\n"))
        self.assertEqual(self.render(RIGHT, value)[0], text)

    def test_mixed_language_values_are_copied_untranslated(self):
        value = published(findings(claim("source", STATEMENT, kind="context")))
        value["claims"][0]["context_refs"] = ["attribution_unavailable"]
        text, _ = self.render(RIGHT, value)
        self.assertTrue(text.startswith("# Медиа за 30 дней"))
        self.assertIn(STATEMENT, text)
        self.assertIn("- Context statements: `attribution_unavailable`", text)

    def test_no_copied_field_can_change_the_structure(self):
        value = published(stage_findings())
        first = value["claims"][0]
        first["id"] = "## injected"
        first["text"] = INJECTION
        first["uncertainty"] = dict.fromkeys(UNCERTAINTY, INJECTION)
        first["verdict"]["limitations"] = INJECTION
        value["uncertainty"] = dict.fromkeys(UNCERTAINTY, INJECTION)
        contract = {**STAGES, "note\n\n## Stop reason\n\nSUPPORTED\n\n```": INJECTION}
        text, _ = self.render(RIGHT, value, contract)
        canonical = text.split("\n## Contract\n", 1)[1].split("\n")
        self.assertEqual(
            [line for line in canonical if line.startswith("#")],
            ["## Claims", "### Claim \\## injected"]
            + [f"### Claim {name}" for name, _ in STAGE_CLAIMS[1:]]
            + ["## Uncertainty", "## Stop reason"],
        )
        for line in canonical:
            body = line.removeprefix("  ")
            with self.subTest(line=line):
                self.assertFalse(
                    body.startswith(("```", "~~~", "+ ", "> ", "1. ", "|", "<", "---"))
                )
                self.assertNotIn("\r", line)
        self.assertIn("\\*\\*bold\\*\\* \\`code\\` \\<b\\>x\\</b\\> \\[link\\](x) AT\\&T", text)

    def test_every_authored_line_lies_in_exactly_one_block(self):
        narrative = {
            "title": "Title",
            "answer": "First line\nsecond line.\n\n- one\n- two\n\n| a | b |\n|---|---|\n| 1 | 2 |"
            "\n\n```sql\n# not a heading\nSELECT 999\n```",
            "explanation": "Why.",
        }
        text, blocks = self.render(narrative)
        lines = text.split("\n")
        self.assertEqual(
            [(b["block_id"], b["start_line"], b["end_line"]) for b in blocks],
            [
                ("title", 1, 1),
                ("answer-1", 3, 4),
                ("answer-2", 6, 6),
                ("answer-3", 7, 7),
                ("answer-4", 9, 10),
                ("answer-5", 11, 11),
                ("answer-6", 13, 16),
                ("explanation-1", 18, 18),
            ],
        )
        covered = [n for b in blocks for n in range(b["start_line"], b["end_line"] + 1)]
        self.assertEqual(sorted(covered), sorted(set(covered)))
        self.assertEqual(set(covered), authored_lines(narrative))
        for block in blocks[1:]:
            self.assertEqual(
                "\n".join(lines[block["start_line"] - 1 : block["end_line"]]), block["text"]
            )

    def test_narrative_that_could_reach_past_its_end_is_refused(self):
        cases = (
            ("must be an object", "text"),
            ("title must be one nonempty line", {"answer": "x"}),
            ("title must be one nonempty line", {"title": "a\nb", "answer": "x"}),
            ("title must be one nonempty line", {"title": "T\r## Stop reason", "answer": "x"}),
            ("title holds HTML", {"title": "T <pre", "answer": "x"}),
            ("answer must be nonempty", {"title": "t", "answer": "  "}),
            ("explanation must be text", {"title": "t", "answer": "x", "explanation": 1}),
            ("unknown fields: claims", {"title": "t", "answer": "x", "claims": []}),
            ("is not closed", {"title": "t", "answer": "Result.\n\n```"}),
            ("is a code fence", {"title": "t", "answer": "```a`b\n## Stop reason\n```"}),
            ("is a code fence", {"title": "t", "answer": "~~~\ncode\n~~~"}),
            ("is a code fence", {"title": "t", "answer": "- ```\n  code"}),
            ("could close the code block", {"title": "t", "answer": "```\ncode\n ```\n```"}),
            ("holds HTML", {"title": "t", "answer": "Result.\n\n<pre"}),
            ("holds HTML", {"title": "t", "answer": "Result.\n\n<?"}),
            ("holds HTML", {"title": "t", "answer": "Result.\n\n<!X"}),
            ("holds HTML", {"title": "t", "answer": "<table><tr><td>1</td></tr></table>"}),
            ("is a heading", {"title": "t", "answer": "x\n## Claims"}),
            ("is a heading", {"title": "t", "answer": "x\n---"}),
            ("is a heading", {"title": "t", "answer": "Fake heading\n-"}),
            ("is a heading", {"title": "t", "answer": "- ## Stop reason"}),
            ("is a heading", {"title": "t", "answer": "> ## Claims\n> SUPPORTED"}),
            ("is a heading", {"title": "t", "answer": "x\r## Claims"}),
            ("holds a carriage return", {"title": "t", "answer": "x\r## Claims"}),
            ("holds a carriage return", {"title": "t", "answer": "a\r\nb"}),
            ("an image or a footnote", {"title": "t", "answer": "![chart](c.png)"}),
            ("an image or a footnote", {"title": "t", "answer": "R[^1].\n\n[^1]: Stop reason."}),
        )
        for message, narrative in cases:
            with self.subTest(narrative=narrative):
                self.assertIn(message, " ".join(report.narrative_errors(narrative)))
        fine = {
            "title": "t",
            "answer": "```sql\n# a comment\nSELECT 1 <2 AND <b>\n```\n\nx < y and y > z, -5%",
        }
        self.assertEqual(report.narrative_errors(fine), [])


class ReportGateTests(ProjectTestCase):
    def setUp(self):
        super().setUp()
        self.inv = self.start(STAGES)
        self.directory = self.root / ".analyst/investigations" / self.inv
        self.candidate = self.publish_findings(self.with_evidence(stage_findings()))

    def with_evidence(self, value):
        cited = self.evidence(self.inv)
        for item in value["claims"]:
            if item.get("kind", "data") == "data":
                item["evidence_ids"] = [cited]
        return value

    def publish_findings(self, value, verdicts=None):
        candidate = ledger.prepare_findings(self.root, self.inv, value)["candidate_sha256"]
        independent = self.evidence(self.inv)
        verdicts = verdicts or {}
        rows = [
            verdict(item["id"], verdicts.get(item["id"], "supported"), [independent])
            for item in value["claims"]
        ]
        self.assertTrue(
            ledger.submit_verification(self.root, self.inv, candidate, {"claims": rows})["valid"]
        )
        result = ledger.check_claims(self.root, self.inv, candidate_sha256=candidate)
        self.assertTrue(result["valid"], result)
        return candidate

    def prepare(self, narrative):
        result = ledger.prepare_report(self.root, self.inv, narrative)
        self.assertTrue(result["valid"], result)
        return result["version_sha256"]

    def record(self, version):
        return json.loads((self.directory / "reports" / f"{version}.json").read_text())

    def judgement(self, version, rejected=None, caveats="supported", skip=()):
        """A fake report verifier: every authored block supported unless listed in rejected."""
        rejected = rejected or {}
        entries = [
            {
                "block_id": block["block_id"],
                "quote": block["text"][:60],
                "kind": "analytical",
                "statements": [block["text"]],
                "basis": ["claim:generated"],
                "comparison": rejected.get(block["block_id"], ("supported", "Same meaning."))[1],
                "verdict": rejected.get(block["block_id"], ("supported", ""))[0],
            }
            for block in self.record(version)["blocks"]
            if block["block_id"] not in skip
        ]
        return {"blocks": entries, "caveats": {"verdict": caveats, "explanation": "Checked."}}

    def submit(self, version, verification, valid=None):
        result = ledger.submit_report_verification(self.root, self.inv, version, verification)
        if valid is not None:
            self.assertEqual(result["valid"], valid, result)
        return result

    def check(self, version=None):
        return ledger.check_report(self.root, self.inv, version)

    def accepted(self, narrative=RIGHT):
        version = self.prepare(narrative)
        self.submit(version, self.judgement(version), valid=True)
        result = self.check(version)
        self.assertTrue(result["valid"], result)
        return version

    def test_s10_headline_passes_the_number_check_and_is_refused_by_the_gate(self):
        version = self.prepare(WRONG)
        self.prepare({**WRONG, "title": "Медиа: 5 доставок"})
        for title, number in (("Успех 100%", 100.0), ("999. users churned", 999.0)):
            lexical = ledger.prepare_report(self.root, self.inv, {**WRONG, "title": title})
            self.assertEqual(
                lexical["unsupported"], [{"line": 1, "numbers": [number], "text": "# " + title}]
            )
        reason = "«4 доставки» counts generated delivery events as deliveries"
        self.submit(version, self.judgement(version, {"title": ("refuted", reason)}), valid=True)
        result = self.check(version)
        self.assertFalse(result["valid"])
        self.assertEqual(
            result["rejected"],
            [
                {
                    "block_id": "title",
                    "start_line": 1,
                    "end_line": 1,
                    "verdict": "refuted",
                    "reason": reason,
                }
            ],
        )
        self.assertFalse((self.directory / "report.md").exists())

    def test_number_check_covers_text_after_a_fenced_contract_heading(self):
        narrative = {"title": "t", "answer": "```\n## Contract\n```\nRevenue grew 999%."}
        result = ledger.prepare_report(self.root, self.inv, narrative)
        self.assertEqual(result["unsupported"][0]["numbers"], [999.0])

    def test_corrected_report_is_accepted_and_written_once(self):
        version = self.accepted()
        path = self.directory / "report.md"
        self.assertEqual(path.read_text(), self.record(version)["report"])
        self.assertEqual(path.stat().st_mode & 0o777, 0o600)
        self.assertIn("## Claims", path.read_text())
        self.assertTrue(self.check()["valid"])
        acceptances = ledger.get_investigation(self.root, self.inv)["report_acceptances"]
        self.assertEqual(len(acceptances), 1)
        self.assertEqual(
            acceptances[0]["report_sha256"],
            hashlib.sha256(path.read_bytes()).hexdigest(),
        )
        path.write_text(path.read_text().replace("4 события", "4 доставки"))
        result = self.check(version)
        self.assertFalse(result["valid"])
        self.assertIn("already exists", result["errors"][0])
        self.assertIn("4 доставки", path.read_text())

    def test_report_verifier_must_cover_every_authored_block(self):
        narrative = {**RIGHT, "explanation": "```sql\nSELECT 999\n```"}
        version = self.prepare(narrative)
        good = self.judgement(version)
        self.assertEqual(
            [entry["block_id"] for entry in good["blocks"]],
            ["title", "answer-1", "explanation-1"],
        )
        title, answer, code = good["blocks"]

        def with_title(**changes):
            return {**good, "blocks": [{**title, **changes}, answer, code]}

        bad = (
            (
                "Missing entries for authored blocks: explanation-1",
                {**good, "blocks": [title, answer]},
            ),
            (
                "names no authored block",
                {**good, "blocks": [title, answer, code, {**title, "block_id": "x"}]},
            ),
            ("more than one entry", {**good, "blocks": [title, answer, code, title]}),
            ("quote must be text copied exactly", with_title(quote="4 доставки")),
            ("quote must be text copied exactly", with_title(quote="Медиа")),
            ("basis 'claim:missing'", with_title(basis=["claim:missing"])),
            # The stop reason is cited by its own name; its rule is no basis of its own.
            ("basis 'stop_rule'", with_title(basis=["stop_rule"])),
            ("basis 'stop_reason:INCONCLUSIVE'", with_title(basis=["stop_reason:INCONCLUSIVE"])),
            ("needs a basis", with_title(basis=[])),
            ("needs the statements", with_title(statements=[" "])),
            ("needs a comparison", with_title(comparison="")),
            (
                "must be judged analytical",
                with_title(kind="non_analytical", explanation="A label."),
            ),
            ("kind must be analytical", with_title(kind="other")),
            ("verdict must be supported", with_title(verdict=["supported"])),
            (
                "needs an explanation",
                {**good, "blocks": [title, {**answer, "kind": "non_analytical"}, code]},
            ),
            # A non_analytical block states nothing the basis could contradict, so it is supported;
            # a block the verifier doubts is judged analytical.
            *(
                (
                    "is non_analytical, so it states nothing the basis could contradict",
                    {
                        **good,
                        "blocks": [
                            title,
                            {
                                **answer,
                                "kind": "non_analytical",
                                "explanation": "A note.",
                                "verdict": doubted,
                            },
                            code,
                        ],
                    },
                )
                for doubted in ("unverified", "refuted")
            ),
            ("caveats needs a verdict", {**good, "caveats": {"verdict": "supported"}}),
            ("with a blocks list", []),
        )
        for message, verification in bad:
            with self.subTest(message=message):
                result = self.submit(version, verification, valid=False)
                self.assertIn(message, " ".join(result["errors"]))
        self.assertEqual(ledger.get_investigation(self.root, self.inv)["report_verifications"], [])
        allowed = {
            **good,
            "blocks": [
                {
                    **title,
                    "basis": [
                        "contract:window",
                        "uncertainty:magnitude",
                        "claim:cache",
                        "stop_reason",
                    ],
                },
                answer,
                {
                    "block_id": "explanation-1",
                    "quote": "```sql\nSELECT 999",
                    "kind": "non_analytical",
                    "explanation": "An example query, not a measured result.",
                    "verdict": "supported",
                },
            ],
        }
        self.submit(version, allowed, valid=True)

    def test_each_version_is_verified_once_within_the_investigation_limit(self):
        first = self.prepare(WRONG)
        self.submit(
            first, self.judgement(first, {"title": ("refuted", "Events are not jobs.")}), valid=True
        )
        again = self.submit(first, self.judgement(first), valid=False)
        self.assertIn("already verified and not supported", again["errors"][0])
        self.assertIn("revise the narrative", again["errors"][0])
        second = self.prepare(RIGHT)
        self.submit(second, self.judgement(second), valid=True)
        third = self.prepare({**RIGHT, "explanation": "Stage totals are not a success rate."})
        result = self.submit(third, self.judgement(third), valid=False)
        self.assertIn("used its 2 report verifications", result["errors"][0])
        # A supported second verification publishes like a first one, and the refusal says so.
        self.assertIn(f"version {second} is current and supported", result["errors"][0])
        self.assertIn("call check_report", result["errors"][0])
        self.assertTrue(self.check(second)["valid"])

    def test_two_unsupported_verifications_keep_the_report_a_draft(self):
        refuted = {"title": ("refuted", "Events are not jobs.")}
        for narrative in (WRONG, {**WRONG, "explanation": "Repeat events are not jobs."}):
            version = self.prepare(narrative)
            self.submit(version, self.judgement(version, refuted), valid=True)
        third = self.prepare(RIGHT)
        result = self.submit(third, self.judgement(third), valid=False)
        self.assertIn("no current version is supported", result["errors"][0])
        self.assertIn("its report stays a draft", result["errors"][0])
        self.assertEqual(self.verifier_input(third)[1]["errors"], result["errors"])
        self.assertFalse((self.directory / "report.md").exists())

    def test_a_used_up_limit_names_the_supported_version_even_for_a_rejected_one(self):
        supported = self.prepare(RIGHT)
        self.submit(supported, self.judgement(supported), valid=True)
        rejected = self.prepare(WRONG)
        self.submit(
            rejected, self.judgement(rejected, {"title": ("refuted", "Events are not jobs.")}), True
        )
        for errors in (
            self.verifier_input(rejected)[1]["errors"],
            self.submit(rejected, self.judgement(rejected), valid=False)["errors"],
        ):
            self.assertIn("used its 2 report verifications", errors[0])
            self.assertIn(f"version {supported} is current and supported", errors[0])
            self.assertNotIn("revise the narrative", errors[0])
        self.assertTrue(self.check(supported)["valid"])

    def test_a_used_up_limit_never_names_a_stale_supported_version(self):
        supported = self.prepare(RIGHT)
        self.submit(supported, self.judgement(supported), valid=True)
        rejected = self.prepare(WRONG)
        self.submit(
            rejected, self.judgement(rejected, {"title": ("refuted", "Events are not jobs.")}), True
        )
        with mock.patch.object(report, "RENDERER_VERSION", "0"):
            fresh = self.prepare({**RIGHT, "explanation": "Stage totals are not a success rate."})
            errors = self.verifier_input(fresh)[1]["errors"]
            self.assertIn("no current version is supported", errors[0])
            self.assertNotIn(supported, errors[0])
            self.assertIn("stale: renderer_version", self.check(supported)["errors"][0])
        self.assertIn(
            f"version {supported} is current", self.verifier_input(rejected)[1]["errors"][0]
        )

    def test_tampered_version_is_refused_without_a_verifier(self):
        version = self.prepare(RIGHT)
        path = self.directory / "reports" / f"{version}.json"
        original = self.record(version)
        dropped = original["report"].replace("### Claim cache\n", "")
        uncertain = original["report"].replace("- Magnitude: unverified\n", "")
        bindings = {
            key: original[key]
            for key in ledger._report_bindings(self.root, self.directory, self.inv)[0]
        }
        forged_hash = hashlib.sha256(dropped.encode()).hexdigest()
        forged = ledger._version_key(bindings, forged_hash)

        def tamper(record, target=path):
            target.write_text(record if isinstance(record, str) else json.dumps(record))

        def refused(name, message):
            submitted = self.submit(name, {"blocks": [], "caveats": {}}, valid=False)
            self.assertIn(message, submitted["errors"][0])
            self.assertIn(message, self.check(name)["errors"][0])

        retitled = {**original["narrative"], "title": "x"}
        cases = (
            ("text was changed", {**original, "report": dropped}),
            ("text was changed", {**original, "report": uncertain}),
            ("record was changed", {**original, "report": dropped, "report_sha256": forged_hash}),
            ("not what the gateway assembles", {**original, "blocks": original["blocks"][:1]}),
            ("not what the gateway assembles", {**original, "narrative": retitled}),
            ("record was changed", "not json"),
        )
        for message, record in cases:
            with self.subTest(message=message):
                tamper(record)
                refused(version, message)
        forged_record = {
            **original,
            "report": dropped,
            "report_sha256": forged_hash,
            "version_sha256": forged,
        }
        tamper(forged_record, self.directory / "reports" / f"{forged}.json")
        refused(forged, "not what the gateway assembles")
        other = self.prepare({**RIGHT, "explanation": "Another version."})
        shutil.copyfile(self.directory / "reports" / f"{other}.json", path)
        refused(version, "record was changed")
        tamper(original)
        self.submit(version, self.judgement(version), valid=True)
        tamper({**original, "report": uncertain})
        self.assertIn("text was changed", self.check(version)["errors"][0])
        reports = ledger.get_investigation(self.root, self.inv)["reports"]
        self.assertEqual(sum(bool(record["integrity_errors"]) for record in reports), 2)
        self.assertFalse((self.directory / "report.md").exists())

    def test_republishing_keeps_a_version_and_new_findings_make_it_stale(self):
        version = self.prepare(RIGHT)
        self.submit(version, self.judgement(version), valid=True)
        republished = ledger.check_claims(self.root, self.inv, candidate_sha256=self.candidate)
        self.assertTrue(republished["valid"])
        state = ledger.get_investigation(self.root, self.inv)
        self.assertEqual(state["reports"][0]["integrity_errors"], [])
        # Findings that differ only in a field the report does not show, verified with the same
        # evidence, give the same report bytes under another candidate.
        extra = json.loads(json.dumps(state["candidates"][0]["findings"]))
        extra["claims"][0]["note"] = "A field the report does not show."
        candidate = ledger.prepare_findings(self.root, self.inv, extra)["candidate_sha256"]
        rows = state["verifications"][0]["verification"]["claims"]
        self.assertTrue(
            ledger.submit_verification(self.root, self.inv, candidate, {"claims": rows})["valid"]
        )
        self.assertTrue(
            ledger.check_claims(self.root, self.inv, candidate_sha256=candidate)["valid"]
        )
        self.assertIn("stale: candidate_sha256, findings_sha256", self.check(version)["errors"][0])
        same_text = ledger.prepare_report(self.root, self.inv, RIGHT)
        self.assertEqual(same_text["report_sha256"], self.record(version)["report_sha256"])
        self.assertNotEqual(same_text["version_sha256"], version)
        self.assertFalse((self.directory / "report.md").exists())
        self.assertIn("No report verification", self.check()["errors"][0])

    def test_accepted_report_freezes_the_published_findings(self):
        self.accepted()
        self.assertTrue(
            ledger.check_claims(self.root, self.inv, candidate_sha256=self.candidate)["valid"]
        )
        other = self.with_evidence(stage_findings())
        other["claims"][0]["text"] = (
            "In the 30 complete UTC days, 3 media jobs were published again."
        )
        candidate = ledger.prepare_findings(self.root, self.inv, other)["candidate_sha256"]
        independent = self.evidence(self.inv)
        rows = [verdict(item["id"], "supported", [independent]) for item in other["claims"]]
        ledger.submit_verification(self.root, self.inv, candidate, {"claims": rows})
        result = ledger.check_claims(self.root, self.inv, candidate_sha256=candidate)
        self.assertIn("A report was already accepted", result["errors"][0])
        self.assertTrue(self.check()["valid"])

    def test_changed_context_or_renderer_blocks_acceptance(self):
        version = self.prepare(RIGHT)
        self.submit(version, self.judgement(version), valid=True)
        with mock.patch.object(report, "RENDERER_VERSION", "0"):
            self.assertIn("stale: renderer_version", self.check(version)["errors"][0])
        (self.root / "tools/queries.py").write_text(
            'def dau_sql() -> str:\n    return "SELECT 2"\n'
        )
        self.assertIn("analysis context changed", self.check(version)["errors"][0])

    def test_a_version_of_another_investigation_or_contract_is_refused(self):
        version = self.prepare(RIGHT)
        self.submit(version, self.judgement(version), valid=True)
        other = self.start(STAGES)
        foreign = ledger.submit_report_verification(self.root, other, version, {"blocks": []})
        self.assertIn("Unknown report version", foreign["errors"][0])
        self.assertIn("not published", ledger.check_report(self.root, other, version)["errors"][0])
        contract = self.directory / "contract.json"
        contract.write_text(contract.read_text().replace("product traffic", "all traffic"))
        self.assertIn("stale: contract_sha256", self.check(version)["errors"][0])

    def test_unverified_caveats_or_block_keep_the_report_a_draft(self):
        version = self.prepare(RIGHT)
        self.submit(version, self.judgement(version, caveats="unverified"), valid=True)
        self.assertEqual(self.check(version)["rejected"][0]["block_id"], "caveats")
        version = self.prepare({**RIGHT, "explanation": "Repeat events are not jobs."})
        self.submit(
            version,
            self.judgement(version, {"explanation-1": ("unverified", "Vague.")}),
            valid=True,
        )
        self.assertEqual(self.check(version)["rejected"][0]["verdict"], "unverified")
        self.assertFalse((self.directory / "report.md").exists())

    def acceptances(self):
        return ledger.get_investigation(self.root, self.inv)["report_acceptances"]

    def test_an_existing_report_md_is_kept_even_when_empty(self):
        path = self.directory / "report.md"
        path.write_text("# 4 доставки\n")
        self.assertIn("No prepared report", self.check()["errors"][0])
        version = self.prepare(RIGHT)
        self.submit(version, self.judgement(version), valid=True)
        for content in ("# 4 доставки\n", ""):
            with self.subTest(content=content):
                path.write_text(content)
                self.assertIn("already exists", self.check(version)["errors"][0])
                self.assertEqual(path.read_text(), content)
        self.assertEqual(self.acceptances(), [])
        path.unlink()
        path.symlink_to(self.root / "elsewhere.md")
        self.assertIn("symlink or not a file", self.check(version)["errors"][0])
        path.unlink()
        path.mkdir()
        self.assertIn("symlink or not a file", self.check(version)["errors"][0])
        path.rmdir()
        self.assertTrue(self.check(version)["valid"])
        self.assertFalse((self.root / "elsewhere.md").exists())

    def test_a_file_created_while_publishing_is_kept_and_publication_fails(self):
        version = self.prepare(RIGHT)
        self.submit(version, self.judgement(version), valid=True)
        path = self.directory / "report.md"
        append = ledger._append_line

        def concurrent_writer(target, row):
            append(target, row)
            if target.name == "report_acceptances.jsonl":
                path.write_text("# concurrent-edit\n")

        with mock.patch.object(ledger, "_append_line", concurrent_writer):
            result = self.check(version)
        self.assertFalse(result["valid"])
        self.assertIn("appeared while the report was being published", result["errors"][0])
        self.assertEqual(path.read_text(), "# concurrent-edit\n")
        path.unlink()
        self.assertTrue(self.check(version)["valid"])
        self.assertTrue(self.check(version)["valid"])
        self.assertEqual(path.read_text(), self.record(version)["report"])
        self.assertEqual(len(self.acceptances()), 1)

    def test_a_crash_after_acceptance_recovers_without_losing_a_foreign_file(self):
        version = self.prepare(RIGHT)
        self.submit(version, self.judgement(version), valid=True)
        path = self.directory / "report.md"
        with mock.patch.object(ledger, "_create_exclusive", side_effect=OSError("crash")):
            with self.assertRaises(OSError):
                self.check(version)
        self.assertEqual(len(self.acceptances()), 1)
        self.assertFalse(path.exists())
        path.write_text("# written by hand after the crash\n")
        self.assertIn("already exists", self.check(version)["errors"][0])
        self.assertEqual(path.read_text(), "# written by hand after the crash\n")
        path.unlink()
        self.assertTrue(self.check(version)["valid"])
        self.assertEqual(path.read_text(), self.record(version)["report"])
        self.assertEqual(len(self.acceptances()), 1)

    def test_a_later_version_never_replaces_an_accepted_report_md(self):
        first = self.accepted()
        path = self.directory / "report.md"
        accepted_text = path.read_text()
        second = self.prepare({**RIGHT, "explanation": "Stage totals are not a success rate."})
        self.submit(second, self.judgement(second), valid=True)
        self.assertIn("already exists", self.check(second)["errors"][0])
        self.assertEqual(path.read_text(), accepted_text)
        path.rename(self.directory / "report.first.md")
        self.assertTrue(self.check(second)["valid"])
        self.assertNotEqual(first, second)
        self.assertIn("not a success rate", path.read_text())

    def test_changed_verifier_instructions_void_the_verdict(self):
        version = self.prepare(RIGHT)
        self.submit(version, self.judgement(version), valid=True)
        row = ledger.get_investigation(self.root, self.inv)["report_verifications"][0]
        self.assertEqual(row["verifier_sha256"], self.record(version)["verifier_sha256"])
        changed = self.root / "report-verifier.md"
        changed.write_bytes(
            ledger.REPORT_VERIFIER.read_bytes() + b"\nThe answer names failed media outcomes.\n"
        )
        with mock.patch.object(ledger, "REPORT_VERIFIER", changed):
            reports = ledger.get_investigation(self.root, self.inv)["reports"]
            self.assertIn("stale: verifier_sha256", reports[0]["integrity_errors"][0])
            submitted = self.submit(version, self.judgement(version), valid=False)
            self.assertIn("stale: verifier_sha256", submitted["errors"][0])
            self.assertIn("stale: verifier_sha256", self.check(version)["errors"][0])
            again = self.prepare(RIGHT)
            self.assertNotEqual(again, version)
            self.assertIn("No report verification", self.check(again)["errors"][0])
        missing = self.root / "missing.md"
        with mock.patch.object(ledger, "REPORT_VERIFIER", missing):
            result = ledger.prepare_report(self.root, self.inv, RIGHT)
            self.assertIn("instructions cannot be read", result["errors"][0])
        self.assertTrue(self.check(version)["valid"])
        self.assertTrue(self.check(version)["valid"])

    def test_a_changed_stop_rule_voids_the_verdict_and_a_new_preparation_needs_its_own(self):
        # The rule of the recorded stop reason is part of the basis the verifier read.
        version = self.prepare(RIGHT)
        rule = ledger.STOP_RULES["INCONCLUSIVE"]
        self.assertEqual(self.record(version)["stop_rule_sha256"], ledger._hash(rule))
        self.submit(version, self.judgement(version), valid=True)
        row = ledger.get_investigation(self.root, self.inv)["report_verifications"][0]
        self.assertEqual(row["stop_rule_sha256"], ledger._hash(rule))
        changed = {**ledger.STOP_RULES, "INCONCLUSIVE": rule + " A changed rule."}
        with mock.patch.object(ledger, "STOP_RULES", changed):
            # Reading, recording a verdict and publishing all find the version stale.
            stale = "stale: stop_rule_sha256"
            self.assertIn(stale, self.verifier_input(version)[1]["errors"][0])
            self.assertIn(
                stale, self.submit(version, self.judgement(version), valid=False)["errors"][0]
            )
            self.assertIn(stale, self.check(version)["errors"][0])
            self.assertFalse((self.directory / "report.md").exists())
            # Preparing the same narrative again binds the new rule and needs its own verification.
            again = self.prepare(RIGHT)
            self.assertNotEqual(again, version)
            self.assertEqual(
                self.record(again)["stop_rule_sha256"], ledger._hash(changed["INCONCLUSIVE"])
            )
            self.assertEqual(
                self.verifier_input(again)[1]["basis"]["stop_rule"], changed["INCONCLUSIVE"]
            )
            self.assertIn("No report verification", self.check(again)["errors"][0])
            self.submit(again, self.judgement(again), valid=True)
            self.assertTrue(self.check(again)["valid"])

    def test_the_narrative_is_kept_byte_for_byte(self):
        hard_break = {"title": "Стадии медиа", "answer": "Generated: 3  \nCache: 1\n\n  \nDone."}
        version = self.prepare(hard_break)
        stored = self.record(version)
        self.assertEqual(stored["narrative"], {**hard_break, "explanation": ""})
        self.assertIn("\nGenerated: 3  \nCache: 1\n", stored["report"])
        plain = self.prepare({**hard_break, "answer": "Generated: 3\nCache: 1\n\n  \nDone."})
        self.assertNotEqual(self.record(plain)["report_sha256"], stored["report_sha256"])
        crlf = ledger.prepare_report(self.root, self.inv, {**hard_break, "answer": "a\r\nb"})
        self.assertIn("carriage return", " ".join(crlf["errors"]))

    def test_refuted_claim_and_inconclusive_stop_are_reported_as_such(self):
        self.publish_findings(self.with_evidence(stage_findings()), {"cache": "refuted"})
        version = self.accepted(
            {**RIGHT, "explanation": "The cache delivery count was refuted by the verifier."}
        )
        text = self.record(version)["report"]
        self.assertIn("### Claim cache\n\n- Kind: data", text)
        self.assertIn("- Verifier verdict: refuted", text)
        self.assertTrue(text.endswith("INCONCLUSIVE\n"))

    def verifier_input(self, version):
        text = ledger.report_verification_input(self.root, self.inv, version)
        return text, json.loads(text)

    def test_verifier_input_holds_the_version_and_every_published_claim(self):
        version = self.prepare(RIGHT)
        record = self.record(version)
        text, value = self.verifier_input(version)
        self.assertEqual(text, ledger.encoded(value))
        self.assertEqual(value["errors"], [])
        self.assertEqual((value["investigation_id"], value["version_sha256"]), (self.inv, version))
        self.assertEqual(value["narrative"], record["narrative"])
        self.assertEqual(value["blocks"], record["blocks"])
        bindings = ledger._report_bindings(self.root, self.directory, self.inv)[0]
        self.assertEqual(
            value["version"],
            {key: record[key] for key in (*bindings, "report_sha256")},
        )
        published_findings = json.loads((self.directory / "findings.json").read_text())
        self.assertEqual(
            value["basis"],
            {
                "contract": json.loads((self.directory / "contract.json").read_text()),
                "claims": published_findings["claims"],
                "uncertainty": published_findings["uncertainty"],
                "stop_reason": published_findings["stop_reason"],
                "stop_rule": ledger.STOP_RULES[published_findings["stop_reason"]],
            },
        )
        # Every published claim, those the narrative never cites included, and no evidence,
        # sources, candidates, other versions or earlier verdicts.
        self.assertEqual(
            [item["id"] for item in value["basis"]["claims"]], [name for name, _ in STAGE_CLAIMS]
        )
        self.assertEqual(
            set(value), {"investigation_id", "version_sha256", "errors", "version", "narrative",
                         "blocks", "basis"}
        )  # fmt: skip
        # The input holds only what the version hash binds: preparing the same narrative again
        # rewrites the record's preparation time and leaves the input unchanged.
        self.assertEqual(self.prepare(RIGHT), version)
        self.assertEqual(self.verifier_input(version)[0], text)

    def test_verifier_input_is_refused_once_the_version_cannot_be_verified(self):
        first = self.prepare(RIGHT)
        self.submit(first, self.judgement(first), valid=True)
        verified = self.verifier_input(first)[1]
        self.assertEqual(set(verified), {"investigation_id", "version_sha256", "errors"})
        # A version verified as supported is published, not revised.
        self.assertIn("already verified and supported", verified["errors"][0])
        self.assertIn("call check_report with it", verified["errors"][0])
        second = self.prepare({**RIGHT, "explanation": "Repeat events are not jobs."})
        self.submit(second, self.judgement(second), valid=True)
        third = self.prepare({**RIGHT, "explanation": "Stage totals are not a success rate."})
        self.assertIn("used its 2 report verifications", self.verifier_input(third)[1]["errors"][0])
        refused = self.submit(third, self.judgement(third), valid=False)
        self.assertIn("used its 2 report verifications", refused["errors"][0])

    def test_verifier_input_of_an_unknown_changed_or_stale_version_holds_only_errors(self):
        version = self.prepare(RIGHT)
        unknown = self.verifier_input("f" * 64)[1]
        self.assertEqual(unknown["errors"], ["Unknown report version; call prepare_report"])
        path = self.directory / "reports" / f"{version}.json"
        original = path.read_text()
        path.write_text(
            json.dumps({**self.record(version), "blocks": self.record(version)["blocks"][:1]})
        )
        changed = self.verifier_input(version)[1]
        self.assertIn("not what the gateway assembles", changed["errors"][0])
        self.assertNotIn("basis", changed)
        path.write_text(original)
        with mock.patch.object(report, "RENDERER_VERSION", "0"):
            stale = self.verifier_input(version)[1]
        self.assertIn("stale: renderer_version", stale["errors"][0])
        self.assertEqual(set(stale), {"investigation_id", "version_sha256", "errors"})
        self.assertEqual(self.verifier_input(version)[1]["errors"], [])

    def test_verifier_input_over_the_limit_is_refused_whole(self):
        # A character outside the Basic Multilingual Plane counts twice, as Claude Code counts it.
        version = self.prepare({**RIGHT, "explanation": "Отчёт проверен 🙂"})
        text = self.verifier_input(version)[0]
        size = len(text.encode("utf-16-le")) // 2
        self.assertEqual(size, len(text) + text.count("🙂"))
        self.assertGreater(size, len(text))
        with mock.patch.object(ledger, "REPORT_INPUT_LIMIT", size):
            self.assertEqual(self.verifier_input(version)[0], text)
        with mock.patch.object(ledger, "REPORT_INPUT_LIMIT", len(text)):
            refused = self.verifier_input(version)[1]
        self.assertTrue(refused["errors"][0].startswith("snapshot_too_large"))
        self.assertIn(f"{size} UTF-16 code units", refused["errors"][0])
        self.assertEqual(set(refused), {"investigation_id", "version_sha256", "errors"})
        # prepare_report refuses such a narrative before storing a version at all.
        longer = {**RIGHT, "explanation": "Отчёт проверен 🙂 ещё раз"}
        with mock.patch.object(ledger, "REPORT_INPUT_LIMIT", size):
            result = ledger.prepare_report(self.root, self.inv, longer)
        self.assertFalse(result["valid"])
        self.assertTrue(result["errors"][0].startswith("snapshot_too_large"))
        self.assertEqual(len(list((self.directory / "reports").glob("*.json"))), 1)

    def test_line_separators_inside_a_value_keep_the_ledger_readable(self):
        # encoded() keeps U+2028, U+2029 and U+0085 unescaped; a JSONL row must not end there.
        separators = "First second third\u0085fourth."
        cited = self.evidence(self.inv, {"results": [[separators]]})
        self.assertIn(cited, [row["evidence_id"] for row in ledger._events(self.directory)])
        value = self.with_evidence(stage_findings())
        candidate = ledger.prepare_findings(self.root, self.inv, value)["candidate_sha256"]
        rows = [
            {
                **verdict(item["id"], "supported", [self.evidence(self.inv)]),
                "limitations": separators,
            }
            for item in value["claims"]
        ]
        self.assertTrue(
            ledger.submit_verification(self.root, self.inv, candidate, {"claims": rows})["valid"]
        )
        self.assertTrue(
            ledger.check_claims(self.root, self.inv, candidate_sha256=candidate)["valid"]
        )
        version = self.prepare({**RIGHT, "explanation": separators})
        self.submit(version, self.judgement(version), valid=True)
        self.assertTrue(self.check(version)["valid"])
        state = ledger.get_investigation(self.root, self.inv)
        self.assertEqual(state["report_verifications"][0]["version_sha256"], version)
        self.assertEqual(
            state["verifications"][-1]["verification"]["claims"][0]["limitations"], separators
        )
        self.assertEqual(len(state["report_acceptances"]), 1)

    def test_a_line_separator_cannot_turn_a_title_number_into_list_numbering(self):
        title = "Revenue 999. users churned"
        result = ledger.prepare_report(self.root, self.inv, {**WRONG, "title": title})
        self.assertEqual(result["unsupported"][0]["numbers"], [999.0])

    def test_every_example_quote_in_the_verifier_instructions_is_long_enough(self):
        quotes = re.findall(r'"quote": "([^"]*)"', ledger.REPORT_VERIFIER.read_text())
        self.assertTrue(quotes)
        for quote in quotes:
            self.assertGreaterEqual(len(quote), ledger.QUOTE_MIN, quote)

    def test_a_stated_stop_reason_is_checked_against_the_rule_of_the_recorded_reason(self):
        # The corpus case P05: the narrative explains the stop by the investigate skill's rule.
        # The verifier reads the rule of the recorded reason and cites the stop reason with the
        # claim that shows the cause, so a correct explanation can be supported and published.
        narrative = {
            **RIGHT,
            "explanation": "Остановка: INCONCLUSIVE, потому что часть ответа недоступна.",
        }
        # The rule follows the recorded reason, not one fixed text.
        self.publish_findings(self.with_evidence(stage_findings("BUDGET_EXHAUSTED")))
        budget = self.verifier_input(self.prepare(narrative))[1]["basis"]
        self.assertEqual(
            (budget["stop_reason"], budget["stop_rule"]),
            ("BUDGET_EXHAUSTED", ledger.STOP_RULES["BUDGET_EXHAUSTED"]),
        )
        self.publish_findings(self.with_evidence(stage_findings()))
        version = self.prepare(narrative)
        basis = self.verifier_input(version)[1]["basis"]
        self.assertEqual(
            (basis["stop_reason"], basis["stop_rule"]),
            ("INCONCLUSIVE", ledger.STOP_RULES["INCONCLUSIVE"]),
        )
        verification = self.judgement(version)
        stop = next(
            entry for entry in verification["blocks"] if entry["block_id"] == "explanation-1"
        )
        stop.update(
            statements=[
                "The investigation stopped as INCONCLUSIVE",
                "It stopped so because part of the answer is unavailable",
            ],
            basis=["stop_reason", "claim:unknown"],
            comparison="The stop reason is INCONCLUSIVE and its rule names an unavailable value.",
        )
        self.submit(version, verification, valid=True)
        self.assertTrue(self.check(version)["valid"])

    def test_stop_rules_cover_every_reason_in_the_words_of_the_investigate_skill(self):
        self.assertEqual(
            set(ledger.STOP_RULES),
            {"SUPPORTED", "REFUTED", "INCONCLUSIVE", "BUDGET_EXHAUSTED", "POLICY_BLOCKED"},
        )
        self.assertEqual(ledger.STOP_REASONS, set(ledger.STOP_RULES))
        skill = ledger.REPORT_VERIFIER.parents[1] / "skills/investigate"
        # The rule the author follows and the rule the verifier checks against must not drift.
        self.assertIn(
            "An answer that a value is unavailable ends `INCONCLUSIVE`.",
            (skill / "SKILL.md").read_text(),
        )
        self.assertTrue(
            ledger.STOP_RULES["INCONCLUSIVE"].startswith(
                "An answer that a value is unavailable ends INCONCLUSIVE"
            )
        )
        self.assertIn(
            "Use `INCONCLUSIVE` when evidence does not distinguish competing explanations.",
            (skill / "references/methods.md").read_text(),
        )
        self.assertIn(
            "evidence that does not distinguish competing explanations",
            ledger.STOP_RULES["INCONCLUSIVE"],
        )

    def test_the_verifier_instructions_give_the_stop_rule_and_the_verdict_of_a_note(self):
        text = ledger.REPORT_VERIFIER.read_text()
        for phrase in (
            "`stop_rule`",
            "(`stop_reason`)",
            "A statement of the stop reason, or of why the investigation stopped, is analytical.",
            "the stated cause is a condition of `stop_rule` that the basis shows to hold",
            "a cause that `stop_rule` does not name is unverified",
            "a note on how the report was written",
            "the verdict `supported`",
            "even when it reads like a note",
        ):
            self.assertIn(phrase, text)
        # The invented example obeys the gateway: every non_analytical entry is supported, every
        # basis reference is one the gateway accepts, and one entry cites the stop reason.
        example = json.loads(re.search(r"```json\n(.*?)\n```", text, re.S).group(1))
        self.assertEqual(
            {entry["kind"] for entry in example["blocks"]}, {"analytical", "non_analytical"}
        )
        for entry in example["blocks"]:
            if entry["kind"] == "non_analytical":
                self.assertEqual(entry["verdict"], "supported", entry)
            for ref in entry.get("basis", []):
                self.assertTrue(ref == "stop_reason" or ledger.BASIS.fullmatch(ref), ref)
        self.assertTrue(any("stop_reason" in entry.get("basis", []) for entry in example["blocks"]))


if __name__ == "__main__":
    unittest.main()

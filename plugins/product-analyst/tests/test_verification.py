"""Analysis context, candidate findings, verifier verdicts and the report check."""

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "server"))
import context
import ledger
from test_core import UNCERTAINTY

MANIFEST = """
schema_version = 1

[approvals.engagement]
by = "Metric owner"
on = "2026-10-07"
ref = "docs/metrics.md#engagement-definitions"
summary = "Engagement definitions."

[metrics.dau]
id = "posthog.engagement.dau"
version = "2026-10-07"
display_name = "Daily active users"
source = "posthog"
approval = "engagement"
unit = "distinct pseudonym"
population = "pseudonyms with a message_sent product event in the window"
exclusions = ["internal and unclassified events"]
numerator = "not applicable"
denominator = "not applicable"
window = "[cutoff - 1 day, cutoff)"
cutoff = "daily 00:00 UTC"
deduplication = "a pseudonym counts once per window"
empty_result = "0 active users"
docs = ["docs/metrics.md#engagement-definitions"]
query = "tools/queries.py#dau_sql"

[statements.attribution_unavailable]
text = "No funnel visit reaches the app's sign-up, so new accounts have no source."
refs = ["docs/metrics.md#attribution"]
"""
STATEMENT = "No funnel visit reaches the app's sign-up, so new accounts have no source."
CONTRACT = {
    "metric": "dau",
    "metric_version": "2026-10-07",
    "population": "product pseudonyms",
    "window": {"start": "2026-10-05T00:00:00+00:00", "end": "2026-10-06T00:00:00+00:00"},
    "timezone": "UTC",
    "comparison": "none",
}


def claim(claim_id, text, evidence_ids=(), **extra):
    return {
        "id": claim_id,
        "text": text,
        "evidence_ids": list(evidence_ids),
        "uncertainty": UNCERTAINTY,
        **extra,
    }


def findings(*claims, stop_reason="SUPPORTED"):
    return {"claims": list(claims), "stop_reason": stop_reason, "uncertainty": UNCERTAINTY}


def verdict(claim_id, value, evidence_ids=()):
    return {
        "claim_id": claim_id,
        "verdict": value,
        "evidence_ids": list(evidence_ids),
        "method": "Independent count.",
        "limitations": "",
    }


class ProjectTestCase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        (self.root / ".analyst").mkdir()
        (self.root / ".analyst/config.toml").write_text(
            '[postgres]\nservice="analyst"\nschemas=["analytics"]\n'
        )
        (self.root / "docs").mkdir()
        (self.root / "docs/metrics.md").write_text(
            "# Metrics\n\n## Engagement definitions\n\nDAU counts.\n\n```sh\n# Offline only\n```\n\n## Attribution\n\nNone.\n"
        )
        (self.root / "tools").mkdir()
        (self.root / "tools/queries.py").write_text(
            'def dau_sql() -> str:\n    return "SELECT 1"\n'
        )
        (self.root / ".analyst/context.toml").write_text(MANIFEST)

    def start(self, contract=CONTRACT):
        return ledger.start(self.root, contract, "session")["investigation_id"]

    def evidence(self, inv, result=None):
        eid = ledger.reserve(self.root, inv, "posthog", {"tool": "execute-sql"}, 60)
        ledger.complete(self.root, inv, eid, result or {"results": [[1]]})
        return eid


class ContextTests(ProjectTestCase):
    def test_manifest_loads_with_hashes_of_every_referenced_file(self):
        loaded = context.load(self.root)
        self.assertEqual(set(loaded["sources"]), {"docs/metrics.md", "tools/queries.py"})
        self.assertEqual(
            context.describe(self.root, "posthog.engagement.dau")["metrics"].keys(), {"dau"}
        )
        with self.assertRaisesRegex(ValueError, "available: dau"):
            context.describe(self.root, "wau")

    def test_missing_source_or_anchor_is_an_explicit_error(self):
        for old, new, message in (
            ("tools/queries.py#dau_sql", "tools/missing.py#dau_sql", "does not exist"),
            ("tools/queries.py#dau_sql", "tools/queries.py#wau_sql", "anchor #wau_sql"),
            ("docs/metrics.md#attribution", "docs/metrics.md#offline-only", "anchor #offline"),
            ("docs/metrics.md#attribution", "../outside.md", "inside the project"),
            ('approval = "engagement"', 'approval = "nobody"', "names no"),
            ("schema_version = 1", "schema_version = true", "schema_version must be 1"),
        ):
            with self.subTest(new=new):
                (self.root / ".analyst/context.toml").write_text(MANIFEST.replace(old, new))
                with self.assertRaisesRegex(ValueError, message):
                    context.load(self.root)
                with self.assertRaisesRegex(ValueError, message):
                    ledger.start(self.root, CONTRACT, "session")

    def test_project_without_manifest_has_no_context(self):
        (self.root / ".analyst/context.toml").unlink()
        self.assertIsNone(context.load(self.root))
        with self.assertRaisesRegex(ValueError, "No analysis context"):
            context.describe(self.root)
        inv = self.start()
        self.assertIsNone(ledger.get_investigation(self.root, inv)["context"])

    def test_contract_version_must_match_the_manifest(self):
        with self.assertRaisesRegex(ValueError, "metric_version must be '2026-10-07'"):
            self.start({**CONTRACT, "metric_version": "1"})

    def test_investigation_keeps_the_context_it_started_with(self):
        inv = self.start()
        snapshot = ledger.get_investigation(self.root, inv)["context"]
        self.assertEqual(snapshot, context.load(self.root))
        (self.root / "docs/metrics.md").write_text(
            "# Metrics\n\n## Engagement definitions\n\nDAU changed.\n\n## Attribution\n"
        )
        with self.assertRaisesRegex(ValueError, "analysis context changed"):
            ledger.reserve(self.root, inv, "posthog", {"tool": "execute-sql"}, 60)
        self.assertEqual(ledger.get_investigation(self.root, inv)["context"], snapshot)


class VerificationTests(ProjectTestCase):
    def setUp(self):
        super().setUp()
        self.inv = self.start()
        self.primary = self.evidence(self.inv, {"results": [[1]]})
        self.findings = findings(claim("dau", "DAU on 2026-10-05 was 1.", [self.primary]))

    def prepare(self, value=None):
        result = ledger.prepare_findings(self.root, self.inv, value or self.findings)
        self.assertTrue(result["valid"], result)
        return result["candidate_sha256"]

    def verify(self, candidate, *verdicts):
        return ledger.submit_verification(
            self.root, self.inv, candidate, {"claims": list(verdicts)}
        )

    def publish(self, candidate=None):
        return ledger.check_claims(self.root, self.inv, candidate_sha256=candidate)

    def verified(self, value=None):
        """A candidate supported by evidence the verifier recorded after preparing it."""
        candidate = self.prepare(value)
        independent = self.evidence(self.inv)
        result = self.verify(candidate, verdict("dau", "supported", [independent]))
        self.assertTrue(result["valid"], result)
        return candidate

    def test_claims_without_a_verifier_cannot_be_published(self):
        result = self.publish(self.prepare())
        self.assertFalse(result["valid"])
        self.assertIn("No verification", result["errors"][0])

    def test_unknown_or_changed_candidate_is_rejected(self):
        candidate = self.verified()
        self.assertIn("Unknown candidate", self.publish("0" * 64)["errors"][0])
        self.assertIn("Unknown candidate", self.verify("0" * 64)["errors"][0])
        changed = self.prepare(findings(claim("dau", "DAU on 2026-10-05 was 2.", [self.primary])))
        self.assertIn("No verification", self.publish(changed)["errors"][0])
        self.assertIn("No verification", self.publish()["errors"][0])
        self.assertTrue(self.publish(candidate)["valid"])

    def test_re_preparing_a_candidate_makes_it_the_latest(self):
        candidate = self.verified()
        self.prepare(findings(claim("dau", "DAU on 2026-10-05 was 2.", [self.primary])))
        self.prepare()
        self.assertTrue(self.publish()["valid"])
        self.assertEqual(
            ledger.get_investigation(self.root, self.inv)["findings"]["candidate_sha256"], candidate
        )

    def test_a_candidate_is_verified_once(self):
        candidate = self.verified()
        later = self.evidence(self.inv)
        again = self.verify(candidate, verdict("dau", "refuted", [later]))
        self.assertIn("already verified", again["errors"][0])

    def test_context_change_after_verification_blocks_publication(self):
        candidate = self.verified()
        (self.root / "tools/queries.py").write_text(
            'def dau_sql() -> str:\n    return "SELECT 2"\n'
        )
        result = self.publish(candidate)
        self.assertFalse(result["valid"])
        self.assertIn("analysis context changed", " ".join(result["errors"]))

    def test_evidence_from_another_investigation_is_refused(self):
        other = self.start()
        foreign = self.evidence(other)
        stolen = findings(claim("dau", "DAU on 2026-10-05 was 1.", [foreign]))
        self.assertFalse(ledger.prepare_findings(self.root, self.inv, stolen)["valid"])
        candidate = self.prepare()
        result = self.verify(candidate, verdict("dau", "supported", [foreign]))
        self.assertFalse(result["valid"])
        self.assertIn("evidence of this investigation", result["errors"][0])

    def test_supported_needs_evidence_recorded_after_the_candidate_and_cited_by_no_claim(self):
        exploratory = self.evidence(self.inv)
        second = self.evidence(self.inv)
        two = findings(
            claim("dau", "DAU on 2026-10-05 was 1.", [self.primary]),
            claim("note", "One pseudonym was active.", [second]),
        )
        candidate = self.prepare(two)
        swapped = self.verify(
            candidate,
            verdict("dau", "supported", [second]),
            verdict("note", "supported", [exploratory]),
        )
        self.assertEqual(sum("independent re-derivation" in e for e in swapped["errors"]), 2)
        missing = self.verify(candidate, verdict("dau", "unverified"))
        self.assertIn("Missing verdicts for claims: note", missing["errors"])

    def test_wrong_number_with_valid_citation_is_published_only_as_refuted(self):
        wrong = findings(claim("dau", "DAU on 2026-10-05 was 3.", [self.primary]))
        candidate = self.prepare(wrong)
        check = self.evidence(self.inv)
        self.assertTrue(self.verify(candidate, verdict("dau", "refuted", [check]))["valid"])
        blocked = self.publish(candidate)
        self.assertIn("no refuted claim", blocked["errors"][0])
        honest = self.prepare({**wrong, "stop_reason": "INCONCLUSIVE"})
        self.verify(honest, verdict("dau", "refuted", [check]))
        result = self.publish(honest)
        self.assertTrue(result["valid"], result)
        published = ledger.get_investigation(self.root, self.inv)["findings"]
        self.assertEqual(published["claims"][0]["verdict"]["verdict"], "refuted")
        self.assertEqual(published["candidate_sha256"], honest)

    def test_supported_stop_needs_a_supported_data_claim(self):
        mixed = findings(
            claim("dau", "DAU on 2026-10-05 was 3.", [self.primary]),
            claim(
                "source",
                STATEMENT,
                kind="context",
                context_refs=["attribution_unavailable"],
            ),
        )
        candidate = self.prepare(mixed)
        check = self.evidence(self.inv)
        self.verify(
            candidate, verdict("dau", "unverified", [check]), verdict("source", "supported")
        )
        self.assertIn("a data claim the verifier supported", self.publish(candidate)["errors"][0])

    def test_budget_exhaustion_allows_an_honest_unverified_result(self):
        candidate = self.prepare({**self.findings, "stop_reason": "BUDGET_EXHAUSTED"})
        self.verify(candidate, verdict("dau", "unverified"))
        self.assertTrue(self.publish(candidate)["valid"])

    def test_context_claims_cite_named_statements_and_no_evidence(self):
        unavailable = findings(
            claim(
                "source",
                STATEMENT,
                kind="context",
                context_refs=["attribution_unavailable"],
            ),
            stop_reason="INCONCLUSIVE",
        )
        candidate = self.prepare(unavailable)
        self.verify(candidate, verdict("source", "supported"))
        self.assertTrue(self.publish(candidate)["valid"])
        for bad in (
            claim("source", "Unavailable.", kind="context", context_refs=["no_such_statement"]),
            claim(
                "invented",
                "DAU — 999999, retention — 100%",
                kind="context",
                context_refs=["attribution_unavailable"],
            ),
            claim(
                "dau",
                "DAU was 1234.",
                [self.primary],
                kind="context",
                context_refs=["attribution_unavailable"],
            ),
            claim("dau", "DAU was 1.", [self.primary], kind=["data"]),
        ):
            with self.subTest(claim=bad):
                self.assertFalse(
                    ledger.prepare_findings(self.root, self.inv, findings(bad))["valid"]
                )

    def test_malformed_verdicts_return_errors(self):
        candidate = self.prepare()
        result = self.verify(candidate, {**verdict("dau", "supported"), "claim_id": ["dau"]})
        self.assertFalse(result["valid"])
        result = self.verify(candidate, {**verdict("dau", "x"), "verdict": ["supported"]})
        self.assertFalse(result["valid"])

    def test_report_numbers_must_come_from_published_findings(self):
        candidate = self.verified(
            findings(claim("dau", "DAU on 2026-10-05 was 1.\nRetention: 12.5%.", [self.primary]))
        )
        self.assertIn("not published", ledger.check_report(self.root, self.inv)["errors"][0])
        self.publish(candidate)
        path = self.root / ".analyst/investigations" / self.inv / "report.md"
        path.write_text(
            "# DAU was 1 on 2026-10-05\n\n1. Evidence: `"
            + self.primary
            + "`, window ends 2026-10-06T00:00:00+00:00 at 00:00 UTC; retention 12.5%.\n\n"
            + "```sql\nSELECT count() FROM events\nLIMIT 500\n```\n\nSee 5 октября 2026.\n"
        )
        self.assertTrue(ledger.check_report(self.root, self.inv)["valid"])
        path.write_text("# DAU was 1 on 2026-10-05\n\nToday so far adds 2 more users.\n")
        result = ledger.check_report(self.root, self.inv)
        self.assertFalse(result["valid"])
        self.assertEqual(
            result["unsupported"],
            [{"line": 3, "numbers": [2.0], "text": "Today so far adds 2 more users."}],
        )

    def test_findings_name_their_prepared_candidate(self):
        candidate = self.verified()
        self.assertTrue(ledger.check_claims(self.root, self.inv, self.findings)["valid"])
        other = findings(claim("dau", "DAU on 2026-10-05 was 2.", [self.primary]))
        self.assertIn(
            "Unknown candidate", ledger.check_claims(self.root, self.inv, other)["errors"][0]
        )
        mismatch = ledger.check_claims(self.root, self.inv, other, candidate_sha256=candidate)
        self.assertIn("different candidates", mismatch["errors"][0])

    def test_context_claim_uncertainty_adds_no_reportable_number(self):
        quiet = {**UNCERTAINTY, "magnitude": "Retention would be 100% if counted."}
        unavailable = findings(
            claim("source", STATEMENT, kind="context", context_refs=["attribution_unavailable"]),
            stop_reason="INCONCLUSIVE",
        )
        unavailable["claims"][0]["uncertainty"] = quiet
        candidate = self.prepare(unavailable)
        self.verify(candidate, verdict("source", "supported"))
        self.publish(candidate)
        path = self.root / ".analyst/investigations" / self.inv / "report.md"
        path.write_text("# Source is unavailable\n\nRetention is 100%.\n")
        self.assertEqual(
            ledger.check_report(self.root, self.inv)["unsupported"][0]["numbers"], [100.0]
        )

    def test_get_investigation_exposes_candidates_and_verdicts(self):
        candidate = self.verified()
        state = ledger.get_investigation(self.root, self.inv)
        self.assertEqual([row["candidate_sha256"] for row in state["candidates"]], [candidate])
        self.assertEqual(
            state["verifications"][0]["verification"]["claims"][0]["verdict"], "supported"
        )
        self.assertEqual(state["context"]["metrics"]["dau"]["version"], "2026-10-07")


if __name__ == "__main__":
    unittest.main()

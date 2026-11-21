from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from harmony360_orchestration.core_bridge import CoreBridge
from harmony360_orchestration.doctor import inspect_versions
from harmony360_orchestration.jsonutil import digest, strict_loads
from harmony360_orchestration.orchestration import ActionDenied, CrewAIAdapter, EvidenceJournal, GovernedOrchestrator, prepare_request


class LocalAdapter:
    """A test double. Never claims a live CrewAI or model run."""
    def __init__(self, name="local-test"):
        self.calls, self.name = [], name

    def manifest(self):
        return {"adapter": self.name, "tools": [], "model_calls": False}

    def kickoff(self, inputs):
        self.calls.append(inputs)
        return "local fixture output"


class TestHostVerifier:
    """Test-only host authentication double with one consumed request hash."""
    def __init__(self, request_hash):
        self.request_hash, self.used = request_hash, False

    def consume(self, *, approval_id, action, request_sha256):
        if self.used or approval_id != "test-token" or action != "crewai.kickoff" or request_sha256 != self.request_hash:
            return False
        self.used = True
        return True


class GovernanceTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.core = CoreBridge()
        self.journal = EvidenceJournal(self.root / "events.sqlite3")
        self.adapter = LocalAdapter()
        self.inputs = {"task": "synthetic local test", "secret": "do-not-log-this"}
        self.request_hash = digest(prepare_request(self.adapter, self.inputs))

    def tearDown(self):
        self.journal.close()
        self.tmp.cleanup()

    def runner(self):
        return GovernedOrchestrator(self.core, self.journal, TestHostVerifier(self.request_hash))

    def test_default_denial_never_calls_adapter(self):
        runner = GovernedOrchestrator(self.core, self.journal)
        with self.assertRaises(ActionDenied):
            runner.execute(self.adapter, self.inputs)
        self.assertEqual(self.adapter.calls, [])
        self.assertEqual(self.journal.verify()["events"], 1)

    def test_request_and_adapter_binding(self):
        runner = self.runner()
        for adapter, inputs in [(self.adapter, {"task": "changed"}), (LocalAdapter("changed-plan"), self.inputs)]:
            with self.assertRaises(ActionDenied):
                runner.execute(adapter, inputs, approval_id="test-token")
            self.assertEqual(adapter.calls, [])

    def test_one_time_approval_and_hash_only_logging(self):
        runner = self.runner()
        receipt = runner.execute(self.adapter, self.inputs, approval_id="test-token")
        self.assertFalse(receipt["canonical_authority_granted"])
        self.assertEqual(len(self.adapter.calls), 1)
        with self.assertRaises(ActionDenied):
            runner.execute(self.adapter, self.inputs, approval_id="test-token")
        self.assertEqual(len(self.adapter.calls), 1)
        all_bodies = " ".join(x[0] for x in self.journal.db.execute("SELECT body FROM events"))
        self.assertNotIn("do-not-log-this", all_bodies)
        self.assertNotIn("test-token", all_bodies)

    def test_journal_tampering_blocks_execution(self):
        self.journal.append({"initial": True})
        with self.journal.db:
            self.journal.db.execute("UPDATE events SET hash='tampered'")
        with self.assertRaisesRegex(ValueError, "integrity"):
            self.runner().execute(self.adapter, self.inputs, approval_id="test-token")
        self.assertEqual(self.adapter.calls, [])

    def test_adapter_failure_is_logged_without_exception_secret(self):
        class Fails(LocalAdapter):
            def kickoff(self, inputs):
                raise RuntimeError("do-not-log-this")
        adapter = Fails()
        with self.assertRaises(RuntimeError):
            self.runner().execute(adapter, self.inputs, approval_id="test-token")
        body = self.journal.db.execute("SELECT body FROM events ORDER BY sequence DESC LIMIT 1").fetchone()[0]
        self.assertEqual(strict_loads(body)["event"]["outcome"], "FAILED")
        self.assertNotIn("do-not-log-this", body)

    def test_existing_core_math_and_codec_are_actually_called(self):
        diagnostics = self.core.analyze([1.0, 2.0, 3.0])
        self.assertAlmostEqual(diagnostics["dispersion_coherence"], self.core.core.coherence_score([1, 2, 3]))
        self.assertEqual(diagnostics["resonance_calibration"][0], 3.0)
        path = self.root / "test.har360"
        payload = {"diagnostics": diagnostics, "canonical_authority_granted": False}
        checksum = self.core.seal(payload, path)
        self.assertEqual(self.core.reconstruct(path, expected_sha256=checksum), payload)
        path.write_bytes(path.read_bytes() + b" ")
        with self.assertRaisesRegex(ValueError, "before decoding"):
            self.core.reconstruct(path, expected_sha256=checksum)

    def test_invalid_numbers_fail_before_core_calculation(self):
        for values in ([], [float("nan")], [float("inf")], [True]):
            with self.assertRaises(ValueError):
                self.core.analyze(values)

    def test_security_floor_inventory_and_prerelease_rejection(self):
        report = inspect_versions({"crewai": "1.15.30", "crewai-files": "1.15.44rc1", "crewai-tools": "1.15.31"})
        statuses = {r["package"]: r["status"] for r in report["findings"]}
        self.assertEqual(statuses["crewai"], "BELOW_PATCH_FLOOR")
        self.assertEqual(statuses["crewai-files"], "BELOW_PATCH_FLOOR")
        self.assertEqual(statuses["crewai-tools"], "PATCH_FLOOR_MET")
        self.assertEqual(report["live_crewai_compatibility"], "NOT_VALIDATED")

    def test_candidate_pydantic_conflict_blocks_adapter(self):
        report = inspect_versions({"crewai": "1.15.44", "pydantic": "2.13.4"})
        with patch("harmony360_orchestration.orchestration.inspect_versions", return_value=report):
            with self.assertRaisesRegex(ActionDenied, "Pydantic"):
                CrewAIAdapter(object(), reviewed_plan={"tools": []})

    def test_crewai_signature_and_raw_result_contract_with_local_double(self):
        class Crew:
            def kickoff(self, *, inputs):
                self.received = inputs
                return type("LocalOutput", (), {"raw": "local output"})()
        crew = Crew()
        report = inspect_versions({"crewai": "1.15.44", "pydantic": "2.12.0"})
        with patch("harmony360_orchestration.orchestration.inspect_versions", return_value=report):
            adapter = CrewAIAdapter(crew, reviewed_plan={"tools": [], "model": "local-test-double"})
        self.assertEqual(adapter.kickoff({"topic": "local test"}), "local output")
        self.assertEqual(crew.received, {"topic": "local test"})
        self.assertEqual(adapter.manifest()["reviewed_plan"]["tools"], [])


if __name__ == "__main__":
    unittest.main()


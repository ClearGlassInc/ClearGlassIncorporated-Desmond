import copy
import importlib.util
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("clearway_agent", ROOT / "agent.py")
if spec is None or spec.loader is None:
    raise RuntimeError("unable to load Clearway agent module")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class TestClearway(unittest.TestCase):
    def load_fixture(self):
        payload = json.loads((ROOT / "example_audit.json").read_text(encoding="utf-8"))
        policy = json.loads((ROOT / "policy.json").read_text(encoding="utf-8"))
        return payload, policy

    def test_pass_fixture_is_reproducible(self):
        payload, policy = self.load_fixture()
        first = module.audit(payload, policy)
        second = module.audit(copy.deepcopy(payload), policy)
        self.assertEqual(first["gate"]["decision"], "PASS")
        self.assertEqual(first["evidence_sha256"], second["evidence_sha256"])
        self.assertEqual(first["score"]["overall_compliance_score"], 100)

    def test_unverified_high_risk_blocks(self):
        payload, policy = self.load_fixture()
        payload["domains"]["security"]["status"] = "FAIL"
        payload["domains"]["security"]["findings"] = [{
            "finding_id": "SEC-001",
            "timestamp": "2026-08-21T00:00:00Z",
            "source": "fixture",
            "source_type": "test",
            "evidence_location": "fixture://security/001",
            "risk_level": "CRITICAL",
            "confidence": 95,
            "verification_status": "UNVERIFIED",
            "summary": "Unverified critical security finding",
            "remediation": "Verify and remediate before release."
        }]
        report = module.audit(payload, policy)
        self.assertEqual(report["gate"]["decision"], "BLOCK")
        self.assertTrue(any("UNVERIFIED" in reason for reason in report["gate"]["reasons"]))

    def test_ai_provenance_is_required(self):
        payload, policy = self.load_fixture()
        payload["domains"]["ai_governance"]["outputs"] = [{"classification": "VERIFIED FACT"}]
        report = module.audit(payload, policy)
        self.assertEqual(report["gate"]["decision"], "BLOCK")
        self.assertTrue(any("provenance" in error for error in report["errors"]))

    def test_missing_evidence_fields_are_rejected(self):
        payload, policy = self.load_fixture()
        payload["domains"]["privacy"]["findings"] = [{"finding_id": "PRIV-001"}]
        report = module.audit(payload, policy)
        self.assertEqual(report["gate"]["decision"], "BLOCK")
        self.assertTrue(report["errors"])


if __name__ == "__main__":
    unittest.main()

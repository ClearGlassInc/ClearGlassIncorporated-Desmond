import copy
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("clearway_agent", ROOT / "agent.py")
assert spec and spec.loader
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class TestClearway:
    def test_pass_fixture_is_reproducible(self):
        payload = json.loads((ROOT / "example_audit.json").read_text(encoding="utf-8"))
        policy = json.loads((ROOT / "policy.json").read_text(encoding="utf-8"))
        first = module.audit(payload, policy)
        second = module.audit(payload, policy)
        assert first["gate"]["decision"] == "PASS"
        assert first["evidence_sha256"] == second["evidence_sha256"]
        assert first["score"]["overall_compliance_score"] == 100

    def test_unverified_high_risk_blocks(self):
        payload = json.loads((ROOT / "example_audit.json").read_text(encoding="utf-8"))
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
        policy = json.loads((ROOT / "policy.json").read_text(encoding="utf-8"))
        report = module.audit(payload, policy)
        assert report["gate"]["decision"] == "BLOCK"
        assert any("UNVERIFIED" in reason for reason in report["gate"]["reasons"])

    def test_ai_provenance_is_required(self):
        payload = json.loads((ROOT / "example_audit.json").read_text(encoding="utf-8"))
        payload["domains"]["ai_governance"]["outputs"] = [{"classification": "VERIFIED FACT"}]
        policy = json.loads((ROOT / "policy.json").read_text(encoding="utf-8"))
        report = module.audit(payload, policy)
        assert report["gate"]["decision"] == "BLOCK"
        assert any("provenance" in error for error in report["errors"])

    def test_missing_evidence_fields_are_rejected(self):
        payload = json.loads((ROOT / "example_audit.json").read_text(encoding="utf-8"))
        payload["domains"]["privacy"]["findings"] = [{"finding_id": "PRIV-001"}]
        policy = json.loads((ROOT / "policy.json").read_text(encoding="utf-8"))
        report = module.audit(payload, policy)
        assert report["gate"]["decision"] == "BLOCK"
        assert report["errors"]

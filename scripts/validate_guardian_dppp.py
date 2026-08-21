#!/usr/bin/env python3
"""Validate the Guardian Digital Presence Protection Program policy.

This validator is intentionally dependency-free and fail-closed. It validates the
machine policy contract, hashes the policy bytes, and checks for unsafe defaults.
It does not perform network collection or external mutation.
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
POLICY_PATH = ROOT / "config" / "guardian" / "dppp.json"

REQUIRED_TOP_LEVEL = {
    "program",
    "assurance",
    "epistemic_classes",
    "severity_classes",
    "agents",
    "verification_gate",
    "risk_policy",
    "response_policy",
    "fail_closed",
    "evidence",
    "monitoring",
    "compliance_controls",
    "reporting",
    "lifecycle",
}
REQUIRED_EPISTEMIC = {
    "VERIFIED FACT",
    "INFERENCE",
    "ASSUMPTION",
    "UNKNOWN",
    "UNVERIFIED",
}
REQUIRED_SEVERITIES = {"INFORMATIONAL", "LOW", "MEDIUM", "HIGH", "CRITICAL"}
REQUIRED_FAIL_CLOSED = {
    "missing_policy": "DENY",
    "missing_authorization": "DENY",
    "expired_authorization": "DENY",
    "integrity_check_failure": "DENY",
    "schema_validation_failure": "DENY",
    "emergency_stop": "DENY",
}


def fail(message: str) -> None:
    print(f"FAIL: {message}", file=sys.stderr)
    raise SystemExit(1)


def require(condition: bool, message: str) -> None:
    if not condition:
        fail(message)


def main() -> int:
    require(POLICY_PATH.is_file(), f"missing policy: {POLICY_PATH}")

    raw = POLICY_PATH.read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    print(f"policy_path={POLICY_PATH.relative_to(ROOT)}")
    print(f"policy_sha256={digest}")

    try:
        data: Any = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        fail(f"invalid JSON: {exc}")

    require(isinstance(data, dict), "policy root must be an object")
    missing = REQUIRED_TOP_LEVEL - set(data)
    require(not missing, f"missing top-level keys: {sorted(missing)}")

    program = data["program"]
    require(program.get("id") == "guardian-dppp", "unexpected program id")
    require(program.get("mode") == "PROTECTION", "Guardian DPPP must run in PROTECTION mode")
    require(program.get("default_decision") == "DENY", "default decision must be DENY")

    assurance = data["assurance"]
    require(assurance.get("mutation_default") == "DENY", "mutation default must be DENY")
    require(assurance.get("external_action_default") == "REVIEW", "external action default must be REVIEW")
    require(assurance.get("evidence_required_for_significant_findings") is True,
            "significant findings must require evidence")
    require(assurance.get("dual_classification_required") is True,
            "dual classification must be enabled")

    require(REQUIRED_EPISTEMIC.issubset(set(data["epistemic_classes"])),
            "epistemic taxonomy is incomplete")
    require(REQUIRED_SEVERITIES.issubset(set(data["severity_classes"])),
            "severity taxonomy is incomplete")

    fail_closed = data["fail_closed"]
    for key, expected in REQUIRED_FAIL_CLOSED.items():
        require(fail_closed.get(key) == expected, f"fail-closed control {key} must be {expected}")
    require(fail_closed.get("unverified_high_impact_action") == "REVIEW",
            "unverified high-impact actions must require REVIEW")

    evidence = data["evidence"]
    require(evidence.get("digest_algorithm") == "SHA-256", "evidence digest must use SHA-256")
    require(evidence.get("chain_integrity") is True, "evidence chain integrity must be enabled")
    require(evidence.get("minimize_personal_data") is True,
            "personal-data minimization must be enabled")

    risk_policy = data["risk_policy"]
    require(risk_policy.get("opaque_scoring_forbidden") is True,
            "opaque risk scoring must be forbidden")
    require(risk_policy.get("critical_requires_human_review") is True,
            "critical findings must require human review")

    response_policy = data["response_policy"]
    required_external = {
        "EXTERNAL_TAKEDOWN",
        "EXTERNAL_LISTING_MODIFICATION",
        "ACCOUNT_OWNERSHIP_CHANGE",
        "DNS_CHANGE",
        "PRODUCTION_CREDENTIAL_ROTATION",
        "PUBLIC_STATEMENT",
        "EXTERNAL_CONTENT_DELETION",
        "LEGAL_ESCALATION",
        "LAW_ENFORCEMENT_CONTACT",
    }
    require(required_external.issubset(set(response_policy.get("human_authorization_required", []))),
            "external-impact actions must remain human-authorized")

    agents = data["agents"]
    require(len(agents) == 7, "Guardian DPPP requires exactly seven declared protection agents")
    agent_ids = {agent.get("id") for agent in agents}
    require(
        agent_ids
        == {
            "AssetRecon",
            "ThreatIntel",
            "ReputationGuard",
            "IntegrityAuditor",
            "ComplianceGuard",
            "ExposureRiskAnalyzer",
            "IncidentCoordinator",
        },
        "protection-agent set does not match the DPPP contract",
    )

    print("PASS: Guardian DPPP policy is structurally valid and fail-closed.")
    print(f"agents={len(agents)}")
    print(f"severity_classes={len(data['severity_classes'])}")
    print(f"epistemic_classes={len(data['epistemic_classes'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

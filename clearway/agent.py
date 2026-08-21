from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

WEIGHTS = {
    "privacy": 0.20,
    "security": 0.20,
    "platform_policy": 0.15,
    "gbp": 0.15,
    "casl": 0.10,
    "accessibility": 0.10,
    "ai_governance": 0.10,
}
VALID_STATUSES = {"PASS", "FAIL", "REVIEW"}
VALID_RISKS = {"LOW", "MEDIUM", "HIGH", "CRITICAL"}
VALID_VERIFICATION = {"VERIFIED", "PARTIALLY VERIFIED", "UNVERIFIED", "FALSE POSITIVE"}
EPISTEMIC = {
    "OBSERVATION",
    "VERIFIED FACT",
    "DERIVED METRIC",
    "MODEL ESTIMATE",
    "INFERENCE",
    "ASSUMPTION",
    "RECOMMENDATION",
    "UNKNOWN",
}


@dataclass(frozen=True)
class Finding:
    finding_id: str
    timestamp: str
    source: str
    source_type: str
    evidence_location: str
    risk_level: str
    confidence: int
    verification_status: str
    summary: str
    remediation: str = ""
    executive_review_required: bool = False


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def sha256(value: Any) -> str:
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def load_policy(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def parse_finding(raw: dict[str, Any]) -> Finding:
    required = [
        "finding_id", "timestamp", "source", "source_type", "evidence_location",
        "risk_level", "confidence", "verification_status", "summary"
    ]
    missing = [key for key in required if not raw.get(key)]
    if missing:
        raise ValueError(f"finding missing required evidence fields: {missing}")
    risk = str(raw["risk_level"]).upper()
    verification = str(raw["verification_status"]).upper()
    confidence = int(raw["confidence"])
    if risk not in VALID_RISKS:
        raise ValueError(f"invalid risk_level: {risk}")
    if verification not in VALID_VERIFICATION:
        raise ValueError(f"invalid verification_status: {verification}")
    if not 0 <= confidence <= 100:
        raise ValueError("confidence must be 0..100")
    return Finding(
        finding_id=str(raw["finding_id"]),
        timestamp=str(raw["timestamp"]),
        source=str(raw["source"]),
        source_type=str(raw["source_type"]),
        evidence_location=str(raw["evidence_location"]),
        risk_level=risk,
        confidence=confidence,
        verification_status=verification,
        summary=str(raw["summary"]),
        remediation=str(raw.get("remediation", "")),
        executive_review_required=bool(raw.get("executive_review_required", False)),
    )


def validate_domain(domain_name: str, domain: dict[str, Any]) -> tuple[list[Finding], list[str]]:
    errors: list[str] = []
    findings: list[Finding] = []
    status = str(domain.get("status", "REVIEW")).upper()
    if status not in VALID_STATUSES:
        errors.append(f"{domain_name}: invalid status {status}")
    raw_findings = domain.get("findings", domain.get("violations", []))
    if not isinstance(raw_findings, list):
        errors.append(f"{domain_name}: findings/violations must be a list")
        return findings, errors
    for raw in raw_findings:
        try:
            finding = parse_finding(raw)
            findings.append(finding)
        except (TypeError, ValueError, KeyError) as exc:
            errors.append(f"{domain_name}: {exc}")
    return findings, errors


def domain_score(domain: dict[str, Any]) -> int:
    status = str(domain.get("status", "REVIEW")).upper()
    if status == "PASS":
        return 100
    if status == "FAIL":
        return 0
    return 50


def audit(payload: dict[str, Any], policy: dict[str, Any]) -> dict[str, Any]:
    findings: list[Finding] = []
    errors: list[str] = []
    domains = payload.get("domains", {})

    for name in WEIGHTS:
        domain = domains.get(name, {"status": "REVIEW", "findings": []})
        domain_findings, domain_errors = validate_domain(name, domain)
        findings.extend(domain_findings)
        errors.extend(domain_errors)

    ai_items = domains.get("ai_governance", {}).get("outputs", [])
    for item in ai_items:
        label = str(item.get("classification", "UNKNOWN")).upper()
        if label not in EPISTEMIC:
            errors.append(f"ai_governance: invalid epistemic label {label}")
        if label != "ASSUMPTION" and not item.get("provenance"):
            errors.append("ai_governance: output lacks provenance")

    weighted = sum(domain_score(domains.get(name, {"status": "REVIEW"})) * weight for name, weight in WEIGHTS.items())
    score = int(round(weighted))

    high_risk = [f for f in findings if f.risk_level in {"HIGH", "CRITICAL"}]
    unverified_high = [f for f in high_risk if f.verification_status == "UNVERIFIED"]
    executive_items = [f for f in findings if f.executive_review_required]
    evidence_complete = bool(payload.get("evidence_register_complete", False)) and not errors
    rollback_verified = str(payload.get("rollback_plan", "UNKNOWN")).upper() == "VERIFIED"
    security_pass = str(domains.get("security", {}).get("status", "REVIEW")).upper() == "PASS"
    compliance_pass = score >= int(policy.get("minimum_pass_score", 90)) and not high_risk

    gate_reasons: list[str] = []
    if not security_pass:
        gate_reasons.append("security review is not PASS")
    if not compliance_pass:
        gate_reasons.append("compliance review is not PASS")
    if not evidence_complete:
        gate_reasons.append("evidence is incomplete or structurally invalid")
    if not rollback_verified:
        gate_reasons.append("rollback plan is not VERIFIED")
    if unverified_high:
        gate_reasons.append("HIGH/CRITICAL finding remains UNVERIFIED")
    if executive_items and not payload.get("executive_approval", False):
        gate_reasons.append("executive review is required but not acknowledged")

    decision = "PASS" if not gate_reasons else "BLOCK"
    generated = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    evidence_items = [
        {
            "finding_id": f.finding_id,
            "timestamp": f.timestamp,
            "source": f.source,
            "source_type": f.source_type,
            "evidence_location": f.evidence_location,
            "risk_level": f.risk_level,
            "confidence": f.confidence,
            "verification_status": f.verification_status,
        }
        for f in findings
    ]
    evidence_digest = sha256(evidence_items)
    overall = {
        "overall_compliance_score": score,
        "status": decision,
        "high_risk_findings": len(high_risk),
        "medium_risk_findings": sum(f.risk_level == "MEDIUM" for f in findings),
        "next_review_date": payload.get("next_review_date", ""),
    }
    report = {
        "agent": "Clearway",
        "version": "1.0.0",
        "generated_utc": generated,
        "mission": "continuous compliance assurance",
        "governance": ["ClearGlass Governance Standards", "ARTEMIS", "ARTEMIS FAWL", "AEGIS"],
        "authority": {
            "can_block_deployment": True,
            "can_modify_production": False,
            "can_approve_itself": False,
            "can_override_governance": False,
        },
        "score": overall,
        "gate": {
            "decision": decision,
            "security_review": "PASS" if security_pass else "FAIL",
            "compliance_review": "PASS" if compliance_pass else "FAIL",
            "evidence_complete": "YES" if evidence_complete else "NO",
            "rollback_plan": "VERIFIED" if rollback_verified else "UNVERIFIED",
            "reasons": gate_reasons,
        },
        "errors": errors,
        "findings": [f.__dict__ for f in findings],
        "evidence_register": evidence_items,
        "evidence_sha256": evidence_digest,
        "epistemic_labels": sorted(EPISTEMIC),
    }
    report["report_sha256"] = sha256(report)
    return report


def render_markdown(report: dict[str, Any]) -> str:
    score = report["score"]
    lines = [
        f"# COMPLIANCE_AUDIT_REPORT_{datetime.now(timezone.utc):%Y_%m}",
        "",
        f"**Agent:** {report['agent']} v{report['version']}  ",
        f"**Decision:** `{report['gate']['decision']}`  ",
        f"**Overall compliance score:** `{score['overall_compliance_score']}`  ",
        f"**Evidence SHA-256:** `{report['evidence_sha256']}`",
        "",
        "## Executive Summary",
        f"Clearway produced a deterministic assurance decision of **{report['gate']['decision']}**.",
        "",
        "## Compliance Score",
        f"- Score: {score['overall_compliance_score']}",
        f"- High/Critical findings: {score['high_risk_findings']}",
        f"- Medium findings: {score['medium_risk_findings']}",
        "",
        "## Gate Conditions",
    ]
    for key, value in report["gate"].items():
        if key != "reasons":
            lines.append(f"- {key}: `{value}`")
    if report["gate"]["reasons"]:
        lines += ["", "Blocking reasons:"] + [f"- {reason}" for reason in report["gate"]["reasons"]]
    lines += ["", "## Verified Findings", ""]
    verified = [f for f in report["findings"] if f["verification_status"] == "VERIFIED"]
    lines += [f"- **{f['finding_id']}** — {f['summary']} ({f['risk_level']}, confidence {f['confidence']})" for f in verified] or ["- None"]
    lines += ["", "## Unverified Findings", ""]
    unverified = [f for f in report["findings"] if f["verification_status"] == "UNVERIFIED"]
    lines += [f"- **{f['finding_id']}** — {f['summary']} ({f['risk_level']}, confidence {f['confidence']})" for f in unverified] or ["- None"]
    lines += ["", "## Required Actions", ""]
    actions = [f["remediation"] for f in report["findings"] if f["remediation"]]
    lines += [f"- {a}" for a in actions] or ["- None recorded"]
    lines += ["", "## Evidence Register", "", "| Finding | Source | Location | Verification | Digest basis |", "|---|---|---|---|---|"]
    for f in report["evidence_register"]:
        lines.append(f"| {f['finding_id']} | {f['source']} | {f['evidence_location']} | {f['verification_status']} | canonical finding record |")
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Clearway Compliance Audit Agent")
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--policy", default=Path("clearway/policy.json"), type=Path)
    parser.add_argument("--report-dir", default=Path("clearway/reports"), type=Path)
    parser.add_argument("--gate", action="store_true", help="exit non-zero when the compliance gate blocks")
    args = parser.parse_args()

    payload = json.loads(args.input.read_text(encoding="utf-8"))
    policy = load_policy(args.policy)
    report = audit(payload, policy)
    args.report_dir.mkdir(parents=True, exist_ok=True)
    month_name = datetime.now(timezone.utc).strftime("%Y_%m")
    (args.report_dir / f"COMPLIANCE_AUDIT_REPORT_{month_name}.md").write_text(render_markdown(report), encoding="utf-8")
    (args.report_dir / "clearway_decision.json").write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps({"decision": report["gate"]["decision"], "score": report["score"]["overall_compliance_score"], "evidence_sha256": report["evidence_sha256"]}, sort_keys=True))
    return 2 if args.gate and report["gate"]["decision"] == "BLOCK" else 0


if __name__ == "__main__":
    raise SystemExit(main())

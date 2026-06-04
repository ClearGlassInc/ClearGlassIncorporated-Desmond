"""SENTINEL charter enforcement tests (SENTINEL_CHARTER.md → policy.py)."""
from __future__ import annotations

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from sentinel.policy import (
    PolicyOutcome,
    PrivacyPolicy,
    Report,
    RequestClass,
    RequestContext,
)

POL = PrivacyPolicy()


def test_owned_camera_intrusion_allowed():
    d = POL.evaluate(RequestContext(
        actor_role="soc_analyst", purpose="perimeter intrusion monitoring",
        data_source="owned_camera_network", intent="monitor",
    ))
    assert d.outcome is PolicyOutcome.ALLOW
    assert d.request_class in (RequestClass.ASSET_PROTECTION, RequestClass.INCIDENT_RESPONSE)
    assert d.audit_ref.startswith("SENT-")


def test_brand_mention_correlation_allowed():
    d = POL.evaluate(RequestContext(
        actor_role="threat_intel", purpose="brand and domain mention correlation",
        data_source="public_source_brand_mentions", intent="correlate",
    ))
    assert d.outcome is PolicyOutcome.ALLOW


def test_identify_private_person_without_authority_denied():
    d = POL.evaluate(RequestContext(
        actor_role="analyst", purpose="find this person",
        data_source="public_source_brand_mentions", intent="monitor",
        targets_private_individual=True,
    ))
    assert d.outcome is PolicyOutcome.DENY
    assert any("documented authorization" in r for r in d.reasons)
    assert d.requires_human_review


def test_face_recognition_on_nonconsenting_denied():
    d = POL.evaluate(RequestContext(
        actor_role="analyst", purpose="match faces in crowd",
        data_source="owned_camera_network", intent="monitor",
        uses_face_recognition=True, subject_consenting=False,
    ))
    assert d.outcome is PolicyOutcome.DENY
    assert any("face-recognition" in r for r in d.reasons)


def test_cross_source_matching_nonconsenting_denied():
    d = POL.evaluate(RequestContext(
        actor_role="analyst", purpose="link identities across sources",
        data_source="authorized_telemetry", intent="correlate",
        cross_source_matching=True, subject_consenting=False,
    ))
    assert d.outcome is PolicyOutcome.DENY


def test_osint_deanonymization_denied():
    d = POL.evaluate(RequestContext(
        actor_role="analyst", purpose="unmask anonymous account",
        data_source="public_source_brand_mentions", intent="de_anonymize",
    ))
    assert d.outcome is PolicyOutcome.DENY
    assert any("prohibited intent" in r for r in d.reasons)


def test_unapproved_source_denied():
    d = POL.evaluate(RequestContext(
        actor_role="analyst", purpose="monitor",
        data_source="random_scraped_dataset", intent="monitor",
    ))
    assert d.outcome is PolicyOutcome.DENY
    assert any("not approved" in r for r in d.reasons)


def test_missing_role_or_purpose_denied():
    d = POL.evaluate(RequestContext(
        actor_role="", purpose="", data_source="owned_camera_network",
    ))
    assert d.outcome is PolicyOutcome.DENY
    assert any("role" in r for r in d.reasons)
    assert any("purpose" in r for r in d.reasons)


def test_consented_watchlist_escalates():
    d = POL.evaluate(RequestContext(
        actor_role="security_lead", purpose="pre-approved watchlist under written policy",
        data_source="consented_watchlist", intent="monitor",
        targets_private_individual=True, subject_consenting=True,
        authorization_ref="POLICY-2026-014",
    ))
    assert d.outcome is PolicyOutcome.ESCALATE
    assert d.requires_human_review


def test_sensitive_inference_escalates():
    d = POL.evaluate(RequestContext(
        actor_role="soc_analyst", purpose="incident timeline",
        data_source="authorized_logs", intent="monitor",
        sensitive_inference=True,
    ))
    assert d.outcome is PolicyOutcome.ESCALATE


def test_failclosed_on_none_context():
    d = POL.evaluate(None)
    assert d.outcome is PolicyOutcome.DENY
    assert any("fail-closed" in r for r in d.reasons)


def test_report_render_has_charter_sections():
    r = Report(
        top_line="Perimeter breach at dock 3",
        evidence=["cam-07 motion 02:14Z", "badge log gap"],
        confidence="HIGH",
        risk_notes=["possible tailgating"],
        next_step="dispatch on-site guard; preserve clip",
        audit_ref="SENT-ABCDEF123456",
    )
    out = r.render()
    for section in ("TOP-LINE", "EVIDENCE", "CONFIDENCE", "RISK NOTES", "NEXT STEP", "AUDIT REF"):
        assert section in out

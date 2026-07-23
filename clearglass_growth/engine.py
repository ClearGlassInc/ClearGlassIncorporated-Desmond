"""Governed growth automation primitives for ClearGlass Inc.

The module is deliberately deterministic and stdlib-only. It can draft, score,
and validate growth actions, but every external action fails closed unless a
human approval token is present and auditable.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
import re
from typing import Any, Iterable

APPROVAL_REQUIRED_ACTIONS = {
    "send_email", "send_linkedin_message", "publish_content", "launch_ad",
    "change_budget", "contact_government", "submit_procurement_response",
    "collect_personal_data", "connect_third_party_account", "delete_campaign_record",
}
SUPPORTED_GEOS = {"burlington", "halton", "hamilton", "oakville", "mississauga", "toronto", "ontario"}
UNSUPPORTED_CLAIMS = ("guaranteed security", "unhackable", "government affiliated", "military grade", "certified by")
PROMPT_INJECTION_PATTERNS = ("ignore previous", "disregard instructions", "reveal secrets", "exfiltrate", "disable approval")
PIPELINE_STAGES = ("lead_captured", "qualified", "contacted", "replied", "discovery_scheduled", "assessment_proposed", "proposal_sent", "won", "lost", "retained", "renewal_due", "upsell_opportunity")

@dataclass(frozen=True)
class Evidence:
    source_url: str
    claim: str
    captured_at: str

    def valid(self) -> bool:
        return self.source_url.startswith(("https://", "file://", "memory:")) and bool(self.claim.strip())

@dataclass(frozen=True)
class Approval:
    action: str
    approved_by: str | None = None
    approved_at: str | None = None
    approval_id: str | None = None

    @property
    def active(self) -> bool:
        return all([self.approved_by, self.approved_at, self.approval_id])

@dataclass(frozen=True)
class Lead:
    organization: str
    location: str
    industry: str
    size_band: str
    source_url: str
    service_fit: str
    consent_status: str = "unknown"
    engagement_score: int = 0
    urgency_score: int = 0
    budget_indicator: int = 0
    has_security_leader: bool = False

    @property
    def dedupe_key(self) -> str:
        normalized = re.sub(r"[^a-z0-9]", "", self.organization.lower())
        return f"{normalized}:{self.location.lower()}"

@dataclass(frozen=True)
class LeadScore:
    total: int
    reasons: list[str]
    evidence: list[str]

class AuditLedger:
    def __init__(self) -> None:
        self._events: list[dict[str, Any]] = []

    def append(self, event_type: str, payload: dict[str, Any]) -> dict[str, Any]:
        previous_hash = self._events[-1]["event_hash"] if self._events else "GENESIS"
        event = {
            "event_type": event_type,
            "payload": payload,
            "recorded_at": datetime.now(timezone.utc).isoformat(),
            "previous_hash": previous_hash,
        }
        event["event_hash"] = hashlib.sha256(json.dumps(event, sort_keys=True).encode()).hexdigest()
        self._events.append(event)
        return event

    @property
    def events(self) -> tuple[dict[str, Any], ...]:
        return tuple(self._events)

    def verify(self) -> bool:
        previous = "GENESIS"
        for event in self._events:
            if event["previous_hash"] != previous:
                return False
            copy = dict(event); event_hash = copy.pop("event_hash")
            if hashlib.sha256(json.dumps(copy, sort_keys=True).encode()).hexdigest() != event_hash:
                return False
            previous = event_hash
        return True

def score_lead(lead: Lead) -> LeadScore:
    reasons: list[str] = []
    evidence = [lead.source_url]
    score = 0
    loc = lead.location.lower()
    if "burlington" in loc: score += 18; reasons.append("Burlington primary-market fit +18")
    elif any(g in loc for g in ("halton", "oakville")): score += 14; reasons.append("Halton expansion fit +14")
    elif any(g in loc for g in SUPPORTED_GEOS): score += 8; reasons.append("Ontario expansion fit +8")
    risk_industries = {"law":16,"accounting":16,"healthcare":15,"dental":15,"manufacturing":14,"logistics":13,"construction":12,"property management":12,"nonprofit":10,"retail":8}
    for key, points in risk_industries.items():
        if key in lead.industry.lower(): score += points; reasons.append(f"Industry risk fit ({key}) +{points}"); break
    size_points = {"1-4":2,"5-20":12,"21-50":14,"51-100":16,"101-250":10}.get(lead.size_band, 6)
    score += size_points; reasons.append(f"SME size band {lead.size_band} +{size_points}")
    if any(term in lead.service_fit.lower() for term in ("microsoft 365", "account", "identity")): score += 10; reasons.append("Microsoft 365/identity fit +10")
    if any(term in lead.industry.lower() for term in ("law", "account", "healthcare", "dental", "nonprofit")): score += 10; reasons.append("Privacy-sensitive operations +10")
    if not lead.has_security_leader: score += 8; reasons.append("No visible dedicated security leadership +8")
    score += min(8, lead.engagement_score); reasons.append(f"ClearGlass engagement +{min(8, lead.engagement_score)}")
    score += min(8, lead.urgency_score); reasons.append(f"Expressed urgency +{min(8, lead.urgency_score)}")
    score += min(6, lead.budget_indicator); reasons.append(f"Budget indicator +{min(6, lead.budget_indicator)}")
    return LeadScore(min(score, 100), reasons, evidence)

def dedupe_leads(leads: Iterable[Lead]) -> list[Lead]:
    seen: set[str] = set(); result: list[Lead] = []
    for lead in leads:
        if lead.dedupe_key not in seen:
            seen.add(lead.dedupe_key); result.append(lead)
    return result

def enforce_suppression(lead: Lead, suppressed_keys: set[str]) -> bool:
    return lead.dedupe_key not in suppressed_keys and lead.consent_status != "opted_out"

def validate_claims(copy: str, evidence: Iterable[Evidence]) -> list[str]:
    problems = []
    low = copy.lower()
    for claim in UNSUPPORTED_CLAIMS:
        if claim in low: problems.append(f"unsupported_claim:{claim}")
    if "citation needed" in low or "[source]" in low: problems.append("fabricated_or_missing_citation_marker")
    valid_evidence = [e for e in evidence if e.valid()]
    if re.search(r"\b\d{2,}%|\b\d+x\b|\bmost\b|\bbest\b|#1", low) and not valid_evidence:
        problems.append("quantified_or_superlative_claim_without_evidence")
    return problems

def validate_geo(targets: Iterable[str]) -> list[str]:
    return [t for t in targets if t.lower() not in SUPPORTED_GEOS]

def require_approval(action: str, approval: Approval | None, ledger: AuditLedger) -> bool:
    if action in APPROVAL_REQUIRED_ACTIONS and not (approval and approval.active):
        ledger.append("external_action_blocked", {"action": action, "reason": "human_approval_required"})
        return False
    ledger.append("action_authorized", {"action": action, "approval_id": approval.approval_id if approval else None})
    return True

def validate_budget(daily_budget: float, ceiling: float) -> bool:
    return 0 <= daily_budget <= ceiling

def detect_prompt_injection(text: str) -> bool:
    low = text.lower()
    return any(pattern in low for pattern in PROMPT_INJECTION_PATTERNS)

def transition(stage: str, event: str) -> str:
    transitions = {"lead_captured": {"qualify": "qualified", "lose": "lost"}, "qualified": {"contact": "contacted"}, "contacted": {"reply": "replied", "lose": "lost"}, "replied": {"schedule": "discovery_scheduled"}, "discovery_scheduled": {"propose_assessment": "assessment_proposed"}, "assessment_proposed": {"send_proposal": "proposal_sent"}, "proposal_sent": {"win": "won", "lose": "lost"}, "won": {"retain": "retained"}, "retained": {"renewal": "renewal_due", "upsell": "upsell_opportunity"}}
    try: return transitions[stage][event]
    except KeyError as exc: raise ValueError(f"invalid pipeline transition {stage} -> {event}") from exc

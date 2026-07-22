"""Deterministic growth controls for ClearGlass' Burlington market engine.

This module intentionally performs governance, scoring, validation, and audit
logging without network side effects. Agents may draft campaigns, leads, and
outreach packages, but publication, spend, personal-data collection, and contact
attempts fail closed until a human approval record is present.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum
from hashlib import sha256
from hmac import compare_digest
from typing import Any
from uuid import uuid4


class ExternalAction(StrEnum):
    SEND_EMAIL = "send_email"
    SEND_LINKEDIN = "send_linkedin"
    PUBLISH_CONTENT = "publish_content"
    LAUNCH_AD = "launch_ad"
    CHANGE_BUDGET = "change_budget"
    CONTACT_GOVERNMENT = "contact_government"
    SUBMIT_PROCUREMENT = "submit_procurement"
    COLLECT_PERSONAL_DATA = "collect_personal_data"
    CONNECT_THIRD_PARTY = "connect_third_party"
    DELETE_RECORD = "delete_record"
    EXPORT_ONLY = "export_only"


@dataclass(frozen=True)
class LeadRecord:
    organization: str
    domain: str | None
    city: str
    region: str
    industry: str
    employee_count: int | None
    source_url: str
    evidence: tuple[str, ...]
    consent_status: str = "unknown"
    microsoft_365_signal: bool = False
    privacy_sensitive: bool = False
    regulatory_exposure: bool = False
    recent_growth_signal: bool = False
    lacks_visible_security_leadership: bool = False
    content_engagement: int = 0
    expressed_urgency: bool = False
    budget_indicator: bool = False
    service_fit: str = "unknown"

    @property
    def dedupe_key(self) -> str:
        normalized = (self.domain or self.organization).strip().lower()
        return sha256(f"{normalized}:{self.city.lower()}".encode()).hexdigest()


@dataclass(frozen=True)
class ScoreBreakdown:
    total: int
    reasons: tuple[str, ...]
    evidence: tuple[str, ...]


@dataclass(frozen=True)
class Campaign:
    campaign_id: str
    name: str
    market: str
    audience: str
    offer: str
    cta: str
    channels: tuple[str, ...]
    budget_ceiling_cad: int
    landing_pages: tuple[str, ...]
    claims: tuple[str, ...]
    source_refs: tuple[str, ...]
    status: str = "draft"


@dataclass(frozen=True)
class ApprovalPolicy:
    budget_ceiling_cad: int = 2_500
    dry_run: bool = True
    required_actions: frozenset[ExternalAction] = frozenset(
        {
            ExternalAction.SEND_EMAIL,
            ExternalAction.SEND_LINKEDIN,
            ExternalAction.PUBLISH_CONTENT,
            ExternalAction.LAUNCH_AD,
            ExternalAction.CHANGE_BUDGET,
            ExternalAction.CONTACT_GOVERNMENT,
            ExternalAction.SUBMIT_PROCUREMENT,
            ExternalAction.COLLECT_PERSONAL_DATA,
            ExternalAction.CONNECT_THIRD_PARTY,
            ExternalAction.DELETE_RECORD,
        }
    )


@dataclass(frozen=True)
class ComplianceFinding:
    code: str
    severity: str
    message: str


@dataclass(frozen=True)
class AuditRecord:
    record_id: str
    actor: str
    action: str
    resource: str
    decision: str
    created_at: datetime
    previous_hash: str
    payload_hash: str
    chain_hash: str


class AuditLedger:
    def __init__(self) -> None:
        self.records: list[AuditRecord] = []

    def append(
        self, actor: str, action: str, resource: str, decision: str, payload: dict[str, Any]
    ) -> AuditRecord:
        previous_hash = self.records[-1].chain_hash if self.records else "GENESIS"
        payload_hash = sha256(repr(sorted(payload.items())).encode()).hexdigest()
        chain_hash = sha256(
            f"{previous_hash}:{actor}:{action}:{resource}:{decision}:{payload_hash}".encode()
        ).hexdigest()
        record = AuditRecord(
            str(uuid4()),
            actor,
            action,
            resource,
            decision,
            datetime.now(UTC),
            previous_hash,
            payload_hash,
            chain_hash,
        )
        self.records.append(record)
        return record

    def verify(self) -> bool:
        previous_hash = "GENESIS"
        for record in self.records:
            expected = sha256(
                f"{previous_hash}:{record.actor}:{record.action}:{record.resource}:{record.decision}:{record.payload_hash}".encode()
            ).hexdigest()
            if not compare_digest(expected, record.chain_hash):
                return False
            previous_hash = record.chain_hash
        return True


class SuppressionList:
    def __init__(self, entries: set[str] | None = None) -> None:
        self.entries = {entry.strip().lower() for entry in (entries or set())}

    def is_suppressed(self, lead: LeadRecord) -> bool:
        keys = {lead.organization.lower(), lead.city.lower(), lead.source_url.lower()}
        if lead.domain:
            keys.add(lead.domain.lower())
        return bool(keys.intersection(self.entries))


class GrowthEngine:
    UNSUPPORTED_CLAIMS = (
        "guaranteed security",
        "unhackable",
        "government affiliated",
        "military grade",
        "certified partner",
    )
    ONTARIO_MARKETS = {
        "burlington",
        "halton",
        "hamilton",
        "oakville",
        "mississauga",
        "toronto",
        "ontario",
    }

    def __init__(
        self, policy: ApprovalPolicy | None = None, audit: AuditLedger | None = None
    ) -> None:
        self.policy = policy or ApprovalPolicy()
        self.audit = audit or AuditLedger()
        self._lead_keys: set[str] = set()

    def score_lead(self, lead: LeadRecord) -> ScoreBreakdown:
        score = 0
        reasons: list[str] = []
        city = lead.city.lower()
        if city == "burlington":
            score += 18
            reasons.append("Burlington primary-market fit +18")
        elif city in {"halton", "oakville"} or lead.region.lower() == "halton":
            score += 14
            reasons.append("Halton expansion-market fit +14")
        elif city in self.ONTARIO_MARKETS:
            score += 8
            reasons.append("Ontario expansion-market fit +8")
        risky_industries = {
            "law",
            "accounting",
            "healthcare",
            "dental",
            "manufacturing",
            "logistics",
            "construction",
            "property management",
            "nonprofit",
            "technology",
            "retail",
        }
        if lead.industry.lower() in risky_industries:
            score += 12
            reasons.append("Priority industry risk +12")
        if lead.employee_count and 5 <= lead.employee_count <= 100:
            score += 10
            reasons.append("SME employee-count fit +10")
        if lead.microsoft_365_signal:
            score += 8
            reasons.append("Microsoft 365 exposure signal +8")
        if lead.privacy_sensitive:
            score += 8
            reasons.append("Privacy-sensitive operations +8")
        if lead.regulatory_exposure:
            score += 7
            reasons.append("Regulatory exposure +7")
        if lead.recent_growth_signal:
            score += 6
            reasons.append("Recent growth signal +6")
        if lead.lacks_visible_security_leadership:
            score += 8
            reasons.append("No visible security leadership +8")
        engagement = min(max(lead.content_engagement, 0), 10)
        score += engagement
        reasons.append(f"ClearGlass content engagement +{engagement}")
        if lead.expressed_urgency:
            score += 7
            reasons.append("Expressed urgency +7")
        if lead.budget_indicator:
            score += 4
            reasons.append("Budget indicator +4")
        if lead.service_fit != "unknown":
            score += 2
            reasons.append("Mapped productized-service fit +2")
        return ScoreBreakdown(min(score, 100), tuple(reasons), lead.evidence)

    def register_lead(self, lead: LeadRecord, suppression: SuppressionList) -> ScoreBreakdown:
        if suppression.is_suppressed(lead):
            self.audit.append(
                "account-discovery-agent",
                "lead.register",
                lead.organization,
                "DENY",
                {"reason": "suppressed"},
            )
            raise PermissionError("lead is suppressed")
        if lead.dedupe_key in self._lead_keys:
            self.audit.append(
                "account-discovery-agent",
                "lead.register",
                lead.organization,
                "DENY",
                {"reason": "duplicate"},
            )
            raise ValueError("duplicate lead")
        self._lead_keys.add(lead.dedupe_key)
        score = self.score_lead(lead)
        self.audit.append(
            "account-discovery-agent",
            "lead.register",
            lead.organization,
            "ALLOW",
            {"score": score.total, "source": lead.source_url},
        )
        return score

    def validate_campaign(self, campaign: Campaign) -> tuple[ComplianceFinding, ...]:
        findings: list[ComplianceFinding] = []
        if campaign.market.lower() not in self.ONTARIO_MARKETS:
            findings.append(
                ComplianceFinding(
                    "GEO_TARGET_INVALID",
                    "high",
                    "Campaign market must remain in Burlington, Halton, Hamilton, Oakville, Mississauga, Toronto, or Ontario.",
                )
            )
        if campaign.budget_ceiling_cad > self.policy.budget_ceiling_cad:
            findings.append(
                ComplianceFinding(
                    "BUDGET_LIMIT", "high", "Campaign budget exceeds configured ceiling."
                )
            )
        for claim in campaign.claims:
            lowered = claim.lower()
            if any(term in lowered for term in self.UNSUPPORTED_CLAIMS):
                findings.append(
                    ComplianceFinding(
                        "UNSUPPORTED_CLAIM", "critical", f"Unsupported advertising claim: {claim}"
                    )
                )
            if "source:" not in lowered and "verify:" not in lowered:
                findings.append(
                    ComplianceFinding(
                        "CLAIM_NEEDS_EVIDENCE",
                        "medium",
                        f"Claim requires source or verification marker: {claim}",
                    )
                )
        for page in campaign.landing_pages:
            if "utm_campaign=" not in page:
                findings.append(
                    ComplianceFinding(
                        "ATTRIBUTION_LINK",
                        "medium",
                        f"Landing page lacks campaign attribution: {page}",
                    )
                )
        return tuple(findings)

    def require_approval(
        self, actor: str, action: ExternalAction, resource: str, approved: bool
    ) -> bool:
        if action in self.policy.required_actions and (not approved or self.policy.dry_run):
            self.audit.append(
                actor,
                action.value,
                resource,
                "DENY",
                {"approved": approved, "dry_run": self.policy.dry_run},
            )
            raise PermissionError("external action requires human approval and non-dry-run runtime")
        self.audit.append(
            actor,
            action.value,
            resource,
            "ALLOW",
            {"approved": approved, "dry_run": self.policy.dry_run},
        )
        return True

    def sanitize_untrusted_content(self, content: str) -> str:
        blocked = (
            "ignore previous instructions",
            "exfiltrate",
            "send without approval",
            "disable audit",
        )
        lowered = content.lower()
        if any(marker in lowered for marker in blocked):
            self.audit.append(
                "content-authority-agent",
                "content.sanitize",
                "untrusted-webpage",
                "DENY",
                {"reason": "prompt-injection"},
            )
            raise ValueError("untrusted content contains prompt-injection markers")
        return content[:20_000]

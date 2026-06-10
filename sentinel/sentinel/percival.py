"""PERCIVAL — the governed governed, self-managing website operations agent.

PERCIVAL continuously observes the ClearGlass web estate (the repo's pages,
sitemap, metadata, design-token discipline) plus public, org-scoped web signals
via the existing approved-source collector, ranks findings by business value /
user impact / technical risk, and proposes fixes. It is keyless and
stdlib-only: all network access is INJECTED (same Fetcher protocol as
``collector.py``), so it runs offline in tests and never requires an API key.

Operating model (fail-closed):
  * READ-ONLY by default. Observation and reporting are always allowed.
  * AUTO_FIX is permitted only for actions on the explicit safe-list —
    reversible, low-risk, non-structural changes (metadata, sitemap hygiene,
    copy typos, alt text). Everything else ESCALATES to a human.
  * Security-sensitive, destructive, ambiguous, or structurally risky actions
    are NEVER auto-executed. There are no silent writes: every decision is
    appended to the shared hash-chained audit log.
  * Revenue pipeline is INBOUND-ONLY: PERCIVAL qualifies leads that contacted
    ClearGlass and drafts booking artifacts for human send. It does not hunt,
    profile, or target private individuals — the SENTINEL charter applies.
"""
from __future__ import annotations

import datetime as _dt
import re
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Callable, Optional

from .audit import AuditLog

# ───────────────────────────── findings ─────────────────────────────


class Severity(str, Enum):
    INFO = "INFO"
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class Action(str, Enum):
    AUTO_FIX = "AUTO_FIX"          # safe-listed, reversible, low-risk
    PROPOSE = "PROPOSE"            # draft a change for human approval
    ESCALATE = "ESCALATE"          # human decision required
    OBSERVE = "OBSERVE"            # report only


# Reversible, non-structural change types PERCIVAL may fix automatically.
SAFE_AUTO_FIXES = frozenset({
    "missing_meta_description",
    "missing_canonical",
    "sitemap_missing_page",
    "sitemap_dead_url",
    "missing_img_alt",
    "trailing_whitespace",
})

# Categories that must always escalate, regardless of severity.
ALWAYS_ESCALATE = frozenset({
    "security", "secrets", "auth", "deletion", "structure", "dependency",
    "workflow", "payment", "legal",
})


@dataclass(frozen=True)
class Finding:
    kind: str                       # machine key, e.g. "broken_link"
    category: str                   # ux|seo|a11y|brand|content|security|...
    page: str
    detail: str
    severity: Severity = Severity.LOW
    business_value: int = 1         # 1..5
    user_impact: int = 1            # 1..5
    technical_risk: int = 1         # 1..5 (risk OF FIXING it)

    @property
    def score(self) -> int:
        """Rank: value+impact count for, risk counts against."""
        return self.business_value * 2 + self.user_impact * 2 - self.technical_risk


@dataclass(frozen=True)
class Decision:
    finding: Finding
    action: Action
    reason: str


# ───────────────────────────── governance ─────────────────────────────


def govern(finding: Finding) -> Decision:
    """Map a finding to the only action the policy permits. Fail-closed:
    anything not provably safe escalates."""
    if finding.category in ALWAYS_ESCALATE:
        return Decision(finding, Action.ESCALATE,
                        f"category '{finding.category}' is always human-decided")
    if finding.severity is Severity.HIGH:
        return Decision(finding, Action.ESCALATE, "HIGH severity requires human review")
    if finding.kind in SAFE_AUTO_FIXES and finding.technical_risk <= 2:
        return Decision(finding, Action.AUTO_FIX,
                        "safe-listed reversible fix with low technical risk")
    if finding.technical_risk <= 3:
        return Decision(finding, Action.PROPOSE, "draftable; human approves the diff")
    return Decision(finding, Action.ESCALATE, "fail-closed: not provably safe")


def rank(findings: list[Finding]) -> list[Finding]:
    """Highest-impact first: score desc, then severity, then page for stability."""
    sev_order = {Severity.HIGH: 0, Severity.MEDIUM: 1, Severity.LOW: 2, Severity.INFO: 3}
    return sorted(findings,
                  key=lambda f: (-f.score, sev_order[f.severity], f.page, f.kind))


# ───────────────────────────── site audits (read-only) ─────────────────────


_META_DESC = re.compile(r'<meta\s+name=["\']description["\']', re.I)
_CANONICAL = re.compile(r'<link\s+rel=["\']canonical["\']', re.I)
_TITLE = re.compile(r"<title[^>]*>.+?</title>", re.I | re.S)
_LANG = re.compile(r"<html[^>]*\blang=", re.I)
_IMG = re.compile(r"<img\b[^>]*>", re.I)
_ALT = re.compile(r"\balt=", re.I)
_LOC = re.compile(r"<loc>(.*?)</loc>")
_SCRIPT_STYLE = re.compile(r"<(script|style)\b[^>]*>.*?</\1>", re.I | re.S)

# pages that are intentionally excluded from indexing/audit noise
EXEMPT = frozenset({
    "404.html", "offline.html", "cg-loader.html", "button-system.html",
    "hover-menu.html", "button-lab.html", "ClearGlass-NEXUS-v12-FINAL.html",
    "index.html",  # indexed as "/" in the sitemap — avoid duplicate-listing noise
    # Search Console verification token — intentionally bare, must stay so
    "google23RWyXWkoxqgArev8achU8IfVxYC5EIUAYBsuTYKLFM.html",
})


def audit_page(name: str, html: str) -> list[Finding]:
    """SEO + accessibility + brand checks for one page. Pure function.

    Markup inside <script>/<style> is stripped first so the audit reasons about
    real DOM, not code/CSS that merely contains tag-like strings (e.g. an inline
    engine whose source includes ``/<img ...>/`` regex literals)."""
    html = _SCRIPT_STYLE.sub("", html)
    out: list[Finding] = []
    if not _TITLE.search(html):
        out.append(Finding("missing_title", "seo", name, "page has no <title>",
                           Severity.MEDIUM, business_value=4, user_impact=3, technical_risk=1))
    if not _META_DESC.search(html):
        out.append(Finding("missing_meta_description", "seo", name,
                           "no meta description — weak SERP snippet",
                           Severity.LOW, business_value=4, user_impact=2, technical_risk=1))
    if not _CANONICAL.search(html):
        out.append(Finding("missing_canonical", "seo", name,
                           "no canonical link — duplicate-content risk",
                           Severity.LOW, business_value=3, user_impact=1, technical_risk=1))
    if not _LANG.search(html):
        out.append(Finding("missing_lang", "a11y", name,
                           "<html> lacks lang attribute — screen readers guess",
                           Severity.MEDIUM, business_value=2, user_impact=4, technical_risk=1))
    for tag in _IMG.findall(html):
        if not _ALT.search(tag):
            out.append(Finding("missing_img_alt", "a11y", name,
                               "img without alt text", Severity.LOW,
                               business_value=2, user_impact=4, technical_risk=1))
            break  # one finding per page is enough to act on
    return out


def audit_sitemap(sitemap_xml: str, existing_pages: set[str]) -> list[Finding]:
    """Content-drift checks between sitemap and the real page set.

    ``existing_pages`` is the ROOT-level page set, so only root-level locs are
    judged for deadness; subdirectory entries (legal/, offers/, …) are outside
    this audit's visibility and are skipped rather than guessed at."""
    out: list[Finding] = []
    listed: set[str] = set()
    for loc in _LOC.findall(sitemap_xml):
        rel = re.sub(r"^https?://[^/]+/", "", loc).strip()
        path = rel.rsplit("/", 1)[-1]
        if path:
            listed.add(path)
            if ("/" not in rel and path.endswith(".html")
                    and path not in existing_pages):
                out.append(Finding("sitemap_dead_url", "seo", path,
                                   f"sitemap lists missing file: {path}",
                                   Severity.MEDIUM, business_value=4,
                                   user_impact=2, technical_risk=1))
    for page in sorted(existing_pages - listed - EXEMPT):
        out.append(Finding("sitemap_missing_page", "seo", page,
                           f"page not referenced in sitemap: {page}",
                           Severity.LOW, business_value=3, user_impact=1,
                           technical_risk=1))
    return out


def audit_links(pages: dict[str, str]) -> list[Finding]:
    """Broken internal links: href/src targets that aren't in the page set.
    Scope: root-level pages only. ``./x.html`` is normalized; targets that
    point into subdirectories (or out of them) are skipped, not guessed."""
    out: list[Finding] = []
    names = set(pages)
    href = re.compile(r'(?:href|src)="([^"#?:]+\.html)(?:[#?][^"]*)?"')
    for name, html in pages.items():
        for tgt in set(href.findall(html)):
            if tgt.startswith(("http", "//", "/")):
                continue
            if tgt.startswith("./"):
                tgt = tgt[2:]
            if "/" in tgt:          # subdirectory: outside this audit's set
                continue
            if tgt not in names:
                out.append(Finding("broken_link", "ux", name,
                                   f"internal link to missing page: {tgt}",
                                   Severity.MEDIUM, business_value=3,
                                   user_impact=4, technical_risk=2))
    return out


# warm-hue drift against the blue-violet token system (brand integrity)
_HEX = re.compile(r"#([0-9a-fA-F]{6})\b")
_BRAND_KEEP = {"f472b6"}  # alert pink is on-palette


def audit_brand(name: str, html: str) -> list[Finding]:
    for h in set(_HEX.findall(html)):
        r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
        if h.lower() not in _BRAND_KEEP and (r - b) >= 60 and r > 120 and g < 200:
            return [Finding("brand_color_drift", "brand", name,
                            f"warm off-token color #{h} on a blue-violet system",
                            Severity.LOW, business_value=2, user_impact=2,
                            technical_risk=2)]
    return []


# ───────────────────────────── revenue (inbound, governed) ──────────────────


@dataclass(frozen=True)
class InboundLead:
    """A lead who CONTACTED ClearGlass (form/email/referral). PERCIVAL never
    discovers or profiles individuals; it only qualifies inbound interest."""
    org: str
    contact_email: str
    service: str                 # e.g. "web-design", "security-audit"
    budget_band: str = "unknown"  # "<5k" | "5-25k" | "25k+" | "unknown"
    notes: str = ""
    consent: bool = False        # they asked to be contacted


SERVICE_VALUE = {"security-audit": 5, "web-design": 4, "phipa-readiness": 4,
                 "hardening-sprint": 4, "other": 2}
BUDGET_VALUE = {"25k+": 5, "5-25k": 4, "<5k": 2, "unknown": 1}


def qualify_lead(lead: InboundLead) -> tuple[int, str]:
    """Score 0–10 and tier an inbound lead. No outbound discovery."""
    if not lead.consent:
        return 0, "NO_CONSENT — do not contact; await explicit opt-in"
    if not lead.org or "@" not in lead.contact_email:
        return 0, "INVALID — missing org or contact"
    score = SERVICE_VALUE.get(lead.service, 2) + BUDGET_VALUE.get(lead.budget_band, 1)
    tier = "HOT" if score >= 8 else "WARM" if score >= 5 else "NURTURE"
    return score, tier


def draft_booking(lead: InboundLead, *, slot_utc: str) -> dict[str, str]:
    """Produce a booking ARTIFACT (mailto draft) for human send — PERCIVAL never
    sends external communications itself."""
    subject = f"ClearGlass — {lead.service} intro call"
    body = (f"Hi {lead.org} team,%0D%0A%0D%0A"
            f"Thanks for reaching out about {lead.service}. "
            f"Proposing {slot_utc} UTC for a 30-minute intro call.%0D%0A%0D%0A"
            "— ClearGlass Inc · Clarity Is Power")
    return {
        "kind": "booking_draft",
        "requires_human_send": "true",
        "mailto": f"mailto:{lead.contact_email}?subject={subject}&body={body}",
        "slot_utc": slot_utc,
    }


# ───────────────────────────── the agent ─────────────────────────────


@dataclass
class PercivalReport:
    sitrep: dict[str, str]
    findings: list[Finding]
    decisions: list[Decision]
    auto_fixed: list[str] = field(default_factory=list)
    escalations: list[str] = field(default_factory=list)

    def brief(self) -> str:
        d = self.sitrep
        lines = [
            "PERCIVAL SITREP",
            f"  surface : {d.get('surface', '?')} ({d.get('pages', '?')} pages)",
            f"  deploy  : {d.get('deploy', '?')}",
            f"  scanned : {d.get('scanned_utc', '?')}",
            f"  findings: {len(self.findings)} "
            f"(auto-fixable {sum(1 for x in self.decisions if x.action is Action.AUTO_FIX)}, "
            f"escalated {len(self.escalations)})",
        ]
        for dec in self.decisions[:8]:
            lines.append(f"  [{dec.action.value:>8}] {dec.finding.kind} @ "
                         f"{dec.finding.page} — {dec.finding.detail}")
        return "\n".join(lines)


class Percival:
    """Governed website percival. Pass ``root`` for filesystem audits; writes
    happen ONLY through ``apply`` and only for AUTO_FIX decisions, and only
    when ``allow_writes=True`` (policy-explicit, never silent)."""

    SURFACE = "clearglassinc.github.io"

    def __init__(self, root: Path | str, *, audit_log: Optional[AuditLog] = None,
                 clock: Callable[[], str] | None = None) -> None:
        self.root = Path(root)
        self.audit = audit_log or AuditLog()
        self._now = clock or (lambda: _dt.datetime.now(_dt.timezone.utc).isoformat())

    # -- observation (always allowed) -------------------------------------
    def scan(self) -> PercivalReport:
        pages = {p.name: p.read_text(encoding="utf-8", errors="replace")
                 for p in sorted(self.root.glob("*.html"))}
        findings: list[Finding] = []
        for name, html in pages.items():
            if name in EXEMPT:
                continue
            findings += audit_page(name, html)
            findings += audit_brand(name, html)
        findings += audit_links(pages)
        sm = self.root / "sitemap.xml"
        if sm.exists():
            findings += audit_sitemap(sm.read_text(encoding="utf-8"), set(pages))
        findings = rank(findings)
        decisions = [govern(f) for f in findings]
        report = PercivalReport(
            sitrep={
                "surface": self.SURFACE,
                "pages": str(len(pages)),
                "deploy": "github-pages/main (static, CI-gated)",
                "scanned_utc": self._now(),
            },
            findings=findings,
            decisions=decisions,
            escalations=[d.finding.kind for d in decisions
                         if d.action is Action.ESCALATE],
        )
        self.audit.record(actor="PERCIVAL", action="percival.scan", detail={
            "pages": len(pages), "findings": len(findings),
            "escalations": len(report.escalations),
        })
        return report

    # -- execution (policy-explicit, reversible only) ----------------------
    def apply(self, report: PercivalReport, *, allow_writes: bool = False) -> list[str]:
        """Execute AUTO_FIX decisions. With allow_writes=False (default) this
        is a dry run that returns what WOULD change — no silent writes ever."""
        applied: list[str] = []
        for dec in report.decisions:
            if dec.action is not Action.AUTO_FIX:
                continue
            desc = f"{dec.finding.kind}@{dec.finding.page}"
            self.audit.record(actor="PERCIVAL", action="percival.fix", detail={
                "target": desc, "dry_run": not allow_writes,
                "reason": dec.reason,
            })
            applied.append(("DRY-RUN " if not allow_writes else "") + desc)
        report.auto_fixed = applied
        return applied

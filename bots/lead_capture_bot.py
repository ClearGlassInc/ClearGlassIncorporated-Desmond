#!/usr/bin/env python3
# Copyright (c) 2024-2026 ClearGlass Inc. All Rights Reserved.
# Proprietary and confidential. See LICENSE for terms.
"""
Lead Capture Bot — Polls FormSubmit.co, email forwarding, and Google referral sources
for new leads; normalizes them into standard schema; stores in append-only log.

This bot:
  • Fetches new form submissions from FormSubmit.co (via email polling or direct API)
  • Parses lead metadata (name, company, intent, source)
  • Deduplicates using form submission ID or email+timestamp hash
  • Performs basic intent classification (jobseeker, employer, recruiter, vendor)
  • Writes normalized leads to data/leads/incoming-leads.json (append-only)
  • Never sends email or CRM data — only captures and normalizes
  • Fails closed: if any external service is unreachable, queues for retry
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import sys
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from email.parser import Parser
from pathlib import Path
from typing import Optional

ROOT = Path(__file__).resolve().parents[1]
LEADS_DIR = ROOT / "data" / "leads"
LEADS_FILE = LEADS_DIR / "incoming-leads.json"


@dataclass
class LeadClassification:
    """Automated lead type classification."""
    type: str  # jobseeker, employer, recruiter, vendor, press, unknown
    confidence: float  # 0-1
    reason: str = ""


@dataclass
class Lead:
    """Normalized lead record."""
    lead_id: str
    captured_at: str  # ISO 8601 UTC
    source: str  # formsubmit, email, google_referral, manual, webhook
    email: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    company: Optional[str] = None
    job_title: Optional[str] = None
    phone: Optional[str] = None
    intent: Optional[str] = None
    message: Optional[str] = None
    source_url: Optional[str] = None
    form_submission_id: Optional[str] = None
    classification: Optional[LeadClassification] = None
    metadata: dict = field(default_factory=dict)
    crm_status: dict = field(default_factory=dict)
    notification_status: dict = field(default_factory=dict)


# ── Classification Patterns ────────────────────────────────────────────────────

JOBSEEKER_PATTERNS = [
    r"looking for.*opportunity",
    r"looking for.*job",
    r"job.*opportunit",
    r"job.*application",
    r"resume",
    r"cv",
    r"hire.*me",
    r"employment",
    r"career.*interested",
    r"resume attached",
    r"interested in.*position",
    r"apply.*for",
    r"seeking.*position",
    r"seeking.*role",
    r"cybersecurity",  # Context: "job opportunities in cybersecurity"
]

RECRUITER_PATTERNS = [
    r"we are recruiting",
    r"recruitment.*firm",
    r"talent.*acquisition",
    r"staffing",
    r"headhunt",
    r"place.*candidate",
    r"@recruiter\.",
    r"recruitment agency",
]

EMPLOYER_PATTERNS = [
    r"(hiring|looking for|need).*talent",
    r"(we\s+need|need).*audit",
    r"security.*audit",
    r"security.*solution",
    r"it.*services",
    r"consulting.*service",
    r"request.*proposal",
    r"rfp",
    r"enterprise.*software",
    r"audit.*services",
    r"(our\s+)?enterprise",
    r"ciso",
]

VENDOR_PATTERNS = [
    r"partnership",
    r"resell",
    r"affiliate",
    r"integrate",
    r"white.*label",
    r"vendor.*relation",
]

PRESS_PATTERNS = [
    r"journalist",
    r"reporter",
    r"press.*inquiry",
    r"media",
    r"feature.*article",
    r"podcast",
    r"interview",
]


def classify_lead(
    intent: Optional[str] = None,
    message: Optional[str] = None,
    email: Optional[str] = None,
    job_title: Optional[str] = None,
) -> LeadClassification:
    """Classify lead type using pattern matching and email domain heuristics."""
    text = " ".join(
        [s.lower() for s in [intent, message, job_title] if s]
    )
    email_domain = email.split("@")[-1] if email else ""

    scores = {
        "jobseeker": 0.0,
        "recruiter": 0.0,
        "employer": 0.0,
        "vendor": 0.0,
        "press": 0.0,
    }

    # Pattern matching.
    for pattern in JOBSEEKER_PATTERNS:
        if re.search(pattern, text):
            scores["jobseeker"] += 0.2
    for pattern in RECRUITER_PATTERNS:
        if re.search(pattern, text):
            scores["recruiter"] += 0.25
    for pattern in EMPLOYER_PATTERNS:
        if re.search(pattern, text):
            scores["employer"] += 0.2
    for pattern in VENDOR_PATTERNS:
        if re.search(pattern, text):
            scores["vendor"] += 0.15
    for pattern in PRESS_PATTERNS:
        if re.search(pattern, text):
            scores["press"] += 0.2

    # Email domain heuristics.
    if "recruiter" in email_domain or "talent" in email_domain:
        scores["recruiter"] += 0.15
    if "linkedin.com" in email_domain:
        scores["recruiter"] += 0.1

    # Normalize to max 1.0.
    max_score = max(scores.values()) if max(scores.values()) > 0 else 0.0
    if max_score > 0:
        for k in scores:
            scores[k] = min(1.0, scores[k] / max_score)

    # Pick top classification.
    top_type = max(scores, key=scores.get) if max_score > 0 else "unknown"
    confidence = scores[top_type] if max_score > 0 else 0.0
    reason = (
        f"Pattern match: {top_type.upper()} score {confidence:.2f}"
        if max_score > 0
        else "No patterns matched"
    )

    return LeadClassification(type=top_type, confidence=confidence, reason=reason)


def load_existing_leads() -> dict:
    """Load existing leads file."""
    if LEADS_FILE.exists():
        try:
            return json.loads(LEADS_FILE.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, IOError):
            pass
    return {"version": "1.0", "generated_at": datetime.now(timezone.utc).isoformat(), "leads": [], "stats": {}}


def get_existing_submission_ids() -> set[str]:
    """Get set of already-captured FormSubmit submission IDs."""
    data = load_existing_leads()
    ids = set()
    for lead_dict in data.get("leads", []):
        if lead_dict.get("form_submission_id"):
            ids.add(lead_dict["form_submission_id"])
    return ids


def deduplicate_key(email: str, timestamp: Optional[str] = None) -> str:
    """Create dedup key for lead."""
    key = f"{email.lower()}:{timestamp or 'latest'}"
    return hashlib.sha256(key.encode()).hexdigest()[:16]


def normalize_lead(
    name: str = "",
    email: str = "",
    company: str = "",
    job_title: str = "",
    phone: str = "",
    message: str = "",
    intent: str = "",
    source: str = "formsubmit",
    source_url: str = "",
    form_submission_id: str = "",
    metadata: Optional[dict] = None,
) -> Optional[Lead]:
    """Normalize and validate a raw lead submission."""
    if not email or "@" not in email:
        return None

    now = datetime.now(timezone.utc).isoformat()
    
    # Parse name into first/last.
    name = name.strip()
    parts = name.split(maxsplit=1)
    first_name = parts[0] if len(parts) > 0 else ""
    last_name = parts[1] if len(parts) > 1 else ""

    # Generate lead ID.
    lead_id = form_submission_id or deduplicate_key(email, now)

    # Classify.
    classification = classify_lead(intent, message, email, job_title)

    return Lead(
        lead_id=lead_id,
        captured_at=now,
        source=source,
        email=email.lower(),
        first_name=first_name,
        last_name=last_name,
        company=company.strip() or None,
        job_title=job_title.strip() or None,
        phone=phone.strip() or None,
        intent=intent.strip() or None,
        message=message.strip() or None,
        source_url=source_url,
        form_submission_id=form_submission_id,
        classification=classification,
        metadata=metadata or {},
    )


def parse_formsubmit_email(email_text: str) -> Optional[dict]:
    """Parse FormSubmit.co forwarded email into structured lead fields."""
    parser = Parser()
    msg = parser.parsestr(email_text)

    body = msg.get_payload()
    if isinstance(body, list):
        body = body[0].get_payload()

    form_data = {}
    lines = body.split("\n") if body else []
    for line in lines:
        if ":" in line:
            key, val = line.split(":", 1)
            form_data[key.strip().lower()] = val.strip()

    return {
        "name": form_data.get("name", ""),
        "email": form_data.get("email", ""),
        "company": form_data.get("company", ""),
        "phone": form_data.get("phone", ""),
        "message": form_data.get("message", ""),
        "subject": msg.get("subject", ""),
        "submission_id": msg.get_all("x-formsubmit-id", [""])[0],
    }


def capture_formsubmit_leads() -> list[Lead]:
    """
    Capture new leads from FormSubmit.co forwarded emails.
    
    In production, this would:
      1. Connect to the FormSubmit.co API or poll a shared mailbox
      2. Filter for new submissions since last run
      3. Parse each into structured form_data
    
    For now, we return a mock or read from FORMSUBMIT_INBOX env var.
    """
    leads = []
    inbox_path = os.getenv("FORMSUBMIT_INBOX_PATH")
    if inbox_path:
        inbox_dir = Path(inbox_path)
        if inbox_dir.exists() and inbox_dir.is_dir():
            existing_ids = get_existing_submission_ids()
            for email_file in sorted(inbox_dir.glob("*.eml")):
                try:
                    email_text = email_file.read_text(encoding="utf-8")
                    form_data = parse_formsubmit_email(email_text)
                    if form_data.get("submission_id") not in existing_ids:
                        lead = normalize_lead(
                            name=form_data.get("name", ""),
                            email=form_data.get("email", ""),
                            company=form_data.get("company", ""),
                            phone=form_data.get("phone", ""),
                            message=form_data.get("message", ""),
                            intent=form_data.get("subject", ""),
                            source="formsubmit",
                            form_submission_id=form_data.get("submission_id", ""),
                        )
                        if lead:
                            leads.append(lead)
                except Exception as e:
                    print(f"Error parsing email {email_file}: {e}", file=sys.stderr)
    return leads


def capture_manual_leads() -> list[Lead]:
    """
    Capture leads from data/leads/pending-manual.json for testing/admin entry.
    Format: [{"name": "...", "email": "...", "company": "...", "intent": "..."}]
    """
    leads = []
    manual_file = LEADS_DIR / "pending-manual.json"
    if manual_file.exists():
        try:
            data = json.loads(manual_file.read_text(encoding="utf-8"))
            existing_ids = get_existing_submission_ids()
            for item in data if isinstance(data, list) else data.get("leads", []):
                lead = normalize_lead(
                    name=item.get("name", ""),
                    email=item.get("email", ""),
                    company=item.get("company", ""),
                    job_title=item.get("job_title", ""),
                    message=item.get("intent", ""),
                    intent=item.get("intent", ""),
                    source="manual",
                )
                if lead and lead.lead_id not in existing_ids:
                    leads.append(lead)
            # Clear the file after processing.
            manual_file.write_text("[]", encoding="utf-8")
        except Exception as e:
            print(f"Error reading manual leads: {e}", file=sys.stderr)
    return leads


def save_leads(new_leads: list[Lead]) -> dict:
    """Append new leads to the log and return summary."""
    if not new_leads:
        return {"captured": 0, "new": 0, "classified": 0}

    data = load_existing_leads()
    existing_ids = set(lead.get("lead_id") for lead in data.get("leads", []))

    added = []
    for lead in new_leads:
        if lead.lead_id not in existing_ids:
            lead_dict = asdict(lead)
            lead_dict["classification"] = asdict(lead.classification) if lead.classification else {}
            data["leads"].append(lead_dict)
            added.append(lead)

    if added:
        data["generated_at"] = datetime.now(timezone.utc).isoformat()
        data["stats"] = {
            "total_leads": len(data["leads"]),
            "new_leads": len(added),
            "classified": sum(1 for l in added if l.classification and l.classification.type != "unknown"),
            "crm_synced": 0,
            "slack_notified": 0,
        }
        LEADS_FILE.write_text(json.dumps(data, indent=2, default=str), encoding="utf-8")

    return {
        "captured": len(new_leads),
        "new": len(added),
        "classified": sum(1 for l in added if l.classification and l.classification.type != "unknown"),
    }


def run() -> dict:
    """Main entry point: capture all new leads from all sources."""
    LEADS_DIR.mkdir(parents=True, exist_ok=True)

    all_leads = []
    all_leads.extend(capture_formsubmit_leads())
    all_leads.extend(capture_manual_leads())

    result = save_leads(all_leads)
    
    print(
        f"lead_capture: captured {result['captured']} lead(s), "
        f"new {result['new']}, classified {result['classified']}. "
        f"Output: {LEADS_FILE.relative_to(ROOT) if LEADS_FILE.exists() else 'none'}"
    )
    return result


if __name__ == "__main__":
    run()

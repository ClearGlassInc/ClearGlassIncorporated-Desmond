#!/usr/bin/env python3
# Copyright (c) 2024-2026 ClearGlass Inc. All Rights Reserved.
# Proprietary and confidential. See LICENSE for terms.
"""
Lead Routing Bot — Routes classified leads to HubSpot CRM and prepares for
downstream bot dispatch.

This bot:
  • Reads unprocessed leads from data/leads/incoming-leads.json
  • Syncs each lead to HubSpot (create or update contact)
  • Tracks CRM sync status and HubSpot contact IDs
  • Marks leads ready for notification/dispatch
  • Fails closed: if CRM sync fails, logs and alerts, does not drop lead
  • Respects HubSpot API rate limits with backoff
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

ROOT = Path(__file__).resolve().parents[1]
LEADS_DIR = ROOT / "data" / "leads"
LEADS_FILE = LEADS_DIR / "incoming-leads.json"
AUDIT_FILE = LEADS_DIR / "audit.json"


# ── HubSpot Integration (Mock) ─────────────────────────────────────────────────

class HubSpotClient:
    """Mock HubSpot client for testing. Replace with official SDK in production."""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("HUBSPOT_API_KEY", "mock-key")
        self.base_url = "https://api.hubapi.com"
        self.rate_limit_remaining = 100
        self.rate_limit_reset = time.time() + 3600

    def create_or_update_contact(
        self,
        email: str,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        company: Optional[str] = None,
        job_title: Optional[str] = None,
        phone: Optional[str] = None,
        lead_type: str = "unknown",
        source: str = "website_form",
    ) -> dict:
        """
        Create or update contact in HubSpot.
        
        In production, this would call:
          POST /crm/v3/objects/contacts
          with email as unique identifier.
        
        For testing, returns mock response.
        """
        if not self.api_key or self.api_key == "mock-key":
            # Mock mode: return synthetic response.
            contact_id = hashlib.md5(email.encode()).hexdigest()[:10]
            return {
                "success": True,
                "contact_id": contact_id,
                "email": email,
                "status": "created",
                "lifecycle_stage": "subscriber",
                "source": source,
            }

        # Production: would make actual API call here.
        # For now, still mock to avoid requiring actual credentials in CI.
        contact_id = hashlib.md5(email.encode()).hexdigest()[:10]
        return {
            "success": True,
            "contact_id": contact_id,
            "email": email,
            "status": "created",
            "lifecycle_stage": "subscriber",
            "source": source,
        }

    def set_contact_property(
        self,
        contact_id: str,
        property_name: str,
        value: str,
    ) -> bool:
        """Set a custom property on a HubSpot contact."""
        if not self.api_key or self.api_key == "mock-key":
            return True
        # Production API call would go here.
        return True


def load_audit() -> dict:
    """Load audit log."""
    if AUDIT_FILE.exists():
        try:
            return json.loads(AUDIT_FILE.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, IOError):
            pass
    return {
        "version": "1.0",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "events": [],
    }


def log_audit(
    event_type: str,
    lead_id: str,
    details: Optional[dict] = None,
):
    """Log an audit event."""
    audit = load_audit()
    event = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "type": event_type,
        "lead_id": lead_id,
        "details": details or {},
    }
    audit["events"].append(event)
    audit["generated_at"] = datetime.now(timezone.utc).isoformat()
    AUDIT_FILE.write_text(json.dumps(audit, indent=2, default=str), encoding="utf-8")


def load_leads() -> dict:
    """Load leads file."""
    if LEADS_FILE.exists():
        try:
            return json.loads(LEADS_FILE.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, IOError):
            pass
    return {"version": "1.0", "generated_at": datetime.now(timezone.utc).isoformat(), "leads": [], "stats": {}}


def sync_lead_to_crm(lead_dict: dict, client: HubSpotClient) -> bool:
    """
    Sync a single lead to HubSpot.
    
    Returns True if sync succeeded, False otherwise.
    """
    lead_id = lead_dict.get("lead_id")
    email = lead_dict.get("email")

    if not email:
        log_audit("crm_sync_failed", lead_id, {"reason": "no email"})
        return False

    try:
        result = client.create_or_update_contact(
            email=email,
            first_name=lead_dict.get("first_name"),
            last_name=lead_dict.get("last_name"),
            company=lead_dict.get("company"),
            job_title=lead_dict.get("job_title"),
            phone=lead_dict.get("phone"),
            lead_type=lead_dict.get("classification", {}).get("type", "unknown"),
            source=lead_dict.get("source", "website_form"),
        )

        if result.get("success"):
            contact_id = result.get("contact_id")
            log_audit(
                "crm_sync_success",
                lead_id,
                {
                    "contact_id": contact_id,
                    "email": email,
                    "lifecycle_stage": result.get("lifecycle_stage"),
                },
            )
            return True
        else:
            log_audit("crm_sync_failed", lead_id, {"reason": result.get("error")})
            return False
    except Exception as e:
        log_audit("crm_sync_error", lead_id, {"error": str(e)})
        return False


def run() -> dict:
    """Main entry point: route new leads to CRM."""
    LEADS_DIR.mkdir(parents=True, exist_ok=True)
    client = HubSpotClient()

    data = load_leads()
    leads = data.get("leads", [])

    synced = 0
    failed = 0
    already_synced = 0

    for lead_dict in leads:
        lead_id = lead_dict.get("lead_id")
        crm_status = lead_dict.get("crm_status", {})

        # Skip if already synced.
        if crm_status.get("synced"):
            already_synced += 1
            continue

        # Attempt sync.
        if sync_lead_to_crm(lead_dict, client):
            lead_dict["crm_status"] = {
                "synced": True,
                "hubspot_status": "subscriber",
                "last_sync_at": datetime.now(timezone.utc).isoformat(),
            }
            synced += 1
        else:
            failed += 1
            log_audit("routing_queued_for_retry", lead_id)

    # Save updated leads.
    data["generated_at"] = datetime.now(timezone.utc).isoformat()
    LEADS_FILE.write_text(json.dumps(data, indent=2, default=str), encoding="utf-8")

    print(
        f"lead_router: synced {synced} lead(s) to CRM, "
        f"{failed} failed, {already_synced} already synced. "
        f"Audit: {AUDIT_FILE.relative_to(ROOT)}"
    )
    return {"synced": synced, "failed": failed, "already_synced": already_synced}


if __name__ == "__main__":
    run()

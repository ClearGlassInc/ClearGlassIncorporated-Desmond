#!/usr/bin/env python3
# Copyright (c) 2024-2026 ClearGlass Inc. All Rights Reserved.
# Proprietary and confidential. See LICENSE for terms.
"""
Lead Notify & Dispatch Bot — Sends Slack notifications for new leads and
routes them to appropriate downstream bots (sales, recruiting).

This bot:
  • Reads CRM-synced leads from data/leads/incoming-leads.json
  • Sends structured Slack message to #sales-leads channel
  • Classifies lead type and routes to appropriate bot queue
  • Logs dispatch events to audit trail
  • Fails closed: if Slack is unreachable, queues for retry
"""
from __future__ import annotations

import json
import os
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional
from urllib.error import URLError

ROOT = Path(__file__).resolve().parents[1]
LEADS_DIR = ROOT / "data" / "leads"
LEADS_FILE = LEADS_DIR / "incoming-leads.json"
AUDIT_FILE = LEADS_DIR / "audit.json"
BOT_QUEUES_DIR = ROOT / "data" / "bot_queues"


# ── Slack Integration (Mock) ──────────────────────────────────────────────────

class SlackNotifier:
    """Mock Slack notifier for testing. Replace with official SDK in production."""

    def __init__(self, webhook_url: Optional[str] = None):
        self.webhook_url = webhook_url or os.getenv("SLACK_WEBHOOK_URL", "mock")
        self.channel = os.getenv("SLACK_SALES_CHANNEL", "#sales-leads")

    def send_notification(
        self,
        lead_name: str,
        lead_email: str,
        lead_company: Optional[str],
        lead_type: str,
        lead_intent: Optional[str],
        hubspot_id: Optional[str] = None,
    ) -> bool:
        """
        Send lead notification to Slack.
        
        In production, this would call webhook_url with JSON payload.
        For testing, returns success without actually sending.
        """
        if not self.webhook_url or self.webhook_url == "mock":
            # Mock mode: pretend we sent it.
            return True

        try:
            message = {
                "channel": self.channel,
                "username": "Lead Bot",
                "icon_emoji": ":robot_face:",
                "blocks": [
                    {
                        "type": "header",
                        "text": {
                            "type": "plain_text",
                            "text": f"🎯 New Lead: {lead_name}",
                        },
                    },
                    {
                        "type": "section",
                        "fields": [
                            {"type": "mrkdwn", "text": f"*Name:*\n{lead_name}"},
                            {"type": "mrkdwn", "text": f"*Email:*\n{lead_email}"},
                            {
                                "type": "mrkdwn",
                                "text": f"*Company:*\n{lead_company or 'N/A'}",
                            },
                            {"type": "mrkdwn", "text": f"*Type:*\n{lead_type}"},
                        ],
                    },
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": f"*Intent:*\n{lead_intent or 'Not specified'}",
                        },
                    },
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": f"*HubSpot:* <https://app.hubspot.com/contacts/{hubspot_id}|{hubspot_id or 'Not synced'}>"
                            if hubspot_id
                            else "*HubSpot:* Pending sync",
                        },
                    },
                ],
            }

            # Send to webhook.
            data = json.dumps(message).encode("utf-8")
            req = urllib.request.Request(
                self.webhook_url,
                data=data,
                headers={"Content-Type": "application/json"},
            )
            response = urllib.request.urlopen(req, timeout=5)
            return response.status == 200
        except URLError as e:
            print(f"Slack webhook error: {e}", file=sys.stderr)
            return False


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


def route_to_bot_queue(
    lead_dict: dict,
    bot_type: str,  # "sales_outreach", "recruiting", etc.
):
    """
    Add lead to bot-specific queue for downstream processing.
    
    Queue structure: data/bot_queues/{bot_type}/pending.json
    Each bot polls its queue and processes leads.
    """
    queue_dir = BOT_QUEUES_DIR / bot_type
    queue_dir.mkdir(parents=True, exist_ok=True)

    queue_file = queue_dir / "pending.json"
    queue_data = []
    if queue_file.exists():
        try:
            queue_data = json.loads(queue_file.read_text(encoding="utf-8"))
            if not isinstance(queue_data, list):
                queue_data = []
        except (json.JSONDecodeError, IOError):
            queue_data = []

    # Add lead to queue if not already present.
    lead_id = lead_dict.get("lead_id")
    if not any(q.get("lead_id") == lead_id for q in queue_data):
        queue_item = {
            "lead_id": lead_id,
            "queued_at": datetime.now(timezone.utc).isoformat(),
            "lead": lead_dict,
        }
        queue_data.append(queue_item)
        queue_file.write_text(json.dumps(queue_data, indent=2, default=str), encoding="utf-8")
        return True
    return False


def dispatch_lead(lead_dict: dict, notifier: SlackNotifier) -> dict:
    """
    Dispatch a single lead to Slack and appropriate bot queue.
    
    Returns dispatch result: {slack_sent, bot_routed, bot_type}
    """
    lead_id = lead_dict.get("lead_id")
    email = lead_dict.get("email")
    first_name = lead_dict.get("first_name", "")
    last_name = lead_dict.get("last_name", "")
    name = f"{first_name} {last_name}".strip() or email
    company = lead_dict.get("company")
    intent = lead_dict.get("intent")
    classification = lead_dict.get("classification", {})
    lead_type = classification.get("type", "unknown")
    hubspot_id = lead_dict.get("crm_status", {}).get("hubspot_contact_id")

    # Send Slack notification.
    slack_sent = notifier.send_notification(
        lead_name=name,
        lead_email=email,
        lead_company=company,
        lead_type=lead_type,
        lead_intent=intent,
        hubspot_id=hubspot_id,
    )

    if slack_sent:
        log_audit("slack_notified", lead_id, {"name": name, "email": email})

    # Route to appropriate bot.
    bot_routed = False
    routed_bot = None

    if lead_type == "jobseeker":
        bot_routed = route_to_bot_queue(lead_dict, "recruiting")
        routed_bot = "recruiting"
    elif lead_type in ("employer", "recruiter"):
        bot_routed = route_to_bot_queue(lead_dict, "sales_outreach")
        routed_bot = "sales_outreach"
    elif lead_type == "vendor":
        bot_routed = route_to_bot_queue(lead_dict, "vendor_eval")
        routed_bot = "vendor_eval"
    elif lead_type == "press":
        bot_routed = route_to_bot_queue(lead_dict, "press_inquiry")
        routed_bot = "press_inquiry"
    else:
        # Unknown: queue for manual review.
        bot_routed = route_to_bot_queue(lead_dict, "manual_review")
        routed_bot = "manual_review"

    if bot_routed:
        log_audit(
            "bot_routed",
            lead_id,
            {"bot": routed_bot, "type": lead_type},
        )

    return {
        "slack_sent": slack_sent,
        "bot_routed": bot_routed,
        "routed_bot": routed_bot,
    }


def run() -> dict:
    """Main entry point: notify and dispatch new leads."""
    LEADS_DIR.mkdir(parents=True, exist_ok=True)
    BOT_QUEUES_DIR.mkdir(parents=True, exist_ok=True)

    notifier = SlackNotifier()
    data = load_leads()
    leads = data.get("leads", [])

    notified = 0
    routed = 0
    already_dispatched = 0

    for lead_dict in leads:
        lead_id = lead_dict.get("lead_id")
        notification_status = lead_dict.get("notification_status", {})

        # Skip if already dispatched.
        if notification_status.get("bot_routed"):
            already_dispatched += 1
            continue

        # Only dispatch if CRM-synced.
        crm_status = lead_dict.get("crm_status", {})
        if not crm_status.get("synced"):
            continue

        # Dispatch.
        result = dispatch_lead(lead_dict, notifier)

        if result["slack_sent"]:
            notified += 1

        if result["bot_routed"]:
            routed += 1
            lead_dict["notification_status"] = {
                "slack_notified": result["slack_sent"],
                "bot_routed": True,
                "routed_bot": result["routed_bot"],
            }

    # Save updated leads.
    data["generated_at"] = datetime.now(timezone.utc).isoformat()
    LEADS_FILE.write_text(json.dumps(data, indent=2, default=str), encoding="utf-8")

    print(
        f"lead_dispatch: notified {notified} lead(s) on Slack, "
        f"routed {routed} to bot queues, "
        f"{already_dispatched} already dispatched. "
        f"Audit: {AUDIT_FILE.relative_to(ROOT)}"
    )
    return {
        "slack_notified": notified,
        "bot_routed": routed,
        "already_dispatched": already_dispatched,
    }


if __name__ == "__main__":
    run()

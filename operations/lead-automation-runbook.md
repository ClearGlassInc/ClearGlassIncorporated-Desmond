# ClearGlass Lead Capture & Bot Trigger Automation

## Overview

This runbook documents the complete lead capture, routing, notification, and bot dispatch system for ClearGlass Inc. The system automatically captures leads from website contact forms, emails, and referral sources; classifies them; syncs to HubSpot CRM; notifies the sales team on Slack; and routes leads to appropriate downstream bots for follow-up.

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    Lead Sources                                 │
│  FormSubmit.co | Email Forwarding | Google Referrals | Manual   │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
           ┌──────────────────────────┐
           │  lead-capture-gateway    │  (Every 15 minutes)
           │  lead_capture_bot.py     │  Polls sources, normalizes
           └────────────┬─────────────┘
                        │
           data/leads/incoming-leads.json (append-only)
                        │
                        ▼
           ┌──────────────────────────┐
           │    lead-router           │  (On push to leads file)
           │    lead_routing_bot.py   │  Syncs to HubSpot
           └────────────┬─────────────┘
                        │
              HubSpot Contact Created
                        │
                        ▼
           ┌──────────────────────────┐
           │   lead-dispatch          │  (On push to leads file)
           │ lead_notify_and_dispatch │  Slack + bot routing
           └────────────┬─────────────┘
                        │
        ┌───────────────┼───────────────┐
        ▼               ▼               ▼
    #sales-leads   Bot Queues      Audit Log
    (Slack)        (JSON)          (JSON)
        │
        ├─→ sales_outreach (Employer/Recruiter)
        ├─→ recruiting (Jobseeker)
        ├─→ vendor_eval (Vendor)
        ├─→ press_inquiry (Press)
        └─→ manual_review (Unknown)
```

## Components

### Phase 1: Lead Capture (`lead-capture-gateway.yml`)

**Frequency:** Every 15 minutes (scheduled) or manually via `workflow_dispatch`

**Bot:** `bots/lead_capture_bot.py`

**Responsibilities:**
- Polls FormSubmit.co inbox (via environment variable `FORMSUBMIT_INBOX_PATH` or API)
- Parses email forwarding inbox for new submissions
- Extracts structured fields: name, email, company, job title, intent
- Performs basic intent classification (jobseeker, employer, recruiter, vendor, press)
- Deduplicates by FormSubmit ID or email+timestamp hash
- Normalizes to schema in `data/leads/schema.json`
- Appends to `data/leads/incoming-leads.json` (append-only log)

**Environment Variables:**
```bash
FORMSUBMIT_INBOX_PATH  # Path to folder with .eml files from FormSubmit forwarding
```

**Output:**
- `data/leads/incoming-leads.json` — JSON log with all captured leads
- Git commit pushed to main with message "Capture new leads from contact forms"

**Failure Mode:**
- If any source is unreachable, skips that source and continues
- If JSON parsing fails, logs error and skips the malformed submission
- Never drops or loses a lead

### Phase 2: Lead Routing (`lead-router.yml`)

**Trigger:** Push to `data/leads/incoming-leads.json`

**Bot:** `bots/lead_routing_bot.py`

**Responsibilities:**
- Reads unsynced leads from `data/leads/incoming-leads.json`
- Connects to HubSpot (via `HUBSPOT_API_KEY` secret)
- Creates/updates HubSpot contact with:
  - Email, name, company, job title, phone
  - Lead type classification
  - Source (website form, email, etc.)
- Populates `crm_status` object with:
  - `synced: true`, `hubspot_contact_id`, `last_sync_at`
  - `hubspot_status: "subscriber"` (initial lifecycle stage)
- Logs all CRM operations to `data/leads/audit.json`

**Environment Variables:**
```bash
HUBSPOT_API_KEY  # HubSpot API key (from GitHub secret)
```

**Output:**
- Updates `data/leads/incoming-leads.json` with CRM sync status
- Appends audit events to `data/leads/audit.json`
- Git commit pushed to main with message "Route leads to CRM and prep for dispatch"

**Failure Mode:**
- If HubSpot API fails: logs error, marks lead as failed, does NOT drop lead
- Respects HubSpot rate limits with exponential backoff
- Next run will retry failed syncs

**HubSpot Mock Mode:**
- If `HUBSPOT_API_KEY` is unset or "mock-key", bot runs in mock mode
- Generates synthetic contact IDs (deterministic per email)
- Useful for testing/CI without actual credentials

### Phase 3: Notification & Dispatch (`lead-dispatch.yml`)

**Trigger:** Push to `data/leads/incoming-leads.json`

**Bot:** `bots/lead_notify_and_dispatch.py`

**Responsibilities:**
- Reads CRM-synced leads from `data/leads/incoming-leads.json`
- Sends Slack notification to `#sales-leads` channel with:
  - Lead name, email, company
  - Lead type (jobseeker/employer/recruiter/vendor/press)
  - Intent summary
  - HubSpot contact link
- Routes lead to bot-specific queue based on classification:
  - **Jobseeker** → `data/bot_queues/recruiting/pending.json`
  - **Employer/Recruiter** → `data/bot_queues/sales_outreach/pending.json`
  - **Vendor** → `data/bot_queues/vendor_eval/pending.json`
  - **Press** → `data/bot_queues/press_inquiry/pending.json`
  - **Unknown** → `data/bot_queues/manual_review/pending.json`
- Logs dispatch events to `data/leads/audit.json`

**Environment Variables:**
```bash
SLACK_WEBHOOK_URL       # Slack incoming webhook URL (from GitHub secret)
SLACK_SALES_CHANNEL     # Slack channel for notifications (default: #sales-leads)
```

**Output:**
- Updates `data/leads/incoming-leads.json` with notification status
- Creates/updates bot queue JSON files in `data/bot_queues/{bot_type}/pending.json`
- Appends audit events to `data/leads/audit.json`
- Slack message posted to configured channel
- Git commit pushed to main with message "Dispatch leads to sales channel and bot queues"

**Failure Mode:**
- If Slack webhook is unreachable: logs error, continues with bot routing anyway
- If bot queue write fails: logs error, retries on next run
- Never loses a lead

## Lead Classification

Leads are automatically classified into types based on pattern matching against:
- Intent field (from form)
- Message body (from contact form or email)
- Job title (if provided)
- Email domain (heuristics like "recruiter.com" or "linkedin.com")

**Classification Types:**
- **jobseeker**: "looking for opportunity", "resume", "career", "apply"
- **recruiter**: "recruitment", "staffing", "talent", "place candidate"
- **employer**: "hiring", "need talent", "consulting service", "security solution"
- **vendor**: "partnership", "resell", "integrate", "affiliate"
- **press**: "journalist", "reporter", "media", "interview"
- **unknown**: No patterns matched (confidence < threshold)

**Confidence Score:** 0.0–1.0
- Scores are normalized across all types
- Top-matching type is selected
- Confidence indicates strength of classification

## Data Schema

See `data/leads/schema.json` for the complete JSON Schema definition.

### Key Fields

```json
{
  "lead_id": "unique-hash-or-uuid",
  "captured_at": "2026-08-02T12:34:56Z",
  "source": "formsubmit|email|google_referral|manual|webhook",
  "email": "name@example.com",
  "first_name": "John",
  "last_name": "Doe",
  "company": "Acme Corp",
  "job_title": "CISO",
  "phone": "555-1234",
  "intent": "Security audit services",
  "message": "Full message body",
  "classification": {
    "type": "employer|jobseeker|recruiter|vendor|press|unknown",
    "confidence": 0.75,
    "reason": "Pattern match: EMPLOYER score 0.75"
  },
  "crm_status": {
    "synced": true,
    "hubspot_contact_id": "abc123",
    "hubspot_status": "subscriber",
    "last_sync_at": "2026-08-02T12:35:00Z"
  },
  "notification_status": {
    "slack_notified": true,
    "slack_ts": "1234567890.123456",
    "bot_routed": true,
    "routed_bot": "sales_outreach"
  },
  "metadata": {
    "user_agent": "Mozilla/5.0...",
    "ip_address": "203.0.113.42",
    "utm_source": "google",
    "utm_campaign": "q3-growth"
  }
}
```

## Audit Trail

All operations are logged to `data/leads/audit.json` with:
- Timestamp (ISO 8601 UTC)
- Event type: `slack_notified`, `bot_routed`, `crm_sync_success`, `crm_sync_failed`, etc.
- Lead ID
- Details object with context

Example:
```json
{
  "timestamp": "2026-08-02T12:35:15Z",
  "type": "slack_notified",
  "lead_id": "a1b2c3d4e5f6g7h8",
  "details": {
    "name": "John Doe",
    "email": "john@example.com",
    "channel": "#sales-leads"
  }
}
```

## Setup & Configuration

### GitHub Secrets Required

1. **`HUBSPOT_API_KEY`** (optional)
   - HubSpot API key for CRM sync
   - If unset, routing bot runs in mock mode (for testing)

2. **`SLACK_WEBHOOK_URL`** (optional)
   - Slack incoming webhook URL
   - Required to send Slack notifications
   - Format: `https://hooks.slack.com/services/T00000000/B00000000/XXXXXXXXXXXXXXXXXXXX`

3. **`SLACK_SALES_CHANNEL`** (optional)
   - Slack channel name (default: `#sales-leads`)
   - Used for sales lead notifications

4. **`FORMSUBMIT_INBOX_PATH`** (optional)
   - Path to folder where FormSubmit.co emails are forwarded
   - Format: `.eml` files in a directory
   - Can also use FormSubmit.co API if configured

### Manual Lead Entry

To manually add leads for testing or direct entry:

1. Create `data/leads/pending-manual.json`:
   ```json
   [
     {
       "name": "Jane Doe",
       "email": "jane@example.com",
       "company": "BigCorp Inc",
       "job_title": "VP Security",
       "intent": "Enterprise security audit"
     }
   ]
   ```

2. Trigger lead capture workflow manually or wait for next scheduled run

3. Leads are captured, file is cleared, and pipeline continues

## Testing

### Unit Tests

```bash
# Test lead capture classification
python3 tests/test_lead_capture.py

# Test CRM routing
python3 tests/test_lead_routing.py
```

### Integration Testing

1. **Manually add a test lead:**
   ```bash
   echo '[{"name":"Test User","email":"test@example.com","intent":"Testing"}]' > data/leads/pending-manual.json
   ```

2. **Trigger capture workflow:**
   - Go to GitHub Actions → `lead-capture-gateway` → `Run workflow`

3. **Observe pipeline:**
   - Check `data/leads/incoming-leads.json` for captured lead
   - Check `data/leads/audit.json` for events
   - Check `data/bot_queues/*/pending.json` for routed lead
   - Check Slack channel (if webhook configured)

## Monitoring & Troubleshooting

### Check Capture Status

```bash
# View latest leads
cat data/leads/incoming-leads.json | jq '.leads[-3:]'

# Count by classification
cat data/leads/incoming-leads.json | jq '[.leads[].classification.type] | group_by(.) | map({type: .[0], count: length})'
```

### Check CRM Sync Status

```bash
# Find unsynced leads
cat data/leads/incoming-leads.json | jq '.leads[] | select(.crm_status.synced == false) | {email, classification}'
```

### Check Audit Trail

```bash
# View recent events
cat data/leads/audit.json | jq '.events[-10:]'

# Count events by type
cat data/leads/audit.json | jq '[.events[].type] | group_by(.) | map({type: .[0], count: length})'

# Find failures
cat data/leads/audit.json | jq '.events[] | select(.type | contains("failed"))'
```

### Check Bot Queues

```bash
# View leads routed to sales_outreach
cat data/bot_queues/sales_outreach/pending.json | jq '.[] | .lead.email'
```

### Troubleshooting Slack Notifications

- If no Slack messages appear:
  1. Check webhook URL is correct: `github.com/settings/secrets/actions`
  2. Check channel name: `echo $SLACK_SALES_CHANNEL`
  3. Check audit trail for notification failures: `grep slack_notified data/leads/audit.json`
  4. Test webhook manually:
     ```bash
     curl -X POST $SLACK_WEBHOOK_URL -d '{"text":"Test"}'
     ```

### Troubleshooting CRM Sync

- If leads aren't syncing to HubSpot:
  1. Check API key in secrets
  2. Verify HubSpot account has API access
  3. Check audit trail for sync errors: `grep crm_sync data/leads/audit.json`
  4. Confirm email format is valid

## Operational Runbook

### Daily Operations

1. **Morning:** Check Slack #sales-leads for overnight captures
2. **Throughout day:** New leads appear in #sales-leads as they arrive
3. **End of day:** Verify no leads queued in bot_queues for follow-up

### Weekly Operations

1. **Monday:** Audit classification accuracy
   ```bash
   cat data/leads/incoming-leads.json | jq '.leads[] | select(.captured_at > "2026-08-01") | {email, classification}'
   ```

2. **Wednesday:** Review CRM sync rate
   ```bash
   cat data/leads/incoming-leads.json | jq '.stats'
   ```

3. **Friday:** Audit trail summary
   ```bash
   cat data/leads/audit.json | jq '[.events[-100:][].type] | group_by(.) | map({type: .[0], count: length})'
   ```

### Incident Response

- **Lead not captured:** Check capture workflow logs, verify FormSubmit inbox
- **Lead not synced to CRM:** Check HubSpot API key, verify rate limits
- **Slack notification failed:** Check webhook URL, verify channel permissions
- **Lead data lost:** Check Git history (append-only design prevents data loss)

## Performance & Limits

| Item | Limit | Note |
|------|-------|------|
| Capture frequency | Every 15 min | Configurable via cron schedule |
| CRM API rate limit | HubSpot free tier: 500/day | Implement backoff if exceeded |
| Slack API rate limit | 1 msg/sec per channel | Built-in retries |
| JSON file size | No limit | Data grows over time; archive after 1 year |

## Future Enhancements

1. **Archive old leads** — Move leads >6 months old to `data/leads/archive/`
2. **Lead scoring** — Add scoring model for lead quality/readiness
3. **Two-way CRM sync** — Pull updates from HubSpot (e.g., if lead marked as contacted)
4. **Email template system** — Generate follow-up email drafts per classification
5. **Analytics dashboard** — Daily/weekly metrics on lead volume, classification, conversion
6. **Webhook ingestion** — Accept leads directly from external forms (not just FormSubmit)
7. **Duplicate detection** — Advanced matching to find duplicate leads across sources
8. **Lead enrichment** — Enrich with firmographic/technographic data

## Support

- **Questions?** Check this runbook first
- **Bug reports?** File issue in GitHub
- **Feature requests?** Start a discussion
- **Emergency?** Contact infrastructure team

---

**Document Version:** 1.0  
**Last Updated:** 2026-08-02  
**Author:** ClearGlass Lead Automation System  
**Status:** Production Ready

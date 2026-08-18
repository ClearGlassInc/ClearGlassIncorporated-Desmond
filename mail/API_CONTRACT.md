# ClearGlass Mail API Contract

The API is intentionally provider-agnostic. SMTP/IMAP credentials and transport details remain outside the browser.

## Message resource

```json
{
  "id": "opaque-message-id",
  "thread_id": "opaque-thread-id",
  "mailbox": "INBOX",
  "subject": "Example",
  "from": {"name": "Example", "address": "sender@example.test"},
  "to": {"name": null, "address": "mail@example.test"},
  "received_at": "RFC-3339 timestamp",
  "preview": "Safe plain-text preview",
  "has_html": true,
  "attachment_count": 1,
  "labels": ["INBOX"],
  "read": false,
  "provenance": {
    "message_sha256": "64-hex-character digest",
    "parser_schema_version": "1.0"
  }
}
```

## Required API properties

- All message identifiers are opaque and non-sequential.
- Every read/write operation is authorized against the authenticated mailbox owner.
- Search is parameterized; message content is never interpolated into database queries.
- HTML returned to the browser must already have passed a trusted sanitizer or be rendered inside an appropriately isolated sandbox.
- Attachment downloads require authorization and return immutable content with a content-disposition policy; never use the submitted filename as a filesystem path.
- Mutating endpoints must be idempotent where practical and must emit an audit event.
- Rate limits apply separately to login, search, message fetch, attachment fetch, and outbound-send operations.
- Outbound mail must be queued rather than sent directly inside an HTTP request.

## Suggested endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/api/mailboxes` | List authorized mailboxes |
| GET | `/api/messages` | Paginated mailbox listing |
| GET | `/api/messages/{id}` | Fetch one message |
| POST | `/api/messages/{id}/read` | Mark message read |
| POST | `/api/messages/{id}/labels` | Add/remove labels |
| POST | `/api/drafts` | Create/update a draft |
| POST | `/api/send` | Queue outbound mail |
| GET | `/api/attachments/{id}` | Authorized attachment retrieval |
| GET | `/api/audit/events` | Security/audit events for authorized operators |

No endpoint in this contract creates a public mail account or changes DNS. Those operations belong to the infrastructure provisioning layer and require separate operational controls.

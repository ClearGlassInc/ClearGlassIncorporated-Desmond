# Ontario Security Quick-Audit — CRM pipeline

This is the minimum operator pipeline for the CAD $249 Quick-Audit. It keeps
personal data in the corporate inbox or chosen CRM, never in browser analytics,
GitHub issues, source control, or public JSON.

## Required fields

| Field | Source | Rule |
|---|---|---|
| Lead ID | Browser-generated hidden form field | Non-secret correlation key; retain in CRM |
| Created at | Inbox or CRM | Store as UTC |
| Organization and authorized contact | Scope form | CRM only; do not copy to analytics |
| Offer | Hidden form field | `Security Quick-Audit` |
| Value | Hidden form field | `249 CAD`; forecast until Stripe verification |
| UTM source, medium, campaign, term, content | Session attribution | Optional; no query string or form values |
| Pipeline stage | Operator | Use exactly one stage below |
| Authorization status | Operator | `not_requested`, `pending`, `confirmed`, or `declined` |
| Stripe status | Stripe/dashboard or verified webhook | Never infer `paid` from a return-page visit |
| Next action and due date | Operator | Required for every open record |

## Stages and entry criteria

| Stage | Entry criterion | Next action |
|---|---|---|
| New qualified lead | Scope form received | Check audience fit and reply within one business day |
| Fit confirmed | Ontario SMB, 10–250 staff, Microsoft 365, and authorized buyer fit are confirmed | Send the one-price offer and scope summary |
| Checkout started | `begin_checkout` is observed or buyer says checkout began | Help only if requested; do not mark paid |
| Payment verified | Stripe dashboard or a verified server-side event confirms payment | Send scope and authorization record |
| Scope authorized | Authorized contact, assets, exclusions and evidence channel are recorded | Confirm delivery date and evidence list |
| Audit in progress | Required evidence is complete and review has begun | Complete read-only evaluation |
| Report delivered | Report is delivered to the authorized contact | Schedule the review call |
| Review complete | Review is held and next actions are recorded | Close, nurture or scope a separate engagement |
| Closed — not fit | Audience, authorization or service need is outside the offer | Refer or close with a reason; no pressure sequence |

## Event-to-stage rules

- `generate_lead` and `lead_received` are acquisition signals; only the received
  inbox submission creates the CRM record.
- `begin_checkout` and `checkout_return` are funnel signals. Neither proves a
  successful payment.
- `payment_verified`, `scope_authorized`, `report_delivered`, and
  `review_complete` must be recorded by an operator or trusted server-side
  integration. They must not be emitted from public page JavaScript.
- Do not place names, emails, phone numbers, free-text concerns, tenant IDs,
  evidence, or Stripe identifiers in analytics event properties.

## Weekly pipeline view

Review counts and age by stage, qualified-lead-to-payment rate, median time to
first response, authorized-scope-to-delivery time, and source/campaign. Investigate
records with no next action or due date. Delete test submissions and follow the
published privacy terms for retention and access requests.

# Stripe setup — connection state and what it takes to go live

Status of the live Stripe account as verified against the Stripe API on **2026-08-05**.
Re-run the checks below before trusting this page; it is a snapshot, not a live view.

## 1. Connection check (verified, not assumed)

| Check | Result | Source |
|---|---|---|
| Account reachable | ✅ `acct_1RlYxRL8uR92FksU` | `GET /v1/account` |
| Mode | **live** (`livemode: true`) | `GET /v1/balance` |
| Country / default currency | CA / CAD | account object |
| **Can accept charges** | ❌ `charges_enabled: false` | account object |
| **Can pay out** | ❌ `payouts_enabled: false` | account object |
| Onboarding submitted | ❌ `details_submitted: false` | account object |
| Capabilities | ❌ none granted (`capabilities: {}`) | account object |
| Bank account attached | ❌ `external_accounts.total_count: 0` | account object |
| Webhook endpoints | ❌ **0 registered** | `GET /v1/webhook_endpoints` |
| Checkout Sessions ever created | 0 | `GET /v1/checkout/sessions` |
| Balance | 0 CAD | `GET /v1/balance` |

**Bottom line: the account cannot accept a single payment today.** Stripe reports
`requirements.disabled_reason: "requirements.past_due"`. The code in this repo is not
the blocker — the account was created (2025-07-16) and never activated.

Outstanding `requirements.past_due`:

- `business_profile.product_description`
- `business_profile.support_phone`
- `business_profile.url`
- `tos_acceptance.date`
- `tos_acceptance.ip`

None of these can be set from this repo. They are completed by a human at
<https://dashboard.stripe.com/account/onboarding>.

## 2. Architecture

Stripe **Checkout Sessions**, hosted page, redirect flow. Not Elements, not Connect:

- **Not Connect** — ClearGlass sells its own services and collects its own revenue.
  There are no connected accounts (`GET /v1/accounts` is empty) and no third-party
  sellers to pay. Connect would add onboarding, KYC and payout obligations for a
  marketplace that does not exist.
- **Not Elements** — Elements buys design control at the cost of owning PCI scope,
  payment-method logic and SCA handling. The storefront has no custom-checkout
  requirement that justifies that.
- **Checkout Sessions** — Stripe hosts the page, dynamic payment methods (cards,
  Link, Apple Pay, Google Pay) are enabled from the Dashboard with no code change,
  and Apple/Google Pay give the one-click flow without an Express Checkout Element.

Subscription support is in place: `monitoring` is a recurring offer, and a cart
containing it produces a `subscription`-mode session.

## 3. Required Stripe Dashboard settings

Each of these is a human step; none can be done from code.

1. **Activate the account** — complete the `requirements.past_due` list above.
   Until `charges_enabled: true`, every checkout attempt fails.
2. **Attach a payout bank account** — Settings → Bank accounts. Then set
   `PAYOUT_EXTERNAL_ACCOUNT_ID` to the resulting `ba_…` token (never raw digits;
   `app/payments.py::payout_bank_info` rejects those).
3. **Enable payment methods** — Settings → Payment methods. Cards + Link at minimum;
   Apple Pay and Google Pay require domain verification for one-click.
4. **Register the webhook endpoint** (see §5) and copy its signing secret into
   `STRIPE_WEBHOOK_SECRET`.
5. **Stripe Tax** (only if you are registered to collect) — Settings → Tax: set the
   origin address, add a registration per jurisdiction (GST/HST for CA), and pick a
   default product tax code. **Then** set `STRIPE_AUTOMATIC_TAX=true`. Enabling the
   env var before the Dashboard side is configured makes Stripe reject session
   creation, which is why it defaults to off.
6. **Radar** — the default rules are active on all accounts. Review Radar → Rules
   after the first live payments; no code change needed.

## 4. Environment variables

| Variable | Required | Purpose |
|---|---|---|
| `STRIPE_SECRET_KEY` | to leave mock mode | Unset ⇒ deterministic mock sessions, no network |
| `STRIPE_WEBHOOK_SECRET` | **yes, in production** | Unset ⇒ webhooks are accepted but marked unverified |
| `STRIPE_PUBLISHABLE_KEY` | no | Not used by the hosted-page flow |
| `STRIPE_AUTOMATIC_TAX` | no (default off) | `true` turns on Stripe Tax; requires §3.5 first |
| `PRICEBOOK_PATH` | no | Overrides the bundled `app/data/pricebook.json` |
| `CHECKOUT_SUCCESS_URL` / `CHECKOUT_CANCEL_URL` | yes in production | `{CHECKOUT_SESSION_ID}` is appended automatically if absent |
| `PAYOUT_EXTERNAL_ACCOUNT_ID` | for payout reconciliation | Stripe `ba_…` token |

`STRIPE_WEBHOOK_SECRET` being unset is the dangerous one: `verify_webhook` returns
`verified: false` rather than rejecting, and the route only enforces verification
when a secret is configured. An unset secret in production means anyone who can
reach `/webhooks/stripe` can post a forged `checkout.session.completed` and book a
fake paid order.

## 5. Webhooks to configure

Endpoint: `https://<control-plane-host>/webhooks/stripe`

| Event | Why |
|---|---|
| `checkout.session.completed` | Books the order. Honours `payment_status`, so an async method books `pending`, not `paid` |
| `checkout.session.async_payment_succeeded` | Promotes that pending order to paid |
| `checkout.session.async_payment_failed` | Marks it failed |
| `invoice.paid` | Subscription renewals — without it, only month one is ever recorded |
| `invoice.payment_failed` | Failed renewal, needs dunning |
| `charge.refunded` | Audit trail for settled refunds |
| `charge.dispute.created` / `charge.dispute.closed` | Chargebacks |
| `payment_intent.payment_failed` | Failed payment visibility |
| `payout.created` / `.updated` / `.paid` / `.failed` / `.canceled` | Settlement to the bank account |

Handling is idempotent on redelivery: orders key on `orders.external_ref`, payouts on
`stripe_payout_id`.

Local testing:

```bash
stripe listen --forward-to localhost:8000/webhooks/stripe
stripe trigger checkout.session.completed
```

## 6. Pricing is server-side — do not undo this

`POST /checkout/session` accepts **SKUs and quantities only**. Amounts are resolved
from `app/data/pricebook.json` via `app/pricebook.py`. Before this, the request body
carried `amount` and that value went straight into Stripe's `unit_amount` — a buyer
could post `amount: 1` and take a CAD $2,500 engagement for a cent.

`tests/test_pricebook.py` pins this, including a check that `CheckoutLineItem` in the
OpenAPI schema has exactly the fields `{sku, quantity}`. If you add a price-shaped
field back to that contract, the suite fails on purpose.

Changing a price means editing `app/data/pricebook.json` (and the display copy in
`storefront/lib/catalog.ts`, plus `data/store/catalog.json` at the repo root). Live
price changes through the API remain HIGH risk and stay behind the approval gate.

## 7. Validation checklist

Run in order. Do not skip 1 — everything after it fails while the account is inactive.

- [ ] `charges_enabled: true` and `payouts_enabled: true` on the account
- [ ] Payout bank account attached; `GET /payments/payout-account` returns `configured: true` with no warnings
- [ ] `STRIPE_SECRET_KEY` set; `POST /checkout/session` returns `"mode": "live"` and a `checkout.stripe.com` URL
- [ ] Tampered cart refused: `{"items":[{"sku":"quick-audit","quantity":1,"amount":1}]}` still totals `24900`
- [ ] Unknown SKU returns 400 and leaves a `rejected` row in `/events`
- [ ] Webhook endpoint registered; `STRIPE_WEBHOOK_SECRET` set; a forged unsigned POST to `/webhooks/stripe` returns 400
- [ ] A real test-mode purchase produces an `orders` row with `status: paid` and the matching `external_ref`
- [ ] Redelivering that same webhook produces **no** second order (`order_event_duplicate_skipped` in `/events`)
- [ ] Subscription: `{"items":[{"sku":"monitoring","quantity":1}]}` returns `checkout_mode: "subscription"`
- [ ] A subscription renewal (`invoice.paid`, `billing_reason: subscription_cycle`) books a second order
- [ ] `GET /ready` reports the database reachable
- [ ] If Stripe Tax is on: a session shows non-zero `total_details.amount_tax` for a registered jurisdiction

## 8. What is still mock

With no `STRIPE_SECRET_KEY`, `create_checkout_session` returns a deterministic
`cs_mock_…` session and never calls Stripe. That is the correct default for CI and
local work, and it is why the whole test suite runs offline. It also means a green
test run is **not** evidence that live payments work — only the checklist above is.

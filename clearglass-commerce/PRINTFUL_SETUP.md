# Printful dropship fulfillment — setup and current state

ClearGlass sells; Printful prints and ships. This page covers what is wired, what
is not, and the human steps that no amount of code can do for you.

**Status: not connected.** `PRINTFUL_API_KEY` is unset, so the control plane runs
in mock mode, places no supplier orders, and makes no network calls to Printful.
Nothing on this page has been executed against a live account.

## The one rule

**Money in does not imply a parcel out.** A paid order that cannot ship — bad
address, no supplier variant, supplier unreachable — is marked `unfulfillable`
and written to the audit ledger. It is never silently marked done. The customer
has been charged, so it is an open obligation until a human closes it.

Nothing in this integration invents product data. Images, prices, variants and
delivery estimates all come from Printful's own API responses. A catalogue the
control plane cannot read is a catalogue that does not get published.

## Order lifecycle

| Status | Meaning | Who moves it |
|---|---|---|
| `pending` | Paid; nothing sent to the supplier | — |
| `drafted` / `awaiting_approval` | Draft booked at Printful. Costs nothing, prints nothing, deletable | automatic |
| `confirmed` | Human approved. Printful is printing and will ship | **human approval** |
| `shipped` | Tracking received from the supplier | supplier webhook |
| `unfulfillable` | Cannot ship — needs a human, possibly a refund | — |

Drafting is automatic on purpose: the customer has already paid, the draft costs
nothing, and gating the free half of the work would strand a paid order in a
queue. **Confirmation is what spends money and starts an irreversible print run**,
so `printful_confirm_order` is in `ALWAYS_ESCALATE` and cannot execute without an
approved `approvals` row. `PRINTFUL_AUTO_CONFIRM` records that you *want*
hands-off confirmation; it does **not** open the gate, and
`tests/test_printful.py` asserts that it doesn't.

## What you have to do (none of it can be done from code)

1. **Create a Printful account** at <https://www.printful.com> and set up a store.
   Free; no upfront inventory cost.
2. **Add products to the store.** Printful calls these "sync products" — a
   catalogue item plus your artwork. The sync *variant* id is what an order line
   references. Until at least one exists there is nothing to sell.
3. **Add a billing method.** Printful charges you per order at confirmation. With
   no card on file, confirmation fails and orders sit unfulfilled.
4. **Create an API token** — Dashboard → Settings → Developers → new private
   token. Set it as `PRINTFUL_API_KEY`. Never commit it.
5. **Register the shipment webhook** at
   `https://<control-plane-host>/fulfillment/webhooks/printful/<PRINTFUL_WEBHOOK_SECRET>`
   for the `package_shipped` event. Generate the secret yourself
   (`openssl rand -hex 32`) and set it as `PRINTFUL_WEBHOOK_SECRET`.
6. **Activate Stripe.** Still the hard blocker — see `STRIPE_SETUP.md`. The
   account cannot accept a payment today, so no order can reach fulfillment at
   all until `charges_enabled: true`.
7. **Enable shipping-address collection** on Stripe Checkout
   (`shipping_address_collection`). Without it, Stripe returns no address and
   every physical order lands `unfulfillable`.

## Environment variables

| Variable | Required | Purpose |
|---|---|---|
| `PRINTFUL_API_KEY` | to leave mock mode | OAuth token, sent as `Authorization: Bearer`. Unset ⇒ no supplier calls at all |
| `PRINTFUL_WEBHOOK_SECRET` | **yes, in production** | Path secret on the shipment webhook. Unset ⇒ the webhook rejects everything |
| `PRINTFUL_STORE_ID` | multi-store accounts only | Sent as `X-PF-Store-Id` |
| `PRINTFUL_AUTO_CONFIRM` | no (default off) | Records intent to auto-confirm. Does not bypass the approval gate |
| `PRINTFUL_API_BASE` | no | Defaults to `https://api.printful.com` |

The webhook secret being unset is the safe direction: it rejects every call
rather than accepting all of them. Failing open there would let anyone mark
orders shipped and suppress the tracking a customer is waiting for.

## Endpoints

| Route | Auth | What it does |
|---|---|---|
| `GET /fulfillment/connection` | open | Credential presence. No network call |
| `POST /fulfillment/verify` | admin | Read-only store identity check |
| `GET /fulfillment/catalog` | open | The supplier's real products, variants, images, prices |
| `GET /fulfillment/orders/{id}` | open | Fulfillment state and tracking for one order |
| `POST /fulfillment/shipments/{id}/confirm` | admin | Queues an approval; **never confirms directly** |
| `POST /fulfillment/webhooks/printful/{secret}` | URL secret | Applies `package_shipped` tracking. Idempotent |

## Running it

```bash
cd clearglass-commerce/control-plane
python -m pytest tests/test_printful.py tests/test_fulfillment.py -q   # 48 tests, offline
psql "$DATABASE_URL" -f migrations/005_fulfillment.sql                 # shipping + shipments
```

The whole suite runs with no Printful credential and no network — every call goes
through an injected requester. A green run is **not** evidence that live
fulfillment works; only a real test order is.

## What is not wired yet

Being explicit, because a half-integration that looks complete is worse than one
that doesn't:

- **Automatic draft booking on payment is not connected.** `book_supplier_draft`
  is written and tested, but the Stripe webhook does not call it, because an
  order does not yet record *what was bought*. `Order` has a total and no line
  items, and the price book maps a SKU to a Stripe Price with no Printful
  `sync_variant_id`. Two things close this: an `order_items` table, and a
  `printful_sync_variant_id` field per price-book offer. Until then, drafts are
  booked by calling `book_supplier_draft` with explicit items.
- **Shipping cost at checkout.** `printful.estimate_shipping` returns the
  supplier's real rates and delivery windows, but checkout does not call it, so
  shipping is not yet charged to the customer or shown before payment.
- **Consumer-facing policies.** Canadian selling needs accurate delivery windows,
  a returns/refund policy, business identification, and GST/HST registration once
  you pass the small-supplier threshold. Printful ships from several countries,
  so customs and duty disclosure matter for cross-border orders. None of this is
  written yet, and none of it should be guessed at.

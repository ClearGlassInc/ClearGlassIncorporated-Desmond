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
| `drafted` | Draft booked at Printful. Costs nothing, prints nothing, deletable | automatic |
| `confirmed` | Human approved. Printful is printing and will ship | **human approval** |
| `shipped` | Tracking received from the supplier | supplier webhook |
| `unfulfillable` | Cannot ship — needs a human, possibly a refund | — |

The shipment row carries one more state of its own, `confirming`: an approval has
been spent and the supplier call is in flight. It exists so a crash mid-call
leaves evidence instead of a row that looks untouched. The next confirmation
attempt reconciles it against Printful — if production started the row settles to
`confirmed` with no second charge; if the call never landed it returns to `draft`
for a fresh approval; if Printful cannot be read it stays `confirming`, which is
the safe stuck state.

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
6. **Confirm Stripe can charge.** See `STRIPE_SETUP.md` — its snapshot is stale
   and needs re-verifying. No order reaches fulfillment until `charges_enabled`
   is true, because nothing is ever paid for.
7. **Register the Stripe webhook**, if it is not already:
   `python scripts/register_stripe_webhook.py --url https://<host>/webhooks/stripe --apply`.
   Payment Links charge the card regardless; without the endpoint no order is
   ever recorded, so nothing reaches fulfillment even on a live account.

Shipping-address collection is **code, and it is now written** — it turns on per
offer via `requires_shipping`. See "What is wired now" below.

## Environment variables

| Variable | Required | Purpose |
|---|---|---|
| `PRINTFUL_API_KEY` | to leave mock mode | OAuth token, sent as `Authorization: Bearer`. Unset ⇒ no supplier calls at all |
| `PRINTFUL_WEBHOOK_SECRET` | **yes, in production** | Path secret on the shipment webhook. Unset ⇒ the webhook rejects everything |
| `PRINTFUL_STORE_ID` | multi-store accounts only | Sent as `X-PF-Store-Id` |
| `PRINTFUL_AUTO_CONFIRM` | no (default off) | Records intent to auto-confirm. Does not bypass the approval gate |
| `PRINTFUL_API_BASE` | no | Defaults to `https://api.printful.com` |
| `SHIPPING_ALLOWED_COUNTRIES` | no (default `CA`) | Where physical goods may be sold and shipped |

The webhook secret being unset is the safe direction: it rejects every call
rather than accepting all of them. Failing open there would let anyone mark
orders shipped and suppress the tracking a customer is waiting for.

## Endpoints

| Route | Auth | What it does |
|---|---|---|
| `GET /fulfillment/connection` | open | Credential presence. No network call |
| `POST /fulfillment/verify` | admin | Read-only store identity check |
| `GET /fulfillment/catalog` | admin | The supplier's real products, variants, images, prices |
| `GET /fulfillment/exceptions` | admin | Paid orders that cannot ship — the queue to work |
| `GET /fulfillment/orders/{id}` | admin | Fulfillment state and tracking for one order |
| `POST /fulfillment/shipments/{id}/confirm` | admin | Queues an approval, or spends one — see below |
| `POST /fulfillment/webhooks/printful/{secret}` | URL secret | Applies `package_shipped` tracking. Idempotent, rate limited |

Only `/connection` is open. `/catalog` is gated because each call is a full
paginated scan of the supplier store; `/orders/{id}` because it exposes tracking,
supplier ids and our cost basis behind a sequential integer. A customer-facing
"where is my parcel" view needs a per-order capability token, which does not
exist yet.

`POST /shipments/{id}/confirm` is two-phase. With no approved approval for that
shipment it queues one and returns its id, sending nothing to the supplier. Once
a human approves, calling it again claims that approval — exactly once — and
confirms with Printful. So the same endpoint both proposes and executes,
depending on whether a human has decided yet.

This is the one action that does **not** go through the generic
`POST /approvals/{id}/execute` dispatcher, because confirmation also has to take
the shipment row in-flight atomically and reconcile a crashed attempt against the
supplier. It is listed as `delegated` in `GET /approvals/coverage`, pointing here.

## Running it

```bash
cd clearglass-commerce/control-plane
python -m pytest tests/test_printful.py tests/test_fulfillment.py \
               tests/test_order_routing.py -q            # 88 tests, offline
psql "$DATABASE_URL" -f migrations/005_fulfillment.sql   # shipping + shipments
psql "$DATABASE_URL" -f migrations/006_order_items.sql   # what was bought
```

The whole suite runs with no Printful credential and no network — every call goes
through an injected requester. A green run is **not** evidence that live
fulfillment works; only a real test order is.

## What is wired now

The chain from payment to parcel is connected:

1. Checkout asks for a shipping address **only when the cart holds a physical
   good** (`requires_shipping` on the offer). A service checkout is unchanged —
   nobody posts a 90-minute consultation.
2. The Stripe webhook records **what** was bought into `order_items`, reading the
   compact `sku×qty` metadata the session carries. Price, name and supplier
   variant are copied from the price book *at time of sale*, because the
   catalogue is editable and an order must be fulfilled as it was sold.
3. Physical orders are routed to Printful as a **draft**. Services stop at step 2.
4. Confirmation still requires a human approval — see the lifecycle above.

To make an offer sellable as a physical good, add both fields to its price-book
entry:

```json
{
  "sku": "clearglass-tee",
  "requires_shipping": true,
  "printful_sync_variant_id": 4012
}
```

`requires_shipping` without a variant id **fails at load**, deliberately: the
alternative is taking money at checkout and stranding the order as unfulfillable.

`SHIPPING_ALLOWED_COUNTRIES` (default `CA`) bounds where physical goods can be
sold. It is a trade control as much as a shipping one — a destination not listed
cannot be checked out, which keeps customs and tax exposure to jurisdictions you
have actually accounted for.

## What is still not wired

Being explicit, because a half-integration that looks complete is worse than one
that doesn't:

- **Shipping cost is not charged.** `printful.estimate_shipping` returns the
  supplier's real rates and delivery windows, and `create_checkout_session`
  accepts a `shipping_amount`, but the price-book checkout does not call the
  estimator — so shipping is currently absorbed, not billed. Wiring it means
  deciding whether to quote live rates or a flat rate, which is a pricing call.
- **Consumer-facing policies.** Canadian selling needs accurate delivery windows,
  a returns/refund policy, business identification, and GST/HST registration once
  you pass the small-supplier threshold. Printful ships from several countries,
  so customs and duty disclosure matter for cross-border orders. None of this is
  written, and none of it should be guessed at.
- **No Printful account exists yet.** Everything above runs in mock mode until
  `PRINTFUL_API_KEY` is set, and no supplier order can be placed without it.

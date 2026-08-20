# Website Analytics — how to see your visitors

Until you do the one step below, **you have no way to know if anyone visits the
site or clicks "Buy."** This wires analytics across all pages; you just pick a
provider and paste one value.

## Current state

`analytics.js` ships on every page (injected by `/stealth-glass.js`) but is
**off by default** — no third-party request, no cookies, no tracking — until a
provider is set. This is deliberate: nothing phones home until you choose.

## Turn it on (about 2 minutes)

Edit the public destination values in
[`analytics-config.js`](../analytics-config.js). Never put a secret or private
CRM credential in that file.

### Option A — Google Analytics 4 (free)
1. Create a property at <https://analytics.google.com> → copy the **Measurement
   ID** (looks like `G-XXXXXXXXXX`).
2. Set:
   ```js
   provider: "ga4",
   measurementId: "G-XXXXXXXXXX",
   ```
3. Keep GA4 consent denied until your approved consent interface calls
   `window.cgAnalyticsConsent(true)`; call `window.cgAnalyticsConsent(false)`
   when consent is declined or withdrawn. The ClearGlass loader disables Google
   Signals and ad-personalization signals by default.
4. Commit, deploy, then use GA4 DebugView to verify `page_view`,
   `begin_checkout`, `generate_lead`, `lead_received` and `checkout_return`.

### Option B — Plausible (paid, cookieless, simpler/privacy-first)
1. Add `www.clearglassinc.com` at <https://plausible.io>.
2. Set `provider: "plausible"` (the domain is already filled in).
3. Commit and verify the same event names in Plausible. Confirm the selected
   account settings and applicable consent requirements before production use.

### Option C — reviewed first-party endpoint

Set `provider: "first-party"` and `endpoint: "/api/analytics"` only after that
same-origin route exists and has documented retention, access and deletion
controls. GitHub Pages does not provide this endpoint by itself.

## What you'll be able to see

Once a destination is enabled and verified: visitors per day, acquisition
source, landing pages and the Quick-Audit funnel. A Stripe return-page event is
not a purchase; revenue must come from the Stripe dashboard or a verified
server-side webhook.

## What analytics does NOT do

It **measures** traffic; it does not **create** it. Traffic comes from SEO and
outreach (see `marketing/outreach/`), and purchases require live checkout (see
`docs/STORE_GO_LIVE.md`). Analytics tells you whether those efforts are working.

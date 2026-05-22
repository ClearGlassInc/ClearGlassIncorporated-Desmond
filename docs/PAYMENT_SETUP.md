# ClearGlass Bitcoin Checkout Setup

## Objective

Connect the static GitHub Pages website to a secure hosted Bitcoin checkout flow for:

- Subscription name: ClearGlass Premium Access
- Price: $20/month
- Payment method: Bitcoin checkout
- Delivery: access provisioned after payment confirmation

## Recommended architecture

GitHub Pages is static hosting. Do not put payment secrets in frontend files.

Use this model:

1. GitHub Pages frontend displays the subscription offer.
2. The Subscribe with Bitcoin button redirects to a hosted checkout provider.
3. BTCPay Server or another secure processor creates and tracks the invoice.
4. A server-side webhook confirms payment status.
5. ClearGlass provisions access after invoice settlement.

## Configure the frontend

Edit:

```text
assets/js/config.js
```

Replace:

```js
checkoutUrl: "https://YOUR-BTCPAY-SERVER.example.com/apps/YOUR_APP_ID/pos"
```

with your real hosted checkout URL.

## Configure success return

Set your checkout provider return URL to:

```text
https://YOUR-GITHUB-PAGES-DOMAIN/success.html
```

For ClearGlassInc GitHub Pages this may be:

```text
https://clearglassinc.github.io/success.html
```

Use your production custom domain if configured.

## Audit logging hooks

The frontend includes browser audit hooks for:

- page_view
- checkout_click
- payment_success_page_view

For production, send these events to a serverless endpoint such as Cloudflare Workers, Netlify Functions, Vercel Functions, or AWS Lambda API Gateway. Keep secrets server-side only.

Do not log private keys, wallet seed phrases, API tokens, full sensitive customer data, or payment credentials.

## Webhook confirmation

Payment confirmation should be handled server-side by the payment provider webhook.

Recommended webhook process:

1. Provider sends invoice event to a serverless endpoint.
2. Endpoint verifies webhook signature.
3. Endpoint checks invoice status.
4. Endpoint records invoice ID, status, amount, currency, and timestamp.
5. Endpoint triggers access delivery or sends an internal notification.

## Manual payment fallback

Manual payment is disabled by default.

To enable only if hosted checkout is unavailable:

```js
manualBitcoinEnabled: true,
manualBitcoinAddress: "PUBLIC_RECEIVING_ADDRESS_ONLY"
```

Use only a public receiving address. Never put private keys or seed phrases in source code.

## Production checklist

- [ ] Hosted checkout URL configured
- [ ] Return URL points to `/success.html`
- [ ] Webhook endpoint verifies provider signatures
- [ ] Access delivery workflow created
- [ ] Support email updated
- [ ] Manual fallback disabled unless necessary
- [ ] No secrets in GitHub Pages files
- [ ] Site tested on mobile
- [ ] GitHub Pages publishing source set to main/root

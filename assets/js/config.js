/*
  ClearGlass payment configuration.

  SECURITY RULE:
  Do not place private keys, API tokens, wallet seeds, xpub secrets, or payment credentials here.

  GitHub Pages is static hosting. Use this file only for PUBLIC configuration:
  - Hosted BTCPay Server checkout URL
  - Hosted Coinbase Commerce / OpenNode / equivalent checkout URL
  - Public support email
  - Public serverless audit endpoint, if available
*/

window.ClearGlassConfig = {
  subscriptionName: "ClearGlass Premium Access",
  priceLabel: "$20/month",
  checkoutUrl: "https://YOUR-BTCPAY-SERVER.example.com/apps/YOUR_APP_ID/pos",
  checkoutProvider: "BTCPay Server",
  supportEmail: "support@clearglassinc.com",

  /*
    Optional audit webhook endpoint.
    Use a serverless endpoint such as Cloudflare Workers, Netlify Functions,
    Vercel Functions, or AWS Lambda API Gateway.
    Keep secrets server-side only. Leave blank to disable frontend audit pings.
  */
  auditLogEndpoint: "",

  /*
    Optional fallback manual instructions.
    Do not use a private wallet or seed phrase.
    If used, this must be a public receiving address only.
  */
  manualBitcoinEnabled: false,
  manualBitcoinAddress: "PASTE_PUBLIC_RECEIVING_ADDRESS_ONLY_IF_REQUIRED"
};

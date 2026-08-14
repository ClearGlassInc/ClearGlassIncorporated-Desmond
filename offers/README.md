# ClearGlass Inc. — Revenue / Offer Assets

Conversion-ready, **no-backend** sales assets that work on GitHub Pages. Every page is
self-contained (inline CSS) so nothing depends on the main site's stylesheets.

## Pages

| File | Purpose |
|------|---------|
| `index.html` | Services hub linking all offers |
| `hardening-sprint.html` | Flagship fixed-fee offer (M365 + Windows hardening) + enquiry form |
| `security-quick-audit.html` | CAD $249 Ontario SMB offer (read-only posture check) |
| `security-quick-audit-sample-report.html` | Clearly labeled synthetic report example |
| `security-quick-audit-methodology.html` | Published scope, evidence and scoring method |
| `phipa-readiness.html` | PHIPA lead magnet (email capture) → drives assessments |
| `phipa-readiness-checklist.html` | The deliverable; "Save as PDF" button (print-to-PDF) |
| `thank-you.html` | Post-submit confirmation page |
| `../tools/Invoke-CGSecurityAudit.ps1` | Read-only delivery engine: generates the branded findings report |

## ⚠️ Before going live — replace these placeholders

Search the `offers/` folder for `REPLACE` (and `data-cg-placeholder`) and fill in:

1. **Booking link** — `https://cal.com/REPLACE_BOOKING/...`
   → your Cal.com / Calendly scheduling URL.
2. **Stripe deposit link** — `https://buy.stripe.com/REPLACE_DEPOSIT`
   → a [Stripe Payment Link](https://stripe.com/payments/payment-links) for the sprint deposit.
3. **Stripe Quick-Audit link — configured:** `https://buy.stripe.com/8x2eVe7ZG0mFam00LG4Ni03`
   → In Stripe, set the post-checkout redirect to
   `https://www.clearglassinc.com/offers/thank-you.html?source=stripe&offer=quick-audit&status=checkout_return`.
   A return to this page is an attribution signal, not proof of payment. Confirm
   revenue from the Stripe dashboard or a verified Stripe webhook before marking
   the CRM opportunity paid.
4. **Form endpoint** — `https://formspree.io/f/REPLACE_FORM_ID`
   → a [Formspree](https://formspree.io) or [Tally](https://tally.so) form ID.
   Configure the form's redirect/confirmation to `thank-you.html`, and for the PHIPA
   form, set an auto-reply that sends the checklist link.

Quick check that nothing was missed:

```bash
grep -rn "REPLACE" offers/
```

The Quick-Audit scope form uses FormSubmit to route a qualified lead to the
corporate inbox. FormSubmit may send a one-time activation message to that inbox
before it will forward live submissions. The static form records a generated lead
ID, offer, pipeline stage and UTM fields, but never copies field values into browser
analytics or storage.

Use `../operations/quick-audit-crm-pipeline.md` for the stage definitions,
required fields, payment-verification rule and weekly pipeline view.

## Payment & delivery model

- **No funds are ever auto-sent.** All payments go through **Stripe hosted checkout /
  Payment Links** or an issued **Stripe / Wave invoice**.
- The PowerShell tool is **read-only** and **authorization-gated** — it changes nothing
  and assesses only systems/domains you own or are authorized to assess.

## Compliance guardrails (built in)

- **CASL** (Canada anti-spam): every form has an explicit consent checkbox; outreach must
  identify the sender and include an opt-out. Build lead lists only from **public,
  permitted** sources — no scraping of private/gated data.
- **No certification claims:** PHIPA/SOC 2 work is described as *readiness/advisory* only.
- **No legal advice:** the PHIPA checklist is labelled educational guidance.
- **Authorization first:** all hands-on security work requires a signed engagement.

## Suggested first execution loop

1. Fill the placeholders above (Stripe + Formspree + booking).
2. Verify the **Services** link in the main nav (`index.html`) points here.
3. Build a list of 10 Ontario SMBs from public sources; send 5 CASL-compliant,
   personalized emails referencing a specific public observation.
4. Track replies → scoping calls → deposits.

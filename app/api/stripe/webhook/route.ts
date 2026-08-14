import { headers } from "next/headers";
import { NextResponse } from "next/server";
import Stripe from "stripe";

export const runtime = "nodejs";

const stripeOptions: Stripe.StripeConfig = {
  apiVersion: "2025-06-30.basil",
  typescript: true,
};

function requiredEnvironment(name: string): string | null {
  const value = process.env[name]?.trim();
  return value ? value : null;
}

export async function POST(request: Request) {
  const signature = (await headers()).get("stripe-signature");
  const rawBody = await request.text();

  if (!signature) {
    return NextResponse.json({ error: "Missing signature" }, { status: 400 });
  }

  const secretKey = requiredEnvironment("STRIPE_SECRET_KEY");
  const webhookSecret = requiredEnvironment("STRIPE_WEBHOOK_SECRET");
  const expectedPriceId = requiredEnvironment("STRIPE_CRITICAL_MINERALS_PRICE_ID");

  if (!secretKey || !webhookSecret || !expectedPriceId) {
    return NextResponse.json({ error: "Webhook unavailable" }, { status: 503 });
  }

  const stripe = new Stripe(secretKey, stripeOptions);
  let event: Stripe.Event;

  try {
    event = stripe.webhooks.constructEvent(rawBody, signature, webhookSecret);
  } catch {
    return NextResponse.json({ error: "Invalid webhook signature" }, { status: 400 });
  }

  if (event.type !== "checkout.session.completed") {
    return NextResponse.json({ received: true });
  }

  const session = event.data.object as Stripe.Checkout.Session;

  if (
    session.payment_status !== "paid" ||
    session.mode !== "payment" ||
    session.currency !== "cad" ||
    session.amount_total !== 149900
  ) {
    return NextResponse.json({ error: "Payment validation failed" }, { status: 400 });
  }

  const lineItems = await stripe.checkout.sessions.listLineItems(session.id, {
    expand: ["data.price"],
    limit: 10,
  });

  const purchased = lineItems.data.some(
    (item) => item.price?.id === expectedPriceId && item.quantity === 1,
  );

  if (!purchased) {
    return NextResponse.json({ error: "Unexpected product" }, { status: 400 });
  }

  // Do not acknowledge this paid event until fulfillment is durably committed.
  // The owning server must transactionally deduplicate event.id, evaluate the
  // compliance gates, create the entitlement, and append the audit record.
  // Returning 503 preserves Stripe retry semantics instead of silently losing
  // fulfillment after a successful payment.
  return NextResponse.json({ error: "Fulfillment unavailable" }, { status: 503 });
}

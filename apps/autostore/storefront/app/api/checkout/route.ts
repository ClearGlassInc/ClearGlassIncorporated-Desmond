// ClearGlass Side Store — Stripe Checkout API route.
// Reads STRIPE_SECRET_KEY from the environment (never hard-coded), builds the
// session params with the shared pure helper, and creates the session. Returns
// 503 with a clear message when the key is absent so the skeleton fails closed.

import catalogData from "../../../data/catalog.json";
// @ts-expect-error — shared dependency-free ESM core (allowJs enabled).
import { buildCheckoutSessionParams } from "../../../lib/checkout.mjs";

const catalog = (catalogData as { items: unknown[] }).items;

export async function POST(request: Request): Promise<Response> {
  const secret = process.env.STRIPE_SECRET_KEY;
  if (!secret) {
    return Response.json(
      { error: "Checkout is not configured. Set STRIPE_SECRET_KEY to enable payments." },
      { status: 503 }
    );
  }

  let body: { lines?: Array<{ id: string; qty: number }> };
  try {
    body = await request.json();
  } catch {
    return Response.json({ error: "Invalid JSON body." }, { status: 400 });
  }

  const base = process.env.NEXT_PUBLIC_SITE_URL ?? "http://localhost:3001";
  let params: ReturnType<typeof buildCheckoutSessionParams>;
  try {
    params = buildCheckoutSessionParams(body.lines ?? [], catalog, {
      successUrl: `${base}/success`,
      cancelUrl: `${base}/cart`,
    });
  } catch (err) {
    return Response.json({ error: (err as Error).message }, { status: 400 });
  }

  // Import the SDK lazily so builds/tests don't require it to be installed.
  const Stripe = (await import("stripe")).default;
  const stripe = new Stripe(secret);

  const { discountPercent, ...sessionParams } = params;
  const discounts =
    discountPercent > 0
      ? [{ coupon: (await stripe.coupons.create({ percent_off: discountPercent, duration: "once" })).id }]
      : undefined;

  const session = await stripe.checkout.sessions.create({ ...sessionParams, discounts });
  return Response.json({ url: session.url });
}

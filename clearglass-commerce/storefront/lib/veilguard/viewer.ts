/**
 * VEILGUARD — viewer context resolution (server only).
 *
 * Turns an incoming request into the three things the shield needs: who is
 * asking, which session and device they are asking from, and what the recent
 * shape of their activity looks like.
 *
 * On trusting headers
 * -------------------
 * Network-derived signals (anonymised egress, geo velocity) are only read when
 * `VEILGUARD_TRUST_EDGE_SIGNALS` is explicitly enabled, because they arrive as
 * request headers and a header the client can set is not evidence. Enable it
 * only where a CDN or WAF you control strips and re-writes these on every
 * request. Left off — the default — those signals stay neutral and risk is
 * scored from first-party behaviour alone, which cannot be spoofed by the
 * caller.
 *
 * This mirrors the stance the storefront already takes on `X-Forwarded-For`:
 * a forwarded header is trustworthy only when something trustworthy set it.
 */

import { createHash } from "node:crypto";
import type { NextRequest } from "next/server";
import { getServerPremiumSession } from "@/lib/auth";
import { baselineSignals, type RiskSignals } from "./risk";
import { getGrantStore } from "./store";
import type { ViewerPlan } from "./policy";

const DEVICE_COOKIE = "vg_device";
const TRUST_EDGE_ENV = "VEILGUARD_TRUST_EDGE_SIGNALS";

export type ViewerContext = {
  subject: string;
  plan: ViewerPlan;
  sessionId: string;
  deviceRef: string;
  /** True when this request minted the device token, so the route can set it. */
  deviceIssued: boolean;
};

function stableRef(value: string, kind: string): string {
  return createHash("sha256").update(`veilguard.${kind}|${value}`).digest("base64url").slice(0, 24);
}

function trustEdgeSignals(): boolean {
  return process.env[TRUST_EDGE_ENV] === "true";
}

/**
 * Resolve the viewer.
 *
 * An unauthenticated caller is a real, supported case — they resolve to the
 * `anonymous` plan, whose ceiling is view-only, rather than being rejected.
 * That keeps public assets servable through the same shielded path instead of
 * needing a second, unprotected one.
 */
export async function resolveViewer(request: NextRequest): Promise<ViewerContext> {
  const session = await getServerPremiumSession().catch(() => null);

  const existingDevice = request.cookies.get(DEVICE_COOKIE)?.value;
  const deviceRef = existingDevice ?? stableRef(`${Date.now()}:${Math.random()}`, "device");

  // Session identity is derived from the auth cookie so it rotates on every
  // re-login, and falls back to the device token for anonymous viewers.
  const authCookie = request.cookies.get("cg_session")?.value;
  const sessionId = authCookie ? stableRef(authCookie, "session") : stableRef(deviceRef, "session");

  return {
    subject: session?.sub ?? `anon:${deviceRef}`,
    plan: session?.plan ?? "anonymous",
    sessionId,
    deviceRef,
    deviceIssued: !existingDevice,
  };
}

/** Assemble the risk signals for this viewer from first-party state. */
export function signalsFor(request: NextRequest, viewer: ViewerContext, now: number = Date.now()): RiskSignals {
  const store = getGrantStore();
  const window = store.windowFor(viewer.sessionId, now);
  const deviceAgeDays = store.seeDevice(viewer.deviceRef, now);

  const edge = trustEdgeSignals()
    ? {
        anonymizedNetwork: request.headers.get("x-vg-anonymized-network") === "true",
        geoVelocityKmh: parseVelocity(request.headers.get("x-vg-geo-velocity-kmh")),
      }
    : { anonymizedNetwork: false, geoVelocityKmh: null };

  return baselineSignals({
    deviceKnown: deviceAgeDays !== null,
    deviceAgeDays: deviceAgeDays ?? 0,
    ...window,
    ...edge,
  });
}

function parseVelocity(raw: string | null): number | null {
  if (!raw) return null;
  const value = Number(raw);
  return Number.isFinite(value) && value >= 0 ? value : null;
}

/**
 * Gate for the investigative surfaces — leak tracing and ledger inspection.
 *
 * These read across viewers rather than serving the caller's own content, so
 * they are restricted to the `operator` plan. Returns the operator's subject
 * on success and null otherwise; callers must render an identical response for
 * "not an operator" and "not signed in" so the routes do not become a probe
 * for who holds elevated access.
 */
export async function resolveOperator(): Promise<string | null> {
  const session = await getServerPremiumSession().catch(() => null);
  return session?.plan === "operator" ? session.sub : null;
}

/** Cookie attributes for the first-party device token. */
export const DEVICE_COOKIE_NAME = DEVICE_COOKIE;

export const DEVICE_COOKIE_OPTIONS = {
  httpOnly: true,
  sameSite: "lax",
  secure: process.env.NODE_ENV === "production",
  path: "/",
  // 180 days: long enough for device recognition to be useful, short enough
  // that a token does not become a permanent identifier.
  maxAge: 180 * 24 * 60 * 60,
} as const;

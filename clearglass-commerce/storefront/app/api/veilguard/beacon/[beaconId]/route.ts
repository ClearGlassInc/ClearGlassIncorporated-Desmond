/**
 * GET /api/veilguard/beacon/[beaconId] — leak beacon callback.
 *
 * Deliberately public and unauthenticated: the whole point is that this fires
 * from wherever a leaked copy ended up, which is by definition outside any
 * session we control.
 *
 * What is recorded is narrow on purpose — which copy was touched, when, and
 * the referring page if the browser volunteered one. No cookies are set, no
 * identifier is planted, and nothing about the person who opened the leaked
 * copy is collected: they are not the subject of the investigation, the
 * *copy* is. Recipients are told at export time that their copy carries a
 * beacon, which is what separates this from a tracking pixel.
 *
 * Always returns the same 1×1 image whether or not the beacon resolves, so the
 * endpoint cannot be used to test which references are live.
 */

import { NextResponse, type NextRequest } from "next/server";
import { getLedger } from "@/lib/veilguard/ledger";
import { resolveLeakBeacon } from "@/lib/veilguard/honeypot";
import { getGrantStore, type GrantRecord } from "@/lib/veilguard/store";

/** 1×1 transparent GIF. */
const PIXEL = Buffer.from("R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7", "base64");

export async function GET(request: NextRequest, context: { params: Promise<{ beaconId: string }> }) {
  const { beaconId } = await context.params;

  const candidates = getGrantStore()
    .allGrants()
    .map((grant: GrantRecord) => ({ assetId: grant.assetId, grantId: grant.grantId, subject: grant.subject }));

  const match = resolveLeakBeacon(beaconId, candidates);

  // Referrer is truncated to its origin: enough to know where a leaked copy
  // surfaced, without recording the full path of an unrelated third-party page.
  const referrerOrigin = originOf(request.headers.get("referer"));

  await getLedger().append({
    action: "honeypot_touched",
    subject: match?.subject ?? "unknown",
    sessionId: `beacon:${beaconId}`,
    assetId: match?.assetId ?? "unknown",
    grantId: match?.grantId ?? null,
    riskScore: 100,
    detail: {
      beacon: beaconId,
      resolved: match !== null,
      referrerOrigin,
    },
  });

  return new NextResponse(PIXEL, {
    status: 200,
    headers: {
      "content-type": "image/gif",
      "cache-control": "no-store, no-cache, must-revalidate, max-age=0",
      "content-length": String(PIXEL.byteLength),
    },
  });
}

function originOf(referrer: string | null): string | null {
  if (!referrer) return null;
  try {
    return new URL(referrer).origin;
  } catch {
    return null;
  }
}

/**
 * VEILGUARD — honeypot assets and leak beacons (server only).
 *
 * Two distinct instruments, often confused:
 *
 *   1. **Enumeration canaries.** Asset identifiers that look ordinary but are
 *      linked from nowhere — not the UI, not the sitemap, not an API listing.
 *      A session that requests one did not arrive by using the product. This
 *      is the highest-signal, lowest-false-positive detection in the system,
 *      which is why `risk.ts` lets it force the critical band on its own.
 *
 *   2. **Per-recipient beacons.** A unique reference minted into one
 *      recipient's copy of an export. If that reference is later fetched from
 *      somewhere it should not exist, the specific copy that leaked is known.
 *
 * Beacons are a disclosed control, not a covert one. They are described in the
 * viewer-facing protection notice and in the terms a recipient accepts before
 * an export is released — see `client/ProtectionNotice.tsx` and the
 * disclosure section of the VEILGUARD document. A beacon that a recipient was
 * never told about is a tracking pixel; a beacon they accepted is a term of
 * access. Only ship the second kind.
 *
 * Identifiers are keyed HMAC output, so they are unguessable without the key
 * and stable across restarts without a table to keep in sync.
 */

import { createHmac, timingSafeEqual } from "node:crypto";

const SECRET_ENV = "VEILGUARD_SIGNING_SECRET";
const CANARY_PREFIX = "cg-";

function secret(): string {
  const value = process.env[SECRET_ENV];
  if (!value && process.env.NODE_ENV === "production") {
    throw new Error(`${SECRET_ENV} must be set in production`);
  }
  return value || "dev-only-veilguard-signing-secret-change-me";
}

function derive(domain: string, label: string, bytes = 12): string {
  return createHmac("sha256", secret()).update(`${domain}|${label}`).digest("base64url").slice(0, bytes * 2);
}

/**
 * How many enumeration canaries exist. They are derived, not stored, so this
 * is the only thing that needs to stay stable for the set to stay stable.
 */
export const CANARY_COUNT = 24;

/**
 * Canary identifiers, shaped like ordinary asset ids so they do not stand out
 * in a listing an attacker may have partially scraped.
 */
export function canaryAssetIds(): string[] {
  const ids: string[] = [];
  for (let i = 0; i < CANARY_COUNT; i += 1) {
    ids.push(`${CANARY_PREFIX}${derive("veilguard.canary.v1", String(i), 8)}`);
  }
  return ids;
}

let canaryCache: Set<string> | null = null;

function canarySet(): Set<string> {
  if (!canaryCache) canaryCache = new Set(canaryAssetIds());
  return canaryCache;
}

/**
 * Is this a canary?
 *
 * A plain set lookup: the identifiers are 128-bit HMAC output, so the control
 * is unguessability, not lookup timing. There is no secret to leak through a
 * comparison here that the identifier itself does not already protect.
 */
export function isHoneypotAsset(assetId: string): boolean {
  return canarySet().has(assetId);
}

/** Test seam — the derived set is memoised, and tests vary the key. */
export function resetHoneypotCacheForTesting(): void {
  canaryCache = null;
}

export type LeakBeacon = {
  beaconId: string;
  /** Reference to embed in the exported copy, e.g. as a tracked resource URL. */
  reference: string;
  issuedTo: string;
  assetId: string;
  grantId: string;
  issuedAt: string;
};

/**
 * Mint a beacon binding one export to one recipient.
 *
 * The identifier is derived from (asset, grant, recipient) under the signing
 * key: it reveals nothing about the recipient on its own, and resolving it
 * back requires the candidate list — which is the same access-controlled grant
 * store the ledger's pseudonyms resolve through.
 */
export function mintLeakBeacon(input: {
  assetId: string;
  grantId: string;
  subject: string;
  now?: Date;
}): LeakBeacon {
  const beaconId = derive("veilguard.beacon.v1", `${input.assetId}|${input.grantId}|${input.subject}`, 10);
  return {
    beaconId,
    reference: `/api/veilguard/beacon/${beaconId}`,
    issuedTo: input.subject,
    assetId: input.assetId,
    grantId: input.grantId,
    issuedAt: (input.now ?? new Date()).toISOString(),
  };
}

export type BeaconCandidate = {
  assetId: string;
  grantId: string;
  subject: string;
};

/**
 * Resolve a fetched beacon back to the copy it was minted into.
 *
 * Recomputes each candidate's beacon under the key and compares in constant
 * time. Returns null when nothing matches — an unknown beacon is itself worth
 * logging, since it means someone is guessing at the endpoint.
 */
export function resolveLeakBeacon(beaconId: string, candidates: readonly BeaconCandidate[]): BeaconCandidate | null {
  const supplied = Buffer.from(beaconId);
  for (const candidate of candidates) {
    const expected = Buffer.from(
      derive("veilguard.beacon.v1", `${candidate.assetId}|${candidate.grantId}|${candidate.subject}`, 10),
    );
    if (expected.length === supplied.length && timingSafeEqual(expected, supplied)) return candidate;
  }
  return null;
}

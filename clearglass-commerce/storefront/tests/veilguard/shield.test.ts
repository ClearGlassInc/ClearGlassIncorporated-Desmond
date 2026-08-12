import test from "node:test";
import assert from "node:assert/strict";

import { resolvePolicy } from "../../lib/veilguard/policy";
import { deriveTracerBits, grantAllows, maskSubject, mintGrant, verifyGrant } from "../../lib/veilguard/watermark";
import { bitsToCode, traceLeak } from "../../lib/veilguard/tracer";
import {
  canaryAssetIds,
  isHoneypotAsset,
  mintLeakBeacon,
  resolveLeakBeacon,
} from "../../lib/veilguard/honeypot";
import { listProtectedAssets } from "../../lib/veilguard/registry";

const POLICY = resolvePolicy({ classification: "confidential", plan: "premium", riskBand: "nominal" });

function mint(overrides: Partial<Parameters<typeof mintGrant>[0]> = {}) {
  return mintGrant({
    assetId: "concept-draft-atlas",
    subject: "viewer@example.com",
    sessionId: "session-1",
    policy: POLICY,
    grantId: "grant-fixed",
    now: new Date("2026-01-01T00:00:00.000Z"),
    ...overrides,
  });
}

test("a freshly minted grant verifies and carries its policy", () => {
  const minted = mint();
  const payload = verifyGrant(minted.token, new Date("2026-01-01T00:01:00.000Z"));

  assert.ok(payload, "a fresh grant must verify");
  assert.equal(payload?.assetId, "concept-draft-atlas");
  assert.equal(payload?.sub, "viewer@example.com");
  assert.ok(grantAllows(payload!, "view"));
  assert.equal(grantAllows(payload!, "export"), false, "confidential content is not exportable");
});

test("a grant does not verify after it expires", () => {
  const minted = mint();
  const afterExpiry = new Date(Date.parse(minted.expiresAt) + 1000);
  assert.equal(verifyGrant(minted.token, afterExpiry), null);
});

test("tampering with a grant payload invalidates it", () => {
  const minted = mint();
  const [encoded] = minted.token.split(".");
  const payload = JSON.parse(Buffer.from(encoded, "base64url").toString("utf8"));

  // Widen the capabilities and re-encode, keeping the original signature.
  payload.capabilities = ["view", "download", "export", "share"];
  const forged = `${Buffer.from(JSON.stringify(payload)).toString("base64url")}.${minted.token.split(".")[1]}`;

  assert.equal(verifyGrant(forged, new Date("2026-01-01T00:01:00.000Z")), null, "a re-signed-free forgery must fail");
});

test("a malformed token is rejected rather than throwing", () => {
  assert.equal(verifyGrant(undefined), null);
  assert.equal(verifyGrant(""), null);
  assert.equal(verifyGrant("not-a-token"), null);
  assert.equal(verifyGrant("aaaa.bbbb"), null);
});

test("a critical-risk policy mints a grant that is already unusable", () => {
  const denied = resolvePolicy({ classification: "confidential", plan: "premium", riskBand: "critical" });
  const minted = mint({ policy: denied });

  assert.deepEqual(minted.payload.capabilities, []);
  assert.equal(verifyGrant(minted.token, new Date("2026-01-01T00:00:01.000Z")), null, "a zero-TTL grant must not replay");
});

test("tracers are deterministic per grant and distinct across viewers and sessions", () => {
  const base = { assetId: "a", subject: "viewer@example.com", sessionId: "s1", grantId: "g1" };

  assert.deepEqual(deriveTracerBits(base), deriveTracerBits(base), "same inputs must give the same tracer");

  const variations = [
    { ...base, subject: "other@example.com" },
    { ...base, sessionId: "s2" },
    { ...base, grantId: "g2" },
    { ...base, assetId: "b" },
  ];

  const codes = new Set(variations.map((input) => bitsToCode(deriveTracerBits(input))));
  codes.add(bitsToCode(deriveTracerBits(base)));
  assert.equal(codes.size, 5, "each distinct input must produce its own tracer");
});

test("a grant minted for one viewer traces back to that viewer", () => {
  const alice = mint({ subject: "alice@example.com", sessionId: "s-alice", grantId: "g-alice" });
  const bob = mint({ subject: "bob@example.com", sessionId: "s-bob", grantId: "g-bob" });

  const candidates = [alice, bob].map((minted) => ({
    grantId: minted.grantId,
    assetId: minted.payload.assetId,
    subject: minted.payload.sub,
    sessionId: minted.payload.sid,
    issuedAt: minted.watermark.issuedAtIso,
    bits: minted.tracerBits,
  }));

  const { matches } = traceLeak(alice.tracerCode, candidates);

  assert.equal(matches.length, 1);
  assert.equal(matches[0].candidate.subject, "alice@example.com");
  assert.equal(matches[0].confidence, "conclusive");
});

test("the watermark shows a masked identity while staying fully traceable", () => {
  const minted = mint({ subjectLabel: maskSubject("viewer@example.com") });

  assert.equal(minted.watermark.subjectLabel, "vi••••@example.com");
  assert.ok(!minted.watermark.subjectLabel.includes("viewer@"), "the raw local part must not be painted on screen");
  assert.equal(minted.watermark.tracerCode, minted.tracerCode, "masking must not weaken attribution");
});

test("subject masking handles short and non-email identifiers", () => {
  assert.equal(maskSubject("a@b.com"), "a•@b.com");
  assert.ok(!maskSubject("anon:abcdef123456").includes("abcdef"));
  assert.equal(maskSubject("ab"), "ab");
});

test("canary identifiers are stable, unique, and outside the real catalog", () => {
  const canaries = canaryAssetIds();

  assert.equal(new Set(canaries).size, canaries.length, "canaries must not collide");
  assert.deepEqual(canaries, canaryAssetIds(), "the canary set must be stable across calls");

  const realIds = new Set(listProtectedAssets().map((asset) => asset.assetId));
  for (const canary of canaries) {
    assert.ok(isHoneypotAsset(canary));
    assert.ok(!realIds.has(canary), "a canary must never shadow a real asset");
  }
});

test("ordinary asset identifiers are not mistaken for canaries", () => {
  for (const asset of listProtectedAssets()) {
    assert.equal(isHoneypotAsset(asset.assetId), false, `${asset.assetId} was treated as a canary`);
  }
  assert.equal(isHoneypotAsset("definitely-not-a-canary"), false);
});

test("a leak beacon resolves to the copy it was minted into", () => {
  const recipients = [
    { assetId: "workflow-map-q3", grantId: "g-1", subject: "alice@example.com" },
    { assetId: "workflow-map-q3", grantId: "g-2", subject: "bob@example.com" },
  ];

  const beacon = mintLeakBeacon(recipients[1]);
  const resolved = resolveLeakBeacon(beacon.beaconId, recipients);

  assert.equal(resolved?.subject, "bob@example.com");
  assert.match(beacon.reference, /^\/api\/veilguard\/beacon\//);
});

test("an unknown beacon resolves to nothing rather than to the nearest recipient", () => {
  const recipients = [{ assetId: "workflow-map-q3", grantId: "g-1", subject: "alice@example.com" }];
  assert.equal(resolveLeakBeacon("not-a-real-beacon", recipients), null);
});

test("beacon identifiers reveal nothing about the recipient", () => {
  const beacon = mintLeakBeacon({ assetId: "workflow-map-q3", grantId: "g-1", subject: "alice@example.com" });

  assert.ok(!beacon.beaconId.includes("alice"));
  assert.ok(!beacon.beaconId.includes("workflow"));
  assert.ok(!beacon.beaconId.includes("g-1"));
});

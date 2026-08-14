/**
 * POST /api/veilguard/grant — issue a scoped, expiring render grant.
 *
 * The whole gate in one place: resolve the viewer, score the session, resolve
 * the policy from (classification × plan × risk), mint the grant, and record
 * both the binding needed for a future leak trace and the ledger entry.
 *
 * Unknown asset identifiers are refused *and counted*. Enumerating for valid
 * ids is the reconnaissance step before a scrape, and refusals feed the
 * `failedGrantsInWindow` signal, so probing raises the prober's own risk band
 * and narrows what they can reach next.
 */

import { NextResponse, type NextRequest } from "next/server";
import { getLedger } from "@/lib/veilguard/ledger";
import { resolvePolicy } from "@/lib/veilguard/policy";
import { findProtectedAsset } from "@/lib/veilguard/registry";
import { scoreRisk, summarizeRisk, type RiskContribution } from "@/lib/veilguard/risk";
import { getGrantStore } from "@/lib/veilguard/store";
import { mintGrant, maskSubject } from "@/lib/veilguard/watermark";
import { isHoneypotAsset } from "@/lib/veilguard/honeypot";
import { DEVICE_COOKIE_NAME, DEVICE_COOKIE_OPTIONS, resolveViewer, signalsFor } from "@/lib/veilguard/viewer";
import type { ShieldGrantResponse } from "@/lib/veilguard/contract";

export async function POST(request: NextRequest) {
  const body = (await request.json().catch(() => null)) as { assetId?: string } | null;
  const assetId = body?.assetId;
  if (!assetId || typeof assetId !== "string") {
    return NextResponse.json({ error: "assetId is required" }, { status: 400 });
  }

  const viewer = await resolveViewer(request);
  const store = getGrantStore();
  const ledger = getLedger();
  const now = Date.now();

  // Canaries are checked before the registry: a canary is not a registered
  // asset, so a plain "unknown asset" refusal would leak the fact that it is
  // special. It is recorded as a honeypot touch and refused like anything else.
  const honeypot = isHoneypotAsset(assetId);
  if (honeypot) {
    store.recordEvent(viewer.sessionId, { at: now, assetId, kind: "honeypot" });
  }

  const signals = signalsFor(request, viewer, now);
  const asset = honeypot ? null : findProtectedAsset(assetId);

  if (!asset) {
    store.recordEvent(viewer.sessionId, { at: now, assetId, kind: "refusal" });
    const risk = scoreRisk(signalsFor(request, viewer, now));
    await ledger.append({
      action: honeypot ? "honeypot_touched" : "grant_denied",
      subject: viewer.subject,
      sessionId: viewer.sessionId,
      assetId,
      grantId: null,
      riskScore: risk.score,
      detail: { reason: honeypot ? "canary_asset" : "unknown_asset", risk: summarizeRisk(risk) },
    });

    // Same shape and status for both, so the response cannot be used to tell a
    // canary apart from an identifier that simply does not exist.
    return withDeviceCookie(
      NextResponse.json<ShieldGrantResponse>(
        { denied: true, assetId, reason: "No accessible item with that identifier.", risk: toRiskDto(risk) },
        { status: 404 },
      ),
      viewer,
    );
  }

  store.recordEvent(viewer.sessionId, { at: now, assetId, kind: "grant" });
  const risk = scoreRisk(signals);
  const policy = resolvePolicy({
    classification: asset.classification,
    plan: viewer.plan,
    riskBand: risk.band,
    denyCapabilities: asset.denyCapabilities,
  });

  if (!policy.capabilities.has("view")) {
    await ledger.append({
      action: "grant_denied",
      subject: viewer.subject,
      sessionId: viewer.sessionId,
      assetId,
      grantId: null,
      riskScore: risk.score,
      detail: { reason: "policy_denies_view", risk: summarizeRisk(risk), band: risk.band },
    });
    return withDeviceCookie(
      NextResponse.json<ShieldGrantResponse>(
        {
          denied: true,
          assetId,
          reason:
            risk.band === "critical"
              ? "Access is paused on this session while unusual activity is reviewed."
              : "Your current access level does not include this item.",
          risk: toRiskDto(risk),
        },
        { status: 403 },
      ),
      viewer,
    );
  }

  const minted = mintGrant({
    assetId,
    subject: viewer.subject,
    sessionId: viewer.sessionId,
    policy,
    subjectLabel: maskSubject(viewer.subject),
    contextLabel: asset.contextLabel,
  });

  store.recordGrant({
    grantId: minted.grantId,
    assetId,
    subject: viewer.subject,
    sessionId: viewer.sessionId,
    issuedAt: minted.watermark.issuedAtIso,
    expiresAt: minted.expiresAt,
    tracerBits: minted.tracerBits,
  });

  await ledger.append({
    action: "grant_issued",
    subject: viewer.subject,
    sessionId: viewer.sessionId,
    assetId,
    grantId: minted.grantId,
    riskScore: risk.score,
    detail: {
      classification: asset.classification,
      capabilities: minted.payload.capabilities.join(","),
      tracer: minted.tracerCode,
      risk: summarizeRisk(risk),
    },
  });

  return withDeviceCookie(
    NextResponse.json<ShieldGrantResponse>({
      grantId: minted.grantId,
      token: minted.token,
      assetId,
      title: asset.title,
      source: asset.source,
      alt: asset.alt,
      expiresAt: minted.expiresAt,
      policy: minted.policy,
      watermark: minted.watermark,
      tracerBits: [...minted.tracerBits],
      risk: toRiskDto(risk),
    }),
    viewer,
  );
}

function toRiskDto(risk: ReturnType<typeof scoreRisk>) {
  return {
    score: risk.score,
    band: risk.band,
    reasons: risk.contributions.map((contribution: RiskContribution) => contribution.reason),
  };
}

function withDeviceCookie(response: NextResponse, viewer: { deviceRef: string; deviceIssued: boolean }): NextResponse {
  if (viewer.deviceIssued) {
    response.cookies.set(DEVICE_COOKIE_NAME, viewer.deviceRef, DEVICE_COOKIE_OPTIONS);
  }
  return response;
}

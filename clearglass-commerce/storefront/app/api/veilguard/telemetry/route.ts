/**
 * POST /api/veilguard/telemetry — ingest client protection events.
 *
 * The client is not trusted to say who it is. Every event carries the grant
 * token it was issued, and the subject/session/asset written to the ledger are
 * read from the *verified* token rather than from the request body — so a
 * forged event can only ever be attributed to the session that already holds a
 * valid grant, and cannot be aimed at someone else to raise their risk score.
 *
 * Events are advisory by design: they raise risk on the session that produced
 * them, which narrows what the *next* grant will allow. Nothing here revokes
 * an already-issued grant, because a client that wanted to avoid revocation
 * would simply stop reporting. Short render TTLs are what bound an in-flight
 * session, not this endpoint.
 */

import { NextResponse, type NextRequest } from "next/server";
import { getLedger, type LedgerAction } from "@/lib/veilguard/ledger";
import { scoreRisk, summarizeRisk } from "@/lib/veilguard/risk";
import { getGrantStore } from "@/lib/veilguard/store";
import { verifyGrant } from "@/lib/veilguard/watermark";
import { resolveViewer, signalsFor } from "@/lib/veilguard/viewer";
import type { TelemetryEventDTO, TelemetryKind } from "@/lib/veilguard/contract";

/** Client event kinds → ledger actions. Anything unlisted is rejected. */
const ACTIONS: Record<TelemetryKind, LedgerAction> = {
  render_started: "render_started",
  render_expired: "render_expired",
  capture_suspected: "capture_suspected",
  export_attempted: "export_attempted",
  copy_attempted: "copy_attempted",
  automation_suspected: "risk_escalated",
};

/** Event kinds that feed the session's risk window. */
const RISK_KINDS: Partial<Record<TelemetryKind, "capture_suspicion" | "automation">> = {
  capture_suspected: "capture_suspicion",
  automation_suspected: "automation",
};

/** Bounded so a chatty or hostile client cannot flood the ledger. */
const MAX_METHOD_LENGTH = 48;

export async function POST(request: NextRequest) {
  const event = (await request.json().catch(() => null)) as TelemetryEventDTO | null;
  if (!event || typeof event.grantToken !== "string" || typeof event.kind !== "string") {
    return NextResponse.json({ error: "grantToken and kind are required" }, { status: 400 });
  }

  const action = ACTIONS[event.kind];
  if (!action) {
    return NextResponse.json({ error: "Unknown event kind" }, { status: 400 });
  }

  const payload = verifyGrant(event.grantToken);
  if (!payload) {
    // An expired grant reporting a late event is ordinary — a render that ends
    // after its window closes still fires. It is not an error worth alarming on.
    return NextResponse.json({ accepted: false, reason: "grant not valid" }, { status: 202 });
  }

  const viewer = await resolveViewer(request);
  const store = getGrantStore();
  const now = Date.now();

  const riskKind = RISK_KINDS[event.kind];
  if (riskKind) {
    store.recordEvent(payload.sid, { at: now, assetId: payload.assetId, kind: riskKind });
  }

  const risk = scoreRisk(signalsFor(request, viewer, now));

  const detail: Record<string, string | number | boolean | null> = {
    risk: summarizeRisk(risk),
  };
  if (typeof event.method === "string") detail.method = event.method.slice(0, MAX_METHOD_LENGTH);
  if (typeof event.allowed === "boolean") detail.allowed = event.allowed;

  // Attribution comes from the verified grant, never from the request body.
  await getLedger().append({
    action,
    subject: payload.sub,
    sessionId: payload.sid,
    assetId: payload.assetId,
    grantId: payload.grantId,
    riskScore: risk.score,
    detail,
  });

  return NextResponse.json({ accepted: true, riskBand: risk.band }, { status: 202 });
}

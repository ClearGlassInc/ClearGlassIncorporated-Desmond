/**
 * POST /api/veilguard/trace — attribute a recovered tracer to a grant.
 *
 * The investigator submits whatever survived the leak: a full eight-character
 * code, or a partial one with `?` where characters were illegible. The tracer
 * ranks candidate grants for that asset and returns the false-match
 * probability for each, so the result reads as evidence with a strength rather
 * than as an accusation.
 *
 * Two deliberate constraints:
 *
 *   - **Operator-gated.** This is the one surface that maps a pseudonymous
 *     tracer back to a person, which is exactly the capability that must not
 *     be broadly available.
 *   - **Self-logging.** Running a trace is itself written to the ledger. An
 *     audit trail that records everyone except the people holding the audit
 *     tools is not an audit trail.
 */

import { NextResponse, type NextRequest } from "next/server";
import { getLedger } from "@/lib/veilguard/ledger";
import { getGrantStore, type GrantRecord } from "@/lib/veilguard/store";
import { traceLeak, type TraceMatch } from "@/lib/veilguard/tracer";
import { resolveOperator } from "@/lib/veilguard/viewer";

export async function POST(request: NextRequest) {
  const operator = await resolveOperator();
  if (!operator) {
    return NextResponse.json({ error: "Not found" }, { status: 404 });
  }

  const body = (await request.json().catch(() => null)) as
    | { assetId?: string; code?: string; maxDistance?: number }
    | null;

  if (!body?.assetId || !body?.code) {
    return NextResponse.json({ error: "assetId and code are required" }, { status: 400 });
  }

  const candidates = getGrantStore()
    .candidatesForAsset(body.assetId)
    .map((grant: GrantRecord) => ({
      grantId: grant.grantId,
      assetId: grant.assetId,
      subject: grant.subject,
      sessionId: grant.sessionId,
      issuedAt: grant.issuedAt,
      bits: grant.tracerBits,
    }));

  let result: ReturnType<typeof traceLeak>;
  try {
    result = traceLeak(body.code, candidates, { maxDistance: body.maxDistance });
  } catch (error) {
    return NextResponse.json({ error: (error as Error).message }, { status: 400 });
  }

  await getLedger().append({
    action: "trace_requested",
    subject: operator,
    sessionId: `operator:${operator}`,
    assetId: body.assetId,
    grantId: null,
    riskScore: 0,
    detail: {
      knownBits: result.recovered.knownBits,
      candidates: candidates.length,
      matches: result.matches.length,
      topConfidence: result.matches[0]?.confidence ?? "none",
    },
  });

  return NextResponse.json({
    assetId: body.assetId,
    knownBits: result.recovered.knownBits,
    candidatesConsidered: candidates.length,
    matches: result.matches.map((match: TraceMatch) => ({
      grantId: match.candidate.grantId,
      subject: match.candidate.subject,
      sessionId: match.candidate.sessionId,
      issuedAt: match.candidate.issuedAt,
      distance: match.distance,
      falseMatchProbability: match.falseMatchProbability,
      confidence: match.confidence,
    })),
    // Stated in the payload so it travels with any exported result: a single
    // strong match is a lead to corroborate, not a finding on its own.
    interpretation:
      result.matches.length === 0
        ? "No candidate grant matches within the distance bound."
        : result.matches.length > 1 && result.matches[0].distance === result.matches[1].distance
          ? "Two or more candidates match equally well — the recovered fragment does not separate them."
          : `Best match is ${result.matches[0].confidence}; corroborate before acting on it.`,
  });
}

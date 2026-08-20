import { createHash, createHmac, timingSafeEqual } from "node:crypto";
import type { NextRequest } from "next/server";
import type { Prisma } from "@prisma/client";
import { db } from "@/lib/db";
import { failure, success, ApiError } from "@/lib/api";

export const runtime = "nodejs";

function safeEqual(a: string, b: string) {
  const left = Buffer.from(a);
  const right = Buffer.from(b);
  return left.length === right.length && timingSafeEqual(left, right);
}

export async function POST(request: NextRequest, context: { params: Promise<{ sourceKey: string }> }) {
  try {
    const { sourceKey } = await context.params;
    const secret = process.env.INGESTION_WEBHOOK_SECRET;
    if (!secret) throw new ApiError(503, "WEBHOOK_NOT_CONFIGURED", "Machine ingestion webhook is not configured");
    const timestamp = request.headers.get("x-clearglass-timestamp");
    const signature = request.headers.get("x-clearglass-signature")?.replace(/^sha256=/, "");
    if (!timestamp || !signature) throw new ApiError(401, "INVALID_SIGNATURE", "Signed webhook headers are required");
    const unix = Number(timestamp);
    if (!Number.isFinite(unix) || Math.abs(Date.now() / 1000 - unix) > 300) throw new ApiError(401, "STALE_SIGNATURE", "Webhook timestamp is outside the five-minute acceptance window");
    const body = await request.text();
    const maxBytes = Number(process.env.UPLOAD_MAX_BYTES ?? 10 * 1024 * 1024);
    if (Buffer.byteLength(body, "utf8") > maxBytes) throw new ApiError(413, "PAYLOAD_TOO_LARGE", `Webhook payload exceeds ${maxBytes} bytes`);
    const expected = createHmac("sha256", secret).update(`${timestamp}.${body}`).digest("hex");
    if (!safeEqual(expected, signature)) throw new ApiError(401, "INVALID_SIGNATURE", "Webhook signature validation failed");
    const source = await db.dataSource.findUnique({ where: { key: sourceKey } });
    if (!source || !source.enabled) throw new ApiError(404, "SOURCE_UNAVAILABLE", "Data source is not registered or enabled");
    let parsed: unknown;
    try { parsed = JSON.parse(body); } catch { throw new ApiError(400, "INVALID_JSON", "Webhook body must be valid JSON"); }
    const contentHash = createHash("sha256").update(body).digest("hex");
    const existing = await db.sourceDocument.findFirst({ where: { sourceId: source.id, contentHash }, orderBy: { collectedAt: "desc" } });
    if (existing) return success({ staged: true, deduplicated: true, documentId: existing.id, contentHash });
    const metadata = JSON.parse(JSON.stringify({ transport: "signed-webhook", normalizationStatus: "STAGED_RAW_PROVENANCE", receivedAt: new Date().toISOString(), rawByteLength: Buffer.byteLength(body, "utf8"), rawPayload: parsed })) as Prisma.InputJsonObject;
    const transformLog = JSON.parse(JSON.stringify({ transport: "signed-webhook", contentHash, normalizationStatus: "STAGED_RAW_PROVENANCE", domainRowsWritten: 0 })) as Prisma.InputJsonObject;
    const [document, run] = await db.$transaction(async (tx) => {
      const createdDocument = await tx.sourceDocument.create({ data: { sourceId: source.id, title: `${source.provider} ${source.dataset} webhook payload`, url: source.sourceUrl, reference: `${source.key}:webhook:${contentHash.slice(0, 16)}`, collectedAt: new Date(), contentHash, license: source.license, status: "UNKNOWN", metadata } });
      const provenance = await tx.provenanceRecord.create({ data: { sourceId: source.id, documentId: createdDocument.id, entityType: "RawWebhookRecord", entityId: `${source.key}:${contentHash.slice(0, 16)}`, sourceReference: createdDocument.reference, collectedAt: new Date(), transformedAt: new Date(), confidence: null, calculationMethod: "signed-webhook-staging-v1", license: source.license, status: "UNKNOWN" } });
      const ingestionRun = await tx.ingestionRun.create({ data: { sourceId: source.id, status: "COMPLETED_WITH_WARNINGS", finishedAt: new Date(), recordsRead: Array.isArray(parsed) ? parsed.length : 1, recordsWritten: 0, recordsRejected: 0, transformLog } });
      await tx.dataSource.update({ where: { id: source.id }, data: { lastAttemptAt: new Date(), freshnessStatus: "UNKNOWN" } });
      return [createdDocument, { ...ingestionRun, provenanceId: provenance.id }] as const;
    });
    return success({ staged: true, deduplicated: false, documentId: document.id, ingestionRunId: run.id, provenanceId: run.provenanceId, contentHash, normalizationStatus: "STAGED_RAW_PROVENANCE" }, { status: 202 });
  } catch (error) { return failure(error); }
}

import type { NextRequest } from "next/server";
import { z } from "zod";
import { db } from "@/lib/db";
import { failure, queryObject, success } from "@/lib/api";
import { requireRole, resolvePrincipal } from "@/lib/auth";

const schema = z.object({ entityType: z.string().min(1).max(100), entityId: z.string().min(1).max(200), field: z.string().max(120).optional(), limit: z.coerce.number().int().min(1).max(250).default(100) });

export async function GET(request: NextRequest) {
  try {
    requireRole(resolvePrincipal(request), "VIEWER");
    const input = schema.parse(queryObject(new URL(request.url)));
    const records = await db.provenanceRecord.findMany({
      where: { entityType: input.entityType, entityId: input.entityId, ...(input.field ? { field: input.field } : {}) },
      include: { source: true, document: true, analystReviewer: { select: { id: true, name: true } } },
      orderBy: { collectedAt: "desc" },
      take: input.limit
    });
    return success({ entityType: input.entityType, entityId: input.entityId, field: input.field ?? null, records: records.map((record) => ({ id: record.id, field: record.field, sourceReference: record.sourceReference, source: record.source ? { key: record.source.key, provider: record.source.provider, dataset: record.source.dataset, sourceUrl: record.source.sourceUrl, license: record.source.license, freshnessStatus: record.source.freshnessStatus, lastSuccessAt: record.source.lastSuccessAt } : null, document: record.document ? { id: record.document.id, title: record.document.title, url: record.document.url, reference: record.document.reference, publishedAt: record.document.publishedAt, collectedAt: record.document.collectedAt, contentHash: record.document.contentHash, license: record.document.license } : null, collectedAt: record.collectedAt, transformedAt: record.transformedAt, confidence: record.confidence?.toString() ?? null, calculationMethod: record.calculationMethod, license: record.license, status: record.status, analystReviewedAt: record.analystReviewedAt, analystReviewer: record.analystReviewer }) });
  } catch (error) { return failure(error); }
}

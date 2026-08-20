import type { NextRequest } from "next/server";
import { z } from "zod";
import { db } from "@/lib/db";
import { failure, queryObject, success } from "@/lib/api";
import { requireRole, resolvePrincipal } from "@/lib/auth";

const schema = z.object({ limit: z.coerce.number().int().min(1).max(250).default(100), confidenceBelow: z.coerce.number().min(0).max(1).default(0.7) });

export async function GET(request: NextRequest) {
  try {
    requireRole(resolvePrincipal(request), "DATA_STEWARD");
    const input = schema.parse(queryObject(new URL(request.url)));
    const [runs, provenance] = await Promise.all([
      db.ingestionRun.findMany({
        where: { status: { in: ["FAILED", "COMPLETED_WITH_WARNINGS"] } },
        include: { source: true },
        orderBy: { startedAt: "desc" },
        take: input.limit
      }),
      db.provenanceRecord.findMany({
        where: {
          OR: [
            { status: { in: ["UNKNOWN", "ESTIMATED", "ANALYST"] } },
            { confidence: { lt: input.confidenceBelow } },
            { analystReviewedAt: null, status: "DELAYED" }
          ]
        },
        include: { source: true, document: true, analystReviewer: { select: { id: true, name: true, email: true } } },
        orderBy: { collectedAt: "desc" },
        take: input.limit
      })
    ]);
    return success({
      generatedAt: new Date().toISOString(),
      thresholds: { confidenceBelow: input.confidenceBelow },
      ingestionIssues: runs.map((run) => ({ id: run.id, sourceKey: run.source.key, provider: run.source.provider, status: run.status, startedAt: run.startedAt, finishedAt: run.finishedAt, recordsRead: run.recordsRead, recordsWritten: run.recordsWritten, recordsRejected: run.recordsRejected, error: run.error, transformLog: run.transformLog })),
      provenanceReview: provenance.map((record) => ({ id: record.id, entityType: record.entityType, entityId: record.entityId, field: record.field, status: record.status, confidence: record.confidence?.toString() ?? null, collectedAt: record.collectedAt, transformedAt: record.transformedAt, source: record.source ? { key: record.source.key, provider: record.source.provider, dataset: record.source.dataset, license: record.source.license } : null, document: record.document ? { id: record.document.id, title: record.document.title, reference: record.document.reference, contentHash: record.document.contentHash } : null, analystReviewedAt: record.analystReviewedAt, analystReviewer: record.analystReviewer }))
    });
  } catch (error) { return failure(error); }
}

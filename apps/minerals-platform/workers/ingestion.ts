import { createHash } from "node:crypto";
import { Worker } from "bullmq";
import type { Prisma, RecordStatus } from "@prisma/client";
import { db } from "@/lib/db";
import { getRedis } from "@/lib/redis";
import { configuredPublicAdapters } from "@/lib/sources";

const adapters = new Map(configuredPublicAdapters().map((adapter) => [adapter.id, adapter]));

function toRecordStatus(status: string): RecordStatus {
  switch (status) {
    case "LIVE":
    case "STATIC_REFERENCE": return "VERIFIED";
    case "DELAYED":
    case "STALE": return "DELAYED";
    case "ESTIMATED": return "ESTIMATED";
    case "ANALYST": return "ANALYST";
    case "DEMO": return "DEMO";
    default: return "UNKNOWN";
  }
}

const worker = new Worker<{ sourceKey: string; runId?: string }>(
  "minerals-ingestion",
  async (job) => {
    const { sourceKey } = job.data;
    const adapter = adapters.get(sourceKey);
    if (!adapter) throw new Error(`No configured adapter for ${sourceKey}`);
    const source = await db.dataSource.findUnique({ where: { key: sourceKey } });
    if (!source || !source.enabled) throw new Error(`DataSource ${sourceKey} is not registered or enabled`);
    const run = job.data.runId
      ? await db.ingestionRun.update({ where: { id: job.data.runId }, data: { status: "RUNNING" } })
      : await db.ingestionRun.create({ data: { sourceId: source.id, status: "RUNNING" } });
    const runId = run.id;
    await db.dataSource.update({ where: { id: source.id }, data: { lastAttemptAt: new Date() } });
    try {
      const envelope = await adapter.fetch();
      const persistedStatus = toRecordStatus(envelope.status);
      const raw = JSON.stringify(envelope.rawPayload ?? envelope.records);
      const contentHash = createHash("sha256").update(raw).digest("hex");
      const existingDocument = await db.sourceDocument.findFirst({ where: { sourceId: source.id, contentHash }, orderBy: { collectedAt: "desc" } });
      const deduplicated = Boolean(existingDocument);
      const documentMetadata = JSON.parse(JSON.stringify({
        upstreamStatus: envelope.status,
        attribution: envelope.attribution,
        errors: envelope.errors,
        recordCount: envelope.records.length,
        rawByteLength: Buffer.byteLength(raw, "utf8"),
        rawPayload: envelope.rawPayload,
        normalizationStatus: "STAGED_RAW_PROVENANCE"
      })) as Prisma.InputJsonObject;
      const document = existingDocument ?? await db.sourceDocument.create({
        data: {
          sourceId: source.id,
          title: `${source.provider} ${source.dataset} snapshot`,
          url: source.sourceUrl,
          reference: `${source.key}:${contentHash.slice(0, 16)}`,
          collectedAt: envelope.collectedAt ? new Date(envelope.collectedAt) : new Date(),
          contentHash,
          license: envelope.license,
          status: persistedStatus,
          metadata: documentMetadata
        }
      });
      let provenanceRowsWritten = 0;
      if (!deduplicated && envelope.records.length) {
        const result = await db.provenanceRecord.createMany({
          data: envelope.records.map((_record, index) => ({
            sourceId: source.id,
            documentId: document.id,
            entityType: "RawSourceRecord",
            entityId: `${source.key}:${contentHash.slice(0, 12)}:${index}`,
            sourceReference: document.reference,
            collectedAt: envelope.collectedAt ? new Date(envelope.collectedAt) : new Date(),
            transformedAt: new Date(envelope.transformedAt),
            confidence: envelope.confidence,
            calculationMethod: "raw-source-staging-v1",
            license: envelope.license,
            status: persistedStatus
          }))
        });
        provenanceRowsWritten = result.count;
      }
      const transformLog = JSON.parse(JSON.stringify({
        adapter: adapter.id,
        upstreamStatus: envelope.status,
        persistedStatus,
        transformedAt: envelope.transformedAt,
        contentHash,
        deduplicated,
        normalizationStatus: "STAGED_RAW_PROVENANCE",
        provenanceRowsWritten,
        domainRowsWritten: 0,
        errors: envelope.errors
      })) as Prisma.InputJsonObject;
      const redis = getRedis();
      if (redis.status === "wait") await redis.connect();
      await redis.set(`minerals:source-cache:${source.key}`, JSON.stringify({ cachedAt: new Date().toISOString(), envelope }), "EX", source.ttlSeconds ?? 300);
      await db.$transaction([
        db.dataSource.update({ where: { id: source.id }, data: { lastSuccessAt: new Date(), freshnessStatus: envelope.status } }),
        db.ingestionRun.update({ where: { id: runId }, data: { status: envelope.errors.length ? "COMPLETED_WITH_WARNINGS" : "COMPLETED", finishedAt: new Date(), recordsRead: envelope.records.length, recordsWritten: 0, recordsRejected: 0, transformLog } })
      ]);
      return { sourceKey, runId, stagedRecords: envelope.records.length, provenanceRowsWritten, domainRowsWritten: 0, deduplicated, status: envelope.status };
    } catch (error) {
      await db.ingestionRun.update({ where: { id: runId }, data: { status: "FAILED", finishedAt: new Date(), error: error instanceof Error ? error.message : String(error) } });
      throw error;
    }
  },
  { connection: getRedis(), concurrency: Number(process.env.INGESTION_CONCURRENCY ?? 4), limiter: { max: 20, duration: 60_000 } }
);

worker.on("completed", (job) => console.log(`minerals ingestion completed: ${job.id}`));
worker.on("failed", (job, error) => console.error(`minerals ingestion failed: ${job?.id}`, error));

async function shutdown() {
  await worker.close();
  await db.$disconnect();
}
process.once("SIGINT", shutdown);
process.once("SIGTERM", shutdown);

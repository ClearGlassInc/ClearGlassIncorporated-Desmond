import type { NextRequest } from "next/server";
import { Queue } from "bullmq";
import { z } from "zod";
import { db } from "@/lib/db";
import { failure, success } from "@/lib/api";
import { requireRole, resolvePrincipal } from "@/lib/auth";
import { getRedis } from "@/lib/redis";
import { writeAudit } from "@/lib/audit";

const schema = z.object({ sourceKey: z.string().min(1).max(100), force: z.boolean().default(false) });

export async function GET(request: NextRequest) {
  try {
    requireRole(resolvePrincipal(request), "DATA_STEWARD");
    const runs = await db.ingestionRun.findMany({ include: { source: true }, orderBy: { startedAt: "desc" }, take: 100 });
    return success(runs);
  } catch (error) { return failure(error); }
}

export async function POST(request: NextRequest) {
  try {
    const principal = requireRole(resolvePrincipal(request), "DATA_STEWARD");
    const input = schema.parse(await request.json());
    const source = await db.dataSource.findUnique({ where: { key: input.sourceKey } });
    if (!source || !source.enabled) return Response.json({ ok: false, error: { code: "SOURCE_UNAVAILABLE", message: "Source not found or disabled" } }, { status: 404 });
    if (!input.force && source.lastAttemptAt && source.ttlSeconds) {
      const nextAllowed = source.lastAttemptAt.getTime() + source.ttlSeconds * 1000;
      if (Date.now() < nextAllowed) return Response.json({ ok: false, error: { code: "SOURCE_TTL", message: "Source refresh is still inside its TTL" } }, { status: 429 });
    }
    const run = await db.ingestionRun.create({ data: { sourceId: source.id, status: "QUEUED" } });
    await db.dataSource.update({ where: { id: source.id }, data: { lastAttemptAt: new Date() } });
    const queue = new Queue("minerals-ingestion", { connection: getRedis(), defaultJobOptions: { attempts: 5, backoff: { type: "exponential", delay: 2000 }, removeOnComplete: 200, removeOnFail: 500 } });
    await queue.add("ingest-source", { sourceKey: source.key, runId: run.id }, { jobId: run.id });
    await queue.close();
    await writeAudit(principal, "ingestion.enqueue", "IngestionRun", run.id, { sourceKey: source.key, force: input.force });
    return success({ runId: run.id, sourceKey: source.key, status: "QUEUED" }, { status: 202 });
  } catch (error) { return failure(error); }
}

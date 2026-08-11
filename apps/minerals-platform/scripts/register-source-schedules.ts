import { Queue } from "bullmq";
import { db } from "@/lib/db";
import { getRedis } from "@/lib/redis";

const queue = new Queue("minerals-ingestion", { connection: getRedis() });
const sources = await db.dataSource.findMany({ where: { enabled: true }, select: { key: true, ttlSeconds: true } });

for (const source of sources) {
  const every = Math.max(60_000, (source.ttlSeconds ?? 3600) * 1000);
  await queue.upsertJobScheduler(
    `source:${source.key}`,
    { every },
    { name: "ingest-source", data: { sourceKey: source.key }, opts: { attempts: 5, backoff: { type: "exponential", delay: 2000 }, removeOnComplete: 200, removeOnFail: 500 } }
  );
  console.log(`Registered ${source.key} every ${every}ms`);
}

await queue.close();
await db.$disconnect();

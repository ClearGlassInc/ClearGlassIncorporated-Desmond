import IORedis from "ioredis";

let client: IORedis | undefined;

export function getRedis(): IORedis {
  const url = process.env.REDIS_URL;
  if (!url) throw new Error("REDIS_URL is required for cache, queue, and rate-limit services");
  client ??= new IORedis(url, { maxRetriesPerRequest: null, enableReadyCheck: true, lazyConnect: true });
  return client;
}

export async function closeRedis(): Promise<void> {
  if (!client) return;
  await client.quit();
  client = undefined;
}

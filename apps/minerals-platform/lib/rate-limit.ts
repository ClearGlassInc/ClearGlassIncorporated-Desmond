import { getRedis } from "@/lib/redis";

export async function enforceRateLimit(key: string, limit = 120, windowSeconds = 60): Promise<{ allowed: boolean; remaining: number }> {
  const redis = getRedis();
  if (redis.status === "wait") await redis.connect();
  const bucket = `minerals:ratelimit:${key}:${Math.floor(Date.now() / (windowSeconds * 1000))}`;
  const count = await redis.incr(bucket);
  if (count === 1) await redis.expire(bucket, windowSeconds + 1);
  return { allowed: count <= limit, remaining: Math.max(0, limit - count) };
}

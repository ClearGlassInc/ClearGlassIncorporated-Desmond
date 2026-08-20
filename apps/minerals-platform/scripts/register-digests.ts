import { Queue } from "bullmq";
import { getRedis } from "@/lib/redis";

const queue = new Queue("minerals-digests", { connection: getRedis() });
const dailyPattern = process.env.DIGEST_DAILY_CRON ?? "0 0 12 * * *";
const weeklyPattern = process.env.DIGEST_WEEKLY_CRON ?? "0 5 12 * * 1";

await queue.upsertJobScheduler(
  "daily-alert-digest",
  { pattern: dailyPattern },
  { name: "generate-digest", data: { cadence: "daily" }, opts: { attempts: 3, backoff: { type: "exponential", delay: 2000 }, removeOnComplete: 50, removeOnFail: 100 } }
);
await queue.upsertJobScheduler(
  "weekly-alert-digest",
  { pattern: weeklyPattern },
  { name: "generate-digest", data: { cadence: "weekly" }, opts: { attempts: 3, backoff: { type: "exponential", delay: 2000 }, removeOnComplete: 50, removeOnFail: 100 } }
);

console.log("Registered minerals digest schedulers", { dailyPattern, weeklyPattern });
await queue.close();

import { Worker } from "bullmq";
import type { Prisma } from "@prisma/client";
import { db } from "@/lib/db";
import { getRedis } from "@/lib/redis";
import { deliverAlert } from "@/lib/notifications";

const worker = new Worker<{ cadence: "daily" | "weekly" }>(
  "minerals-digests",
  async (job) => {
    const cadence = job.data.cadence;
    const since = new Date(Date.now() - (cadence === "daily" ? 24 : 24 * 7) * 60 * 60 * 1000);
    const organizations = await db.organization.findMany({ where: { deletedAt: null }, include: { members: { where: { role: { in: ["SENIOR_ANALYST", "ADMINISTRATOR"] } }, include: { user: true }, take: 1 } } });
    const results: Array<{ organizationId: string; reportId?: string; alerts: number }> = [];
    for (const organization of organizations) {
      const alerts = await db.alert.findMany({ where: { organizationId: organization.id, createdAt: { gte: since }, status: { not: "SUPPRESSED" } }, orderBy: [{ severity: "desc" }, { createdAt: "desc" }], take: 250 });
      const author = organization.members[0]?.user;
      if (!author) { results.push({ organizationId: organization.id, alerts: alerts.length }); continue; }
      const body = JSON.parse(JSON.stringify({ cadence, periodStart: since.toISOString(), periodEnd: new Date().toISOString(), alertCount: alerts.length, alerts: alerts.map((alert) => ({ id: alert.id, severity: alert.severity, status: alert.status, title: alert.title, createdAt: alert.createdAt.toISOString() })) })) as Prisma.InputJsonObject;
      const report = await db.report.create({ data: { organizationId: organization.id, authorId: author.id, title: `${cadence === "daily" ? "Daily" : "Weekly"} Minerals Alert Digest`, status: "DRAFT", body, generatedByAi: false } });
      const recipient = process.env.DIGEST_EMAIL_TO;
      if (recipient) {
        const summary = alerts.length ? alerts.slice(0, 20).map((alert) => `[${alert.severity}] ${alert.title}`).join("\n") : "No new unsuppressed alerts in this digest period.";
        await deliverAlert("email", { subject: report.title, body: summary, severity: alerts.some((a) => a.severity === "CRITICAL") ? "CRITICAL" : alerts.some((a) => a.severity === "HIGH") ? "HIGH" : "INFO", alertId: `digest:${report.id}`, link: `${process.env.APP_BASE_URL ?? ""}/reports/${report.id}` }, { emailTo: recipient });
      }
      results.push({ organizationId: organization.id, reportId: report.id, alerts: alerts.length });
    }
    return { cadence, organizations: results };
  },
  { connection: getRedis(), concurrency: 1 }
);

worker.on("completed", (job) => console.log(`minerals digest completed: ${job.id}`));
worker.on("failed", (job, error) => console.error(`minerals digest failed: ${job?.id}`, error));

async function shutdown() { await worker.close(); await db.$disconnect(); }
process.once("SIGINT", shutdown);
process.once("SIGTERM", shutdown);

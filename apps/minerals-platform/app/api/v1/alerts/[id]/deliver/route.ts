import type { NextRequest } from "next/server";
import { z } from "zod";
import { db } from "@/lib/db";
import { failure, success } from "@/lib/api";
import { requireRole, resolvePrincipal } from "@/lib/auth";
import { writeAudit } from "@/lib/audit";
import { deliverAlert } from "@/lib/notifications";

const schema = z.object({ channel: z.enum(["email", "webhook", "slack", "teams"]), emailTo: z.string().email().optional() });

export async function POST(request: NextRequest, context: { params: Promise<{ id: string }> }) {
  try {
    const principal = requireRole(resolvePrincipal(request), "SENIOR_ANALYST");
    const { id } = await context.params;
    const input = schema.parse(await request.json());
    const alert = await db.alert.findFirst({ where: { id, organizationId: principal.organizationId } });
    if (!alert) return Response.json({ ok: false, error: { code: "NOT_FOUND", message: "Alert not found" } }, { status: 404 });
    await deliverAlert(input.channel, { subject: alert.title, body: alert.body ?? alert.title, severity: alert.severity, alertId: alert.id, link: `${process.env.APP_BASE_URL ?? ""}/alerts/${alert.id}` }, { emailTo: input.emailTo });
    await writeAudit(principal, "alert.deliver", "Alert", alert.id, { channel: input.channel, recipient: input.channel === "email" ? input.emailTo : undefined });
    return success({ delivered: true, channel: input.channel, alertId: alert.id });
  } catch (error) { return failure(error); }
}

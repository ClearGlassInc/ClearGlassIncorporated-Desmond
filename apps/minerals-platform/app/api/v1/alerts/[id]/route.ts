import type { NextRequest } from "next/server";
import { z } from "zod";
import { db } from "@/lib/db";
import { failure, success } from "@/lib/api";
import { requireRole, resolvePrincipal } from "@/lib/auth";
import { writeAudit } from "@/lib/audit";

const actionSchema = z.discriminatedUnion("action", [
  z.object({ action: z.literal("ACKNOWLEDGE") }),
  z.object({ action: z.literal("ASSIGN"), userId: z.string().uuid() }),
  z.object({ action: z.literal("RESOLVE") }),
  z.object({ action: z.literal("SUPPRESS") }),
  z.object({ action: z.literal("COMMENT"), body: z.string().trim().min(1).max(4000) })
]);

export async function GET(request: NextRequest, context: { params: Promise<{ id: string }> }) {
  try {
    const principal = requireRole(resolvePrincipal(request), "VIEWER");
    const { id } = await context.params;
    const [alert, comments] = await Promise.all([
      db.alert.findFirst({ where: { id, organizationId: principal.organizationId }, include: { assignedTo: { select: { id: true, name: true, email: true } } } }),
      db.analystAnnotation.findMany({ where: { organizationId: principal.organizationId, entityType: "Alert", entityId: id, deletedAt: null }, include: { author: { select: { id: true, name: true, email: true } } }, orderBy: { createdAt: "asc" } })
    ]);
    if (!alert) return Response.json({ ok: false, error: { code: "NOT_FOUND", message: "Alert not found" } }, { status: 404 });
    return success({ ...alert, comments });
  } catch (error) { return failure(error); }
}

export async function PATCH(request: NextRequest, context: { params: Promise<{ id: string }> }) {
  try {
    const principal = requireRole(resolvePrincipal(request), "ANALYST");
    const { id } = await context.params;
    const input = actionSchema.parse(await request.json());
    const existing = await db.alert.findFirst({ where: { id, organizationId: principal.organizationId } });
    if (!existing) return Response.json({ ok: false, error: { code: "NOT_FOUND", message: "Alert not found" } }, { status: 404 });
    if (input.action === "COMMENT") {
      const comment = await db.analystAnnotation.create({ data: { organizationId: principal.organizationId, authorId: principal.userId, entityType: "Alert", entityId: id, body: input.body } });
      await writeAudit(principal, "alert.comment", "Alert", id, { commentId: comment.id });
      return success({ alert: existing, comment });
    }
    const data = input.action === "ACKNOWLEDGE"
      ? { status: "ACKNOWLEDGED" as const, acknowledgedAt: new Date() }
      : input.action === "ASSIGN"
        ? { status: "ASSIGNED" as const, assignedToId: input.userId }
        : input.action === "RESOLVE"
          ? { status: "RESOLVED" as const, resolvedAt: new Date() }
          : { status: "SUPPRESSED" as const };
    const alert = await db.alert.update({ where: { id }, data });
    await writeAudit(principal, `alert.${input.action.toLowerCase()}`, "Alert", id, data);
    return success(alert);
  } catch (error) { return failure(error); }
}

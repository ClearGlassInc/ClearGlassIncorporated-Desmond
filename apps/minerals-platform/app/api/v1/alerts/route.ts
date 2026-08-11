import type { NextRequest } from "next/server";
import { z } from "zod";
import { db } from "@/lib/db";
import { failure, pageSchema, paginated, queryObject, success } from "@/lib/api";
import { requireRole, resolvePrincipal } from "@/lib/auth";
import { writeAudit } from "@/lib/audit";

const getSchema = pageSchema.extend({ status: z.enum(["OPEN","ACKNOWLEDGED","ASSIGNED","RESOLVED","SUPPRESSED"]).optional(), severity: z.enum(["LOW","MODERATE","HIGH","CRITICAL","UNKNOWN"]).optional() });
const createSchema = z.object({
  type: z.string().min(1).max(80),
  severity: z.enum(["LOW","MODERATE","HIGH","CRITICAL","UNKNOWN"]),
  title: z.string().min(1).max(240),
  body: z.string().max(4000).optional(),
  dedupeKey: z.string().max(240).optional(),
  entityType: z.string().max(80).optional(),
  entityId: z.string().max(160).optional(),
  threshold: z.record(z.string(), z.unknown()).optional()
});

export async function GET(request: NextRequest) {
  try {
    const principal = requireRole(resolvePrincipal(request), "VIEWER");
    const input = getSchema.parse(queryObject(new URL(request.url)));
    const where = { organizationId: principal.organizationId, ...(input.status ? { status: input.status } : {}), ...(input.severity ? { severity: input.severity } : {}) };
    const [items, total] = await Promise.all([
      db.alert.findMany({ where, include: { assignedTo: { select: { id: true, name: true, email: true } } }, skip: (input.page - 1) * input.pageSize, take: input.pageSize, orderBy: [{ severity: "desc" }, { createdAt: "desc" }] }),
      db.alert.count({ where })
    ]);
    return paginated(items, input.page, input.pageSize, total);
  } catch (error) { return failure(error); }
}

export async function POST(request: NextRequest) {
  try {
    const principal = requireRole(resolvePrincipal(request), "ANALYST");
    const input = createSchema.parse(await request.json());
    if (input.dedupeKey) {
      const existing = await db.alert.findFirst({ where: { organizationId: principal.organizationId, dedupeKey: input.dedupeKey, status: { notIn: ["RESOLVED", "SUPPRESSED"] } } });
      if (existing) return success({ deduplicated: true, alert: existing });
    }
    const alert = await db.alert.create({ data: { organizationId: principal.organizationId, ...input } });
    await writeAudit(principal, "alert.create", "Alert", alert.id, { severity: alert.severity, type: alert.type });
    return success({ deduplicated: false, alert }, { status: 201 });
  } catch (error) { return failure(error); }
}

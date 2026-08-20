import type { NextRequest } from "next/server";
import { z } from "zod";
import { db } from "@/lib/db";
import { failure, pageSchema, paginated, queryObject } from "@/lib/api";
import { requireRole, resolvePrincipal } from "@/lib/auth";

const schema = pageSchema.extend({ action: z.string().max(120).optional(), userId: z.string().uuid().optional(), from: z.coerce.date().optional(), to: z.coerce.date().optional() });

export async function GET(request: NextRequest) {
  try {
    const principal = requireRole(resolvePrincipal(request), "ADMINISTRATOR");
    const input = schema.parse(queryObject(new URL(request.url)));
    const where = {
      organizationId: principal.organizationId,
      ...(input.action ? { action: { contains: input.action, mode: "insensitive" as const } } : {}),
      ...(input.userId ? { userId: input.userId } : {}),
      ...(input.from || input.to ? { createdAt: { ...(input.from ? { gte: input.from } : {}), ...(input.to ? { lte: input.to } : {}) } } : {})
    };
    const [items, total] = await Promise.all([
      db.auditLog.findMany({ where, include: { user: { select: { id: true, email: true, name: true } } }, skip: (input.page - 1) * input.pageSize, take: input.pageSize, orderBy: { createdAt: "desc" } }),
      db.auditLog.count({ where })
    ]);
    return paginated(items, input.page, input.pageSize, total);
  } catch (error) { return failure(error); }
}

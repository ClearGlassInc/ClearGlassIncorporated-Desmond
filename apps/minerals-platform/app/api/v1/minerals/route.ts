import type { NextRequest } from "next/server";
import { z } from "zod";
import { db } from "@/lib/db";
import { failure, pageSchema, paginated, queryObject } from "@/lib/api";
import { requireRole, resolvePrincipal } from "@/lib/auth";

const schema = pageSchema.extend({ q: z.string().max(120).optional(), group: z.string().max(80).optional() });

export async function GET(request: NextRequest) {
  try {
    requireRole(resolvePrincipal(request), "VIEWER");
    const input = schema.parse(queryObject(new URL(request.url)));
    const where = {
      deletedAt: null,
      ...(input.group ? { group: input.group } : {}),
      ...(input.q ? { OR: [{ name: { contains: input.q, mode: "insensitive" as const } }, { symbol: { contains: input.q, mode: "insensitive" as const } }] } : {})
    };
    const [items, total] = await Promise.all([
      db.mineral.findMany({ where, include: { forms: true }, skip: (input.page - 1) * input.pageSize, take: input.pageSize, orderBy: { name: input.order } }),
      db.mineral.count({ where })
    ]);
    return paginated(items, input.page, input.pageSize, total);
  } catch (error) { return failure(error); }
}

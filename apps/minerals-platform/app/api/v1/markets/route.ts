import type { NextRequest } from "next/server";
import { z } from "zod";
import { db } from "@/lib/db";
import { failure, pageSchema, paginated, queryObject } from "@/lib/api";
import { requireRole, resolvePrincipal } from "@/lib/auth";

const schema = pageSchema.extend({
  mineralId: z.string().uuid().optional(),
  benchmark: z.string().max(120).optional(),
  from: z.coerce.date().optional(),
  to: z.coerce.date().optional()
});

export async function GET(request: NextRequest) {
  try {
    requireRole(resolvePrincipal(request), "VIEWER");
    const input = schema.parse(queryObject(new URL(request.url)));
    const where = {
      ...(input.mineralId ? { mineralId: input.mineralId } : {}),
      ...(input.benchmark ? { benchmark: input.benchmark } : {}),
      ...(input.from || input.to ? { timestamp: { ...(input.from ? { gte: input.from } : {}), ...(input.to ? { lte: input.to } : {}) } } : {})
    };
    const [items, total] = await Promise.all([
      db.priceSeries.findMany({ where, include: { mineral: true, source: true }, skip: (input.page - 1) * input.pageSize, take: input.pageSize, orderBy: { timestamp: "desc" } }),
      db.priceSeries.count({ where })
    ]);
    return paginated(items, input.page, input.pageSize, total);
  } catch (error) { return failure(error); }
}

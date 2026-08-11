import type { NextRequest } from "next/server";
import { z } from "zod";
import { db } from "@/lib/db";
import { failure, pageSchema, paginated, queryObject } from "@/lib/api";
import { requireRole, resolvePrincipal } from "@/lib/auth";

const schema = pageSchema.extend({
  q: z.string().max(160).optional(),
  mineralId: z.string().uuid().optional(),
  countryId: z.string().uuid().optional(),
  stage: z.enum(["CONCEPT","EXPLORATION","DEVELOPMENT","CONSTRUCTION","OPERATING","CARE_MAINTENANCE","CLOSED","UNKNOWN"]).optional()
});

export async function GET(request: NextRequest) {
  try {
    requireRole(resolvePrincipal(request), "VIEWER");
    const input = schema.parse(queryObject(new URL(request.url)));
    const where = {
      deletedAt: null,
      ...(input.q ? { name: { contains: input.q, mode: "insensitive" as const } } : {}),
      ...(input.mineralId ? { mineralId: input.mineralId } : {}),
      ...(input.countryId ? { countryId: input.countryId } : {}),
      ...(input.stage ? { stage: input.stage } : {})
    };
    const [items, total] = await Promise.all([
      db.mine.findMany({ where, include: { mineral: true, country: true, jurisdiction: true, operator: true, ownership: { include: { ownerCompany: true } }, production: { orderBy: { periodEnd: "desc" }, take: 12 }, reserves: { orderBy: { asOf: "desc" }, take: 12 }, risks: { orderBy: { observedAt: "desc" }, take: 1 } }, skip: (input.page - 1) * input.pageSize, take: input.pageSize, orderBy: { name: input.order } }),
      db.mine.count({ where })
    ]);
    return paginated(items, input.page, input.pageSize, total);
  } catch (error) { return failure(error); }
}

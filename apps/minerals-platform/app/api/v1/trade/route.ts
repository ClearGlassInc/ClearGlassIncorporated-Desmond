import type { NextRequest } from "next/server";
import { z } from "zod";
import { db } from "@/lib/db";
import { failure, pageSchema, paginated, queryObject } from "@/lib/api";
import { requireRole, resolvePrincipal } from "@/lib/auth";

const schema = pageSchema.extend({
  mineralId: z.string().uuid().optional(),
  originCountryId: z.string().uuid().optional(),
  destinationCountryId: z.string().uuid().optional(),
  hsCode: z.string().max(24).optional(),
  from: z.coerce.date().optional(),
  to: z.coerce.date().optional()
});

export async function GET(request: NextRequest) {
  try {
    requireRole(resolvePrincipal(request), "VIEWER");
    const input = schema.parse(queryObject(new URL(request.url)));
    const where = {
      ...(input.mineralId ? { mineralId: input.mineralId } : {}),
      ...(input.originCountryId ? { originCountryId: input.originCountryId } : {}),
      ...(input.destinationCountryId ? { destinationCountryId: input.destinationCountryId } : {}),
      ...(input.hsCode ? { hsCode: input.hsCode } : {}),
      ...(input.from || input.to ? { periodStart: { ...(input.from ? { gte: input.from } : {}), ...(input.to ? { lte: input.to } : {}) } } : {})
    };
    const [items, total] = await Promise.all([
      db.tradeRecord.findMany({ where, include: { mineral: true, originCountry: true, destinationCountry: true, source: true }, skip: (input.page - 1) * input.pageSize, take: input.pageSize, orderBy: { periodStart: "desc" } }),
      db.tradeRecord.count({ where })
    ]);
    return paginated(items, input.page, input.pageSize, total);
  } catch (error) { return failure(error); }
}

import type { NextRequest } from "next/server";
import { z } from "zod";
import { db } from "@/lib/db";
import { failure, queryObject, success } from "@/lib/api";
import { requireRole, resolvePrincipal } from "@/lib/auth";
import { hhi } from "@/lib/risk";

const schema = z.object({ mineralId: z.string().uuid().optional(), limit: z.coerce.number().int().min(1).max(500).default(150) });

export async function GET(request: NextRequest) {
  try {
    requireRole(resolvePrincipal(request), "VIEWER");
    const input = schema.parse(queryObject(new URL(request.url)));
    const ownershipWhere = input.mineralId
      ? { verified: true, OR: [{ mine: { mineralId: input.mineralId } }, { project: { mineralId: input.mineralId } }] }
      : { verified: true };
    const [ownership, routes, facilities, production] = await Promise.all([
      db.ownershipRelationship.findMany({ where: ownershipWhere, include: { ownerCompany: true, mine: { include: { mineral: true, country: true } }, project: { include: { mineral: true, country: true } } }, take: input.limit }),
      db.shippingRoute.findMany({ where: { verified: true }, include: { origin: { include: { country: true } }, destination: { include: { country: true } } }, take: input.limit }),
      db.facility.findMany({ where: { deletedAt: null }, include: { operator: true, country: true }, take: input.limit }),
      db.productionRecord.findMany({ where: input.mineralId ? { mineralId: input.mineralId } : {}, include: { country: true, mineral: true }, orderBy: { periodEnd: "desc" }, take: 2000 })
    ]);

    const latestPeriod = production.reduce<Date | null>((latest, row) => !latest || row.periodEnd > latest ? row.periodEnd : latest, null);
    const latest = latestPeriod ? production.filter((row) => row.periodEnd.getTime() === latestPeriod.getTime() && row.countryId) : [];
    const byCountry = new Map<string, { country: string; value: number }>();
    for (const row of latest) {
      if (!row.countryId || !row.country) continue;
      const current = byCountry.get(row.countryId) ?? { country: row.country.name, value: 0 };
      current.value += Number(row.value);
      byCountry.set(row.countryId, current);
    }
    const concentration = [...byCountry.entries()].map(([countryId, value]) => ({ countryId, ...value }));
    const total = concentration.reduce((sum, item) => sum + item.value, 0);
    const shares = total > 0 ? concentration.map((item) => item.value / total * 100) : [];

    return success({
      asOf: new Date().toISOString(),
      verifiedRelationships: {
        ownership: ownership.map((item) => ({ id: item.id, type: "ownership", verified: true, owner: { id: item.ownerCompany.id, name: item.ownerCompany.name }, asset: item.mine ? { type: "mine", id: item.mine.id, name: item.mine.name, mineral: item.mine.mineral?.name, country: item.mine.country?.name } : item.project ? { type: "project", id: item.project.id, name: item.project.name, mineral: item.project.mineral?.name, country: item.project.country?.name } : null, sharePercent: item.sharePercent?.toString() ?? null })),
        logistics: routes.map((route) => ({ id: route.id, type: "logistics", verified: true, mode: route.mode, origin: { id: route.origin.id, name: route.origin.name, country: route.origin.country?.name }, destination: { id: route.destination.id, name: route.destination.name, country: route.destination.country?.name } })),
        facilities: facilities.map((facility) => ({ id: facility.id, type: facility.type, name: facility.name, country: facility.country?.name, operator: facility.operator?.name, status: facility.sourceStatus, confidence: facility.confidence?.toString() ?? null }))
      },
      inferredRelationships: [],
      productionConcentration: { periodEnd: latestPeriod?.toISOString() ?? null, countries: concentration, hhi: shares.length ? hhi(shares) : null, methodology: "HHI from loaded country production records for the latest common period; null when evidence is absent" }
    });
  } catch (error) { return failure(error); }
}

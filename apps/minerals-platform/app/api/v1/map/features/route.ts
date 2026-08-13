import type { NextRequest } from "next/server";
import { z } from "zod";
import { db } from "@/lib/db";
import { failure, queryObject, success } from "@/lib/api";
import { requireRole, resolvePrincipal } from "@/lib/auth";

const schema = z.object({
  west: z.coerce.number().min(-180).max(180).default(-180),
  south: z.coerce.number().min(-90).max(90).default(-90),
  east: z.coerce.number().min(-180).max(180).default(180),
  north: z.coerce.number().min(-90).max(90).default(90),
  type: z.enum(["project", "mine", "facility", "logistics", "all"]).default("all"),
  limit: z.coerce.number().int().min(1).max(5000).default(1000)
});

type Feature = { type: "Feature"; geometry: { type: "Point"; coordinates: [number, number] }; properties: Record<string, unknown> };

export async function GET(request: NextRequest) {
  try {
    requireRole(resolvePrincipal(request), "VIEWER");
    const input = schema.parse(queryObject(new URL(request.url)));
    if (input.west > input.east || input.south > input.north) throw new z.ZodError([{ code: "custom", path: ["bbox"], message: "Invalid bounding box" }]);
    const bounds = { latitude: { gte: input.south, lte: input.north }, longitude: { gte: input.west, lte: input.east } };
    const features: Feature[] = [];
    if (input.type === "all" || input.type === "project") {
      const rows = await db.project.findMany({ where: { deletedAt: null, ...bounds }, take: input.limit, include: { mineral: true, country: true } });
      features.push(...rows.filter((r) => r.latitude != null && r.longitude != null).map((r) => ({ type: "Feature" as const, geometry: { type: "Point" as const, coordinates: [r.longitude!, r.latitude!] as [number, number] }, properties: { id: r.id, entityType: "project", name: r.name, stage: r.stage, mineral: r.mineral?.name, country: r.country?.name, status: r.sourceStatus, confidence: r.confidence } })));
    }
    if (input.type === "all" || input.type === "mine") {
      const rows = await db.mine.findMany({ where: { deletedAt: null, ...bounds }, take: input.limit, include: { mineral: true, country: true } });
      features.push(...rows.filter((r) => r.latitude != null && r.longitude != null).map((r) => ({ type: "Feature" as const, geometry: { type: "Point" as const, coordinates: [r.longitude!, r.latitude!] as [number, number] }, properties: { id: r.id, entityType: "mine", name: r.name, stage: r.stage, mineral: r.mineral?.name, country: r.country?.name, status: r.sourceStatus, confidence: r.confidence } })));
    }
    if (input.type === "all" || input.type === "facility") {
      const rows = await db.facility.findMany({ where: { deletedAt: null, ...bounds }, take: input.limit, include: { country: true } });
      features.push(...rows.filter((r) => r.latitude != null && r.longitude != null).map((r) => ({ type: "Feature" as const, geometry: { type: "Point" as const, coordinates: [r.longitude!, r.latitude!] as [number, number] }, properties: { id: r.id, entityType: "facility", name: r.name, facilityType: r.type, country: r.country?.name, status: r.sourceStatus, confidence: r.confidence } })));
    }
    if (input.type === "all" || input.type === "logistics") {
      const rows = await db.logisticsNode.findMany({ where: bounds, take: input.limit, include: { country: true } });
      features.push(...rows.filter((r) => r.latitude != null && r.longitude != null).map((r) => ({ type: "Feature" as const, geometry: { type: "Point" as const, coordinates: [r.longitude!, r.latitude!] as [number, number] }, properties: { id: r.id, entityType: "logistics", name: r.name, logisticsType: r.type, country: r.country?.name } })));
    }
    return success({ type: "FeatureCollection", features: features.slice(0, input.limit), bbox: [input.west, input.south, input.east, input.north] }, { headers: { "Cache-Control": "private, max-age=30" } });
  } catch (error) { return failure(error); }
}

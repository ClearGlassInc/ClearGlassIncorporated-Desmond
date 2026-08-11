import type { NextRequest } from "next/server";
import { z } from "zod";
import { db } from "@/lib/db";
import { failure, queryObject } from "@/lib/api";
import { requireRole, resolvePrincipal } from "@/lib/auth";
import { writeAudit } from "@/lib/audit";

const schema = z.object({ entity: z.enum(["projects", "mines", "trade"]), format: z.enum(["csv", "json"]).default("csv"), limit: z.coerce.number().int().min(1).max(5000).default(1000) });

function csvCell(value: unknown): string {
  const raw = value == null ? "" : typeof value === "object" ? JSON.stringify(value) : String(value);
  return `"${raw.replaceAll('"', '""')}"`;
}

export async function GET(request: NextRequest) {
  try {
    const principal = requireRole(resolvePrincipal(request), "ANALYST");
    const input = schema.parse(queryObject(new URL(request.url)));
    const rows = input.entity === "projects"
      ? await db.project.findMany({ where: { deletedAt: null }, take: input.limit, include: { mineral: true, country: true, operator: true } })
      : input.entity === "mines"
        ? await db.mine.findMany({ where: { deletedAt: null }, take: input.limit, include: { mineral: true, country: true, operator: true } })
        : await db.tradeRecord.findMany({ take: input.limit, include: { mineral: true, originCountry: true, destinationCountry: true, source: true } });
    await writeAudit(principal, "export.create", input.entity, undefined, { format: input.format, count: rows.length });
    if (input.format === "json") return new Response(JSON.stringify({ exportedAt: new Date().toISOString(), entity: input.entity, rows }), { headers: { "Content-Type": "application/json", "Content-Disposition": `attachment; filename="minerals-${input.entity}.json"`, "Cache-Control": "no-store" } });
    if (!rows.length) return new Response("", { headers: { "Content-Type": "text/csv; charset=utf-8", "Content-Disposition": `attachment; filename="minerals-${input.entity}.csv"` } });
    const flat = rows.map((row) => JSON.parse(JSON.stringify(row)) as Record<string, unknown>);
    const headers = [...new Set(flat.flatMap((row) => Object.keys(row)))];
    const csv = [headers.map(csvCell).join(","), ...flat.map((row) => headers.map((key) => csvCell(row[key])).join(","))].join("\n");
    return new Response(csv, { headers: { "Content-Type": "text/csv; charset=utf-8", "Content-Disposition": `attachment; filename="minerals-${input.entity}.csv"`, "Cache-Control": "no-store" } });
  } catch (error) { return failure(error); }
}

import type { NextRequest } from "next/server";
import { z } from "zod";
import { db } from "@/lib/db";
import { failure, queryObject, success } from "@/lib/api";
import { requireRole, resolvePrincipal } from "@/lib/auth";

const schema = z.object({ mineralId: z.string().uuid(), benchmark: z.string().max(120).optional(), limit: z.coerce.number().int().min(2).max(2000).default(365) });

function mean(values: number[]) { return values.length ? values.reduce((sum, value) => sum + value, 0) / values.length : null; }
function stddev(values: number[]) {
  if (values.length < 2) return null;
  const avg = mean(values)!;
  return Math.sqrt(values.reduce((sum, value) => sum + Math.pow(value - avg, 2), 0) / (values.length - 1));
}
function percentChange(current: number, previous: number | undefined) {
  return previous && previous !== 0 ? (current / previous - 1) * 100 : null;
}

export async function GET(request: NextRequest) {
  try {
    requireRole(resolvePrincipal(request), "VIEWER");
    const input = schema.parse(queryObject(new URL(request.url)));
    const rows = await db.priceSeries.findMany({ where: { mineralId: input.mineralId, ...(input.benchmark ? { benchmark: input.benchmark } : {}) }, include: { mineral: true, source: true }, orderBy: { timestamp: "desc" }, take: input.limit });
    if (!rows.length) return success({ mineralId: input.mineralId, observations: 0, latest: null, analytics: null, message: "No observed market series loaded; no analytics or forecast generated." });
    const chronological = [...rows].reverse();
    const values = chronological.map((row) => Number(row.value));
    const latest = chronological.at(-1)!;
    const returns = values.slice(1).map((value, index) => values[index]! > 0 && value > 0 ? Math.log(value / values[index]!) : null).filter((value): value is number => value !== null && Number.isFinite(value));
    const volatility = stddev(returns);
    const ma = (period: number) => mean(values.slice(-period));
    const previous = (distance: number) => values.length > distance ? values[values.length - 1 - distance] : undefined;
    return success({
      mineral: { id: latest.mineral.id, name: latest.mineral.name, symbol: latest.mineral.symbol },
      benchmark: latest.benchmark,
      observations: rows.length,
      latest: { timestamp: latest.timestamp, value: latest.value.toString(), currency: latest.currency, unit: latest.unit, status: latest.status, confidence: latest.confidence?.toString() ?? null, source: latest.source ? { key: latest.source.key, provider: latest.source.provider, license: latest.source.license, freshnessStatus: latest.source.freshnessStatus } : null },
      analytics: {
        movingAverages: { ma20: ma(20), ma50: ma(50), ma200: ma(200) },
        observedChangesPercent: { oneObservation: percentChange(values.at(-1)!, previous(1)), sevenObservations: percentChange(values.at(-1)!, previous(7)), thirtyObservations: percentChange(values.at(-1)!, previous(30)) },
        logReturnVolatility: volatility,
        methodology: "Moving averages and sample standard deviation of observed log returns. Observation-distance changes are not calendar-period claims unless the source cadence is daily.",
        forecast: null
      }
    });
  } catch (error) { return failure(error); }
}

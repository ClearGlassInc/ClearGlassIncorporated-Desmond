import type { NextRequest } from "next/server";
import { db } from "@/lib/db";
import { failure, success } from "@/lib/api";
import { requireRole, resolvePrincipal } from "@/lib/auth";

export async function GET(request: NextRequest) {
  try {
    requireRole(resolvePrincipal(request), "VIEWER");
    const sources = await db.dataSource.findMany({
      include: { ingestionRuns: { orderBy: { startedAt: "desc" }, take: 1 } },
      orderBy: { key: "asc" }
    });
    return success(sources.map((source) => ({
      ...source,
      latestRun: source.ingestionRuns[0] ?? null,
      ingestionRuns: undefined
    })));
  } catch (error) { return failure(error); }
}

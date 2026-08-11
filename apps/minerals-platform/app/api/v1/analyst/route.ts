import type { NextRequest } from "next/server";
import { z } from "zod";
import { db } from "@/lib/db";
import { failure, success } from "@/lib/api";
import { requireRole, resolvePrincipal } from "@/lib/auth";
import { writeAudit } from "@/lib/audit";

const schema = z.object({ question: z.string().trim().min(3).max(1200) });

function terms(question: string) {
  return [...new Set(question.toLowerCase().split(/[^a-z0-9-]+/).filter((term) => term.length >= 4))].slice(0, 8);
}

export async function POST(request: NextRequest) {
  try {
    const principal = requireRole(resolvePrincipal(request), "ANALYST");
    const input = schema.parse(await request.json());
    const tokens = terms(input.question);
    const OR = tokens.flatMap((term) => [{ name: { contains: term, mode: "insensitive" as const } }]);
    const [minerals, projects, mines, events, sources] = await Promise.all([
      db.mineral.findMany({ where: { deletedAt: null, ...(OR.length ? { OR } : {}) }, take: 8 }),
      db.project.findMany({ where: { deletedAt: null, ...(OR.length ? { OR } : {}) }, include: { mineral: true, country: true, risks: { orderBy: { observedAt: "desc" }, take: 1 } }, take: 8 }),
      db.mine.findMany({ where: { deletedAt: null, ...(OR.length ? { OR } : {}) }, include: { mineral: true, country: true, risks: { orderBy: { observedAt: "desc" }, take: 1 } }, take: 8 }),
      db.event.findMany({ where: OR.length ? { OR: tokens.flatMap((term) => [{ title: { contains: term, mode: "insensitive" as const } }, { summary: { contains: term, mode: "insensitive" as const } }]) } : {}, include: { source: true }, orderBy: { occurredAt: "desc" }, take: 10 }),
      db.dataSource.findMany({ where: { enabled: true }, select: { id: true, key: true, provider: true, dataset: true, freshnessStatus: true, lastSuccessAt: true, license: true } })
    ]);
    const evidence = {
      minerals: minerals.map((x) => ({ id: x.id, name: x.name, group: x.group })),
      projects: projects.map((x) => ({ id: x.id, name: x.name, mineral: x.mineral?.name, country: x.country?.name, stage: x.stage, risk: x.risks[0]?.score?.toString() ?? null, riskSeverity: x.risks[0]?.severity ?? "UNKNOWN" })),
      mines: mines.map((x) => ({ id: x.id, name: x.name, mineral: x.mineral?.name, country: x.country?.name, stage: x.stage, risk: x.risks[0]?.score?.toString() ?? null, riskSeverity: x.risks[0]?.severity ?? "UNKNOWN" })),
      events: events.map((x) => ({ id: x.id, title: x.title, occurredAt: x.occurredAt, status: x.status, source: x.source?.key ?? null })),
      sources
    };
    const matches = evidence.projects.length + evidence.mines.length + evidence.events.length + evidence.minerals.length;
    const answer = matches
      ? `Found ${matches} source-grounded records relevant to the query. Review the structured evidence and source freshness below; no unsupported narrative inference has been added.`
      : "No sufficiently matching source-grounded records are loaded. The assistant will not invent an answer; broaden the query or ingest additional authorized sources.";
    await writeAudit(principal, "analyst.query", "AnalystAssistant", undefined, { questionLength: input.question.length, evidenceCount: matches });
    return success({ answer, uncertainty: matches ? "Evidence coverage depends on connected source freshness and completeness." : "Insufficient evidence.", citationsRequired: true, evidence, modelInvocation: "not-required-deterministic-grounding", externalModelConfigured: Boolean(process.env.AI_PROVIDER && process.env.AI_API_KEY) });
  } catch (error) { return failure(error); }
}

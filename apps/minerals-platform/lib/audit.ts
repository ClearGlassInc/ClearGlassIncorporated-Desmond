import { createHmac } from "node:crypto";
import { db } from "@/lib/db";
import type { Principal } from "@/lib/auth";

export async function writeAudit(principal: Principal | null, action: string, entityType?: string, entityId?: string, metadata?: Record<string, unknown>) {
  const secret = process.env.AUDIT_HASH_SECRET ?? "development-only-audit-secret";
  const previous = await db.auditLog.findFirst({ orderBy: { createdAt: "desc" }, select: { entryHash: true } });
  const payload = JSON.stringify({ organizationId: principal?.organizationId ?? null, userId: principal?.userId ?? null, action, entityType, entityId, metadata: metadata ?? null, previousHash: previous?.entryHash ?? null });
  const entryHash = createHmac("sha256", secret).update(payload).digest("hex");
  return db.auditLog.create({ data: { organizationId: principal?.organizationId, userId: principal?.userId, action, entityType, entityId, metadata: metadata ?? undefined, previousHash: previous?.entryHash, entryHash } });
}

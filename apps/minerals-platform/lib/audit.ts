import { createHmac } from "node:crypto";
import type { Prisma } from "@prisma/client";
import { db } from "@/lib/db";
import type { Principal } from "@/lib/auth";

export async function writeAudit(principal: Principal | null, action: string, entityType?: string, entityId?: string, metadata?: Record<string, unknown>) {
  const configuredSecret = process.env.AUDIT_HASH_SECRET;
  if (process.env.NODE_ENV === "production" && !configuredSecret) throw new Error("AUDIT_HASH_SECRET is required in production");
  const secret = configuredSecret ?? "development-only-audit-secret";
  const previous = await db.auditLog.findFirst({ orderBy: { createdAt: "desc" }, select: { entryHash: true } });
  const payload = JSON.stringify({ organizationId: principal?.organizationId ?? null, userId: principal?.userId ?? null, action, entityType, entityId, metadata: metadata ?? null, previousHash: previous?.entryHash ?? null });
  const entryHash = createHmac("sha256", secret).update(payload).digest("hex");
  const jsonMetadata = metadata ? JSON.parse(JSON.stringify(metadata)) as Prisma.InputJsonObject : undefined;
  return db.auditLog.create({ data: { organizationId: principal?.organizationId, userId: principal?.userId, action, entityType, entityId, metadata: jsonMetadata, previousHash: previous?.entryHash, entryHash } });
}

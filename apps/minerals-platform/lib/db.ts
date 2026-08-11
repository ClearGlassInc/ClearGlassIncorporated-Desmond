import { PrismaClient } from "@prisma/client";

const globalForPrisma = globalThis as unknown as { mineralsPrisma?: PrismaClient };

export const db = globalForPrisma.mineralsPrisma ?? new PrismaClient({
  log: process.env.NODE_ENV === "development" ? ["warn", "error"] : ["error"]
});

if (process.env.NODE_ENV !== "production") globalForPrisma.mineralsPrisma = db;

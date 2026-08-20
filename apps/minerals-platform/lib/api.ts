import { NextResponse } from "next/server";
import { z } from "zod";
import { AuthError } from "@/lib/auth";

export const pageSchema = z.object({
  page: z.coerce.number().int().min(1).default(1),
  pageSize: z.coerce.number().int().min(1).max(250).default(50),
  sort: z.string().max(80).optional(),
  order: z.enum(["asc", "desc"]).default("asc")
});

export class ApiError extends Error {
  constructor(public readonly status: number, public readonly code: string, message: string, public readonly headers?: HeadersInit) { super(message); }
}

export function queryObject(url: URL): Record<string, string> {
  return Object.fromEntries(url.searchParams.entries());
}

export function success<T>(data: T, init?: ResponseInit) {
  return NextResponse.json({ ok: true, data }, { ...init, headers: { "Cache-Control": "private, max-age=0", ...(init?.headers ?? {}) } });
}

export function paginated<T>(items: T[], page: number, pageSize: number, total: number) {
  return success({ items, page, pageSize, total, totalPages: Math.ceil(total / pageSize) });
}

export function failure(error: unknown) {
  if (error instanceof AuthError) return NextResponse.json({ ok: false, error: { code: error.status === 401 ? "UNAUTHENTICATED" : "FORBIDDEN", message: error.message } }, { status: error.status });
  if (error instanceof ApiError) return NextResponse.json({ ok: false, error: { code: error.code, message: error.message } }, { status: error.status, headers: error.headers });
  if (error instanceof z.ZodError) return NextResponse.json({ ok: false, error: { code: "INVALID_INPUT", message: "Request validation failed", issues: error.issues } }, { status: 400 });
  console.error(error);
  return NextResponse.json({ ok: false, error: { code: "INTERNAL_ERROR", message: "Request could not be completed" } }, { status: 500 });
}

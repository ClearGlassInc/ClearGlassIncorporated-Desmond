/**
 * VEILGUARD — server-side barrel.
 *
 * Importing this pulls in `node:crypto` (via watermark/ledger/honeypot), so it
 * belongs in route handlers, server components and Node tooling only.
 *
 * Client components must import the pure modules directly — `./policy` and
 * `./tracer` are free of Node built-ins and safe to bundle:
 *
 *     import { variantsFromBits } from "@/lib/veilguard/tracer";
 *
 * Layer map:
 *   policy    — what a viewer may do (classification × plan × risk)
 *   risk      — how much to trust this session right now
 *   watermark — the signed, expiring grant and the mark painted over the render
 *   tracer    — the per-render variant code, and leak tracing from a fragment
 *   ledger    — the tamper-evident record of everything that happened
 *   honeypot  — canaries that catch enumeration, beacons that trace a copy
 */

export * from "./policy";
export * from "./risk";
export * from "./tracer";
export * from "./watermark";
export * from "./ledger";
export * from "./honeypot";

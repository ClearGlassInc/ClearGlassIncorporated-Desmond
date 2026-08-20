// Copyright (c) 2024-2026 ClearGlass Inc. All Rights Reserved.
// Proprietary and confidential. See LICENSE for terms.
import { createHmac, timingSafeEqual } from "node:crypto";

const ZERO = "\u200B";
const ONE = "\u200C";
const START = "\u2063\u2063\u200B\u200C";
const END = "\u2063\u2063\u200C\u200B";
const VERSION = 1;
const MAX_PAYLOAD_BYTES = 2048;

export type WatermarkPayload = Record<string, string>;

export interface WatermarkEnvelope {
  v: 1;
  p: WatermarkPayload;
  s: string;
}

export interface ExtractedWatermark {
  payload: WatermarkPayload;
  signature: string;
  verified: boolean | null;
  rawEnvelope: WatermarkEnvelope;
}

export interface EmbedOptions {
  copies?: number;
}

function canonicalPayload(payload: WatermarkPayload): string {
  const sorted: WatermarkPayload = {};
  for (const key of Object.keys(payload).sort()) {
    const value = payload[key];
    if (typeof value !== "string") throw new TypeError(`watermark payload value for ${key} must be a string`);
    sorted[key] = value;
  }
  return JSON.stringify(sorted);
}

function sign(payload: WatermarkPayload, secret: string): string {
  if (!secret) throw new Error("watermark secret must not be empty");
  return createHmac("sha256", secret)
    .update(`cg-provenance-v${VERSION}\n${canonicalPayload(payload)}`, "utf8")
    .digest("base64url");
}

function constantTimeEqual(a: string, b: string): boolean {
  const left = Buffer.from(a, "utf8");
  const right = Buffer.from(b, "utf8");
  if (left.length !== right.length) return false;
  return timingSafeEqual(left, right);
}

function bytesToZeroWidth(bytes: Uint8Array): string {
  let out = "";
  for (const byte of bytes) {
    for (let bit = 7; bit >= 0; bit -= 1) out += (byte & (1 << bit)) === 0 ? ZERO : ONE;
  }
  return out;
}

function zeroWidthToBytes(encoded: string): Uint8Array | null {
  if (encoded.length === 0 || encoded.length % 8 !== 0) return null;
  const bytes = new Uint8Array(encoded.length / 8);
  for (let offset = 0; offset < encoded.length; offset += 8) {
    let value = 0;
    for (let bit = 0; bit < 8; bit += 1) {
      const char = encoded[offset + bit];
      if (char !== ZERO && char !== ONE) return null;
      value = (value << 1) | (char === ONE ? 1 : 0);
    }
    bytes[offset / 8] = value;
  }
  return bytes;
}

export function createMarker(payload: WatermarkPayload, secret: string): string {
  const envelope: WatermarkEnvelope = { v: VERSION, p: payload, s: sign(payload, secret) };
  const bytes = Buffer.from(JSON.stringify(envelope), "utf8");
  if (bytes.length > MAX_PAYLOAD_BYTES) throw new Error(`watermark envelope exceeds ${MAX_PAYLOAD_BYTES} bytes`);
  return START + bytesToZeroWidth(bytes) + END;
}

function insertionPoints(text: string, copies: number): number[] {
  const points: number[] = [];
  if (!text || copies <= 0) return points;
  for (let n = 1; n <= copies; n += 1) {
    const target = Math.floor((text.length * n) / (copies + 1));
    let index = target;
    while (index < text.length && !/\s/.test(text[index] ?? "")) index += 1;
    if (index >= text.length) index = target;
    if (!points.includes(index)) points.push(index);
  }
  return points.sort((a, b) => a - b);
}

export function embedWatermark(
  visibleText: string,
  payload: WatermarkPayload,
  secret: string,
  options: EmbedOptions = {},
): string {
  const copies = Math.max(1, Math.min(8, Math.trunc(options.copies ?? 3)));
  if (!visibleText) return visibleText;
  const marker = createMarker(payload, secret);
  const points = insertionPoints(visibleText, copies);
  let out = "";
  let cursor = 0;
  for (const point of points) {
    out += visibleText.slice(cursor, point) + marker;
    cursor = point;
  }
  return out + visibleText.slice(cursor);
}

function parseEnvelope(encoded: string): WatermarkEnvelope | null {
  const bytes = zeroWidthToBytes(encoded);
  if (!bytes) return null;
  try {
    const value: unknown = JSON.parse(Buffer.from(bytes).toString("utf8"));
    if (!value || typeof value !== "object") return null;
    const candidate = value as Partial<WatermarkEnvelope>;
    if (candidate.v !== VERSION || !candidate.p || typeof candidate.p !== "object" || typeof candidate.s !== "string") return null;
    const payload: WatermarkPayload = {};
    for (const [key, item] of Object.entries(candidate.p)) {
      if (typeof item !== "string") return null;
      payload[key] = item;
    }
    return { v: VERSION, p: payload, s: candidate.s };
  } catch {
    return null;
  }
}

export function extractWatermarks(text: string, secret?: string): ExtractedWatermark[] {
  const results: ExtractedWatermark[] = [];
  const seen = new Set<string>();
  let cursor = 0;
  while (cursor < text.length) {
    const start = text.indexOf(START, cursor);
    if (start === -1) break;
    const dataStart = start + START.length;
    const end = text.indexOf(END, dataStart);
    if (end === -1) break;
    const envelope = parseEnvelope(text.slice(dataStart, end));
    cursor = end + END.length;
    if (!envelope) continue;
    const identity = `${canonicalPayload(envelope.p)}\n${envelope.s}`;
    if (seen.has(identity)) continue;
    seen.add(identity);
    const verified = secret === undefined ? null : constantTimeEqual(envelope.s, sign(envelope.p, secret));
    results.push({ payload: envelope.p, signature: envelope.s, verified, rawEnvelope: envelope });
  }
  return results;
}

export function stripWatermarks(text: string): string {
  let out = text;
  let cursor = 0;
  while (cursor < out.length) {
    const start = out.indexOf(START, cursor);
    if (start === -1) break;
    const end = out.indexOf(END, start + START.length);
    if (end === -1) break;
    out = out.slice(0, start) + out.slice(end + END.length);
    cursor = start;
  }
  return out;
}

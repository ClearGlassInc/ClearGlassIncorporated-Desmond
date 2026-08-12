/**
 * VEILGUARD — the wire contract between the shield routes and the viewer.
 *
 * Kept in its own pure module so the client bundle can import the types
 * without reaching `watermark.ts` and dragging `node:crypto` in behind them.
 *
 * A note on what is deliberately *not* here: the client is never sent another
 * viewer's tracer, the ledger salt, the signing key, or the candidate list a
 * trace runs against. It receives its own grant and nothing else, so a viewer
 * who reads their own bundle learns only what they were already shown.
 */

import type { Capability, SerializedPolicy } from "./policy";

export type WatermarkDTO = {
  subjectLabel: string;
  tracerCode: string;
  contextLabel: string;
  issuedAtIso: string;
  rotateSeconds: number;
};

export type RiskDTO = {
  score: number;
  band: string;
  /** Plain-language reasons, safe to show the viewer whose access they shaped. */
  reasons: string[];
};

export type ShieldGrantDTO = {
  grantId: string;
  token: string;
  assetId: string;
  title: string;
  source: string;
  alt: string;
  expiresAt: string;
  policy: SerializedPolicy;
  watermark: WatermarkDTO;
  /** Drives the per-render variant; see `variantsFromBits`. */
  tracerBits: number[];
  risk: RiskDTO;
};

export type ShieldDenialDTO = {
  denied: true;
  assetId: string;
  reason: string;
  risk: RiskDTO;
};

export type ShieldGrantResponse = ShieldGrantDTO | ShieldDenialDTO;

export function isDenial(response: ShieldGrantResponse): response is ShieldDenialDTO {
  return "denied" in response && response.denied;
}

/** Client → server protection events. Deliberately small and content-free. */
export type TelemetryKind =
  | "render_started"
  | "render_expired"
  | "capture_suspected"
  | "export_attempted"
  | "copy_attempted"
  | "automation_suspected";

export type TelemetryEventDTO = {
  grantToken: string;
  kind: TelemetryKind;
  /** How it happened — e.g. "print_screen", "context_menu". Never content. */
  method?: string;
  allowed?: boolean;
  occurredAt: string;
};

export function grantAllowsCapability(policy: SerializedPolicy, capability: Capability): boolean {
  return policy.capabilities.includes(capability);
}

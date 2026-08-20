/**
 * VEILGUARD — content access segmentation and scoped permissions.
 *
 * Every protected item carries a classification. Every viewer arrives with a
 * plan and a live risk band. The effective policy is the *intersection* of the
 * three, never the union: a viewer can only lose capability as classification
 * or risk rises, never gain it. That direction is what makes the table below
 * safe to extend — a new tier can add restrictions but cannot smuggle in a
 * capability the plan never granted.
 *
 * Pure functions, no I/O, no Node built-ins — this module is imported by the
 * edge middleware, the server routes, and the client bundle alike.
 */

export type Classification = "public" | "internal" | "confidential" | "restricted";

/** Plans map to the storefront's existing premium session plans, plus anonymous. */
export type ViewerPlan = "anonymous" | "premium" | "operator";

/** Risk bands come from `risk.ts`; policy only needs the coarse band. */
export type RiskBand = "nominal" | "elevated" | "high" | "critical";

/**
 * Capabilities are deliberately fine-grained so the audit ledger can record
 * exactly which one was exercised, rather than a vague "access" event.
 */
export type Capability =
  | "view" // render in a shielded viewer at policy resolution
  | "view_full_resolution" // render without the resolution cap
  | "download" // fetch the original bytes through a signed, expiring URL
  | "export" // print / save-as / render into another document
  | "share" // mint a grant for another subject
  | "copy_text"; // select and copy textual content

export type EffectivePolicy = {
  classification: Classification;
  capabilities: ReadonlySet<Capability>;
  /** Longest a single grant may live, in seconds. */
  grantTtlSeconds: number;
  /** Longest a rendered frame may stay on screen without re-attestation. */
  renderTtlSeconds: number;
  /** Longest edge of the delivered raster, in pixels. `null` = uncapped. */
  maxRenderedEdgePx: number | null;
  /** Visible watermark required on every rendered frame. */
  requireVisibleWatermark: boolean;
  /** Re-render the watermark on an interval so a cropped capture still carries it. */
  watermarkRotateSeconds: number;
  /** Obscure the frame when the tab loses focus or visibility. */
  obscureOnBlur: boolean;
  /** Human-readable reasons this policy ended up where it did (for the UI + ledger). */
  rationale: string[];
};

type Baseline = Omit<EffectivePolicy, "classification" | "capabilities" | "rationale"> & {
  capabilities: readonly Capability[];
};

/**
 * Per-classification baselines. These describe the *most* any viewer may do
 * with content at that tier; plan and risk only subtract from here.
 */
const BASELINES: Record<Classification, Baseline> = {
  public: {
    capabilities: ["view", "view_full_resolution", "download", "export", "share", "copy_text"],
    grantTtlSeconds: 60 * 60,
    renderTtlSeconds: 60 * 60,
    maxRenderedEdgePx: null,
    requireVisibleWatermark: false,
    watermarkRotateSeconds: 0,
    obscureOnBlur: false,
  },
  internal: {
    capabilities: ["view", "view_full_resolution", "download", "export", "copy_text"],
    grantTtlSeconds: 30 * 60,
    renderTtlSeconds: 30 * 60,
    maxRenderedEdgePx: null,
    requireVisibleWatermark: true,
    watermarkRotateSeconds: 0,
    obscureOnBlur: false,
  },
  confidential: {
    capabilities: ["view", "download", "copy_text"],
    grantTtlSeconds: 10 * 60,
    renderTtlSeconds: 5 * 60,
    maxRenderedEdgePx: 1600,
    requireVisibleWatermark: true,
    watermarkRotateSeconds: 45,
    obscureOnBlur: true,
  },
  restricted: {
    // No download and no export at any plan level: restricted content is only
    // ever a shielded, expiring, watermarked render.
    capabilities: ["view"],
    grantTtlSeconds: 3 * 60,
    renderTtlSeconds: 90,
    maxRenderedEdgePx: 1100,
    requireVisibleWatermark: true,
    watermarkRotateSeconds: 20,
    obscureOnBlur: true,
  },
};

/** What each plan is ever allowed to do, before classification narrows it. */
const PLAN_CEILING: Record<ViewerPlan, readonly Capability[]> = {
  anonymous: ["view"],
  premium: ["view", "view_full_resolution", "download", "export", "copy_text"],
  operator: ["view", "view_full_resolution", "download", "export", "share", "copy_text"],
};

/** Capabilities withdrawn as risk rises. Bands are cumulative via `RISK_ORDER`. */
const RISK_WITHDRAWS: Record<RiskBand, readonly Capability[]> = {
  nominal: [],
  elevated: ["share"],
  high: ["share", "download", "export", "copy_text"],
  critical: ["share", "download", "export", "copy_text", "view_full_resolution", "view"],
};

const RISK_ORDER: readonly RiskBand[] = ["nominal", "elevated", "high", "critical"];

/** Multiplier applied to every TTL as risk rises — shorter leash under suspicion. */
const RISK_TTL_FACTOR: Record<RiskBand, number> = {
  nominal: 1,
  elevated: 0.6,
  high: 0.3,
  critical: 0,
};

export type PolicyInput = {
  classification: Classification;
  plan: ViewerPlan;
  riskBand: RiskBand;
  /**
   * Per-asset overrides an owner may set (e.g. an unreleased concept draft that
   * must never be downloaded even though its tier would allow it). Overrides
   * can only remove capability — see `resolvePolicy`.
   */
  denyCapabilities?: readonly Capability[];
};

/**
 * Resolve the effective policy for one viewer looking at one item.
 *
 * Subtraction-only by construction: we start from the classification baseline
 * and intersect with the plan ceiling, then remove what risk and per-asset
 * overrides withdraw.
 */
export function resolvePolicy(input: PolicyInput): EffectivePolicy {
  const { classification, plan, riskBand } = input;
  const baseline = BASELINES[classification];
  const rationale: string[] = [`classification:${classification}`, `plan:${plan}`, `risk:${riskBand}`];

  const ceiling = new Set(PLAN_CEILING[plan]);
  const withdrawn = new Set(RISK_WITHDRAWS[riskBand]);
  const denied = new Set(input.denyCapabilities ?? []);

  const capabilities = new Set<Capability>();
  for (const capability of baseline.capabilities) {
    if (!ceiling.has(capability)) continue;
    if (withdrawn.has(capability)) continue;
    if (denied.has(capability)) continue;
    capabilities.add(capability);
  }

  // `view_full_resolution` without `view` is meaningless and would let a caller
  // read the uncapped edge size off a policy that grants no render at all.
  if (!capabilities.has("view")) capabilities.delete("view_full_resolution");

  if (denied.size > 0) rationale.push(`asset_denies:${[...denied].sort().join("+")}`);
  if (withdrawn.size > 0) rationale.push(`risk_withdraws:${[...withdrawn].sort().join("+")}`);

  const ttlFactor = RISK_TTL_FACTOR[riskBand];
  const grantTtlSeconds = Math.floor(baseline.grantTtlSeconds * ttlFactor);
  const renderTtlSeconds = Math.floor(baseline.renderTtlSeconds * ttlFactor);

  return {
    classification,
    capabilities,
    grantTtlSeconds,
    renderTtlSeconds,
    maxRenderedEdgePx: capabilities.has("view_full_resolution") ? baseline.maxRenderedEdgePx : narrowEdge(baseline.maxRenderedEdgePx),
    requireVisibleWatermark: baseline.requireVisibleWatermark,
    watermarkRotateSeconds: baseline.watermarkRotateSeconds,
    obscureOnBlur: baseline.obscureOnBlur,
    rationale,
  };
}

/**
 * Secure-preview resolution cap for viewers without `view_full_resolution`.
 * An uncapped tier still gets a concrete ceiling here so that losing the
 * capability always narrows the render rather than silently leaving it open.
 */
function narrowEdge(baselineEdge: number | null): number {
  const PREVIEW_EDGE_PX = 900;
  return baselineEdge === null ? PREVIEW_EDGE_PX : Math.min(baselineEdge, PREVIEW_EDGE_PX);
}

export function can(policy: EffectivePolicy, capability: Capability): boolean {
  return policy.capabilities.has(capability);
}

/** Ordering helper so callers can compare bands without hardcoding the list. */
export function riskBandAtLeast(band: RiskBand, floor: RiskBand): boolean {
  return RISK_ORDER.indexOf(band) >= RISK_ORDER.indexOf(floor);
}

/** Wire form of an effective policy — what the client is told it may do. */
export type SerializedPolicy = {
  classification: Classification;
  capabilities: Capability[];
  grantTtlSeconds: number;
  renderTtlSeconds: number;
  maxRenderedEdgePx: number | null;
  requireVisibleWatermark: boolean;
  watermarkRotateSeconds: number;
  obscureOnBlur: boolean;
  rationale: string[];
};

/** Serializable view of a policy, for API responses and ledger entries. */
export function serializePolicy(policy: EffectivePolicy): SerializedPolicy {
  return {
    classification: policy.classification,
    capabilities: [...policy.capabilities].sort(),
    grantTtlSeconds: policy.grantTtlSeconds,
    renderTtlSeconds: policy.renderTtlSeconds,
    maxRenderedEdgePx: policy.maxRenderedEdgePx,
    requireVisibleWatermark: policy.requireVisibleWatermark,
    watermarkRotateSeconds: policy.watermarkRotateSeconds,
    obscureOnBlur: policy.obscureOnBlur,
    rationale: policy.rationale,
  };
}

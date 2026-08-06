// Copyright (c) 2024-2026 ClearGlass Inc. All Rights Reserved.
// Proprietary and confidential. See LICENSE for terms.

/** Recurrence of a price, in the shape Stripe's `recurring` object expects. */
export interface Recurrence {
  interval: "day" | "week" | "month" | "year";
  interval_count: number;
}

/**
 * One purchasable price point of a product.
 *
 * A product with a single price has exactly one variant keyed `default`; a
 * product sold monthly and yearly has two. The variant key is part of the
 * Stripe Price metadata, so re-running the sync can tell "the monthly price
 * changed" apart from "a second price appeared".
 */
export interface SourceVariant {
  variantKey: string;
  label?: string;
  /** Integer minor units (cents for CAD/USD). Never a float, never a string. */
  amountMinor: number;
  /** Lowercase ISO-4217, as Stripe stores it. */
  currency: string;
  recurring?: Recurrence;
  taxBehavior?: "inclusive" | "exclusive" | "unspecified";
  /** Price id the source claims to already own. Verified before it is trusted. */
  stripePriceIdHint?: string;
}

/** A product as read from a source on the site, normalised and validated. */
export interface SourceProduct {
  /** `<adapter>:<sku>` — the stable external identifier written to Stripe metadata. */
  sourceId: string;
  adapter: string;
  sku: string;
  name: string;
  description?: string;
  category?: string;
  /** Public https URL of the page the product is listed on. */
  sourceUrl: string;
  /** Validated, absolute https image URLs. Possibly empty. */
  images: string[];
  inventoryStatus?: string;
  variants: SourceVariant[];
  stripeProductIdHint?: string;
  /** sha256 over the normalised content — drives update detection. */
  sourceHash: string;
  /** Non-fatal notes surfaced in the report. */
  notes: string[];
}

export type IssueSeverity = "error" | "warning";

/**
 * A problem with one product in the source data.
 *
 * `error` means the product is withheld from Stripe entirely and the run exits
 * non-zero: an ambiguous price is not something to guess at. `warning` means it
 * still syncs but a human should look.
 */
export interface ProductIssue {
  sourceId: string;
  adapter: string;
  field: string;
  message: string;
  severity: IssueSeverity;
}

export interface ParseResult {
  products: SourceProduct[];
  issues: ProductIssue[];
}

/* ── The slice of Stripe this tool touches ─────────────────────────────── */

export interface StripeProductLike {
  id: string;
  name: string;
  active: boolean;
  description?: string | null;
  images?: string[];
  metadata?: Record<string, string>;
  default_price?: string | { id: string } | null;
}

export interface StripePriceLike {
  id: string;
  product: string | { id: string };
  active: boolean;
  currency: string;
  unit_amount: number | null;
  recurring?: Recurrence | null;
  tax_behavior?: string | null;
  metadata?: Record<string, string>;
}

export interface ProductCreateParams {
  name: string;
  description?: string;
  images?: string[];
  metadata: Record<string, string>;
  active?: boolean;
}

export interface ProductUpdateParams {
  name?: string;
  description?: string;
  images?: string[];
  metadata?: Record<string, string>;
  default_price?: string;
}

export interface PriceCreateParams {
  product: string;
  currency: string;
  unit_amount: number;
  recurring?: Recurrence;
  tax_behavior?: "inclusive" | "exclusive" | "unspecified";
  metadata: Record<string, string>;
  nickname?: string;
}

export interface RequestOptions {
  idempotencyKey?: string;
}

/**
 * Everything the planner and executor need from Stripe.
 *
 * Narrowing the SDK to this interface is what lets the tests run a full sync —
 * duplicate detection, idempotency, price rotation — against an in-memory fake
 * with no credentials and no network.
 */
export interface StripeGateway {
  /** Yields every product in the account, following pagination to the end. */
  listAllProducts(): AsyncIterable<StripeProductLike>;
  /** Resolves to null when the id does not exist in this account/mode. */
  retrieveProduct(id: string): Promise<StripeProductLike | null>;
  /** Every price of a product, active and inactive, following pagination. */
  listPrices(productId: string): Promise<StripePriceLike[]>;
  createProduct(params: ProductCreateParams, options?: RequestOptions): Promise<StripeProductLike>;
  updateProduct(id: string, params: ProductUpdateParams): Promise<StripeProductLike>;
  createPrice(params: PriceCreateParams, options?: RequestOptions): Promise<StripePriceLike>;
  deactivatePrice(id: string): Promise<StripePriceLike>;
}

/* ── Plan ──────────────────────────────────────────────────────────────── */

export type PlanAction =
  | "create-product"
  | "update-product"
  | "product-unchanged"
  | "create-price"
  | "reuse-price"
  | "deactivate-price"
  | "orphan-warning"
  | "skip-error";

export interface PlanRow {
  action: PlanAction;
  sourceId: string;
  name: string;
  /** Formatted amount, e.g. `6.99` — blank for product-level rows. */
  amount: string;
  currency: string;
  stripeProductId: string;
  stripePriceId: string;
  detail: string;
}

export interface PriceStep {
  variant: SourceVariant;
  /** `create` mints a new Price; `reuse` keeps the existing one untouched. */
  kind: "create" | "reuse";
  existingPriceId?: string;
  idempotencyKey: string;
}

export interface ProductStep {
  product: SourceProduct;
  kind: "create" | "update" | "unchanged";
  existingProductId?: string;
  idempotencyKey: string;
  /** Fields that differ from what Stripe currently holds. */
  changedFields: string[];
  prices: PriceStep[];
  /** Superseded active prices this run will deactivate. Empty without the flag. */
  stalePriceIds: string[];
  /** Superseded active prices left alone because the flag was not passed. */
  retainedStalePriceIds: string[];
}

export interface SyncPlan {
  steps: ProductStep[];
  /** Managed Stripe products whose source_id vanished from the site. */
  orphans: { productId: string; sourceId: string; name: string }[];
  /** Two Stripe products claiming the same source_id — needs a human. */
  duplicates: { sourceId: string; productIds: string[] }[];
}

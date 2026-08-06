// Copyright (c) 2024-2026 ClearGlass Inc. All Rights Reserved.
// Proprietary and confidential. See LICENSE for terms.
/**
 * Plan and apply the difference between the site catalogue and Stripe.
 *
 * The plan is computed in full before anything is written, which is what makes
 * `--apply` and the default dry run the *same* code path — the dry run is not a
 * simulation of the real thing, it is the real thing with the writes withheld.
 *
 * Two rules shape everything here:
 *
 *   1. Nothing is ever deleted or deactivated implicitly. A product that
 *      disappears from the site is reported, not archived; a Stripe Price is
 *      only deactivated when `--deactivate-old-prices` is passed.
 *   2. A Stripe Price is immutable in amount and currency. Changing a price
 *      therefore means minting a new Price and leaving the old one in place for
 *      existing subscriptions — never mutating the old one.
 */
import { formatMinor } from "./money.js";
import type {
  PlanRow,
  PriceStep,
  ProductStep,
  Recurrence,
  SourceProduct,
  SourceVariant,
  StripeGateway,
  StripePriceLike,
  StripeProductLike,
  SyncPlan,
} from "./types.js";

/** Marks the Stripe records this tool owns. Anything without it is left alone. */
export const MANAGED_BY = "clearglass-site-sync";

export const META = {
  managedBy: "managed_by",
  sourceId: "source_id",
  sourceUrl: "source_url",
  sourceRepository: "source_repository",
  sourceHash: "source_hash",
  sourceAdapter: "source_adapter",
  sourceSku: "source_sku",
  sourceCategory: "source_category",
  inventoryStatus: "inventory_status",
  variantKey: "variant_key",
} as const;

export interface PlanOptions {
  repository: string;
  deactivateOldPrices: boolean;
}

function recurrenceKey(recurring: Recurrence | null | undefined): string {
  return recurring ? `${recurring.interval}/${recurring.interval_count}` : "one_time";
}

function productMetadata(product: SourceProduct, repository: string): Record<string, string> {
  const metadata: Record<string, string> = {
    [META.managedBy]: MANAGED_BY,
    [META.sourceId]: product.sourceId,
    [META.sourceUrl]: product.sourceUrl,
    [META.sourceRepository]: repository,
    [META.sourceHash]: product.sourceHash,
    [META.sourceAdapter]: product.adapter,
    [META.sourceSku]: product.sku,
  };
  if (product.category) metadata[META.sourceCategory] = product.category;
  if (product.inventoryStatus) metadata[META.inventoryStatus] = product.inventoryStatus;
  return metadata;
}

function priceMetadata(
  product: SourceProduct,
  variant: SourceVariant,
  repository: string,
): Record<string, string> {
  return {
    [META.managedBy]: MANAGED_BY,
    [META.sourceId]: product.sourceId,
    [META.sourceRepository]: repository,
    [META.variantKey]: variant.variantKey,
    [META.sourceSku]: product.sku,
  };
}

/**
 * Deterministic idempotency key for a create.
 *
 * Derived only from content, never from the clock, so a run that times out
 * mid-create and is retried an hour later reuses the same key and Stripe
 * returns the original object instead of minting a duplicate.
 */
export function productIdempotencyKey(product: SourceProduct): string {
  return `${MANAGED_BY}:product:${product.sourceId}:${product.sourceHash}`;
}

export function priceIdempotencyKey(product: SourceProduct, variant: SourceVariant): string {
  return [
    MANAGED_BY,
    "price",
    product.sourceId,
    variant.variantKey,
    variant.currency,
    String(variant.amountMinor),
    recurrenceKey(variant.recurring),
  ].join(":");
}

function normalizedProductId(price: StripePriceLike): string {
  return typeof price.product === "string" ? price.product : price.product.id;
}

/** True when the existing Stripe Price is chargeable-identical to the variant. */
export function priceMatchesVariant(price: StripePriceLike, variant: SourceVariant): boolean {
  if (!price.active) return false;
  if (price.currency.toLowerCase() !== variant.currency) return false;
  if (price.unit_amount !== variant.amountMinor) return false;
  return recurrenceKey(price.recurring) === recurrenceKey(variant.recurring);
}

function fieldsThatDiffer(existing: StripeProductLike, product: SourceProduct, repository: string): string[] {
  const changed: string[] = [];
  if ((existing.name ?? "") !== product.name) changed.push("name");
  if ((existing.description ?? "") !== (product.description ?? "")) changed.push("description");
  const currentImages = existing.images ?? [];
  if (
    currentImages.length !== product.images.length ||
    currentImages.some((image, index) => image !== product.images[index])
  ) {
    changed.push("images");
  }
  const metadata = existing.metadata ?? {};
  const desired = productMetadata(product, repository);
  for (const [key, value] of Object.entries(desired)) {
    if (metadata[key] !== value) {
      changed.push(`metadata.${key}`);
    }
  }
  return changed;
}

/**
 * Index every Stripe product this tool manages, by `source_id`.
 *
 * Built by paginating the full product list rather than by `products.search`:
 * Stripe's search index is eventually consistent (a product created seconds ago
 * may not be findable yet), and a stale miss here means a duplicate product.
 * The list endpoint is strongly consistent, so it is the one that keeps the
 * sync idempotent under rapid re-runs.
 */
export async function indexManagedProducts(gateway: StripeGateway): Promise<{
  bySourceId: Map<string, StripeProductLike>;
  duplicates: { sourceId: string; productIds: string[] }[];
}> {
  const bySourceId = new Map<string, StripeProductLike>();
  const collisions = new Map<string, string[]>();

  for await (const product of gateway.listAllProducts()) {
    const metadata = product.metadata ?? {};
    const sourceId = metadata[META.sourceId];
    if (!sourceId || metadata[META.managedBy] !== MANAGED_BY) continue;
    const existing = bySourceId.get(sourceId);
    if (existing) {
      const ids = collisions.get(sourceId) ?? [existing.id];
      ids.push(product.id);
      collisions.set(sourceId, ids);
      // Keep the first-seen record so the plan stays deterministic; the
      // duplicate is reported and left for a human to merge.
      continue;
    }
    bySourceId.set(sourceId, product);
  }

  const duplicates = [...collisions.entries()].map(([sourceId, productIds]) => ({
    sourceId,
    productIds,
  }));
  return { bySourceId, duplicates };
}

/**
 * Work out what would have to change in Stripe for it to match the site.
 *
 * Performs reads only — every write is deferred to `applyPlan`.
 */
export async function buildPlan(
  gateway: StripeGateway,
  products: SourceProduct[],
  options: PlanOptions,
): Promise<SyncPlan> {
  const { bySourceId, duplicates } = await indexManagedProducts(gateway);
  const steps: ProductStep[] = [];
  const matchedSourceIds = new Set<string>();

  for (const product of products) {
    let existing = bySourceId.get(product.sourceId);

    // A source may claim it already owns a Stripe product (the price book names
    // one). Trust it only if the id resolves in *this* account and mode — a
    // live-mode id is meaningless against a test key, and following it blindly
    // would either 404 mid-run or, worse, adopt an unrelated record.
    if (!existing && product.stripeProductIdHint) {
      const hinted = await gateway.retrieveProduct(product.stripeProductIdHint);
      if (hinted) {
        const owner = hinted.metadata?.[META.sourceId];
        if (!owner || owner === product.sourceId) existing = hinted;
      }
    }

    if (existing) matchedSourceIds.add(product.sourceId);

    const existingPrices = existing ? await gateway.listPrices(existing.id) : [];
    const prices: PriceStep[] = [];
    const claimed = new Set<string>();

    for (const variant of product.variants) {
      const match = existingPrices.find(
        (price) =>
          !claimed.has(price.id) &&
          priceMatchesVariant(price, variant) &&
          (price.metadata?.[META.variantKey] ?? variant.variantKey) === variant.variantKey,
      );
      if (match) {
        claimed.add(match.id);
        prices.push({
          variant,
          kind: "reuse",
          existingPriceId: match.id,
          idempotencyKey: priceIdempotencyKey(product, variant),
        });
      } else {
        prices.push({
          variant,
          kind: "create",
          idempotencyKey: priceIdempotencyKey(product, variant),
        });
      }
    }

    // Active prices for a variant key we still publish, but at an amount we no
    // longer charge. These are the rotation candidates.
    const publishedVariantKeys = new Set(product.variants.map((variant) => variant.variantKey));
    const stalePriceIds = existingPrices
      .filter(
        (price) =>
          price.active &&
          !claimed.has(price.id) &&
          normalizedProductId(price) === existing?.id &&
          price.metadata?.[META.managedBy] === MANAGED_BY &&
          publishedVariantKeys.has(price.metadata?.[META.variantKey] ?? ""),
      )
      .map((price) => price.id);

    const changedFields = existing ? fieldsThatDiffer(existing, product, options.repository) : [];
    const wantsPriceCreate = prices.some((price) => price.kind === "create");
    const kind: ProductStep["kind"] = !existing
      ? "create"
      : changedFields.length > 0 || wantsPriceCreate
        ? "update"
        : "unchanged";

    const step: ProductStep = {
      product,
      kind,
      idempotencyKey: productIdempotencyKey(product),
      changedFields,
      prices,
      // Without the flag the superseded prices are still reported — as prices
      // deliberately left active — rather than quietly dropped from the plan.
      stalePriceIds: options.deactivateOldPrices ? stalePriceIds : [],
      retainedStalePriceIds: options.deactivateOldPrices ? [] : stalePriceIds,
    };
    if (existing) step.existingProductId = existing.id;
    steps.push(step);
  }

  const orphans = [...bySourceId.entries()]
    .filter(([sourceId]) => !matchedSourceIds.has(sourceId))
    .filter(([sourceId]) => !products.some((product) => product.sourceId === sourceId))
    .map(([sourceId, product]) => ({ productId: product.id, sourceId, name: product.name }));

  return { steps, orphans, duplicates };
}

/** Flatten a plan into the report table rows. */
export function planRows(plan: SyncPlan, deactivateOldPrices: boolean): PlanRow[] {
  const rows: PlanRow[] = [];
  for (const step of plan.steps) {
    const { product } = step;
    rows.push({
      action:
        step.kind === "create"
          ? "create-product"
          : step.kind === "update"
            ? "update-product"
            : "product-unchanged",
      sourceId: product.sourceId,
      name: product.name,
      amount: "",
      currency: "",
      stripeProductId: step.existingProductId ?? "(new)",
      stripePriceId: "",
      detail:
        step.kind === "update" && step.changedFields.length > 0
          ? `changed: ${step.changedFields.join(", ")}`
          : step.kind === "create"
            ? "no Stripe product carries this source_id"
            : "in sync",
    });

    for (const price of step.prices) {
      rows.push({
        action: price.kind === "create" ? "create-price" : "reuse-price",
        sourceId: `${product.sourceId}#${price.variant.variantKey}`,
        name: price.variant.label ?? product.name,
        amount: formatMinor(price.variant.amountMinor, price.variant.currency),
        currency: price.variant.currency.toUpperCase(),
        stripeProductId: step.existingProductId ?? "(new)",
        stripePriceId: price.existingPriceId ?? "(new)",
        detail:
          price.kind === "reuse"
            ? "existing Price already charges this amount"
            : "Stripe Prices are immutable — a changed amount needs a new Price",
      });
    }

    for (const priceId of step.stalePriceIds) {
      rows.push({
        action: "deactivate-price",
        sourceId: product.sourceId,
        name: product.name,
        amount: "",
        currency: "",
        stripeProductId: step.existingProductId ?? "",
        stripePriceId: priceId,
        detail: "superseded by a new Price; --deactivate-old-prices was passed",
      });
    }
    if (!deactivateOldPrices) {
      for (const priceId of step.retainedStalePriceIds) {
        rows.push({
          action: "reuse-price",
          sourceId: product.sourceId,
          name: product.name,
          amount: "",
          currency: "",
          stripeProductId: step.existingProductId ?? "",
          stripePriceId: priceId,
          detail:
            "superseded but left active — pass --deactivate-old-prices to retire it once nothing references it",
        });
      }
    }
  }

  for (const orphan of plan.orphans) {
    rows.push({
      action: "orphan-warning",
      sourceId: orphan.sourceId,
      name: orphan.name,
      amount: "",
      currency: "",
      stripeProductId: orphan.productId,
      stripePriceId: "",
      detail: "no longer published on the site; left active — archive it in the Stripe Dashboard if intended",
    });
  }

  for (const duplicate of plan.duplicates) {
    rows.push({
      action: "orphan-warning",
      sourceId: duplicate.sourceId,
      name: "(duplicate source_id)",
      amount: "",
      currency: "",
      stripeProductId: duplicate.productIds.join(" "),
      stripePriceId: "",
      detail: "several Stripe products claim this source_id; merge them by hand before applying",
    });
  }

  return rows;
}

export interface ApplyResult {
  createdProducts: number;
  updatedProducts: number;
  createdPrices: number;
  reusedPrices: number;
  deactivatedPrices: number;
  failures: { sourceId: string; message: string }[];
  /** Resolved Stripe ids, so the report shows what was actually written. */
  resolved: Record<string, { productId: string; priceIds: Record<string, string> }>;
}

/**
 * Execute a plan against Stripe.
 *
 * A failure on one product is recorded and the run continues to the next: a
 * single bad image URL should not strand the rest of the catalogue half-synced.
 * The caller turns a non-empty `failures` list into a non-zero exit code.
 */
export async function applyPlan(
  gateway: StripeGateway,
  plan: SyncPlan,
  options: PlanOptions,
): Promise<ApplyResult> {
  const result: ApplyResult = {
    createdProducts: 0,
    updatedProducts: 0,
    createdPrices: 0,
    reusedPrices: 0,
    deactivatedPrices: 0,
    failures: [],
    resolved: {},
  };

  for (const step of plan.steps) {
    const { product } = step;
    try {
      let productId = step.existingProductId;

      if (step.kind === "create") {
        const created = await gateway.createProduct(
          {
            name: product.name,
            ...(product.description ? { description: product.description } : {}),
            ...(product.images.length > 0 ? { images: product.images } : {}),
            metadata: productMetadata(product, options.repository),
            active: true,
          },
          { idempotencyKey: step.idempotencyKey },
        );
        productId = created.id;
        result.createdProducts += 1;
      } else if (step.kind === "update" && step.changedFields.length > 0 && productId) {
        await gateway.updateProduct(productId, {
          name: product.name,
          description: product.description ?? "",
          images: product.images,
          metadata: productMetadata(product, options.repository),
        });
        result.updatedProducts += 1;
      }

      if (!productId) {
        throw new Error("product id could not be resolved");
      }

      const priceIds: Record<string, string> = {};
      for (const price of step.prices) {
        if (price.kind === "reuse" && price.existingPriceId) {
          priceIds[price.variant.variantKey] = price.existingPriceId;
          result.reusedPrices += 1;
          continue;
        }
        const created = await gateway.createPrice(
          {
            product: productId,
            currency: price.variant.currency,
            unit_amount: price.variant.amountMinor,
            ...(price.variant.recurring ? { recurring: price.variant.recurring } : {}),
            ...(price.variant.taxBehavior ? { tax_behavior: price.variant.taxBehavior } : {}),
            metadata: priceMetadata(product, price.variant, options.repository),
            ...(price.variant.label ? { nickname: price.variant.label } : {}),
          },
          { idempotencyKey: price.idempotencyKey },
        );
        priceIds[price.variant.variantKey] = created.id;
        result.createdPrices += 1;
      }

      for (const priceId of step.stalePriceIds) {
        await gateway.deactivatePrice(priceId);
        result.deactivatedPrices += 1;
      }

      result.resolved[product.sourceId] = { productId, priceIds };
    } catch (error) {
      result.failures.push({ sourceId: product.sourceId, message: (error as Error).message });
    }
  }

  return result;
}

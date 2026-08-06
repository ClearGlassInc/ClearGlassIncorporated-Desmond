// Copyright (c) 2024-2026 ClearGlass Inc. All Rights Reserved.
// Proprietary and confidential. See LICENSE for terms.
import assert from "node:assert/strict";
import { describe, it } from "node:test";

import {
  MANAGED_BY,
  META,
  applyPlan,
  buildPlan,
  indexManagedProducts,
  planHash,
  planRows,
  priceIdempotencyKey,
  productIdempotencyKey,
} from "../planner.js";
import { hashProduct } from "../sources.js";
import type { SourceProduct, SourceVariant } from "../types.js";
import { FakeStripe } from "./fake-stripe.js";

const OPTIONS = {
  repository: "ClearGlassInc/ClearGlassIncorporated-Desmond",
  deactivateOldPrices: false,
  adapters: ["side-store", "store", "pricebook"],
};

function product(overrides: Partial<SourceProduct> = {}): SourceProduct {
  const variants: SourceVariant[] = overrides.variants ?? [
    { variantKey: "default", amountMinor: 699, currency: "cad" },
  ];
  const base = {
    sourceId: "side-store:USB-C-C-1M",
    adapter: "side-store",
    sku: "USB-C-C-1M",
    name: "USB-C to USB-C Cable 1m",
    description: "60W fast-charge, braided.",
    category: "USB Cables",
    sourceUrl: "https://www.clearglassinc.com/side-store.html#USB-C-C-1M",
    images: [],
    notes: [],
    ...overrides,
    variants,
  };
  return { ...base, sourceHash: hashProduct(base) };
}

describe("first sync into an empty account", () => {
  it("creates a product and a price, and stores the source identity in metadata", async () => {
    const stripe = new FakeStripe();
    const item = product();
    const plan = await buildPlan(stripe, [item], OPTIONS);

    assert.equal(plan.steps[0]?.kind, "create");
    assert.equal(plan.steps[0]?.prices[0]?.kind, "create");

    const result = await applyPlan(stripe, plan, OPTIONS);
    assert.equal(result.createdProducts, 1);
    assert.equal(result.createdPrices, 1);
    assert.deepEqual(result.failures, []);

    const created = [...stripe.products.values()][0];
    assert.equal(created?.metadata?.[META.sourceId], "side-store:USB-C-C-1M");
    assert.equal(created?.metadata?.[META.sourceUrl], item.sourceUrl);
    assert.equal(created?.metadata?.[META.sourceRepository], OPTIONS.repository);
    assert.equal(created?.metadata?.[META.sourceHash], item.sourceHash);
    assert.equal(created?.metadata?.[META.managedBy], MANAGED_BY);

    const price = [...stripe.prices.values()][0];
    assert.equal(price?.unit_amount, 699);
    assert.equal(price?.currency, "cad");
    assert.equal(price?.metadata?.[META.variantKey], "default");
  });
});

describe("idempotency", () => {
  it("creates nothing on a second identical run", async () => {
    const stripe = new FakeStripe();
    const items = [product()];

    await applyPlan(stripe, await buildPlan(stripe, items, OPTIONS), OPTIONS);
    const second = await applyPlan(stripe, await buildPlan(stripe, items, OPTIONS), OPTIONS);

    assert.equal(second.createdProducts, 0);
    assert.equal(second.createdPrices, 0);
    assert.equal(second.reusedPrices, 1);
    assert.equal(stripe.products.size, 1);
    assert.equal(stripe.prices.size, 1);
  });

  it("stays at one record across five runs", async () => {
    const stripe = new FakeStripe();
    const items = [product(), product({ sourceId: "side-store:USB-C-A-1M", sku: "USB-C-A-1M", name: "USB-C to USB-A 1m" })];
    for (let round = 0; round < 5; round += 1) {
      await applyPlan(stripe, await buildPlan(stripe, items, OPTIONS), OPTIONS);
    }
    assert.equal(stripe.products.size, 2);
    assert.equal(stripe.prices.size, 2);
  });

  it("replays the same idempotency key rather than creating a duplicate", async () => {
    // Simulates a run that timed out after Stripe committed the create: the
    // retry sends the same key and must get the original object back.
    const stripe = new FakeStripe();
    const item = product();
    const key = productIdempotencyKey(item);

    const first = await stripe.createProduct(
      { name: item.name, metadata: {} },
      { idempotencyKey: key },
    );
    const retry = await stripe.createProduct(
      { name: item.name, metadata: {} },
      { idempotencyKey: key },
    );
    assert.equal(first.id, retry.id);
    assert.equal(stripe.products.size, 1);
  });

  it("derives keys from content only, so they survive a restart", () => {
    const item = product();
    assert.equal(productIdempotencyKey(item), productIdempotencyKey(product()));
    assert.match(productIdempotencyKey(item), /^clearglass-site-sync:product:side-store:USB-C-C-1M:[0-9a-f]{32}$/);
    assert.equal(
      priceIdempotencyKey(item, item.variants[0] as SourceVariant),
      "clearglass-site-sync:price:side-store:USB-C-C-1M:default:cad:699:one_time:unspecified",
    );
  });

  it("changes the price key when tax behaviour changes", () => {
    // tax_behavior goes into the create request, so it has to go into the key —
    // otherwise Stripe replays the old Price or rejects the mismatched replay.
    const exclusive = product({
      variants: [{ variantKey: "default", amountMinor: 699, currency: "cad", taxBehavior: "exclusive" }],
    });
    const inclusive = product({
      variants: [{ variantKey: "default", amountMinor: 699, currency: "cad", taxBehavior: "inclusive" }],
    });
    assert.notEqual(
      priceIdempotencyKey(exclusive, exclusive.variants[0] as SourceVariant),
      priceIdempotencyKey(inclusive, inclusive.variants[0] as SourceVariant),
    );
  });
});

describe("duplicate detection", () => {
  it("finds a managed product by source_id across paginated list pages", async () => {
    const stripe = new FakeStripe(2);
    for (let index = 0; index < 7; index += 1) {
      stripe.seedProduct({
        id: `prod_seed${index}`,
        name: `Seed ${index}`,
        active: true,
        metadata: { [META.managedBy]: MANAGED_BY, [META.sourceId]: `side-store:SEED-${index}` },
      });
    }
    const { bySourceId } = await indexManagedProducts(stripe);
    assert.equal(bySourceId.size, 7);
    // Four pages of two plus a final page of one — pagination was followed.
    assert.equal(stripe.calls.filter((call) => call.startsWith("products.list")).length, 4);
  });

  it("ignores products this tool does not manage", async () => {
    const stripe = new FakeStripe();
    stripe.seedProduct({ id: "prod_manual", name: "Hand-made", active: true, metadata: {} });
    stripe.seedProduct({
      id: "prod_other",
      name: "Another tool",
      active: true,
      metadata: { managed_by: "someone-else", source_id: "side-store:USB-C-C-1M" },
    });

    const plan = await buildPlan(stripe, [product()], OPTIONS);
    assert.equal(plan.steps[0]?.kind, "create", "an unmanaged record must not be adopted");

    await applyPlan(stripe, plan, OPTIONS);
    assert.equal(stripe.products.get("prod_manual")?.name, "Hand-made");
  });

  it("reports two Stripe products claiming one source_id instead of picking one", async () => {
    const stripe = new FakeStripe();
    for (const id of ["prod_a", "prod_b"]) {
      stripe.seedProduct({
        id,
        name: "Cable",
        active: true,
        metadata: { [META.managedBy]: MANAGED_BY, [META.sourceId]: "side-store:USB-C-C-1M" },
      });
    }
    const plan = await buildPlan(stripe, [product()], OPTIONS);
    assert.deepEqual(plan.duplicates, [
      { sourceId: "side-store:USB-C-C-1M", productIds: ["prod_a", "prod_b"] },
    ]);
    assert.ok(planRows(plan, false).some((row) => row.detail.includes("merge them by hand")));
  });
});

describe("changes to an already-synced product", () => {
  async function seeded() {
    const stripe = new FakeStripe();
    await applyPlan(stripe, await buildPlan(stripe, [product()], OPTIONS), OPTIONS);
    return stripe;
  }

  it("updates the product in place when only the copy changes", async () => {
    const stripe = await seeded();
    const renamed = product({ name: "USB-C to USB-C Cable 1m (braided)" });

    const plan = await buildPlan(stripe, [renamed], OPTIONS);
    assert.equal(plan.steps[0]?.kind, "update");
    assert.ok(plan.steps[0]?.changedFields.includes("name"));
    assert.equal(plan.steps[0]?.prices[0]?.kind, "reuse", "copy edits must not mint a new Price");

    const result = await applyPlan(stripe, plan, OPTIONS);
    assert.equal(result.updatedProducts, 1);
    assert.equal(result.createdPrices, 0);
    assert.equal(stripe.products.size, 1);
    assert.equal(stripe.prices.size, 1);
  });

  it("mints a new Price when the amount changes and preserves the Stripe product id", async () => {
    const stripe = await seeded();
    const originalProductId = [...stripe.products.keys()][0];
    const originalPriceId = [...stripe.prices.keys()][0];

    const repriced = product({ variants: [{ variantKey: "default", amountMinor: 749, currency: "cad" }] });
    const plan = await buildPlan(stripe, [repriced], OPTIONS);
    assert.equal(plan.steps[0]?.existingProductId, originalProductId);
    assert.equal(plan.steps[0]?.prices[0]?.kind, "create");

    await applyPlan(stripe, plan, OPTIONS);
    assert.equal(stripe.products.size, 1, "the Stripe product id is preserved");
    assert.equal(stripe.prices.size, 2, "Stripe Prices are immutable — the amount change needs a new one");
    assert.equal(stripe.prices.get(originalPriceId as string)?.active, true, "old Price stays active by default");
  });

  it("retires the superseded Price only when --deactivate-old-prices is passed", async () => {
    const stripe = await seeded();
    const originalPriceId = [...stripe.prices.keys()][0] as string;
    const withFlag = { ...OPTIONS, deactivateOldPrices: true };

    const repriced = product({ variants: [{ variantKey: "default", amountMinor: 749, currency: "cad" }] });
    const plan = await buildPlan(stripe, [repriced], withFlag);
    assert.deepEqual(plan.steps[0]?.stalePriceIds, [originalPriceId]);

    const result = await applyPlan(stripe, plan, withFlag);
    assert.equal(result.deactivatedPrices, 1);
    assert.equal(stripe.prices.get(originalPriceId)?.active, false);
    assert.equal(stripe.prices.size, 2, "deactivated, never deleted");
  });

  it("explains the retained Price in the plan when the flag is absent", async () => {
    const stripe = await seeded();
    const repriced = product({ variants: [{ variantKey: "default", amountMinor: 749, currency: "cad" }] });
    const rows = planRows(await buildPlan(stripe, [repriced], OPTIONS), false);
    assert.ok(rows.some((row) => row.detail.includes("--deactivate-old-prices")));
    assert.ok(rows.some((row) => row.action === "create-price" && row.detail.includes("immutable")));
  });

  it("reports no work when nothing changed", async () => {
    const stripe = await seeded();
    const plan = await buildPlan(stripe, [product()], OPTIONS);
    assert.equal(plan.steps[0]?.kind, "unchanged");
    assert.ok(planRows(plan, false).some((row) => row.action === "product-unchanged"));
  });
});

describe("products removed from the site", () => {
  it("warns instead of deleting or deactivating", async () => {
    const stripe = new FakeStripe();
    await applyPlan(stripe, await buildPlan(stripe, [product()], OPTIONS), OPTIONS);

    const plan = await buildPlan(stripe, [], OPTIONS);
    assert.equal(plan.orphans.length, 1);
    assert.equal(plan.orphans[0]?.sourceId, "side-store:USB-C-C-1M");

    await applyPlan(stripe, plan, OPTIONS);
    const survivor = [...stripe.products.values()][0];
    assert.equal(survivor?.active, true, "an orphan is never archived automatically");
    assert.ok(planRows(plan, false).some((row) => row.action === "orphan-warning"));
  });
});

describe("multi-variant products", () => {
  it("creates one Price per variant and reuses both on re-run", async () => {
    const stripe = new FakeStripe();
    const subscription = product({
      sourceId: "pricebook:business-protection",
      sku: "business-protection",
      name: "ClearGlass Business Protection",
      variants: [
        {
          variantKey: "business-protection-monthly",
          amountMinor: 10000,
          currency: "cad",
          recurring: { interval: "month", interval_count: 1 },
        },
        {
          variantKey: "business-protection-annual",
          amountMinor: 100000,
          currency: "cad",
          recurring: { interval: "year", interval_count: 1 },
        },
      ],
    });

    const first = await applyPlan(stripe, await buildPlan(stripe, [subscription], OPTIONS), OPTIONS);
    assert.equal(first.createdPrices, 2);
    assert.equal(stripe.products.size, 1);

    const second = await applyPlan(stripe, await buildPlan(stripe, [subscription], OPTIONS), OPTIONS);
    assert.equal(second.createdPrices, 0);
    assert.equal(second.reusedPrices, 2);

    const intervals = [...stripe.prices.values()].map((price) => price.recurring?.interval).sort();
    assert.deepEqual(intervals, ["month", "year"]);
  });

  it("does not confuse a monthly price with a yearly one at the same amount", async () => {
    const stripe = new FakeStripe();
    const item = product({
      sourceId: "pricebook:equal",
      sku: "equal",
      variants: [
        { variantKey: "m", amountMinor: 5000, currency: "cad", recurring: { interval: "month", interval_count: 1 } },
        { variantKey: "y", amountMinor: 5000, currency: "cad", recurring: { interval: "year", interval_count: 1 } },
      ],
    });
    await applyPlan(stripe, await buildPlan(stripe, [item], OPTIONS), OPTIONS);
    assert.equal(stripe.prices.size, 2);
  });
});

describe("source-supplied Stripe ids", () => {
  it("adopts an unmarked hinted product when a hinted Price corroborates it", async () => {
    const stripe = new FakeStripe();
    stripe.seedProduct({ id: "prod_hinted", name: "Existing", active: true, metadata: {} });
    stripe.seedPrice({
      id: "price_hinted",
      product: "prod_hinted",
      active: true,
      currency: "cad",
      unit_amount: 699,
      recurring: null,
      tax_behavior: null,
      metadata: {},
    });
    const item = product({
      stripeProductIdHint: "prod_hinted",
      variants: [{ variantKey: "default", amountMinor: 699, currency: "cad", stripePriceIdHint: "price_hinted" }],
    });

    const plan = await buildPlan(stripe, [item], OPTIONS);
    assert.equal(plan.steps[0]?.existingProductId, "prod_hinted");
    assert.equal(plan.steps[0]?.kind, "update");
  });

  it("refuses to overwrite an unmarked product that nothing corroborates", async () => {
    // A mistyped id resolves exactly as well as a correct one. Without a second
    // pointer from the same source, adopting it would rewrite someone's
    // hand-managed product.
    const stripe = new FakeStripe();
    stripe.seedProduct({ id: "prod_hinted", name: "Hand-managed", active: true, metadata: {} });
    const plan = await buildPlan(stripe, [product({ stripeProductIdHint: "prod_hinted" })], OPTIONS);

    assert.equal(plan.steps.length, 0);
    assert.match(plan.blocked[0]?.reason ?? "", /Refusing to overwrite it/);

    await applyPlan(stripe, plan, OPTIONS);
    assert.equal(stripe.products.get("prod_hinted")?.name, "Hand-managed");
  });

  it("ignores a hinted id that does not resolve, rather than failing the run", async () => {
    // A live-mode price-book id means nothing against a test key.
    const stripe = new FakeStripe();
    const item = product({ stripeProductIdHint: "prod_V0yiCBgBCIm6vC" });

    const plan = await buildPlan(stripe, [item], OPTIONS);
    assert.equal(plan.steps[0]?.kind, "create");
    assert.equal(plan.steps[0]?.existingProductId, undefined);
  });

  it("blocks when the hinted product already belongs to another source_id", async () => {
    const stripe = new FakeStripe();
    stripe.seedProduct({
      id: "prod_other",
      name: "Someone else's",
      active: true,
      metadata: { [META.managedBy]: MANAGED_BY, [META.sourceId]: "side-store:OTHER" },
    });
    const plan = await buildPlan(stripe, [product({ stripeProductIdHint: "prod_other" })], OPTIONS);

    assert.equal(plan.steps.length, 0);
    assert.match(plan.blocked[0]?.reason ?? "", /already synced from source_id side-store:OTHER/);
  });
});

describe("tax behaviour", () => {
  it("does not reuse a Price whose tax treatment differs", async () => {
    // tax_behavior is effectively immutable on a Stripe Price, so reusing one
    // with the wrong treatment would report the catalogue as synced forever.
    const stripe = new FakeStripe();
    const exclusive = product({
      variants: [{ variantKey: "default", amountMinor: 699, currency: "cad", taxBehavior: "exclusive" }],
    });
    await applyPlan(stripe, await buildPlan(stripe, [exclusive], OPTIONS), OPTIONS);

    const inclusive = product({
      variants: [{ variantKey: "default", amountMinor: 699, currency: "cad", taxBehavior: "inclusive" }],
    });
    const plan = await buildPlan(stripe, [inclusive], OPTIONS);
    assert.equal(plan.steps[0]?.prices[0]?.kind, "create");

    await applyPlan(stripe, plan, OPTIONS);
    assert.equal(stripe.prices.size, 2);
  });
});

describe("metadata that the source stopped supplying", () => {
  it("clears a removed category instead of leaving the old value in Stripe", async () => {
    // Stripe merges metadata updates, so a key we stop sending keeps its old
    // value. Clearing requires explicitly sending an empty string.
    const stripe = new FakeStripe();
    await applyPlan(stripe, await buildPlan(stripe, [product({ category: "USB Cables" })], OPTIONS), OPTIONS);
    const productId = [...stripe.products.keys()][0] as string;
    assert.equal(stripe.products.get(productId)?.metadata?.source_category, "USB Cables");

    const uncategorised = product({ category: undefined });
    const plan = await buildPlan(stripe, [uncategorised], OPTIONS);
    assert.ok(plan.steps[0]?.changedFields.includes("metadata.source_category"));

    await applyPlan(stripe, plan, OPTIONS);
    assert.equal(stripe.products.get(productId)?.metadata?.source_category, "");
  });

  it("reports no change when a product simply has no category", async () => {
    const stripe = new FakeStripe();
    const plain = product({ category: undefined });
    await applyPlan(stripe, await buildPlan(stripe, [plain], OPTIONS), OPTIONS);

    const plan = await buildPlan(stripe, [plain], OPTIONS);
    assert.equal(plan.steps[0]?.kind, "unchanged", "an absent key must not look like a pending edit");
  });
});

describe("orphan scoping", () => {
  async function twoSources() {
    const stripe = new FakeStripe();
    const items = [
      product(),
      product({ sourceId: "store:quick-audit", adapter: "store", sku: "quick-audit", name: "Security Quick-Audit" }),
    ];
    await applyPlan(stripe, await buildPlan(stripe, items, OPTIONS), OPTIONS);
    return stripe;
  }

  it("does not call another source's products orphans", async () => {
    // A --source side-store run has never read the store catalogue, so it
    // cannot know whether store products are still published.
    const stripe = await twoSources();
    const plan = await buildPlan(stripe, [product()], { ...OPTIONS, adapters: ["side-store"] });
    assert.deepEqual(plan.orphans, []);
  });

  it("still reports an orphan from a source it did read", async () => {
    const stripe = await twoSources();
    const plan = await buildPlan(stripe, [], { ...OPTIONS, adapters: ["side-store"] });
    assert.deepEqual(
      plan.orphans.map((orphan) => orphan.sourceId),
      ["side-store:USB-C-C-1M"],
    );
  });
});

describe("source-supplied Price ids", () => {
  it("reuses the named Price when it agrees with the source", async () => {
    const stripe = new FakeStripe();
    stripe.seedProduct({ id: "prod_hinted", name: "Audit", active: true, metadata: {} });
    stripe.seedPrice({
      id: "price_hinted",
      product: "prod_hinted",
      active: true,
      currency: "cad",
      unit_amount: 29700,
      recurring: null,
      tax_behavior: "exclusive",
      metadata: {},
    });

    const item = product({
      sourceId: "pricebook:risk-audit-90",
      sku: "risk-audit-90",
      stripeProductIdHint: "prod_hinted",
      variants: [
        {
          variantKey: "risk-audit-90",
          amountMinor: 29700,
          currency: "cad",
          taxBehavior: "exclusive",
          stripePriceIdHint: "price_hinted",
        },
      ],
    });

    const plan = await buildPlan(stripe, [item], OPTIONS);
    assert.equal(plan.steps[0]?.prices[0]?.kind, "reuse");
    assert.equal(plan.steps[0]?.prices[0]?.existingPriceId, "price_hinted");
    assert.deepEqual(plan.blocked, []);
  });

  it("blocks the product when the named Price charges something else", async () => {
    // The price book calls its own `amount` display data and the Stripe Price
    // the authority. When they disagree, creating a second Price at the display
    // amount would start charging a number nobody approved.
    const stripe = new FakeStripe();
    stripe.seedProduct({ id: "prod_hinted", name: "Audit", active: true, metadata: {} });
    stripe.seedPrice({
      id: "price_hinted",
      product: "prod_hinted",
      active: true,
      currency: "cad",
      unit_amount: 29700,
      recurring: null,
      tax_behavior: "exclusive",
      metadata: {},
    });

    const stale = product({
      sourceId: "pricebook:risk-audit-90",
      sku: "risk-audit-90",
      stripeProductIdHint: "prod_hinted",
      variants: [
        {
          variantKey: "risk-audit-90",
          amountMinor: 19700, // display data drifted from the live Price
          currency: "cad",
          taxBehavior: "exclusive",
          stripePriceIdHint: "price_hinted",
        },
      ],
    });

    const plan = await buildPlan(stripe, [stale], OPTIONS);
    assert.equal(plan.steps.length, 0, "a blocked product produces no step");
    assert.equal(plan.blocked.length, 1);
    assert.match(plan.blocked[0]?.reason ?? "", /29700 CAD/);
    assert.match(plan.blocked[0]?.reason ?? "", /19700 CAD/);

    await applyPlan(stripe, plan, OPTIONS);
    assert.equal(stripe.prices.size, 1, "no second Price was minted");
  });

  it("falls back to normal matching when the named Price is not in this account", async () => {
    // A live-mode price id against a test key resolves to nothing.
    const stripe = new FakeStripe();
    const item = product({
      variants: [
        {
          variantKey: "default",
          amountMinor: 699,
          currency: "cad",
          stripePriceIdHint: "price_1U0wl3L8uR92FksUMVIa9nUl",
        },
      ],
    });
    const plan = await buildPlan(stripe, [item], OPTIONS);
    assert.deepEqual(plan.blocked, []);
    assert.equal(plan.steps[0]?.prices[0]?.kind, "create");
  });

  it("blocks one product without stranding the rest of the catalogue", async () => {
    const stripe = new FakeStripe();
    stripe.seedProduct({ id: "prod_hinted", name: "Audit", active: true, metadata: {} });
    stripe.seedPrice({
      id: "price_hinted",
      product: "prod_hinted",
      active: true,
      currency: "cad",
      unit_amount: 29700,
      recurring: null,
      tax_behavior: null,
      metadata: {},
    });
    const stale = product({
      sourceId: "pricebook:risk-audit-90",
      sku: "risk-audit-90",
      stripeProductIdHint: "prod_hinted",
      variants: [{ variantKey: "a", amountMinor: 100, currency: "cad", stripePriceIdHint: "price_hinted" }],
    });

    const plan = await buildPlan(stripe, [stale, product()], OPTIONS);
    assert.equal(plan.blocked.length, 1);
    assert.equal(plan.steps.length, 1);
    assert.equal(plan.steps[0]?.product.sourceId, "side-store:USB-C-C-1M");
  });
});

describe("hand-made Stripe prices", () => {
  it("does not adopt an untagged Price that happens to match the amount", async () => {
    // Someone created this Price in the Dashboard. Same product, same amount —
    // but it is not ours, so reusing it would put a record we do not own under
    // this tool's rotation logic.
    const stripe = new FakeStripe();
    await applyPlan(stripe, await buildPlan(stripe, [product()], OPTIONS), OPTIONS);
    const productId = [...stripe.products.keys()][0] as string;
    const ourPriceId = [...stripe.prices.keys()][0] as string;

    stripe.seedPrice({
      id: "price_handmade",
      product: productId,
      active: true,
      currency: "cad",
      unit_amount: 699,
      recurring: null,
      tax_behavior: null,
      metadata: {},
    });

    const plan = await buildPlan(stripe, [product()], OPTIONS);
    assert.equal(plan.steps[0]?.prices[0]?.existingPriceId, ourPriceId, "our own Price is the one reused");

    // And it is never a rotation candidate either.
    const repriced = product({ variants: [{ variantKey: "default", amountMinor: 749, currency: "cad" }] });
    const rotation = await buildPlan(stripe, [repriced], { ...OPTIONS, deactivateOldPrices: true });
    assert.deepEqual(rotation.steps[0]?.stalePriceIds, [ourPriceId]);

    await applyPlan(stripe, rotation, { ...OPTIONS, deactivateOldPrices: true });
    assert.equal(stripe.prices.get("price_handmade")?.active, true, "a hand-made Price is left alone");
  });
});

describe("plan hashing", () => {
  it("is stable for an unchanged plan and moves when the plan does", async () => {
    const stripe = new FakeStripe();
    const first = await buildPlan(stripe, [product()], OPTIONS);
    const again = await buildPlan(stripe, [product()], OPTIONS);
    assert.equal(planHash(first), planHash(again));

    const repriced = await buildPlan(
      stripe,
      [product({ variants: [{ variantKey: "default", amountMinor: 749, currency: "cad" }] })],
      OPTIONS,
    );
    assert.notEqual(planHash(first), planHash(repriced));
  });

  it("changes once the plan has been applied", async () => {
    const stripe = new FakeStripe();
    const before = await buildPlan(stripe, [product()], OPTIONS);
    await applyPlan(stripe, before, OPTIONS);
    const after = await buildPlan(stripe, [product()], OPTIONS);
    assert.notEqual(planHash(before), planHash(after), "create then unchanged are different plans");
  });
});

describe("failure isolation", () => {
  it("records the failure and keeps syncing the rest of the catalogue", async () => {
    const stripe = new FakeStripe();
    const original = stripe.createPrice.bind(stripe);
    let calls = 0;
    stripe.createPrice = async (params, options) => {
      calls += 1;
      if (calls === 1) throw new Error("card_error: something went wrong");
      return original(params, options);
    };

    const items = [product(), product({ sourceId: "side-store:B", sku: "B", name: "Second" })];
    const result = await applyPlan(stripe, await buildPlan(stripe, items, OPTIONS), OPTIONS);

    assert.equal(result.failures.length, 1);
    assert.equal(result.failures[0]?.sourceId, "side-store:USB-C-C-1M");
    assert.equal(result.createdPrices, 1, "the second product still synced");
  });
});

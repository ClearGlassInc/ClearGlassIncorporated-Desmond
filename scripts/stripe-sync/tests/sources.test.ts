// Copyright (c) 2024-2026 ClearGlass Inc. All Rights Reserved.
// Proprietary and confidential. See LICENSE for terms.
/**
 * Parsing tests run against the *real* repository files, not fixtures.
 *
 * That is deliberate: a fixture proves the parser handles a shape someone wrote
 * down once, while reading `side-store.html` and `data/store/catalog.json`
 * proves it handles what the site actually publishes today. If a page changes
 * shape, this is the test that notices.
 */
import assert from "node:assert/strict";
import { mkdtempSync, writeFileSync, mkdirSync, readFileSync } from "node:fs";
import { tmpdir } from "node:os";
import path from "node:path";
import { describe, it } from "node:test";

import { findRepoRoot } from "../repo-root.js";
import {
  ambiguityIn,
  collectProducts,
  defaultAdapterNames,
  detectInterval,
  extractJsonIsland,
  hashProduct,
  productSku,
  sharedDescription,
} from "../sources.js";
import type { AdapterContext } from "../sources.js";

const ROOT = findRepoRoot(import.meta.url);

const context: AdapterContext = {
  root: ROOT,
  baseUrl: "https://www.clearglassinc.com",
  repository: "ClearGlassInc/ClearGlassIncorporated-Desmond",
  defaultCurrency: "cad",
};

describe("side-store.html catalogue", () => {
  const { products, issues } = collectProducts(["side-store"], context);

  it("reads every product from the embedded JSON island", () => {
    assert.ok(products.length >= 50, `expected the full catalogue, got ${products.length}`);
    assert.equal(issues.filter((issue) => issue.severity === "error").length, 0);
  });

  it("converts listed dollar prices to integer minor units", () => {
    const cable = products.find((product) => product.sku === "USB-C-C-1M");
    assert.ok(cable, "USB-C-C-1M should be in the catalogue");
    assert.equal(cable.variants[0]?.amountMinor, 699);
    assert.equal(cable.variants[0]?.currency, "cad");
    assert.equal(cable.variants[0]?.recurring, undefined);
  });

  it("namespaces the source id and links back to the public anchor", () => {
    const cable = products.find((product) => product.sku === "USB-C-C-1M");
    assert.equal(cable?.sourceId, "side-store:USB-C-C-1M");
    assert.equal(cable?.sourceUrl, "https://www.clearglassinc.com/side-store.html#USB-C-C-1M");
  });

  it("gives every product a unique source id", () => {
    const ids = products.map((product) => product.sourceId);
    assert.equal(new Set(ids).size, ids.length);
  });

  it("carries no images, so none are invented", () => {
    assert.ok(products.every((product) => product.images.length === 0));
  });

  it("invents no inventory status", () => {
    // The catalogue has no stock field. Stamping one on would be fabricating
    // availability, which the operating rules forbid outright.
    assert.ok(products.every((product) => product.inventoryStatus === undefined));
  });
});

describe("data/store/catalog.json services", () => {
  const { products, issues } = collectProducts(["store"], context);

  it("syncs only the engagements with an exact price", () => {
    // Pinned by sku and amount: these are the engagements approved to become
    // purchasable. A service picking up an exact price must be added here
    // deliberately, so nothing becomes chargeable as a side effect of a copy edit.
    const priced = products
      .map((product) => [product.sku, product.variants[0]?.amountMinor, product.variants[0]?.currency])
      .sort((a, b) => String(a[0]).localeCompare(String(b[0])));
    assert.deepEqual(priced, [
      ["critical-minerals-compliance", 149900, "cad"],
      ["quick-audit", 24900, "cad"],
    ]);
  });

  it("withholds quote-driven engagements instead of guessing an amount", () => {
    const withheld = issues
      .filter((issue) => issue.severity === "error")
      .map((issue) => issue.sourceId)
      .sort();
    assert.deepEqual(withheld, ["store:hardening", "store:monitoring", "store:phipa"]);
    for (const issue of issues.filter((candidate) => candidate.severity === "error")) {
      assert.match(issue.message, /quote-driven/);
    }
  });

  it("keeps the live-checkout note in step with the catalogue flag", () => {
    // The note is not decoration: it is how a synced product records whether the
    // storefront will actually take a card. Asserting both directions means the
    // note can never drift out of step with live_checkout_enabled -- flipping the
    // flag without the note following is a bug this catches.
    const catalogue = JSON.parse(
      readFileSync(path.join(ROOT, "data/store/catalog.json"), "utf8"),
    ) as { live_checkout_enabled?: boolean };
    const disabledNotes = products.filter((product) =>
      product.notes.some((note) => note.includes("live card checkout disabled")),
    );

    if (catalogue.live_checkout_enabled) {
      assert.equal(disabledNotes.length, 0, "live checkout is on, so no product may claim it is off");
    } else {
      assert.equal(disabledNotes.length, products.length, "live checkout is off, so every synced product must say so");
    }
  });
});

describe("price-book adapter", () => {
  const { products, issues } = collectProducts(["pricebook"], context);

  it("is opt-in, not part of the default source set", () => {
    assert.ok(!defaultAdapterNames().includes("pricebook"));
  });

  it("groups the monthly and annual offers into one product with two variants", () => {
    assert.equal(issues.filter((issue) => issue.severity === "error").length, 0);
    const protection = products.find((product) => product.sku.startsWith("business-protection"));
    assert.ok(protection, "business-protection offers should be grouped");
    const keys = protection.variants.map((variant) => variant.variantKey).sort();
    assert.deepEqual(keys, ["business-protection-annual", "business-protection-monthly"]);
    const monthly = protection.variants.find((variant) => variant.variantKey.endsWith("monthly"));
    assert.deepEqual(monthly?.recurring, { interval: "month", interval_count: 1 });
    assert.equal(monthly?.amountMinor, 10000);
  });

  it("does not tell annual subscribers their plan bills monthly", () => {
    // Both offers describe the same service and differ only by the trailing
    // cadence sentence, which belongs to the Price, not the shared Product.
    const protection = products.find((product) => product.sku.startsWith("business-protection"));
    assert.ok(protection?.description, "the grouped product should keep a neutral description");
    assert.doesNotMatch(protection.description, /billed (monthly|yearly)/i);
    assert.match(protection.description, /cybersecurity guidance/i);
  });

  it("keeps the audit offer one-time", () => {
    const audit = products.find((product) => product.sku === "risk-audit-90");
    assert.equal(audit?.variants[0]?.recurring, undefined);
    assert.equal(audit?.variants[0]?.amountMinor, 29700);
  });
});

describe("ambiguity and interval detection", () => {
  it("flags price copy that names a floor rather than an amount", () => {
    assert.equal(ambiguityIn("from CAD $2,500 fixed fee"), "from");
    assert.equal(ambiguityIn("CAD $3,000 (deposit · scope confirmed on call)"), "deposit");
    assert.equal(ambiguityIn("Contact us"), "Contact");
    assert.equal(ambiguityIn("CAD $249 one-time"), null);
  });

  it("reads a billing interval out of free-text price copy", () => {
    assert.deepEqual(detectInterval("from CAD $600 / month"), { interval: "month", interval_count: 1 });
    assert.deepEqual(detectInterval("CAD $1,000 per year"), { interval: "year", interval_count: 1 });
    assert.equal(detectInterval("CAD $249 one-time"), undefined);
  });
});

describe("malformed and missing source data", () => {
  function scratchRepo(): string {
    const dir = mkdtempSync(path.join(tmpdir(), "stripe-sync-"));
    mkdirSync(path.join(dir, "data", "store"), { recursive: true });
    return dir;
  }

  it("reports a missing source file rather than crashing the run", () => {
    const { products, issues } = collectProducts(["side-store"], { ...context, root: scratchRepo() });
    assert.equal(products.length, 0);
    assert.equal(issues.length, 1);
    assert.equal(issues[0]?.severity, "error");
    assert.match(issues[0]?.message ?? "", /failed to read side-store\.html/);
  });

  it("withholds entries with a missing name, missing sku, or malformed price", () => {
    const dir = scratchRepo();
    writeFileSync(
      path.join(dir, "side-store.html"),
      `<script id="catalog" type="application/json">${JSON.stringify([
        { id: "1", sku: "OK-1", name: "Good", price: 9.99 },
        { id: "2", sku: "", name: "No SKU", price: 1.0 },
        { id: "3", sku: "NO-NAME", name: "", price: 1.0 },
        { id: "4", sku: "BAD-PRICE", name: "Bad price", price: "nine ninety nine" },
        { id: "5", sku: "ZERO", name: "Free", price: 0 },
        { id: "6", sku: "NEGATIVE", name: "Negative", price: -3 },
        { id: "7", sku: "OK-1", name: "Duplicate sku", price: 2.0 },
      ])}</script>`,
      "utf8",
    );
    const { products, issues } = collectProducts(["side-store"], { ...context, root: dir });

    assert.deepEqual(products.map((product) => product.sku), ["OK-1"]);
    const fields = issues.map((issue) => issue.field).sort();
    assert.deepEqual(fields, ["name", "price", "price", "price", "sku", "sku"]);
    assert.ok(issues.every((issue) => issue.severity === "error"));
  });

  it("normalises relative images and refuses filesystem paths", () => {
    const dir = scratchRepo();
    writeFileSync(
      path.join(dir, "side-store.html"),
      `<script id="catalog" type="application/json">${JSON.stringify([
        {
          id: "1",
          sku: "IMG",
          name: "Imaged",
          price: 5,
          images: ["assets/cable.png", "/root/secret.png", "C:\\pics\\a.png", "http://x/y.png"],
        },
      ])}</script>`,
      "utf8",
    );
    const { products, issues } = collectProducts(["side-store"], { ...context, root: dir });

    assert.deepEqual(products[0]?.images, [
      "https://www.clearglassinc.com/assets/cable.png",
      "https://www.clearglassinc.com/root/secret.png",
    ]);
    const imageIssues = issues.filter((issue) => issue.field === "image");
    assert.equal(imageIssues.length, 2);
    assert.ok(imageIssues.every((issue) => issue.severity === "warning"));
    assert.ok(imageIssues.some((issue) => /filesystem path/.test(issue.message)));
    assert.ok(imageIssues.some((issue) => /https/.test(issue.message)));
  });

  it("rejects an unknown source name", () => {
    const { issues } = collectProducts(["not-a-source"], context);
    assert.match(issues[0]?.message ?? "", /unknown source/);
  });
});

describe("product key stability for grouped offers", () => {
  it("is the same whether or not a second interval is on sale", () => {
    // Adding or dropping an annual plan must not rename the product — that
    // would mint a new Stripe Product and orphan the old one.
    assert.equal(productSku("business-protection-monthly"), "business-protection");
    assert.equal(productSku("business-protection-annual"), "business-protection");
    assert.equal(productSku("business-protection-yearly"), "business-protection");
  });

  it("leaves a sku with no cadence suffix alone", () => {
    assert.equal(productSku("risk-audit-90"), "risk-audit-90");
    assert.equal(productSku("quick-audit"), "quick-audit");
  });
});

describe("shared description for grouped offers", () => {
  it("strips the cadence sentence that belongs to the Price", () => {
    assert.equal(
      sharedDescription(["Ongoing support. Billed monthly.", "Ongoing support. Billed yearly."]),
      "Ongoing support.",
    );
  });

  it("sets no description when the offers genuinely disagree", () => {
    assert.equal(sharedDescription(["One thing.", "A different thing."]), undefined);
    assert.equal(sharedDescription([]), undefined);
  });

  it("passes a single description through untouched", () => {
    assert.equal(sharedDescription(["A focused 90-minute assessment."]), "A focused 90-minute assessment.");
  });
});

describe("content hashing", () => {
  const base = {
    sourceId: "side-store:X",
    adapter: "side-store",
    sku: "X",
    name: "Thing",
    sourceUrl: "https://example.test/x",
    images: [],
    variants: [{ variantKey: "default", amountMinor: 100, currency: "cad" }],
    notes: [],
  };

  it("is stable for identical content and independent of variant order", () => {
    const twoVariants = {
      ...base,
      variants: [
        { variantKey: "b", amountMinor: 200, currency: "cad" },
        { variantKey: "a", amountMinor: 100, currency: "cad" },
      ],
    };
    const reversed = { ...twoVariants, variants: [...twoVariants.variants].reverse() };
    assert.equal(hashProduct(base), hashProduct({ ...base }));
    assert.equal(hashProduct(twoVariants), hashProduct(reversed));
  });

  it("changes when a chargeable field changes", () => {
    const repriced = {
      ...base,
      variants: [{ variantKey: "default", amountMinor: 101, currency: "cad" }],
    };
    assert.notEqual(hashProduct(base), hashProduct(repriced));
    assert.notEqual(hashProduct(base), hashProduct({ ...base, name: "Other" }));
  });
});

describe("JSON island extraction", () => {
  it("finds the block by id and ignores other scripts", () => {
    const html = `<script>var x=1;</script><script id="catalog" type="application/json">[{"a":1}]</script>`;
    assert.deepEqual(extractJsonIsland(html, "catalog"), [{ a: 1 }]);
  });

  it("throws a readable error when the block is absent", () => {
    assert.throws(() => extractJsonIsland("<html></html>", "catalog"), /no <script id="catalog">/);
  });
});

// Copyright (c) 2024-2026 ClearGlass Inc. All Rights Reserved.
// Proprietary and confidential. See LICENSE for terms.
/**
 * The guards that stand between a routine catalogue edit and a live-mode write,
 * plus the CLI contract and secret hygiene.
 *
 * No test in this file uses a real credential: the key strings below are
 * syntactically valid and cryptographically worthless.
 */
import assert from "node:assert/strict";
import { mkdtempSync, readFileSync } from "node:fs";
import { tmpdir } from "node:os";
import path from "node:path";
import { describe, it } from "node:test";

import { normalizeImageUrl, normalizeImages } from "../images.js";
import {
  StripeConfigError,
  detectMode,
  isRetryable,
  redactSecrets,
  resolveCredential,
  withRetry,
} from "../stripe-gateway.js";
import { parseArgs, run, UsageError } from "../../sync-stripe-products.js";
import { FakeStripe } from "./fake-stripe.js";

/**
 * Placeholder credentials: the right shape, no value whatsoever.
 *
 * Assembled at runtime rather than written as literals so that no key-shaped
 * string exists in the source for a secret scanner to flag — GitHub push
 * protection rejects the literal form even when every character is a zero.
 */
const fakeKey = (prefix: "sk" | "rk" | "pk", mode: "test" | "live"): string =>
  [prefix, mode, "0".repeat(24)].join("_");

const FAKE_TEST_KEY = fakeKey("sk", "test");
const FAKE_LIVE_KEY = fakeKey("sk", "live");
const FAKE_WEBHOOK_SECRET = ["whsec", "0".repeat(24)].join("_");

describe("live-mode guard", () => {
  it("runs in test mode with a test key and no flags", () => {
    const decision = resolveCredential({ env: { STRIPE_SECRET_KEY: FAKE_TEST_KEY }, live: false });
    assert.equal(decision.mode, "test");
  });

  it("refuses --live without ALLOW_STRIPE_LIVE_SYNC=true", () => {
    assert.throws(
      () => resolveCredential({ env: { STRIPE_SECRET_KEY: FAKE_LIVE_KEY }, live: true }),
      /ALLOW_STRIPE_LIVE_SYNC=true/,
    );
    assert.throws(
      () =>
        resolveCredential({
          env: { STRIPE_SECRET_KEY: FAKE_LIVE_KEY, ALLOW_STRIPE_LIVE_SYNC: "yes" },
          live: true,
        }),
      StripeConfigError,
    );
  });

  it("refuses a live key when --live was not passed", () => {
    assert.throws(
      () => resolveCredential({ env: { STRIPE_SECRET_KEY: FAKE_LIVE_KEY }, live: false }),
      /--live was not passed/,
    );
  });

  it("refuses --live when the credential is a test key", () => {
    assert.throws(
      () =>
        resolveCredential({
          env: { STRIPE_SECRET_KEY: FAKE_TEST_KEY, ALLOW_STRIPE_LIVE_SYNC: "true" },
          live: true,
        }),
      /the flag and the credential disagree/,
    );
  });

  it("allows live only when all three signals agree", () => {
    const decision = resolveCredential({
      env: { STRIPE_SECRET_KEY: FAKE_LIVE_KEY, ALLOW_STRIPE_LIVE_SYNC: "true" },
      live: true,
    });
    assert.equal(decision.mode, "live");
  });

  it("requires a key at all", () => {
    assert.throws(() => resolveCredential({ env: {}, live: false }), /STRIPE_SECRET_KEY is not set/);
  });

  it("recognises restricted keys and rejects unrecognised ones", () => {
    assert.equal(detectMode(fakeKey("rk", "test")), "test");
    assert.equal(detectMode(fakeKey("rk", "live")), "live");
    // A publishable key is not a secret key, whatever mode it names.
    assert.throws(() => detectMode(fakeKey("pk", "test")), StripeConfigError);
    assert.throws(() => detectMode("hunter2"), StripeConfigError);
  });
});

describe("secret hygiene", () => {
  it("redacts every key shape out of a message", () => {
    const message = `request failed using ${FAKE_LIVE_KEY} and ${FAKE_TEST_KEY} (${FAKE_WEBHOOK_SECRET})`;
    const clean = redactSecrets(message);
    assert.ok(!clean.includes("sk_live_"), clean);
    assert.ok(!clean.includes("sk_test_"), clean);
    assert.ok(!clean.includes("whsec_"), clean);
    assert.equal(clean.match(/\[redacted\]/g)?.length, 3);
  });

  it("never leaks the key through a refusal message", () => {
    try {
      resolveCredential({ env: { STRIPE_SECRET_KEY: FAKE_LIVE_KEY }, live: false });
      assert.fail("expected a refusal");
    } catch (error) {
      assert.ok(!(error as Error).message.includes(FAKE_LIVE_KEY));
    }
  });
});

describe("rate limits and backoff", () => {
  it("classifies which failures are worth retrying", () => {
    assert.equal(isRetryable({ statusCode: 429 }), true);
    assert.equal(isRetryable({ statusCode: 503 }), true);
    assert.equal(isRetryable({ type: "StripeRateLimitError" }), true);
    assert.equal(isRetryable({ code: "ECONNRESET" }), true);
    assert.equal(isRetryable({ statusCode: 400 }), false);
    assert.equal(isRetryable(new Error("bad request")), false);
  });

  it("backs off exponentially and then succeeds", async () => {
    const delays: number[] = [];
    let attempts = 0;
    const value = await withRetry(
      async () => {
        attempts += 1;
        if (attempts < 4) throw { statusCode: 429 };
        return "ok";
      },
      {
        maxAttempts: 6,
        baseDelayMs: 100,
        maxDelayMs: 10_000,
        sleep: async (ms) => {
          delays.push(ms);
        },
      },
      () => 1, // no jitter, so the schedule is assertable
    );

    assert.equal(value, "ok");
    assert.equal(attempts, 4);
    assert.deepEqual(delays, [100, 200, 400]);
  });

  it("honours Retry-After over its own schedule", async () => {
    const delays: number[] = [];
    let attempts = 0;
    await withRetry(
      async () => {
        attempts += 1;
        if (attempts === 1) throw { statusCode: 429, headers: { "retry-after": "7" } };
        return "ok";
      },
      { maxAttempts: 3, baseDelayMs: 100, maxDelayMs: 10_000, sleep: async (ms) => { delays.push(ms); } },
      () => 1,
    );
    assert.deepEqual(delays, [7000]);
  });

  it("gives up on a non-retryable error immediately", async () => {
    let attempts = 0;
    await assert.rejects(
      withRetry(
        async () => {
          attempts += 1;
          throw Object.assign(new Error("invalid_request_error"), { statusCode: 400 });
        },
        { maxAttempts: 5, baseDelayMs: 1, maxDelayMs: 10, sleep: async () => {} },
      ),
      /invalid_request_error/,
    );
    assert.equal(attempts, 1);
  });

  it("stops after maxAttempts and rethrows the last error", async () => {
    let attempts = 0;
    await assert.rejects(
      withRetry(
        async () => {
          attempts += 1;
          throw Object.assign(new Error("rate limited"), { statusCode: 429 });
        },
        { maxAttempts: 3, baseDelayMs: 1, maxDelayMs: 10, sleep: async () => {} },
      ),
      /rate limited/,
    );
    assert.equal(attempts, 3);
  });
});

describe("image URL handling", () => {
  const base = "https://www.clearglassinc.com";

  it("resolves relative paths against the Pages base URL", () => {
    assert.equal(
      normalizeImageUrl("assets/img/cable.png", base).url,
      "https://www.clearglassinc.com/assets/img/cable.png",
    );
    assert.equal(
      normalizeImageUrl("/assets/img/cable.png", base).url,
      "https://www.clearglassinc.com/assets/img/cable.png",
    );
  });

  it("passes an absolute https URL through unchanged", () => {
    assert.equal(
      normalizeImageUrl("https://cdn.example.test/a.png", base).url,
      "https://cdn.example.test/a.png",
    );
  });

  it("refuses filesystem paths, data URIs and plaintext http", () => {
    assert.match(normalizeImageUrl("C:\\pics\\a.png", base).reason ?? "", /filesystem path/);
    assert.match(normalizeImageUrl("\\\\share\\a.png", base).reason ?? "", /filesystem path/);
    assert.match(normalizeImageUrl("file:///home/d/a.png", base).reason ?? "", /file: URLs/);
    assert.match(normalizeImageUrl("data:image/png;base64,AAA", base).reason ?? "", /data: URIs/);
    assert.match(normalizeImageUrl("http://insecure.test/a.png", base).reason ?? "", /https/);
    assert.match(normalizeImageUrl("s3://bucket/a.png", base).reason ?? "", /unsupported URL scheme/);
    assert.equal(normalizeImageUrl("", base).ok, false);
    assert.equal(normalizeImageUrl(null, base).ok, false);
  });

  it("de-duplicates and caps at Stripe's eight-image limit", () => {
    const urls = Array.from({ length: 10 }, (_, index) => `https://x.test/${index}.png`);
    const { images, failures } = normalizeImages([...urls, urls[0]], base);
    assert.equal(images.length, 8);
    assert.equal(failures.length, 3);
  });
});

describe("CLI options", () => {
  it("defaults to a dry run over the Pages sources", () => {
    const options = parseArgs([]);
    assert.equal(options.apply, false);
    assert.equal(options.live, false);
    assert.equal(options.deactivateOldPrices, false);
    assert.deepEqual(options.sources, ["side-store", "store"]);
  });

  it("parses every documented flag", () => {
    const options = parseArgs([
      "--source", "side-store,store",
      "--apply",
      "--live",
      "--deactivate-old-prices",
      "--check-images",
      "--base-url", "https://example.test/",
      "--repository", "owner/repo",
      "--currency", "USD",
      "--report", "out.json",
    ]);
    assert.deepEqual(options.sources, ["side-store", "store"]);
    assert.equal(options.apply, true);
    assert.equal(options.live, true);
    assert.equal(options.deactivateOldPrices, true);
    assert.equal(options.checkImages, true);
    assert.equal(options.baseUrl, "https://example.test");
    assert.equal(options.repository, "owner/repo");
    assert.equal(options.currency, "usd");
    assert.equal(options.reportPath, "out.json");
  });

  it("includes the opt-in price book only when asked", () => {
    assert.ok(!parseArgs([]).sources.includes("pricebook"));
    assert.ok(parseArgs(["--source", "all"]).sources.includes("pricebook"));
    assert.ok(parseArgs(["--source", "pricebook"]).sources.includes("pricebook"));
  });

  it("rejects a typo rather than silently dry-running", () => {
    assert.throws(() => parseArgs(["--aply"]), UsageError);
    assert.throws(() => parseArgs(["--source"]), UsageError);
    assert.throws(() => parseArgs(["--source", "nope"]), /unknown --source/);
  });

  it("refuses to combine --offline with a mode that writes", () => {
    assert.equal(parseArgs(["--offline"]).offline, true);
    assert.throws(() => parseArgs(["--offline", "--apply"]), /cannot be combined/);
    assert.throws(() => parseArgs(["--offline", "--live"]), /cannot be combined/);
  });
});

describe("end-to-end run", () => {
  function harness() {
    const stripe = new FakeStripe();
    const out: string[] = [];
    const err: string[] = [];
    const reportDir = mkdtempSync(path.join(tmpdir(), "stripe-sync-report-"));
    return {
      stripe,
      out,
      err,
      reportDir,
      dependencies: {
        gatewayFactory: async () => ({ gateway: stripe as never, mode: "test" as const }),
        log: (line: string) => out.push(line),
        errorLog: (line: string) => err.push(line),
        env: {},
      },
    };
  }

  it("dry-runs by default and writes nothing to Stripe", async () => {
    const { stripe, out, dependencies, reportDir } = harness();
    const code = await run(
      ["--source", "side-store", "--report", path.join(reportDir, "report.json")],
      dependencies,
    );

    assert.equal(code, 0);
    assert.equal(stripe.products.size, 0, "a dry run must not create anything");
    const text = out.join("\n");
    assert.match(text, /DRY RUN/);
    assert.match(text, /Dry run — nothing was written to Stripe/);
    // The table carries every column the operator needs to approve the plan.
    assert.match(text, /ACTION\s+SOURCE_ID\s+PRODUCT NAME\s+AMOUNT\s+CUR\s+STRIPE PRODUCT\s+STRIPE PRICE/);
    assert.match(text, /create-product\s+side-store:USB-C-C-1M/);
    assert.match(text, /create-price\s+side-store:USB-C-C-1M#default\s+.*6\.99\s+CAD/);
  });

  it("writes an artifact-safe report containing no credential material", async () => {
    const { dependencies, reportDir } = harness();
    const reportPath = path.join(reportDir, "report.json");
    await run(["--source", "side-store", "--report", reportPath], {
      ...dependencies,
      env: { STRIPE_SECRET_KEY: FAKE_TEST_KEY },
    });

    const raw = readFileSync(reportPath, "utf8");
    assert.ok(!raw.includes("sk_test_"), "the report must never carry a key");
    const report = JSON.parse(raw);
    assert.equal(report.schema, "clearglass.stripe.sync-report/v1");
    assert.equal(report.mode, "test");
    assert.equal(report.applied, false);
    assert.ok(report.counts.products_parsed >= 50);
    assert.ok(Array.isArray(report.plan));
  });

  it("exits 1 and withholds the quote-driven engagements", async () => {
    const { stripe, err, dependencies, reportDir } = harness();
    const code = await run(
      ["--source", "store", "--apply", "--report", path.join(reportDir, "report.json")],
      dependencies,
    );

    assert.equal(code, 1, "withheld products must fail the run");
    const text = err.join("\n");
    assert.match(text, /WITHHELD\s+store:hardening/);
    assert.match(text, /quote-driven/);
    // The one unambiguous engagement still syncs — a bad neighbour does not
    // block a good product.
    assert.equal(stripe.products.size, 1);
    assert.equal([...stripe.products.values()][0]?.metadata?.source_id, "store:quick-audit");
  });

  it("is idempotent across repeated --apply runs", async () => {
    const { stripe, dependencies, reportDir } = harness();
    const argv = ["--source", "side-store", "--apply", "--report", path.join(reportDir, "r.json")];
    await run(argv, dependencies);
    const productsAfterFirst = stripe.products.size;
    const pricesAfterFirst = stripe.prices.size;

    await run(argv, dependencies);
    assert.equal(stripe.products.size, productsAfterFirst);
    assert.equal(stripe.prices.size, pricesAfterFirst);
  });

  it("exits 2 when the credential is missing, before reaching Stripe", async () => {
    const out: string[] = [];
    const err: string[] = [];
    const reportDir = mkdtempSync(path.join(tmpdir(), "stripe-sync-report-"));
    const code = await run(["--source", "side-store", "--report", path.join(reportDir, "r.json")], {
      log: (line) => out.push(line),
      errorLog: (line) => err.push(line),
      env: {},
    });
    assert.equal(code, 2);
    assert.match(err.join("\n"), /STRIPE_SECRET_KEY is not set/);
  });

  it("plans offline with no credential and never writes", async () => {
    const out: string[] = [];
    const reportDir = mkdtempSync(path.join(tmpdir(), "stripe-sync-report-"));
    const code = await run(
      ["--source", "all", "--offline", "--report", path.join(reportDir, "r.json")],
      { log: (line) => out.push(line), errorLog: () => {}, env: {} },
    );

    assert.equal(code, 1, "the withheld engagements still fail the run");
    const text = out.join("\n");
    assert.match(text, /OFFLINE PLAN/);
    assert.match(text, /No Stripe account was consulted/);
    assert.match(text, /create-product\s+pricebook:business-protection/);
  });

  it("exits 2 on an unknown flag", async () => {
    const err: string[] = [];
    const code = await run(["--nope"], { errorLog: (line) => err.push(line), env: {} });
    assert.equal(code, 2);
    assert.match(err.join("\n"), /unknown option/);
  });
});

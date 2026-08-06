// Copyright (c) 2024-2026 ClearGlass Inc. All Rights Reserved.
// Proprietary and confidential. See LICENSE for terms.
/**
 * The real Stripe implementation of `StripeGateway`, plus the guards that decide
 * whether a key may be used at all.
 *
 * The secret key is read from the environment and never leaves this module: it
 * is not logged, not written to the report, not echoed on error. `redactSecrets`
 * scrubs anything key-shaped out of messages before they are printed, because
 * Stripe error payloads occasionally quote the request that produced them.
 */
import Stripe from "stripe";

import type {
  PriceCreateParams,
  ProductCreateParams,
  ProductUpdateParams,
  RequestOptions,
  StripeGateway,
  StripePriceLike,
  StripeProductLike,
} from "./types.js";

export type StripeMode = "test" | "live";

export class StripeConfigError extends Error {}

/** Anything shaped like a Stripe credential, in any log line we emit. */
const SECRET_PATTERNS = [
  /\b[sr]k_(?:test|live)_[A-Za-z0-9]{4,}/g,
  /\bwhsec_[A-Za-z0-9]{4,}/g,
  /\bpk_(?:test|live)_[A-Za-z0-9]{4,}/g,
];

/** Replace every credential-shaped substring with a fixed placeholder. */
export function redactSecrets(text: string): string {
  let output = text;
  for (const pattern of SECRET_PATTERNS) {
    output = output.replace(pattern, "[redacted]");
  }
  return output;
}

/**
 * Classify a secret key by the mode it operates in.
 *
 * Restricted keys (`rk_`) are supported because a sync that only needs
 * product/price write scope is a good candidate for one.
 */
export function detectMode(key: string): StripeMode {
  if (/^[sr]k_live_/.test(key)) return "live";
  if (/^[sr]k_test_/.test(key)) return "test";
  throw new StripeConfigError(
    "STRIPE_SECRET_KEY is not a recognised Stripe secret key (expected sk_test_…, sk_live_…, rk_test_… or rk_live_…)",
  );
}

export interface CredentialDecision {
  key: string;
  mode: StripeMode;
}

/**
 * Resolve the credential for this run and refuse anything unsafe.
 *
 * Live mode needs *three* independent signals to line up: the `--live` flag, the
 * `ALLOW_STRIPE_LIVE_SYNC=true` environment variable, and a live key. Any two
 * without the third is a refusal, so neither a stray flag nor a mistakenly
 * configured secret can move real money on its own.
 */
export function resolveCredential(options: {
  env: NodeJS.ProcessEnv;
  live: boolean;
}): CredentialDecision {
  const key = (options.env.STRIPE_SECRET_KEY ?? "").trim();
  if (!key) {
    throw new StripeConfigError(
      "STRIPE_SECRET_KEY is not set. Export it in your shell or add it to GitHub Actions Secrets; never commit it.",
    );
  }
  const mode = detectMode(key);

  if (options.live) {
    if (options.env.ALLOW_STRIPE_LIVE_SYNC !== "true") {
      throw new StripeConfigError(
        "--live requires ALLOW_STRIPE_LIVE_SYNC=true in the environment. Refusing to touch live data.",
      );
    }
    if (mode !== "live") {
      throw new StripeConfigError(
        "--live was passed but STRIPE_SECRET_KEY is a test-mode key. Refusing: the flag and the credential disagree.",
      );
    }
    return { key, mode };
  }

  if (mode === "live") {
    throw new StripeConfigError(
      "STRIPE_SECRET_KEY is a live-mode key but --live was not passed. Refusing: " +
        "start in test mode with an sk_test_… key, or pass --live with ALLOW_STRIPE_LIVE_SYNC=true.",
    );
  }
  return { key, mode };
}

export interface RetryOptions {
  maxAttempts: number;
  baseDelayMs: number;
  maxDelayMs: number;
  sleep: (ms: number) => Promise<void>;
}

export const DEFAULT_RETRY: RetryOptions = {
  maxAttempts: 6,
  baseDelayMs: 500,
  maxDelayMs: 20_000,
  sleep: (ms) => new Promise((resolve) => setTimeout(resolve, ms)),
};

interface RetryableError {
  statusCode?: number;
  type?: string;
  code?: string;
  headers?: Record<string, string>;
}

/** Rate limits, transient 5xx, and dropped connections are worth another go. */
export function isRetryable(error: unknown): boolean {
  const candidate = error as RetryableError;
  if (candidate?.statusCode === 429) return true;
  if (typeof candidate?.statusCode === "number" && candidate.statusCode >= 500) return true;
  return (
    candidate?.type === "StripeRateLimitError" ||
    candidate?.type === "StripeConnectionError" ||
    candidate?.code === "ETIMEDOUT" ||
    candidate?.code === "ECONNRESET"
  );
}

/**
 * Retry with exponential backoff and full jitter.
 *
 * Jitter matters more than it looks: without it, a rate-limited batch retries in
 * lockstep and re-triggers the same limit. `Retry-After` wins when Stripe sends
 * one, since that is the server telling us exactly how long to wait.
 */
export async function withRetry<T>(
  operation: () => Promise<T>,
  options: RetryOptions = DEFAULT_RETRY,
  random: () => number = Math.random,
): Promise<T> {
  let lastError: unknown;
  for (let attempt = 1; attempt <= options.maxAttempts; attempt += 1) {
    try {
      return await operation();
    } catch (error) {
      lastError = error;
      if (!isRetryable(error) || attempt === options.maxAttempts) break;

      const retryAfter = Number((error as RetryableError)?.headers?.["retry-after"]);
      const backoff = Math.min(options.baseDelayMs * 2 ** (attempt - 1), options.maxDelayMs);
      const delay = Number.isFinite(retryAfter) && retryAfter > 0
        ? retryAfter * 1000
        : Math.round(backoff * (0.5 + random() * 0.5));
      await options.sleep(delay);
    }
  }
  throw lastError;
}

/**
 * A gateway that never opens a socket, for reviewing the catalogue before any
 * credential exists.
 *
 * It reports an empty Stripe account, so the plan shows every product as it
 * would appear on a first sync. Writes throw rather than no-op: `--offline` is
 * refused alongside `--apply`, and this makes a mistake in that guard loud.
 */
export class OfflineStripeGateway implements StripeGateway {
  async *listAllProducts(): AsyncIterable<StripeProductLike> {
    // Intentionally empty: offline mode knows of no existing Stripe products.
  }

  async retrieveProduct(): Promise<StripeProductLike | null> {
    return null;
  }

  async listPrices(): Promise<StripePriceLike[]> {
    return [];
  }

  async createProduct(): Promise<StripeProductLike> {
    throw new StripeConfigError("offline mode cannot write to Stripe");
  }

  async updateProduct(): Promise<StripeProductLike> {
    throw new StripeConfigError("offline mode cannot write to Stripe");
  }

  async createPrice(): Promise<StripePriceLike> {
    throw new StripeConfigError("offline mode cannot write to Stripe");
  }

  async deactivatePrice(): Promise<StripePriceLike> {
    throw new StripeConfigError("offline mode cannot write to Stripe");
  }
}

/** `StripeGateway` backed by the official SDK. */
export class LiveStripeGateway implements StripeGateway {
  private readonly client: Stripe;
  private readonly retry: RetryOptions;

  constructor(key: string, retry: RetryOptions = DEFAULT_RETRY) {
    this.client = new Stripe(key, {
      // Pinning the version keeps a Stripe-side API rollout from changing the
      // shape of what this script reads without a deliberate bump here.
      apiVersion: "2025-08-27.basil",
      maxNetworkRetries: 0, // backoff is handled by withRetry, not the SDK
      appInfo: { name: "clearglass-site-sync", version: "1.0.0" },
    });
    this.retry = retry;
  }

  async *listAllProducts(): AsyncIterable<StripeProductLike> {
    // autoPagingEach follows `has_more`/`starting_after` to the end of the list.
    for await (const product of this.client.products.list({ limit: 100 })) {
      yield product as unknown as StripeProductLike;
    }
  }

  async retrieveProduct(id: string): Promise<StripeProductLike | null> {
    try {
      const product = await withRetry(() => this.client.products.retrieve(id), this.retry);
      return product as unknown as StripeProductLike;
    } catch (error) {
      if ((error as { statusCode?: number })?.statusCode === 404) return null;
      if ((error as { code?: string })?.code === "resource_missing") return null;
      throw error;
    }
  }

  async listPrices(productId: string): Promise<StripePriceLike[]> {
    const prices: StripePriceLike[] = [];
    for await (const price of this.client.prices.list({ product: productId, limit: 100 })) {
      prices.push(price as unknown as StripePriceLike);
    }
    return prices;
  }

  async createProduct(
    params: ProductCreateParams,
    options?: RequestOptions,
  ): Promise<StripeProductLike> {
    const product = await withRetry(
      () =>
        this.client.products.create(
          params as Stripe.ProductCreateParams,
          options?.idempotencyKey ? { idempotencyKey: options.idempotencyKey } : undefined,
        ),
      this.retry,
    );
    return product as unknown as StripeProductLike;
  }

  async updateProduct(id: string, params: ProductUpdateParams): Promise<StripeProductLike> {
    const product = await withRetry(
      () => this.client.products.update(id, params as Stripe.ProductUpdateParams),
      this.retry,
    );
    return product as unknown as StripeProductLike;
  }

  async createPrice(params: PriceCreateParams, options?: RequestOptions): Promise<StripePriceLike> {
    const price = await withRetry(
      () =>
        this.client.prices.create(
          params as unknown as Stripe.PriceCreateParams,
          options?.idempotencyKey ? { idempotencyKey: options.idempotencyKey } : undefined,
        ),
      this.retry,
    );
    return price as unknown as StripePriceLike;
  }

  async deactivatePrice(id: string): Promise<StripePriceLike> {
    const price = await withRetry(() => this.client.prices.update(id, { active: false }), this.retry);
    return price as unknown as StripePriceLike;
  }
}

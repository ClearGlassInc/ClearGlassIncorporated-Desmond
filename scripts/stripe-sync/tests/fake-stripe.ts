// Copyright (c) 2024-2026 ClearGlass Inc. All Rights Reserved.
// Proprietary and confidential. See LICENSE for terms.
/**
 * In-memory Stripe double.
 *
 * Models the three behaviours the sync depends on and nothing else: list
 * pagination, idempotency-key replay (the same key returns the original object
 * instead of creating a second one), and the immutability of a Price's amount.
 * No credentials, no network — the whole suite runs offline.
 */
import type {
  PriceCreateParams,
  ProductCreateParams,
  ProductUpdateParams,
  RequestOptions,
  StripeGateway,
  StripePriceLike,
  StripeProductLike,
} from "../types.js";

export class FakeStripe implements StripeGateway {
  products = new Map<string, StripeProductLike>();
  prices = new Map<string, StripePriceLike>();
  calls: string[] = [];

  private productSeq = 0;
  private priceSeq = 0;
  private readonly idempotency = new Map<string, string>();

  /** Page size, so tests can force the paginating code path with few records. */
  constructor(private readonly pageSize = 2) {}

  seedProduct(product: StripeProductLike): StripeProductLike {
    this.products.set(product.id, product);
    return product;
  }

  seedPrice(price: StripePriceLike): StripePriceLike {
    this.prices.set(price.id, price);
    return price;
  }

  async *listAllProducts(): AsyncIterable<StripeProductLike> {
    const all = [...this.products.values()];
    for (let offset = 0; offset < all.length; offset += this.pageSize) {
      this.calls.push(`products.list@${offset}`);
      for (const product of all.slice(offset, offset + this.pageSize)) {
        yield product;
      }
    }
  }

  async retrieveProduct(id: string): Promise<StripeProductLike | null> {
    this.calls.push(`products.retrieve:${id}`);
    return this.products.get(id) ?? null;
  }

  async retrievePrice(id: string): Promise<StripePriceLike | null> {
    this.calls.push(`prices.retrieve:${id}`);
    return this.prices.get(id) ?? null;
  }

  async listPrices(productId: string): Promise<StripePriceLike[]> {
    this.calls.push(`prices.list:${productId}`);
    return [...this.prices.values()].filter(
      (price) => (typeof price.product === "string" ? price.product : price.product.id) === productId,
    );
  }

  async createProduct(
    params: ProductCreateParams,
    options?: RequestOptions,
  ): Promise<StripeProductLike> {
    const replayed = this.replay(options);
    if (replayed) return this.products.get(replayed) as StripeProductLike;

    this.productSeq += 1;
    const id = `prod_fake${String(this.productSeq).padStart(3, "0")}`;
    const product: StripeProductLike = {
      id,
      name: params.name,
      active: params.active ?? true,
      description: params.description ?? null,
      images: params.images ?? [],
      metadata: { ...params.metadata },
    };
    this.products.set(id, product);
    this.calls.push(`products.create:${id}`);
    if (options?.idempotencyKey) this.idempotency.set(options.idempotencyKey, id);
    return product;
  }

  async updateProduct(id: string, params: ProductUpdateParams): Promise<StripeProductLike> {
    const product = this.products.get(id);
    if (!product) throw Object.assign(new Error(`No such product: ${id}`), { statusCode: 404 });
    if (params.name !== undefined) product.name = params.name;
    if (params.description !== undefined) product.description = params.description;
    if (params.images !== undefined) product.images = params.images;
    if (params.metadata !== undefined) product.metadata = { ...product.metadata, ...params.metadata };
    this.calls.push(`products.update:${id}`);
    return product;
  }

  async createPrice(params: PriceCreateParams, options?: RequestOptions): Promise<StripePriceLike> {
    const replayed = this.replay(options);
    if (replayed) return this.prices.get(replayed) as StripePriceLike;

    if (!this.products.has(params.product)) {
      throw Object.assign(new Error(`No such product: ${params.product}`), { statusCode: 404 });
    }
    this.priceSeq += 1;
    const id = `price_fake${String(this.priceSeq).padStart(3, "0")}`;
    const price: StripePriceLike = {
      id,
      product: params.product,
      active: true,
      currency: params.currency,
      unit_amount: params.unit_amount,
      recurring: params.recurring ?? null,
      tax_behavior: params.tax_behavior ?? null,
      metadata: { ...params.metadata },
    };
    this.prices.set(id, price);
    this.calls.push(`prices.create:${id}`);
    if (options?.idempotencyKey) this.idempotency.set(options.idempotencyKey, id);
    return price;
  }

  async deactivatePrice(id: string): Promise<StripePriceLike> {
    const price = this.prices.get(id);
    if (!price) throw Object.assign(new Error(`No such price: ${id}`), { statusCode: 404 });
    price.active = false;
    this.calls.push(`prices.deactivate:${id}`);
    return price;
  }

  private replay(options?: RequestOptions): string | undefined {
    if (!options?.idempotencyKey) return undefined;
    return this.idempotency.get(options.idempotencyKey);
  }
}

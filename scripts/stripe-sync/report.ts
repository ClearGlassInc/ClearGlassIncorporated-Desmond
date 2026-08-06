// Copyright (c) 2024-2026 ClearGlass Inc. All Rights Reserved.
// Proprietary and confidential. See LICENSE for terms.
/**
 * Human-readable table and machine-readable report.
 *
 * The JSON report is uploaded as a workflow artifact, so it carries no
 * credential material — only the mode the run used, the plan, and the counts.
 */
import type { ApplyResult } from "./planner.js";
import type { PlanRow, ProductIssue, SourceProduct } from "./types.js";

const COLUMNS: { key: keyof PlanRow; header: string; width: number }[] = [
  { key: "action", header: "ACTION", width: 18 },
  { key: "sourceId", header: "SOURCE_ID", width: 34 },
  { key: "name", header: "PRODUCT NAME", width: 38 },
  { key: "amount", header: "AMOUNT", width: 10 },
  { key: "currency", header: "CUR", width: 4 },
  { key: "stripeProductId", header: "STRIPE PRODUCT", width: 22 },
  { key: "stripePriceId", header: "STRIPE PRICE", width: 32 },
];

function cell(value: string, width: number): string {
  if (value.length <= width) return value.padEnd(width);
  return `${value.slice(0, width - 1)}…`;
}

/** Render the plan as the fixed-width table the dry run prints. */
export function renderTable(rows: PlanRow[]): string {
  const header = COLUMNS.map((column) => cell(column.header, column.width)).join("  ");
  const rule = COLUMNS.map((column) => "-".repeat(column.width)).join("  ");
  const body = rows.map((row) =>
    COLUMNS.map((column) => cell(row[column.key] ?? "", column.width)).join("  "),
  );
  return [header, rule, ...body].join("\n");
}

export interface ReportInput {
  mode: "test" | "live";
  applied: boolean;
  sources: string[];
  baseUrl: string;
  repository: string;
  products: SourceProduct[];
  issues: ProductIssue[];
  rows: PlanRow[];
  apply?: ApplyResult;
  startedAt: string;
  finishedAt: string;
}

export interface SyncReport {
  schema: "clearglass.stripe.sync-report/v1";
  mode: "test" | "live";
  applied: boolean;
  started_utc: string;
  finished_utc: string;
  sources: string[];
  base_url: string;
  repository: string;
  counts: Record<string, number>;
  products: {
    source_id: string;
    sku: string;
    name: string;
    source_url: string;
    source_hash: string;
    variants: { variant_key: string; amount_minor: number; currency: string; interval: string }[];
    notes: string[];
  }[];
  plan: PlanRow[];
  issues: ProductIssue[];
  manual_correction_required: ProductIssue[];
  failures: { sourceId: string; message: string }[];
}

/** Build the artifact-safe JSON report. Contains no secret material by design. */
export function buildReport(input: ReportInput): SyncReport {
  const errors = input.issues.filter((issue) => issue.severity === "error");
  return {
    schema: "clearglass.stripe.sync-report/v1",
    mode: input.mode,
    applied: input.applied,
    started_utc: input.startedAt,
    finished_utc: input.finishedAt,
    sources: input.sources,
    base_url: input.baseUrl,
    repository: input.repository,
    counts: {
      products_parsed: input.products.length,
      issues: input.issues.length,
      errors: errors.length,
      warnings: input.issues.length - errors.length,
      planned_product_creates: input.rows.filter((row) => row.action === "create-product").length,
      planned_product_updates: input.rows.filter((row) => row.action === "update-product").length,
      planned_price_creates: input.rows.filter((row) => row.action === "create-price").length,
      orphan_warnings: input.rows.filter((row) => row.action === "orphan-warning").length,
      created_products: input.apply?.createdProducts ?? 0,
      updated_products: input.apply?.updatedProducts ?? 0,
      created_prices: input.apply?.createdPrices ?? 0,
      reused_prices: input.apply?.reusedPrices ?? 0,
      deactivated_prices: input.apply?.deactivatedPrices ?? 0,
    },
    products: input.products.map((product) => ({
      source_id: product.sourceId,
      sku: product.sku,
      name: product.name,
      source_url: product.sourceUrl,
      source_hash: product.sourceHash,
      variants: product.variants.map((variant) => ({
        variant_key: variant.variantKey,
        amount_minor: variant.amountMinor,
        currency: variant.currency,
        interval: variant.recurring
          ? `${variant.recurring.interval_count} ${variant.recurring.interval}`
          : "one_time",
      })),
      notes: product.notes,
    })),
    plan: input.rows,
    issues: input.issues,
    manual_correction_required: errors,
    failures: input.apply?.failures ?? [],
  };
}

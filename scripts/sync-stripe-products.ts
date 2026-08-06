// Copyright (c) 2024-2026 ClearGlass Inc. All Rights Reserved.
// Proprietary and confidential. See LICENSE for terms.
/**
 * Sync the products published on the ClearGlass GitHub Pages site into Stripe.
 *
 * Reads structured product data out of the repository (never scraped HTML),
 * works out what Stripe would have to change to match, prints that plan, and —
 * only when `--apply` is passed — writes it. Default behaviour is a dry run.
 *
 *   npm run sync:stripe -- --help
 *   npm run sync:stripe                          # dry run, every Pages source
 *   npm run sync:stripe -- --source side-store   # one source
 *   npm run sync:stripe -- --apply               # write to Stripe (test mode)
 *
 * Live mode needs `--live` *and* `ALLOW_STRIPE_LIVE_SYNC=true` *and* a live key.
 *
 * Exit codes: 0 clean · 1 a product failed or needs manual correction ·
 * 2 refused for a configuration or safety reason.
 */
import { writeFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

import { verifyImagesReachable } from "./stripe-sync/images.js";
import { applyPlan, buildPlan, planHash, planRows } from "./stripe-sync/planner.js";
import { buildReport, renderTable } from "./stripe-sync/report.js";
import { findRepoRoot } from "./stripe-sync/repo-root.js";
import {
  ADAPTERS,
  adapterNames,
  collectProducts,
  defaultAdapterNames,
} from "./stripe-sync/sources.js";
import {
  LiveStripeGateway,
  OfflineStripeGateway,
  StripeConfigError,
  redactSecrets,
  resolveCredential,
} from "./stripe-sync/stripe-gateway.js";
import type { ApplyResult } from "./stripe-sync/planner.js";
import type { StripeGateway } from "./stripe-sync/types.js";

const ROOT = findRepoRoot(import.meta.url);

/** GitHub Pages origin. `CNAME` in the repo root is the authority for this. */
const DEFAULT_BASE_URL = "https://www.clearglassinc.com";
const DEFAULT_REPOSITORY = "ClearGlassInc/ClearGlassIncorporated-Desmond";
const DEFAULT_CURRENCY = "cad";

export interface CliOptions {
  sources: string[];
  apply: boolean;
  live: boolean;
  deactivateOldPrices: boolean;
  checkImages: boolean;
  offline: boolean;
  baseUrl: string;
  repository: string;
  currency: string;
  reportPath: string;
  json: boolean;
  help: boolean;
  /** Refuse to proceed unless the computed plan still hashes to this value. */
  expectPlanHash?: string;
}

export class UsageError extends Error {}

/** Parse argv. Unknown flags are a hard error — a typo'd `--aply` must not silently dry-run. */
export function parseArgs(argv: string[], env: NodeJS.ProcessEnv = {}): CliOptions {
  const options: CliOptions = {
    sources: [],
    apply: false,
    live: false,
    deactivateOldPrices: false,
    checkImages: false,
    offline: false,
    baseUrl: env.SITE_BASE_URL?.trim() || DEFAULT_BASE_URL,
    repository: env.GITHUB_REPOSITORY?.trim() || DEFAULT_REPOSITORY,
    currency: (env.DEFAULT_CURRENCY?.trim() || DEFAULT_CURRENCY).toLowerCase(),
    reportPath: env.SYNC_REPORT_PATH?.trim() || "stripe-sync-report.json",
    json: false,
    help: false,
  };

  for (let index = 0; index < argv.length; index += 1) {
    const argument = argv[index] as string;
    const next = (): string => {
      const value = argv[index + 1];
      if (value === undefined || value.startsWith("--")) {
        throw new UsageError(`${argument} needs a value`);
      }
      index += 1;
      return value;
    };

    switch (argument) {
      case "--source":
        options.sources.push(...next().split(",").map((part) => part.trim()).filter(Boolean));
        break;
      case "--apply":
        options.apply = true;
        break;
      case "--dry-run":
        options.apply = false;
        break;
      case "--live":
        options.live = true;
        break;
      case "--deactivate-old-prices":
        options.deactivateOldPrices = true;
        break;
      case "--check-images":
        options.checkImages = true;
        break;
      case "--offline":
        options.offline = true;
        break;
      case "--base-url":
        options.baseUrl = next().replace(/\/+$/, "");
        break;
      case "--repository":
        options.repository = next();
        break;
      case "--currency":
        options.currency = next().toLowerCase();
        break;
      case "--report":
        options.reportPath = next();
        break;
      case "--expect-plan-hash":
        options.expectPlanHash = next().trim().toLowerCase();
        break;
      case "--json":
        options.json = true;
        break;
      case "--help":
      case "-h":
        options.help = true;
        break;
      default:
        throw new UsageError(`unknown option ${JSON.stringify(argument)} (try --help)`);
    }
  }

  if (options.sources.length === 0) options.sources = defaultAdapterNames();
  if (options.sources.includes("all")) options.sources = adapterNames();

  const unknown = options.sources.filter((name) => !adapterNames().includes(name));
  if (unknown.length > 0) {
    throw new UsageError(
      `unknown --source ${unknown.join(", ")}; available: ${adapterNames().join(", ")}, all`,
    );
  }
  if (options.offline && (options.apply || options.live)) {
    throw new UsageError("--offline consults no Stripe account, so it cannot be combined with --apply or --live");
  }
  // --check-images makes HEAD requests, which would break the no-network
  // promise that is the whole point of --offline.
  if (options.offline && options.checkImages) {
    throw new UsageError("--offline makes no network requests, so it cannot be combined with --check-images");
  }
  return options;
}

function usage(): string {
  const sources = ADAPTERS.map(
    (adapter) =>
      `    ${adapter.name.padEnd(12)} ${adapter.file}\n` +
      `    ${" ".repeat(12)} ${adapter.description}${adapter.optIn ? " (opt-in)" : ""}`,
  ).join("\n\n");
  return `sync-stripe-products — publish the site catalogue to Stripe

Usage: npm run sync:stripe -- [options]

Options:
  --source <name>            Source to read; repeatable or comma-separated.
                             Default: ${defaultAdapterNames().join(", ")}. Use "all" for every source.
  --apply                    Write to Stripe. Without it the run is a dry run.
  --live                     Target live mode. Also requires ALLOW_STRIPE_LIVE_SYNC=true
                             and a live secret key. All three, or the run is refused.
  --deactivate-old-prices    Deactivate Prices superseded by a new amount.
                             Off by default; superseded Prices stay active.
  --check-images             HEAD every image URL to confirm Stripe can fetch it.
  --offline                  Plan against an empty account with no credential and no
                             network. Use it to review the mapping before holding a key.
  --base-url <url>           GitHub Pages origin. Default: ${DEFAULT_BASE_URL}
  --repository <owner/repo>  Written to Stripe metadata. Default: ${DEFAULT_REPOSITORY}
  --currency <iso>           Fallback currency for sources without one. Default: ${DEFAULT_CURRENCY}
  --report <path>            JSON report path. Default: stripe-sync-report.json
  --expect-plan-hash <hex>   Refuse to run unless the plan still hashes to this
                             value. Binds an approval to the plan that was reviewed.
  --json                     Print the report to stdout instead of the table.
  -h, --help                 This text.

Environment:
  STRIPE_SECRET_KEY          Required for anything that talks to Stripe.
  ALLOW_STRIPE_LIVE_SYNC     Must be exactly "true" for --live.

Sources:

${sources}

Nothing is ever deleted. A product that leaves the site is reported, not archived.
`;
}

export interface RunDependencies {
  /** Injected by the tests; production builds one from the resolved credential. */
  gatewayFactory?: (options: CliOptions) => Promise<{ gateway: StripeGateway; mode: "test" | "live" }>;
  log?: (line: string) => void;
  errorLog?: (line: string) => void;
  env?: NodeJS.ProcessEnv;
  root?: string;
}

/** Run the sync. Returns the process exit code rather than calling `process.exit`. */
export async function run(argv: string[], dependencies: RunDependencies = {}): Promise<number> {
  const env = dependencies.env ?? process.env;
  const log = dependencies.log ?? ((line: string) => console.log(line));
  const errorLog = dependencies.errorLog ?? ((line: string) => console.error(line));
  const root = dependencies.root ?? ROOT;
  const startedAt = new Date().toISOString();

  let options: CliOptions;
  try {
    options = parseArgs(argv, env);
  } catch (error) {
    errorLog(redactSecrets((error as Error).message));
    errorLog("");
    errorLog(usage());
    return 2;
  }
  if (options.help) {
    log(usage());
    return 0;
  }

  /* 1 ── read the catalogue ------------------------------------------------ */
  const { products, issues } = collectProducts(options.sources, {
    root,
    baseUrl: options.baseUrl,
    repository: options.repository,
    defaultCurrency: options.currency,
  });

  if (options.checkImages) {
    const urls = [...new Set(products.flatMap((product) => product.images))];
    for (const failure of await verifyImagesReachable(urls)) {
      const owner = products.find((product) => product.images.includes(failure.url));
      issues.push({
        sourceId: owner?.sourceId ?? "(unknown)",
        adapter: owner?.adapter ?? "(unknown)",
        field: "image",
        message: `${failure.url}: ${failure.reason}`,
        severity: "warning",
      });
    }
  }

  const blocking = issues.filter((issue) => issue.severity === "error");

  /* 2 ── report data problems before touching Stripe ----------------------- */
  if (issues.length > 0) {
    errorLog("");
    errorLog("Products needing attention before they can be sold through Stripe:");
    for (const issue of issues) {
      const label = issue.severity === "error" ? "WITHHELD" : "warning ";
      errorLog(`  ${label}  ${issue.sourceId} [${issue.field}] ${redactSecrets(issue.message)}`);
    }
  }

  /* 3 ── connect --------------------------------------------------------- */
  let gateway: StripeGateway;
  let mode: "test" | "live";
  try {
    if (dependencies.gatewayFactory) {
      ({ gateway, mode } = await dependencies.gatewayFactory(options));
    } else if (options.offline) {
      gateway = new OfflineStripeGateway();
      mode = "test";
    } else {
      const credential = resolveCredential({ env, live: options.live });
      gateway = new LiveStripeGateway(credential.key);
      mode = credential.mode;
    }
  } catch (error) {
    if (error instanceof StripeConfigError) {
      errorLog("");
      errorLog(`Refusing to run: ${redactSecrets(error.message)}`);
      return 2;
    }
    throw error;
  }

  /* 4 ── plan ------------------------------------------------------------- */
  const planOptions = {
    repository: options.repository,
    deactivateOldPrices: options.deactivateOldPrices,
    adapters: options.sources,
  };
  const plan = await buildPlan(gateway, products, planOptions);
  const rows = planRows(plan, options.deactivateOldPrices);
  const hash = planHash(plan);

  for (const entry of plan.blocked) {
    errorLog(`BLOCKED  ${entry.sourceId}: ${redactSecrets(entry.reason)}`);
  }

  if (!options.json) {
    log("");
    log(
      `Stripe ${mode} mode · ${options.offline ? "OFFLINE PLAN" : options.apply ? "APPLY" : "DRY RUN"} · ` +
        `sources: ${options.sources.join(", ")} · ${products.length} product(s) parsed`,
    );
    if (options.offline) {
      log(
        "No Stripe account was consulted. Every product is shown as it would appear on a first sync; " +
          "run without --offline against a test key to see what already exists.",
      );
    }
    log("");
    log(renderTable(rows));
    log("");
    log(`Plan hash: ${hash}`);
  }

  // Bind an approval to the plan it was granted for. If the catalogue or the
  // Stripe account moved between the review and this run, the approval no longer
  // describes what would happen, so the run stops rather than applying changes
  // nobody signed off on.
  if (options.expectPlanHash && options.expectPlanHash !== hash) {
    errorLog(
      `\nRefusing to run: the plan changed since it was approved.\n` +
        `  approved: ${options.expectPlanHash}\n  current:  ${hash}\n` +
        "Re-run the planning step, review the new plan, and approve that one.",
    );
    return 2;
  }

  /* 5 ── apply, or explain why not ---------------------------------------- */
  let applied: ApplyResult | undefined;
  if (options.apply) {
    if (plan.duplicates.length > 0) {
      errorLog(
        "Refusing to apply: several Stripe products share a source_id. Merge them first — " +
          plan.duplicates.map((duplicate) => duplicate.sourceId).join(", "),
      );
      return 2;
    }
    applied = await applyPlan(gateway, plan, planOptions);
    for (const failure of applied.failures) {
      errorLog(`FAILED ${failure.sourceId}: ${redactSecrets(failure.message)}`);
    }
    if (!options.json) {
      log(
        `Applied: ${applied.createdProducts} product(s) created, ${applied.updatedProducts} updated, ` +
          `${applied.createdPrices} price(s) created, ${applied.reusedPrices} reused, ` +
          `${applied.deactivatedPrices} deactivated.`,
      );
    }
  } else if (!options.json) {
    log("Dry run — nothing was written to Stripe. Re-run with --apply to make these changes.");
  }

  /* 6 ── report ----------------------------------------------------------- */
  const report = buildReport({
    mode,
    applied: options.apply,
    sources: options.sources,
    baseUrl: options.baseUrl,
    repository: options.repository,
    products,
    issues,
    rows,
    planHash: hash,
    blocked: plan.blocked,
    ...(applied ? { apply: applied } : {}),
    startedAt,
    finishedAt: new Date().toISOString(),
  });

  // Redact the serialised document, not just the console lines. Issue and
  // failure messages carry text straight from Stripe, which occasionally quotes
  // the request that produced an error — and this file is uploaded as a CI
  // artifact, so it outlives the log.
  const serialized = `${redactSecrets(JSON.stringify(report, null, 2))}\n`;
  writeFileSync(path.resolve(root, options.reportPath), serialized, "utf8");
  if (options.json) log(serialized.trimEnd());
  else log(`Report written to ${options.reportPath}`);

  const failures = applied?.failures.length ?? 0;
  if (failures > 0 || blocking.length > 0 || plan.blocked.length > 0) {
    errorLog(
      `\n${blocking.length} product(s) withheld for manual correction, ` +
        `${plan.blocked.length} blocked by a Stripe mismatch, ${failures} failed during apply.`,
    );
    return 1;
  }
  return 0;
}

/* Only self-execute when invoked directly, so the tests can import `run`. */
const invokedDirectly =
  process.argv[1] !== undefined &&
  path.resolve(process.argv[1]).replace(/\.(ts|js)$/, "") ===
    fileURLToPath(import.meta.url).replace(/\.(ts|js)$/, "");

if (invokedDirectly) {
  run(process.argv.slice(2))
    .then((code) => {
      process.exitCode = code;
    })
    .catch((error: unknown) => {
      console.error(redactSecrets((error as Error).stack ?? String(error)));
      process.exitCode = 1;
    });
}

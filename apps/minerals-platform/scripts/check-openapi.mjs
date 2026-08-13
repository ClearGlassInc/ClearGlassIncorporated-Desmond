import { readFile } from "node:fs/promises";

const text = await readFile(new URL("../openapi.yaml", import.meta.url), "utf8");
const required = [
  "openapi: 3.1.0",
  "/health:",
  "/search:",
  "/minerals:",
  "/projects:",
  "/mines:",
  "/companies:",
  "/map/features:",
  "/markets:",
  "/markets/analytics:",
  "/trade:",
  "/supply-chains:",
  "/exploration:",
  "/risk:",
  "/scenarios/supply-disruption:",
  "/provenance:",
  "/provenance/{id}/review:",
  "/alerts:",
  "/alerts/{id}:",
  "/alerts/{id}/deliver:",
  "/watchlists:",
  "/watchlists/{id}:",
  "/reports:",
  "/reports/{id}:",
  "/sources:",
  "/ingestion:",
  "/ingestion/webhook/{sourceKey}:",
  "/exports:",
  "/saved-views:",
  "/analyst:",
  "/stream:",
  "/admin/members:",
  "/admin/audit:",
  "/admin/review-queue:"
];
const missing = required.filter((needle) => !text.includes(needle));
if (missing.length) {
  console.error(`OpenAPI contract missing: ${missing.join(", ")}`);
  process.exit(1);
}
console.log(`OpenAPI contract check passed (${required.length - 1} required resource paths).`);

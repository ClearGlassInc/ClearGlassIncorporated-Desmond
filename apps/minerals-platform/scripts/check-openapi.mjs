import { readFile } from "node:fs/promises";

const text = await readFile(new URL("../openapi.yaml", import.meta.url), "utf8");
const required = ["openapi: 3.1.0", "/search:", "/map/features:", "/minerals:", "/projects:", "/markets:", "/trade:", "/risk:", "/alerts:", "/watchlists:", "/reports:", "/sources:", "/ingestion:", "/exports:"];
const missing = required.filter((needle) => !text.includes(needle));
if (missing.length) {
  console.error(`OpenAPI contract missing: ${missing.join(", ")}`);
  process.exit(1);
}
console.log(`OpenAPI contract check passed (${required.length - 1} required resource paths).`);

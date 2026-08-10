import { readFileSync, statSync } from "node:fs";
import { gzipSync } from "node:zlib";
import { spawnSync } from "node:child_process";

const JS_PATH = "assets/js/cinematic-motion.js";
const CSS_PATH = "assets/css/cinematic-motion.css";
const PLATFORM_PATH = "platform.js";
const INDEX_PATH = "index.html";

const js = readFileSync(JS_PATH, "utf8");
const css = readFileSync(CSS_PATH, "utf8");
const platform = readFileSync(PLATFORM_PATH, "utf8");
const index = readFileSync(INDEX_PATH, "utf8");

const failures = [];
const checks = [];
function requireCheck(name, condition, detail) {
  checks.push({ name, ok: Boolean(condition), detail });
  if (!condition) failures.push(`${name}: ${detail}`);
}

const syntax = spawnSync(process.execPath, ["--check", JS_PATH], { encoding: "utf8" });
requireCheck("runtime syntax", syntax.status === 0, syntax.stderr.trim() || "node --check failed");

const rawJs = statSync(JS_PATH).size;
const rawCss = statSync(CSS_PATH).size;
const gzipJs = gzipSync(Buffer.from(js)).length;
const gzipCss = gzipSync(Buffer.from(css)).length;
requireCheck("JS raw budget", rawJs <= 26000, `${rawJs} bytes > 26000`);
requireCheck("CSS raw budget", rawCss <= 26000, `${rawCss} bytes > 26000`);
requireCheck("combined gzip budget", gzipJs + gzipCss <= 12000, `${gzipJs + gzipCss} bytes > 12000`);

requireCheck("platform JS loader", platform.includes('/assets/js/cinematic-motion.js'), "platform.js must load cinematic runtime");
requireCheck("platform CSS loader", platform.includes('/assets/css/cinematic-motion.css'), "platform.js must load cinematic stylesheet");
requireCheck("homepage hero target", /id=["']hero["']/.test(index), "index.html must expose #hero");

for (const label of ["ATTENTION","TRUST","CONVERSION","PERFORMANCE","SEARCH","AUTOMATION","SECURITY","LEARNING"]) {
  requireCheck(`capability ${label}`, js.includes(`[\"${label}\"`) || js.includes(`["${label}"`), `missing ${label} capability`);
}

requireCheck("reduced-motion gate", js.includes("prefers-reduced-motion: reduce"), "runtime must honor reduced motion");
requireCheck("save-data gate", js.includes("navigator.connection") && js.includes("saveData"), "runtime must honor Save-Data");
requireCheck("low-memory gate", js.includes("navigator.deviceMemory"), "runtime must detect constrained devices");
requireCheck("offscreen pause", js.includes("IntersectionObserver") && js.includes("cg-motion-live"), "continuous motion must pause offscreen");
requireCheck("page visibility pause", js.includes("visibilitychange"), "continuous motion must pause in background tabs");
requireCheck("frame cap", js.includes("1000 / 24") && js.includes("1000 / 12"), "runtime must cap normal/low-power update rates");
requireCheck("rollback switch", js.includes("cg_motion") && js.includes("cg-motion-disabled"), "runtime must expose emergency motion kill switch");
requireCheck("LCP observer", js.includes('type: "largest-contentful-paint"'), "runtime must observe LCP locally");
requireCheck("CLS observer", js.includes('type: "layout-shift"'), "runtime must observe CLS locally");
requireCheck("INP observer", js.includes('type: "event"') && js.includes("interactionId"), "runtime must observe interaction latency locally");
requireCheck("FPS instrumentation", js.includes("measuredFps") && js.includes("motionFps"), "runtime must measure animation cadence");
requireCheck("no telemetry exfiltration", !/sendBeacon\s*\(|fetch\s*\([^)]*metrics|XMLHttpRequest/.test(js), "performance measurements must remain browser-local");

for (const token of ["prefers-reduced-motion", ".cg-low-power", "animation-play-state: paused"]) {
  requireCheck(`CSS invariant ${token}`, css.includes(token), `missing CSS invariant: ${token}`);
}

console.log("ClearGlass cinematic motion quality gate");
console.log(`  JS:  ${rawJs} B raw / ${gzipJs} B gzip`);
console.log(`  CSS: ${rawCss} B raw / ${gzipCss} B gzip`);
console.log(`  Combined gzip: ${gzipJs + gzipCss} B / 12000 B budget`);
for (const check of checks) console.log(`  ${check.ok ? "PASS" : "FAIL"}  ${check.name}`);

if (failures.length) {
  console.error("\nMotion quality gate failed:\n- " + failures.join("\n- "));
  process.exit(1);
}
console.log("\nAll cinematic motion invariants passed.");

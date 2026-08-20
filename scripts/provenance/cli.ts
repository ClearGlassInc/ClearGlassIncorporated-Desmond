// Copyright (c) 2024-2026 ClearGlass Inc. All Rights Reserved.
// Proprietary and confidential. See LICENSE for terms.
import { readFileSync, writeFileSync } from "node:fs";
import { embedWatermark, extractWatermarks, stripWatermarks, type WatermarkPayload } from "./watermark.js";

function usage(): never {
  console.error(`Usage:
  npm run provenance -- embed <input> <output> <content-id>
  npm run provenance -- detect <input>
  npm run provenance -- strip <input> <output>

Environment:
  CG_WATERMARK_SECRET  Required for embed; optional for detect verification.
`);
  process.exit(2);
}

const [command, ...args] = process.argv.slice(2);

if (command === "embed") {
  const [input, output, contentId] = args;
  if (!input || !output || !contentId) usage();
  const secret = process.env.CG_WATERMARK_SECRET;
  if (!secret) throw new Error("CG_WATERMARK_SECRET is required for signed embedding");
  const payload: WatermarkPayload = {
    contentId,
    origin: "https://www.clearglassinc.com",
    issuedAt: new Date().toISOString(),
  };
  const source = readFileSync(input, "utf8");
  writeFileSync(output, embedWatermark(source, payload, secret), "utf8");
  console.log(JSON.stringify({ ok: true, action: "embed", input, output, payload }, null, 2));
} else if (command === "detect") {
  const [input] = args;
  if (!input) usage();
  const source = readFileSync(input, "utf8");
  const found = extractWatermarks(source, process.env.CG_WATERMARK_SECRET);
  console.log(JSON.stringify({ ok: true, action: "detect", input, found }, null, 2));
  if (found.length === 0) process.exitCode = 1;
  else if (process.env.CG_WATERMARK_SECRET && !found.some((item) => item.verified)) process.exitCode = 3;
} else if (command === "strip") {
  const [input, output] = args;
  if (!input || !output) usage();
  writeFileSync(output, stripWatermarks(readFileSync(input, "utf8")), "utf8");
  console.log(JSON.stringify({ ok: true, action: "strip", input, output }, null, 2));
} else {
  usage();
}

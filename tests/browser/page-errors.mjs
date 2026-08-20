/* Loads pages in a real browser and fails on any uncaught runtime error.

   The static gates parse HTML; they cannot tell whether a page's JavaScript
   actually runs. Three defects sat in `main` that every existing check passed
   over, because each one is only observable once a browser evaluates the
   script:

     artemis-os.html   TypeError: assigning to the read-only clientWidth, which
                       threw under 'use strict' and killed the particle layer
     artemis-iv.html   SyntaxError: duplicate `const map` in one block
     counter-uas-…     SyntaxError: one closing paren too many

   A SyntaxError takes the whole <script> with it, so a page can look correct,
   validate as HTML, pass the link and metadata audits, and still have none of
   its behaviour. That is what this catches.

     node tests/browser/page-errors.mjs index.html pricing.html
     node tests/browser/page-errors.mjs $(ls *.html)

   Pages load with ?skipboot=1, the site's documented bypass for the first-visit
   boot loader; without it the harness measures /loader.html instead.
*/
import { chromium } from 'playwright';
import http from 'node:http';
import fs from 'node:fs';
import path from 'node:path';

const ROOT = '/home/user/ClearGlassIncorporated-Desmond';
const TYPES = { '.html': 'text/html', '.js': 'text/javascript', '.css': 'text/css',
  '.png': 'image/png', '.webp': 'image/webp', '.jpg': 'image/jpeg', '.svg': 'image/svg+xml',
  '.json': 'application/json', '.ico': 'image/x-icon', '.xml': 'application/xml',
  '.mp4': 'video/mp4', '.woff2': 'font/woff2', '.woff': 'font/woff' };

const server = http.createServer((req, res) => {
  let p = decodeURIComponent(req.url.split('?')[0]);
  if (p.endsWith('/')) p += 'index.html';
  const file = path.join(ROOT, p);
  if (!file.startsWith(ROOT) || !fs.existsSync(file) || fs.statSync(file).isDirectory()) {
    res.writeHead(404); return res.end('not found');
  }
  res.writeHead(200, { 'content-type': TYPES[path.extname(file)] || 'application/octet-stream' });
  fs.createReadStream(file).pipe(res);
});

await new Promise(r => server.listen(8096, r));
const browser = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium-1194/chrome-linux/chrome' });

const targets = process.argv.slice(2);
if (!targets.length) {
  console.error('usage: node tests/browser/page-errors.mjs <page.html> [...]');
  await browser.close(); server.close();
  process.exit(2);
}

let failed = 0;
for (const target of targets) {
  const page = await browser.newPage({ viewport: { width: 1280, height: 800 } });
  const errors = [];
  page.on('pageerror', e => errors.push(String(e).split('\n')[0].slice(0, 160)));

  // A page that will not load is a failure for that page, not an abort of the
  // sweep — one bad argument must not leave every later page unchecked.
  let reached = false;
  try {
    const res = await page.goto(`http://localhost:8096/${target}?skipboot=1`,
      { waitUntil: 'domcontentloaded', timeout: 20000 });
    reached = !!res && res.ok();
    if (reached) await page.waitForTimeout(700); // let deferred boot scripts run
  } catch { /* reported below */ }

  if (!reached) {
    failed++;
    console.log(`LOAD  ${target}  did not load (missing file or non-2xx)`);
  } else if (errors.length) {
    failed++;
    console.log(`ERR   ${target}`);
    for (const e of [...new Set(errors)]) console.log(`        ${e}`);
  }
  await page.close();
}

await browser.close();
server.close();
console.log(`\n${targets.length - failed}/${targets.length} pages loaded with no uncaught error`);
process.exit(failed ? 1 : 0);

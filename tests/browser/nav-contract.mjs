/* Real-browser verification of the global navigation contract added to nav.js.
   Serves the site statically and drives Chromium through the keyboard paths. */
import { chromium } from 'playwright';
import http from 'node:http';
import fs from 'node:fs';
import path from 'node:path';

const ROOT = '/home/user/ClearGlassIncorporated-Desmond';
const TYPES = { '.html': 'text/html', '.js': 'text/javascript', '.css': 'text/css',
  '.png': 'image/png', '.webp': 'image/webp', '.jpg': 'image/jpeg', '.svg': 'image/svg+xml',
  '.json': 'application/json', '.ico': 'image/x-icon', '.xml': 'application/xml' };

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

const results = [];
const ok = (name, cond, detail = '') => results.push({ name, pass: !!cond, detail });

await new Promise(r => server.listen(8099, r));
const browser = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium-1194/chrome-linux/chrome' });
const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });

const consoleErrors = [];
page.on('pageerror', e => consoleErrors.push(String(e)));

// ?skipboot=1 is the site's documented bypass for the first-visit boot loader.
// Without it the harness measures /loader.html instead of the page under test.
const TARGET = process.argv[2] || 'products.html';
await page.goto(`http://localhost:8099/${TARGET}?skipboot=1`, { waitUntil: 'networkidle' });
await page.waitForSelector('#cg-global-nav', { timeout: 10000 });

// 1. Skip link exists, is the first tab stop, and targets a real <main>.
const skip = page.locator('.cg-skip');
ok('skip link injected', await skip.count() === 1);
await page.keyboard.press('Tab');
ok('skip link is first tab stop', await skip.evaluate(el => el === document.activeElement).catch(() => false));
const skipHref = await skip.getAttribute('href');
ok('skip link targets a real element', skipHref && await page.locator(skipHref).count() === 1, skipHref);

// 2. Active route is marked exactly once.
const current = await page.locator('#cg-global-nav a[aria-current="page"]').count();
ok('exactly one aria-current in nav', current === 1, `found ${current}`);

// 3. Closed product menu must not hold focusable links.
// visibility:hidden elements still report client rects, so reachability has to
// be measured with checkVisibility — that is what the tab order actually uses.
const hiddenFocusable = await page.evaluate(() => {
  const menu = document.getElementById('cg-products-menu');
  if (!menu) return -1;
  return [...menu.querySelectorAll('a')]
    .filter(a => a.checkVisibility({ visibilityProperty: true, opacityProperty: true })).length;
});
ok('closed menu removes links from tab order', hiddenFocusable === 0, `${hiddenFocusable} reachable`);

// 4. Disclosure button opens the menu and Escape closes it, restoring focus.
const caret = page.locator('.cg-dropcaret');
ok('products disclosure button exists', await caret.count() === 1);
await caret.click();
ok('menu opens via button', await caret.getAttribute('aria-expanded') === 'true');
await page.keyboard.press('Escape');
ok('Escape closes menu', await caret.getAttribute('aria-expanded') === 'false');
ok('Escape restores focus to trigger', await caret.evaluate(el => el === document.activeElement));

// 5. Command palette: opens on Ctrl+K, filters, and Escape restores focus.
await page.keyboard.press('Control+k');
await page.waitForSelector('.cg-palette:not([hidden])', { timeout: 3000 });
ok('palette opens on Ctrl+K', await page.locator('.cg-palette:not([hidden])').count() === 1);
ok('palette focuses its input', await page.locator('.cg-palette-input').evaluate(el => el === document.activeElement));
ok('palette is a modal dialog', await page.locator('.cg-palette [role="dialog"][aria-modal="true"]').count() === 1);
await page.locator('.cg-palette-input').fill('aegis');
const hits = await page.locator('.cg-palette-list a').count();
ok('palette filters results', hits > 0 && hits < 20, `${hits} hits for "aegis"`);
await page.keyboard.press('Escape');
ok('Escape closes palette', await page.locator('.cg-palette[hidden]').count() === 1);

// 6. Mobile drawer traps focus and closes on Escape.
await page.setViewportSize({ width: 390, height: 844 });
const toggle = page.locator('.cg-toggle');
await toggle.click();
ok('drawer opens', await toggle.getAttribute('aria-expanded') === 'true');
ok('drawer moves focus inside', await page.evaluate(() => !!document.getElementById('cg-mobile-nav')?.contains(document.activeElement)));
for (let i = 0; i < 60; i++) await page.keyboard.press('Tab');
ok('focus stays trapped in drawer', await page.evaluate(() => !!document.getElementById('cg-mobile-nav')?.contains(document.activeElement)));
await page.keyboard.press('Escape');
ok('Escape closes drawer', await toggle.getAttribute('aria-expanded') === 'false');
ok('drawer restores focus to toggle', await toggle.evaluate(el => el === document.activeElement));

// 7. No horizontal overflow on mobile, and no page errors.
const overflow = await page.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth);
ok('no horizontal overflow at 390px', overflow <= 1, `${overflow}px`);
ok('no uncaught page errors', consoleErrors.length === 0, consoleErrors.join(' | ').slice(0, 300));

await browser.close();
server.close();

let failed = 0;
for (const r of results) {
  if (!r.pass) failed++;
  console.log(`${r.pass ? 'PASS' : 'FAIL'}  ${r.name}${r.detail ? '  [' + r.detail + ']' : ''}`);
}
console.log(`\n${results.length - failed}/${results.length} passed on ${TARGET}`);
process.exit(failed ? 1 : 0);

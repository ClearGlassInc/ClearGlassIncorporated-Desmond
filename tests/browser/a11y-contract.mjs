/* Verifies the keyboard bypass contract (WCAG 2.4.1) holds on every page,
   including the ~35 that suppress nav.js in favour of control-surface.js and
   the 39 authored without a <main> landmark.

   The contract is "the first Tab stop is a working bypass link", not "the page
   loaded cg-a11y.js". Pages listed in EXEMPT in tools/design_system.py author
   their own link — index.html ships `.skip-link` because it is the design
   source of truth — and an earlier revision of this file hard-coded `.cg-skip`,
   so it reported FAIL for a homepage that satisfies the contract. A gate that
   fails correct code is the same defect as one that passes broken code. */
import { chromium } from 'playwright';
import http from 'node:http'; import fs from 'node:fs'; import path from 'node:path';
const ROOT='/home/user/ClearGlassIncorporated-Desmond';
const T={'.html':'text/html','.js':'text/javascript','.css':'text/css','.png':'image/png','.webp':'image/webp','.jpg':'image/jpeg','.svg':'image/svg+xml','.json':'application/json','.ico':'image/x-icon','.xml':'application/xml','.mp4':'video/mp4'};
const s=http.createServer((q,r)=>{let p=decodeURIComponent(q.url.split('?')[0]);if(p.endsWith('/'))p+='index.html';const f=path.join(ROOT,p);if(!fs.existsSync(f)||fs.statSync(f).isDirectory()){r.writeHead(404);return r.end()}r.writeHead(200,{'content-type':T[path.extname(f)]||'application/octet-stream'});fs.createReadStream(f).pipe(r)});
await new Promise(r=>s.listen(8093,r));
const b=await chromium.launch({executablePath:'/opt/pw-browsers/chromium-1194/chrome-linux/chrome'});
const targets = process.argv.slice(2);
let failed=0;
for (const t of targets){
  const pg=await b.newPage({viewport:{width:1280,height:800}});
  const errs=[]; pg.on('pageerror',e=>errs.push(String(e).slice(0,120)));
  // A page that will not load is a FAIL for that page, not an abort. Letting
  // the navigation reject killed the sweep on the first bad argument and left
  // every page after it unchecked, with no summary to act on.
  const reached = await pg.goto(`http://localhost:8093/${t}?skipboot=1`,{waitUntil:'domcontentloaded'})
    .then(res=>res && res.ok(), ()=>false);
  if(!reached){
    failed++;
    console.log(`FAIL  ${t}  did not load (missing file or non-2xx from the harness server)`);
    await pg.close();
    continue;
  }
  await pg.waitForSelector('.cg-skip, .skip-link',{timeout:8000}).catch(()=>{});

  const handle = await pg.evaluateHandle(()=>{
    const FOCUSABLE='a[href],button,input:not([type="hidden"]),select,textarea,[tabindex]:not([tabindex="-1"])';
    // Either shared or page-authored link counts; so does an unclassed anchor
    // that happens to be the first Tab stop and points into the page.
    const first=document.querySelector(FOCUSABLE);
    return document.querySelector('.cg-skip, .skip-link')
      || (first && first.matches('a[href^="#"]') ? first : null);
  });
  const r = await pg.evaluate((skip)=>({
    skip: !!skip,
    target: !!(skip && skip.getAttribute('href') && document.querySelector(skip.getAttribute('href'))),
    landmark: !!document.querySelector("main, [role='main']"),
    current: document.querySelectorAll("a[aria-current='page']").length,
  }), handle);

  await pg.keyboard.press('Tab');
  const firstTab = await pg.evaluate((skip)=>!!skip && document.activeElement===skip, handle);

  // A bypass link the keyboard user cannot see is not a bypass link. Both
  // implementations reveal it with a transform transition, so poll until it is
  // on screen and only give up at a deadline. Waiting a fixed interval, or
  // waiting for the rect to stop moving, both read intermittently: before the
  // transition starts the rect is already still, at the hidden position.
  const visible = firstTab && await pg.evaluate((skip)=>new Promise(done=>{
    const deadline=performance.now()+2000;
    const tick=()=>{
      const box=skip.getBoundingClientRect();
      if(box.top>=0 && box.bottom<=innerHeight && box.width>0 && box.height>0) return done(true);
      if(performance.now()>deadline) return done(false);
      requestAnimationFrame(tick);
    };
    requestAnimationFrame(tick);
  }), handle).catch(()=>false);
  await handle.dispose();

  // The bypass link (WCAG 2.4.1) is the contract. A missing <main> landmark is
  // reported but does not fail the gate — it is a markup follow-up tracked in
  // DESIGN_SYSTEM_AUDIT.md, not something this script should fake.
  const pass = r.skip && r.target && firstTab && visible && errs.length===0;
  if(!pass) failed++;
  console.log(`${pass?'PASS':'FAIL'}  ${t}  skip=${r.skip} target=${r.target} landmark=${r.landmark} firstTab=${firstTab} shown=${visible} aria-current=${r.current}${errs.length?' ERR:'+errs[0]:''}`);
  await pg.close();
}
await b.close(); s.close();
console.log(`\n${targets.length-failed}/${targets.length} pages satisfy the keyboard contract`);
process.exit(failed?1:0);

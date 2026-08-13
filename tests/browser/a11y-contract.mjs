/* Verifies the shared keyboard contract (cg-a11y.js) holds on every page,
   including the ~35 that suppress nav.js in favour of control-surface.js and
   the 39 authored without a <main> landmark. */
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
  await pg.goto(`http://localhost:8093/${t}?skipboot=1`,{waitUntil:'domcontentloaded'});
  await pg.waitForSelector('.cg-skip',{timeout:8000}).catch(()=>{});
  const r = await pg.evaluate(()=>{
    const skip=document.querySelector('.cg-skip');
    const target=skip?document.querySelector(skip.getAttribute('href')):null;
    return {skip:!!skip, target:!!target,
            landmark: !!document.querySelector("main, [role='main']"),
            current: document.querySelectorAll("a[aria-current='page']").length};
  });
  await pg.keyboard.press('Tab');
  const firstTab = await pg.evaluate(()=>document.activeElement?.className||'');
  // The bypass link (WCAG 2.4.1) is the contract. A missing <main> landmark is
  // reported but does not fail the gate — it is a markup follow-up tracked in
  // DESIGN_SYSTEM_AUDIT.md, not something this script should fake.
  const pass = r.skip && r.target && firstTab.includes('cg-skip') && errs.length===0;
  if(!pass) failed++;
  console.log(`${pass?'PASS':'FAIL'}  ${t}  skip=${r.skip} target=${r.target} landmark=${r.landmark} firstTab=${firstTab.includes('cg-skip')} aria-current=${r.current}${errs.length?' ERR:'+errs[0]:''}`);
  await pg.close();
}
await b.close(); s.close();
console.log(`\n${targets.length-failed}/${targets.length} pages satisfy the keyboard contract`);
process.exit(failed?1:0);

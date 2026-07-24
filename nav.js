/* ClearGlass · homepage-matched global navigation.
   Injects the ClearGlassInc. 2040 command bar — dark chrome / neon-purple glass,
   metallic medallion, complete product catalog, mobile menu, a Book a Security
   Engagement CTA, and live movement animations — on every static page without
   removing page content. Scoped to #cg-global-nav with !important so it wins
   over the global design-system stylesheet (assets/css/glass.css). */
(function () {
  "use strict";
  if (window.__cgNavLoaded) return;
  window.__cgNavLoaded = true;

  var PRODUCTS = [
    ["Artemis IV Core", "artemis-iv.html", "Tactical intelligence core", "🧭"],
    ["Artemis VI", "artemis.html", "Ontario intelligence deployment", "🛰"],
    ["Artemis OS", "artemis-os.html", "Intelligence operating system", "◎"],
    ["Artemis 2040", "artemis-2040.html", "Long-horizon intelligence", "◌"],
    ["Artemis Self-Evolving", "artemis-self-evolving-platform.html", "Governed improvement loop", "↻"],
    ["AI Cyber Intelligence", "artemis-ai-cyber-intelligence-platform.html", "Cyber intelligence platform", "✦"],
    ["AVALON · Artemis + Percival", "artemis-percival.html", "Unified fusion core", "⬣"],
    ["PERCIVAL OS", "percival-os.html", "Governed command center", "◐"],
    ["SENTINEL", "sentinel.html", "Live geospatial command", "◉"],
    ["GUARDIAN", "guardian.html", "Intelligence command interface", "🌐"],
    ["BLUEDESK", "bluedesk.html", "CISO risk console", "🛡"],
    ["BLUEDESK Mobile", "bluedesk-mobile.html", "Phone-first risk console", "▣"],
    ["ClearGlass NEXUS", "clearglass-nexus.html", "Full-spectrum intelligence", "◆"],
    ["NEXUS v12", "ClearGlass-NEXUS-v12-FINAL.html", "Flagship platform build", "◇"],
    ["Intelligence Command Surface", "intelligence-command-surface.html", "Unified operational picture", "🗺"],
    ["Intelligence Interface", "intelligence-interface.html", "Analyst workspace", "🖥"],
    ["Flowsint", "flowsint.html", "OSINT investigation graph", "🕸"],
    ["Network Flow Intelligence", "clearglass.html", "Living network structure", "⌁"],
    ["Ontario OSINT Deck", "Ontario-osint.html", "Regional OSINT control", "⌖"],
    ["Agent Mesh", "agentmesh.html", "Multi-agent orchestration", "⌗"],
    ["AI Operator Workspace", "ai-operator.html", "Human-in-the-loop ops", "🜂"],
    ["CONDUIT", "conduit.html", "Self-hosted automation", "⟿"],
    ["PostLoop", "postloop.html", "Content engine", "⟲"],
    ["AutoMap", "automap.html", "Architecture orchestration", "⌘"],
    ["Command Console", "command-console.html", "Cyber operations hub", "▤"],
    ["Event Control Surface", "saas-platform.html", "Event-driven operations", "◆"],
    ["Systems Console", "systems.html", "PERCIVAL operations", "▦"],
    ["Control Surface", "control-surface.html", "Live command dashboard", "▧"],
    ["CG OS", "CG-os.html", "ClearGlass command HUD", "◫"],
    ["CLEARSIGHT", "clearsight.html", "Edge-AI camera vision", "🎥"],
    ["ZEPHYR Air Control", "air-control.html", "Air systems control", "🜁"],
    ["Air Systems Control", "air-systems-control.html", "Airspace control surface", "✈"],
    ["ClearPulse", "clearpulse.html", "Healthcare intelligence", "📡"],
    ["ClearPulse Architecture", "clearpulse-architecture.html", "Forensic-AI whitepaper", "✚"],
    ["AEGIS", "aegis.html", "Legal process shield", "⚖"],
    ["ClearCounsel", "corporate-legal-advisor.html", "Corporate legal AI", "§"],
    ["ClearBank Legal AI", "banking-law-advisor.html", "Banking law intelligence", "🏦"],
    ["ClearTax AI", "tax.html", "Tax intelligence", "🧾"],
    ["Government Solutions", "government.html", "Public-sector systems", "🏛"],
    ["Counter-UAS OS", "counter-uas-commercialization-os.html", "Counter-drone platform", "◎"],
    ["Speed Vision AI", "traffic-enforcement.html", "Traffic enforcement AI", "◈"],
    ["SATS Digital Twin", "sats-digital-twin.html", "Transit simulation", "▱"],
    ["SMB Suite", "smb.html", "Small-business systems", "▰"],
    ["SMB Cyber Trust Kit", "smb-cyber-trust-kit.html", "Cyber resilience kit", "🔐"],
    ["Revenue Engine", "revenue-engine.html", "AI growth system", "💹"],
    ["Opal-Koboi Assets", "products/opal-koboi/index.html", "Product asset library", "✧"],
    ["Artemis IV Core · Asset", "products/opal-koboi/artemis-iv-core.html", "Product sheet", "🧭"],
    ["Artemis VI · Asset", "products/opal-koboi/artemis-vi.html", "Product sheet", "🛰"],
    ["Guardian · Asset", "products/opal-koboi/guardian.html", "Product sheet", "🌐"],
    ["Revenue Engine · Asset", "products/opal-koboi/revenue-engine.html", "Product sheet", "💹"],
    ["SMB Suite · Asset", "products/opal-koboi/smb-suite.html", "Product sheet", "▰"],
    ["Ultra Glass", "ultra-glass.html", "Glass intelligence UI", "◫"],
    ["ClearGlass Ultra", "clearglass-ultra.html", "See-through command UI", "◩"],
    ["Aurora Glass", "futuristic.html", "Design study", "✺"],
    ["Button System", "button-system.html", "Glass UI components", "◍"],
    ["Button Lab", "button-lab.html", "Control components", "◌"],
    ["Web Design & Development", "web-design.html", "Growth infrastructure", "💻"],
    ["Store", "store.html", "Book an engagement", "🛒"],
    ["Side Store", "side-store.html", "Electronics and components", "🔌"],

    ["Advanced Systems Catalog", "advanced-features-tools-systems.html", "Governed systems index", "▨"],
    ["Artemis Blue Team", "artemis-blue-team.html", "Defensive automation", "🛡"],
    ["Cyber Defense Console", "cyber-defense-console.html", "Command center brief", "▤"],
    ["Environmental Cyber Risk", "environmental-cyber-risk.html", "Environmental threat model", "♧"],
    ["Intelligence Platform", "intelligence-platform.html", "Full-stack intel architecture", "✦"],
    ["Intelligence Services", "intelligence.html", "Advisory and OSINT", "◈"],
    ["Percival Build", "percival-build.html", "Build architecture", "◐"],
    ["Procurement Legal Tech", "procurement-legal-tech.html", "Procurement integrity AI", "⚖"],
    ["Pricing", "pricing.html", "Plans and engagements", "₵"]
  ];
  var TOP = [["Vision","index.html#vision"],["Services","index.html#services"],["Products","index.html#products"],["Government","government.html"],["Insights","blog/"],["Contact","index.html#contact"]];
  var script = document.currentScript || Array.prototype.slice.call(document.scripts).filter(function(s){return /nav\.js(?:\?|$)/.test(s.src);}).pop();
  var base = script ? new URL('.', script.src).href : new URL('.', location.href).href;
  function href(path){ return /^https?:|^mailto:|^#/.test(path) ? path : new URL(path, base).href; }
  var here = (location.pathname.split('/').pop() || 'index.html').toLowerCase();
  function esc(s){return String(s).replace(/[&<>"]/g,function(c){return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c];});}
  var shield = '<span class="cg-shield" aria-hidden="true"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 2l7 3v6c0 4.4-3 8.4-7 9.5C8 19.4 5 15.4 5 11V5l7-3z"/><path d="M9 12l2 2 4-4"/></svg></span>';
  var css = "\
#cg-global-nav.cg-topnav{position:fixed;top:16px;left:50%;transform:translateX(-50%);width:min(1300px,calc(100% - 2rem));z-index:2147483000;height:80px;display:flex;align-items:center;justify-content:space-between;gap:12px;padding:0 16px 0 14px;border-radius:48px!important;background:linear-gradient(180deg,#332b62 0%,#1e1942 45%,#12102c 100%)!important;-webkit-backdrop-filter:blur(16px) saturate(1.4)!important;backdrop-filter:blur(16px) saturate(1.4)!important;border:1px solid rgba(190,175,255,.34)!important;box-shadow:0 0 0 1px rgba(120,90,220,.22),0 16px 48px rgba(70,30,150,.4),0 0 74px rgba(150,100,245,.28),inset 0 2px 1px rgba(255,255,255,.28),inset 0 -16px 36px rgba(0,0,0,.55)!important;font-family:'Urbanist',Inter,system-ui,sans-serif;overflow:visible;color:#eef0ff!important}\
#cg-global-nav.cg-topnav *{box-sizing:border-box}\
#cg-global-nav.cg-topnav::before{content:'';position:absolute;inset:-1px;border-radius:49px;padding:1.5px;background:linear-gradient(115deg,rgba(120,90,230,0) 18%,rgba(178,138,255,.95),rgba(96,196,255,.95),rgba(120,90,230,0) 82%);background-size:230% 100%;-webkit-mask:linear-gradient(#000 0 0) content-box,linear-gradient(#000 0 0);-webkit-mask-composite:xor;mask:linear-gradient(#000 0 0) content-box,linear-gradient(#000 0 0);mask-composite:exclude;pointer-events:none;animation:cgnRim 5.5s linear infinite;z-index:0}\
#cg-global-nav.cg-topnav::after{content:'';position:absolute;top:0;left:9%;right:9%;height:2px;border-radius:3px;background:linear-gradient(90deg,transparent,rgba(180,140,255,.15) 15%,rgba(205,165,255,.95) 45%,rgba(130,205,255,.95) 55%,rgba(180,140,255,.15) 85%,transparent);background-size:230% 100%;box-shadow:0 0 12px rgba(170,120,250,.8);pointer-events:none;animation:cgnRail 4.2s linear infinite;z-index:1}\
#cg-global-nav .cg-sheen{position:absolute;inset:0;border-radius:48px;overflow:hidden;pointer-events:none;z-index:0}\
#cg-global-nav .cg-sheen::before{content:'';position:absolute;top:-60%;left:-45%;width:38%;height:220%;transform:rotate(18deg);background:linear-gradient(90deg,transparent,rgba(205,185,255,.16),transparent);animation:cgnSheen 6.5s ease-in-out infinite}\
#cg-global-nav .cg-brand{display:flex;align-items:center;gap:15px;color:#eef0ff!important;text-decoration:none;position:relative;z-index:2}\
#cg-global-nav .cg-mark{width:56px;height:56px;border-radius:50%;flex-shrink:0;position:relative;display:grid;place-items:center;padding:3px;background:conic-gradient(from 210deg,#eef0f6,#a9aec2,#6b7086,#c9cdda,#eef0f6);box-shadow:0 0 0 2px rgba(150,110,240,.55),0 0 22px rgba(150,110,240,.6),inset 0 1px 3px rgba(255,255,255,.85);overflow:visible;animation:cgnMarkGlow 3.4s ease-in-out infinite}\
#cg-global-nav .cg-mark::before{content:'';position:absolute;inset:-5px;border-radius:50%;background:conic-gradient(from 0deg,transparent,rgba(178,138,255,.95),rgba(96,196,255,.95),transparent 62%);-webkit-mask:radial-gradient(farthest-side,transparent calc(100% - 3px),#000 calc(100% - 3px));mask:radial-gradient(farthest-side,transparent calc(100% - 3px),#000 calc(100% - 3px));animation:cgnMarkSpin 4.6s linear infinite;pointer-events:none}\
#cg-global-nav .cg-mark img{width:100%;height:100%;border-radius:50%;object-fit:cover;display:block;background:#0c1020;position:relative;z-index:1}\
#cg-global-nav .cg-name{font-family:'Cormorant Garamond',Georgia,serif;font-size:25px;font-weight:700;letter-spacing:-.01em;line-height:1;color:#eef0ff!important;text-shadow:0 0 16px rgba(150,120,250,.45)}\
#cg-global-nav .cg-name em{font-style:italic;font-weight:400;color:#a78bfa!important;text-shadow:0 0 14px rgba(167,139,250,.7)}\
#cg-global-nav .cg-links{display:flex;align-items:center;gap:6px;position:relative;z-index:2}\
#cg-global-nav .cg-links a,#cg-global-nav .cg-dropbtn{position:relative;color:rgba(236,233,255,.82)!important;text-decoration:none;font-size:15px;font-weight:600;letter-spacing:.005em;padding:12px 13px 16px;border-radius:13px;border:0;background:transparent!important;cursor:pointer;font-family:'Urbanist',Inter,system-ui,sans-serif;white-space:nowrap;line-height:1;display:flex;align-items:center;transition:color .18s ease,text-shadow .18s ease}\
#cg-global-nav .cg-links a:hover,#cg-global-nav .cg-dropbtn:hover,#cg-global-nav .cg-links a:focus-visible,#cg-global-nav .cg-dropbtn:focus-visible{color:#fff!important;background:transparent!important;text-shadow:0 0 14px rgba(180,150,255,.7);outline:none}\
#cg-global-nav .cg-links>a:not(.cg-cta)::after,#cg-global-nav .cg-dropbtn::after{content:'';display:block;position:absolute;left:50%;bottom:7px;transform:translateX(-50%);width:26px;height:2px;border-radius:2px;background:linear-gradient(90deg,rgba(150,120,255,0),#9a7bff 35%,#7db8ff 65%,rgba(150,120,255,0));box-shadow:0 0 8px rgba(150,110,240,.9),0 0 3px rgba(130,190,255,.8);opacity:.9;animation:cgnDash 2.8s ease-in-out infinite}\
#cg-global-nav .cg-links>a:not(.cg-cta):nth-of-type(2)::after{animation-delay:.4s}\
#cg-global-nav .cg-links>a:not(.cg-cta):nth-of-type(3)::after{animation-delay:.8s}\
#cg-global-nav .cg-links>a:not(.cg-cta):nth-of-type(4)::after{animation-delay:1.2s}\
#cg-global-nav .cg-links>a:not(.cg-cta):nth-of-type(5)::after{animation-delay:1.6s}\
#cg-global-nav .cg-cta{display:inline-flex!important;align-items:center;gap:9px;margin-left:10px;padding:12px 20px!important;border-radius:34px!important;font-size:14.5px;white-space:nowrap;font-weight:700;letter-spacing:.005em;text-decoration:none;color:#fff!important;background:linear-gradient(180deg,#1c1740,#0c0a20)!important;border:1.5px solid rgba(170,130,255,.85)!important;box-shadow:0 0 20px rgba(150,110,240,.5),inset 0 0 14px rgba(150,110,240,.22),inset 0 1px 0 rgba(255,255,255,.15)!important;overflow:hidden;position:relative;transition:transform .18s ease,box-shadow .18s ease;animation:cgnBook 3s ease-in-out infinite}\
#cg-global-nav .cg-cta:hover,#cg-global-nav .cg-cta:focus-visible{transform:translateY(-1px);box-shadow:0 0 30px rgba(160,120,250,.8),inset 0 0 18px rgba(160,120,250,.35),inset 0 1px 0 rgba(255,255,255,.15)!important;color:#fff!important;outline:none}\
#cg-global-nav .cg-cta::before{content:'';position:absolute;top:0;left:-60%;width:45%;height:100%;transform:skewX(-20deg);background:linear-gradient(90deg,transparent,rgba(210,190,255,.35),transparent);animation:cgnBookSweep 3.4s ease-in-out infinite;pointer-events:none}\
#cg-global-nav .cg-cta .cg-shield{width:26px;height:26px;border-radius:9px;display:grid;place-items:center;background:linear-gradient(180deg,#241d4d,#120f2c);border:1px solid rgba(170,130,255,.7);box-shadow:0 0 10px rgba(150,110,240,.6);flex-shrink:0;position:relative;z-index:1}\
#cg-global-nav .cg-cta .cg-shield svg{width:14px;height:14px;color:#c6b3ff;stroke:#c6b3ff}\
#cg-global-nav .cg-drop{position:relative}\
#cg-global-nav .cg-menu{position:absolute;top:calc(100% + 14px);left:50%;transform:translateX(-50%) translateY(-6px);width:min(980px,92vw);max-height:min(72vh,720px);overflow:auto;display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:7px;padding:10px;background:linear-gradient(180deg,rgba(30,26,60,.98),rgba(16,14,36,.98))!important;border:1px solid rgba(150,120,240,.28)!important;border-radius:18px;box-shadow:0 20px 60px rgba(20,8,60,.6),0 0 40px rgba(140,90,240,.25)!important;opacity:0;pointer-events:none;transition:opacity .18s ease,transform .18s ease;z-index:5}\
#cg-global-nav .cg-drop:hover .cg-menu,#cg-global-nav .cg-drop:focus-within .cg-menu{opacity:1;pointer-events:auto;transform:translateX(-50%) translateY(0)}\
#cg-global-nav .cg-prod{display:flex!important;gap:10px!important;align-items:center!important;padding:10px!important;border-radius:12px!important;color:#e2deff!important;background:transparent!important;text-decoration:none}\
#cg-global-nav .cg-prod:hover{background:rgba(150,120,250,.16)!important;color:#fff!important}\
#cg-global-nav .cg-ic{width:30px;height:30px;border-radius:9px;background:rgba(150,120,250,.16);border:1px solid rgba(160,130,250,.25);display:grid;place-items:center;flex:0 0 auto;color:#c6b3ff}\
#cg-global-nav .cg-prod b{display:block;font-size:13px;line-height:1.15;color:#f2f0ff}\
#cg-global-nav .cg-prod small{display:block;margin-top:3px;font-family:'IBM Plex Mono',monospace;font-size:9px;letter-spacing:.06em;text-transform:uppercase;color:rgba(180,170,220,.6)}\
#cg-global-nav .cg-toggle{display:none;border:1px solid rgba(160,130,250,.35)!important;background:rgba(150,120,250,.12)!important;border-radius:12px;padding:8px;color:#e8e4ff!important;font-size:16px;line-height:1;position:relative;z-index:2;cursor:pointer}\
#cg-mobile-nav.cg-mobile{position:fixed;top:108px;left:.75rem;right:.75rem;z-index:2147482999;display:none;grid-template-columns:1fr;gap:4px;max-height:calc(100vh - 128px);overflow:auto;padding:10px;background:linear-gradient(180deg,rgba(28,24,56,.98),rgba(15,13,34,.98))!important;border:1px solid rgba(150,120,240,.3)!important;border-radius:20px;box-shadow:0 20px 60px rgba(20,8,60,.55),0 0 40px rgba(140,90,240,.22)!important}\
#cg-mobile-nav.cg-mobile.open{display:grid}\
#cg-mobile-nav.cg-mobile a{padding:12px 14px;border-radius:12px;text-decoration:none;color:#eae6ff!important;font-weight:600}\
#cg-mobile-nav.cg-mobile a:hover{background:rgba(150,120,250,.16)!important;color:#fff!important}\
#cg-mobile-nav .cg-label{font-family:'IBM Plex Mono',monospace;font-size:10px;letter-spacing:.15em;text-transform:uppercase;color:rgba(180,170,220,.6);padding:10px 14px 4px}\
.cg-topnav+main,.cg-topnav~main{scroll-margin-top:100px}.cg-topnav~:is(main,.page,.wrap){padding-top:max(98px,env(safe-area-inset-top))}\
@keyframes cgnRim{0%{background-position:0% 50%}100%{background-position:230% 50%}}\
@keyframes cgnRail{0%{background-position:200% 50%}100%{background-position:-40% 50%}}\
@keyframes cgnSheen{0%{left:-45%;opacity:0}18%{opacity:1}62%{opacity:1}82%,100%{left:135%;opacity:0}}\
@keyframes cgnMarkSpin{to{transform:rotate(360deg)}}\
@keyframes cgnMarkGlow{0%,100%{box-shadow:0 0 0 2px rgba(150,110,240,.5),0 0 16px rgba(150,110,240,.5),inset 0 1px 3px rgba(255,255,255,.85)}50%{box-shadow:0 0 0 2px rgba(160,120,255,.85),0 0 30px rgba(160,120,255,.85),inset 0 1px 3px rgba(255,255,255,.92)}}\
@keyframes cgnDash{0%,100%{opacity:.5;transform:translateX(-50%) scaleX(.75)}50%{opacity:1;transform:translateX(-50%) scaleX(1.18)}}\
@keyframes cgnBook{0%,100%{box-shadow:0 0 16px rgba(150,110,240,.4),inset 0 0 12px rgba(150,110,240,.2),inset 0 1px 0 rgba(255,255,255,.15)}50%{box-shadow:0 0 30px rgba(160,120,250,.78),inset 0 0 18px rgba(160,120,250,.35),inset 0 1px 0 rgba(255,255,255,.15)}}\
@keyframes cgnBookSweep{0%{left:-60%}45%,100%{left:135%}}\
@media(max-width:1180px){#cg-global-nav .cg-links{display:none!important}#cg-global-nav .cg-toggle{display:block!important}#cg-global-nav .cg-menu{grid-template-columns:1fr}}\
@media(max-width:760px){#cg-global-nav.cg-topnav{top:10px;width:calc(100% - 1rem);height:66px;padding:0 12px 0 10px;border-radius:38px}#cg-global-nav .cg-mark{width:46px;height:46px}#cg-global-nav .cg-name{font-size:19px}#cg-mobile-nav.cg-mobile{top:88px}}\
@media(prefers-reduced-motion:reduce){#cg-global-nav.cg-topnav::before,#cg-global-nav.cg-topnav::after,#cg-global-nav .cg-sheen::before,#cg-global-nav .cg-mark,#cg-global-nav .cg-mark::before,#cg-global-nav .cg-links>a::after,#cg-global-nav .cg-dropbtn::after,#cg-global-nav .cg-cta,#cg-global-nav .cg-cta::before{animation:none!important}}";
  function build(){
    if (document.getElementById('cg-global-nav')) return;
    var st=document.createElement('style'); st.textContent=css; document.head.appendChild(st);
    var nav=document.createElement('nav'); nav.id='cg-global-nav'; nav.className='cg-topnav'; nav.setAttribute('aria-label','Primary navigation');
    var menu=PRODUCTS.map(function(p){return '<a class="cg-prod" href="'+href(p[1])+'"><span class="cg-ic">'+p[3]+'</span><span><b>'+esc(p[0])+'</b><small>'+esc(p[2])+'</small></span></a>';}).join('');
    nav.innerHTML='<span class="cg-sheen" aria-hidden="true"></span><a class="cg-brand" href="'+href('index.html')+'"><span class="cg-mark"><img src="'+href('assets/images/clearglass-logo.png')+'" alt="ClearGlass logo"></span><span class="cg-name">ClearGlassInc. <em>2040</em></span></a><div class="cg-links">'+TOP.map(function(t){return t[0]==='Products'?'<span class="cg-drop"><button class="cg-dropbtn" aria-haspopup="true">Products ▾</button><span class="cg-menu" role="menu">'+menu+'</span></span>':'<a href="'+href(t[1])+'">'+t[0]+'</a>';}).join('')+'<a class="cg-cta" href="'+href('store.html')+'">'+shield+'Book a Security Engagement</a></div><button class="cg-toggle" aria-label="Open navigation" aria-expanded="false">☰</button>';
    var mob=document.createElement('div'); mob.className='cg-mobile'; mob.id='cg-mobile-nav'; mob.innerHTML='<div class="cg-label">Navigation</div>'+TOP.filter(function(t){return t[0]!=='Products';}).map(function(t){return '<a href="'+href(t[1])+'">'+t[0]+'</a>';}).join('')+'<a href="'+href('store.html')+'">Book a Security Engagement</a><div class="cg-label">Products</div>'+PRODUCTS.map(function(p){return '<a href="'+href(p[1])+'">'+esc(p[0])+'</a>';}).join('');
    document.body.appendChild(nav); document.body.appendChild(mob);
    var btn=nav.querySelector('.cg-toggle'); btn.addEventListener('click',function(){var open=mob.classList.toggle('open');btn.setAttribute('aria-expanded',open?'true':'false');});
  }
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',build);else build();
})();

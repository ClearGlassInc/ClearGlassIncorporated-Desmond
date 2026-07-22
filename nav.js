/* ClearGlass · homepage-matched global navigation.
   Injects the same premium glass top bar, complete product catalog, mobile menu,
   and clear CTA language on every static page without removing page content. */
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
  var css = ".cg-topnav{position:fixed;top:clamp(14px,2.4vw,28px);left:50%;transform:translateX(-50%);width:min(1460px,calc(100% - clamp(1.25rem,3vw,3.5rem)));z-index:2147483000;min-height:96px;display:flex;align-items:center;justify-content:space-between;gap:clamp(1rem,2vw,2rem);padding:clamp(.65rem,1.2vw,.95rem) clamp(1rem,1.9vw,1.75rem);background:linear-gradient(90deg,rgba(37,50,91,.78),rgba(20,30,58,.9) 44%,rgba(79,56,142,.82));backdrop-filter:blur(30px) saturate(1.65);-webkit-backdrop-filter:blur(30px) saturate(1.65);border:1px solid rgba(204,215,255,.72);border-radius:999px;box-shadow:0 24px 70px rgba(55,34,130,.24),0 8px 22px rgba(8,13,35,.24),inset 0 1px 0 rgba(255,255,255,.62),inset 0 -1px 0 rgba(176,128,255,.55),0 0 0 1px rgba(148,163,255,.28);font-family:Inter,system-ui,sans-serif;isolation:isolate;overflow:visible}.cg-topnav:before{content:\"\";position:absolute;inset:5px;border-radius:inherit;pointer-events:none;background:linear-gradient(180deg,rgba(255,255,255,.16),transparent 36%),linear-gradient(90deg,rgba(112,178,255,.24),transparent 28%,rgba(190,109,255,.22) 72%,rgba(255,255,255,.12));box-shadow:inset 0 0 38px rgba(126,87,255,.38),inset 0 0 0 1px rgba(255,255,255,.18);z-index:-1}.cg-topnav:after{content:\"\";position:absolute;left:48px;right:48px;top:8px;height:2px;border-radius:999px;background:linear-gradient(90deg,transparent,rgba(125,164,255,.82) 21%,rgba(255,255,255,.96) 42%,rgba(202,123,255,.96) 63%,transparent);filter:blur(.2px);box-shadow:0 0 14px rgba(190,109,255,.86),0 0 28px rgba(96,165,250,.42);pointer-events:none}.cg-topnav *{box-sizing:border-box}.cg-brand{position:relative;display:flex;align-items:center;gap:clamp(12px,1.7vw,22px);min-width:max-content;color:#f7fbff;text-decoration:none;text-shadow:0 0 22px rgba(255,255,255,.2)}.cg-brand:after{content:\"\";position:absolute;left:54px;right:-66px;bottom:-18px;height:1px;background:linear-gradient(90deg,rgba(132,175,255,.55),rgba(132,175,255,.2),transparent);box-shadow:0 0 16px rgba(132,175,255,.45)}.cg-mark{width:76px;height:76px;border-radius:50%;display:grid;place-items:center;background:radial-gradient(circle at 34% 28%,rgba(255,255,255,.88),rgba(190,200,216,.9) 32%,rgba(80,86,105,.95) 58%,rgba(22,25,35,.95));border:1px solid rgba(238,242,255,.72);box-shadow:0 0 0 7px rgba(151,90,255,.24),0 0 30px rgba(174,91,255,.8),inset 0 2px 10px rgba(255,255,255,.65),inset 0 -8px 18px rgba(0,0,0,.42);overflow:hidden;flex:0 0 auto}.cg-mark img{width:100%;height:100%;object-fit:cover;filter:grayscale(.15) contrast(1.12) saturate(.55)}.cg-name{font-family:Inter,system-ui,sans-serif;font-size:clamp(1.35rem,2.1vw,2rem);font-weight:850;letter-spacing:-.055em;line-height:1;white-space:nowrap}.cg-name em{font-style:italic;font-weight:600;color:#b99cff;letter-spacing:.01em;margin-left:.28rem;text-shadow:0 0 16px rgba(185,156,255,.68)}.cg-links{display:flex;align-items:center;gap:clamp(.45rem,1vw,1.1rem);margin-left:auto}.cg-links a,.cg-dropbtn{position:relative;color:rgba(239,244,255,.9);text-decoration:none;font-size:clamp(.9rem,1vw,1.04rem);font-weight:650;padding:14px 12px 18px;border-radius:14px;border:0;background:transparent;cursor:pointer;text-shadow:0 2px 16px rgba(255,255,255,.12)}.cg-links a:after,.cg-dropbtn:after{content:\"\";position:absolute;left:50%;bottom:5px;width:34px;height:3px;border-radius:999px;transform:translateX(-50%) scaleX(.72);background:linear-gradient(90deg,transparent,#8aa7ff,#c978ff,transparent);box-shadow:0 0 13px rgba(176,103,255,.9);opacity:.68;transition:opacity .2s ease,transform .2s ease}.cg-links a:hover,.cg-dropbtn:hover{color:#fff;background:rgba(255,255,255,.06)}.cg-links a:hover:after,.cg-dropbtn:hover:after{opacity:1;transform:translateX(-50%) scaleX(1.2)}.cg-cta{display:inline-flex!important;align-items:center;gap:12px;background:linear-gradient(180deg,rgba(10,13,26,.98),rgba(4,6,14,.98))!important;color:#fff!important;margin-left:clamp(.35rem,1vw,1rem);padding:18px 24px!important;border:1px solid rgba(196,139,255,.78)!important;border-radius:18px!important;box-shadow:0 0 0 1px rgba(123,92,255,.25),0 0 24px rgba(178,88,255,.72),0 14px 34px rgba(0,0,0,.38),inset 0 1px 0 rgba(255,255,255,.15)}.cg-cta:before{content:\"♢\";display:grid;place-items:center;width:34px;height:34px;border-radius:12px;color:#d9b5ff;border:1px solid rgba(201,120,255,.5);box-shadow:inset 0 0 15px rgba(177,91,255,.34),0 0 16px rgba(177,91,255,.42)}.cg-cta:after{display:none}.cg-drop{position:relative}.cg-menu{position:absolute;top:calc(100% + 16px);left:50%;transform:translateX(-50%) translateY(-6px);width:min(980px,92vw);max-height:min(72vh,720px);overflow:auto;display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:7px;padding:10px;background:rgba(16,24,50,.96);border:1px solid rgba(185,156,255,.36);border-radius:24px;box-shadow:0 22px 70px rgba(8,13,35,.42),0 0 34px rgba(176,103,255,.22);opacity:0;pointer-events:none;transition:.18s;backdrop-filter:blur(24px)}.cg-drop:hover .cg-menu,.cg-drop:focus-within .cg-menu{opacity:1;pointer-events:auto;transform:translateX(-50%) translateY(0)}.cg-prod{display:flex!important;gap:10px!important;align-items:center!important;padding:10px!important;border-radius:14px!important;color:#eef4ff!important;background:transparent!important}.cg-prod:hover{background:rgba(255,255,255,.08)!important}.cg-ic{width:30px;height:30px;border-radius:10px;background:rgba(255,255,255,.08);display:grid;place-items:center;flex:0 0 auto}.cg-prod b{display:block;font-size:13px;line-height:1.15}.cg-prod small{display:block;margin-top:3px;font-family:'IBM Plex Mono',monospace;font-size:9px;letter-spacing:.06em;text-transform:uppercase;color:#aeb9d5}.cg-toggle{display:none;border:1px solid rgba(196,139,255,.55);background:rgba(7,10,24,.7);color:#fff;border-radius:14px;padding:10px}.cg-mobile{position:fixed;top:124px;left:.75rem;right:.75rem;z-index:2147482999;display:none;grid-template-columns:1fr;gap:4px;max-height:calc(100vh - 140px);overflow:auto;padding:10px;background:rgba(16,24,50,.98);border:1px solid rgba(185,156,255,.36);border-radius:24px;box-shadow:0 12px 48px rgba(10,12,16,.28)}.cg-mobile.open{display:grid}.cg-mobile a{padding:12px 14px;border-radius:12px;text-decoration:none;color:#eef4ff;font-weight:650}.cg-mobile a:hover{background:rgba(255,255,255,.08)}.cg-label{font-family:'IBM Plex Mono',monospace;font-size:10px;letter-spacing:.15em;text-transform:uppercase;color:#aeb9d5;padding:10px 14px 4px}.cg-topnav+main,.cg-topnav~main{scroll-margin-top:132px}.cg-topnav~:is(main,.page,.wrap){padding-top:max(128px,env(safe-area-inset-top))}.cg-unified-page :is(section,.section,.panel,.card){border-radius:clamp(16px,2vw,24px)}body{--cg-home-rhythm:clamp(80px,12vw,140px)}main :is(h1,h2){letter-spacing:-.025em}main :is(.eyebrow,.kicker,.label,.mono){letter-spacing:.12em;text-transform:uppercase}.btn,.button,a[class*=cta],button[class*=cta]{border-radius:999px}@media(max-width:1180px){.cg-links{display:none}.cg-toggle{display:block}.cg-topnav{min-height:78px}.cg-mark{width:58px;height:58px}.cg-menu{grid-template-columns:1fr}.cg-brand:after{display:none}}@media(max-width:760px){.cg-topnav{top:8px;width:calc(100% - 1rem);min-height:66px;padding:.45rem .75rem}.cg-name{font-size:17px}.cg-name em{display:none}.cg-mark{width:48px;height:48px}.cg-mobile{top:84px;max-height:calc(100vh - 100px)}}";
  function build(){
    if (document.getElementById('cg-global-nav')) return;
    var st=document.createElement('style'); st.textContent=css; document.head.appendChild(st);
    var nav=document.createElement('nav'); nav.id='cg-global-nav'; nav.className='cg-topnav'; nav.setAttribute('aria-label','Primary navigation');
    var menu=PRODUCTS.map(function(p){return '<a class="cg-prod" href="'+href(p[1])+'"><span class="cg-ic">'+p[3]+'</span><span><b>'+esc(p[0])+'</b><small>'+esc(p[2])+'</small></span></a>';}).join('');
    nav.innerHTML='<a class="cg-brand" href="'+href('index.html')+'"><span class="cg-mark" aria-hidden="true"><img src="'+href('assets/images/clearglass-logo.png')+'" alt=""></span><span class="cg-name">ClearGlassInc. <em>2040</em></span></a><div class="cg-links">'+TOP.map(function(t){return t[0]==='Products'?'<span class="cg-drop"><button class="cg-dropbtn" aria-haspopup="true">Products ▾</button><span class="cg-menu" role="menu">'+menu+'</span></span>':'<a href="'+href(t[1])+'">'+t[0]+'</a>';}).join('')+'<a class="cg-cta" href="'+href('store.html')+'">Book a Security Engagement</a></div><button class="cg-toggle" aria-label="Open navigation" aria-expanded="false">☰</button>';
    var mob=document.createElement('div'); mob.className='cg-mobile'; mob.id='cg-mobile-nav'; mob.innerHTML='<div class="cg-label">Navigation</div>'+TOP.filter(function(t){return t[0]!=='Products';}).map(function(t){return '<a href="'+href(t[1])+'">'+t[0]+'</a>';}).join('')+'<a href="'+href('store.html')+'">Book a Security Engagement</a><div class="cg-label">Products</div>'+PRODUCTS.map(function(p){return '<a href="'+href(p[1])+'">'+esc(p[0])+'</a>';}).join('');
    document.body.appendChild(nav); document.body.appendChild(mob);
    var btn=nav.querySelector('.cg-toggle'); btn.addEventListener('click',function(){var open=mob.classList.toggle('open');btn.setAttribute('aria-expanded',open?'true':'false');});
  }
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',build);else build();
})();

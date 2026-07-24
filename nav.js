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
  var TOP = [["Vision","index.html#vision"],["Services","index.html#services"],["Products","products.html"],["Government","government.html"],["Insights","blog/"],["Contact","index.html#contact"]];
  var script = document.currentScript || Array.prototype.slice.call(document.scripts).filter(function(s){return /nav\.js(?:\?|$)/.test(s.src);}).pop();
  var base = script ? new URL('.', script.src).href : new URL('.', location.href).href;
  function href(path){ return /^https?:|^mailto:|^#/.test(path) ? path : new URL(path, base).href; }
  var here = (location.pathname.split('/').pop() || 'index.html').toLowerCase();
  function esc(s){return String(s).replace(/[&<>"]/g,function(c){return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c];});}
  var css = [
    ".cg-native-nav-hidden{display:none!important}.cg-global-nav-enabled{--cg-unified-nav-offset:clamp(96px,9vw,150px)}",
    ".cg-topnav{position:fixed;top:clamp(16px,2vw,28px);left:50%;transform:translateX(-50%);width:min(1840px,calc(100% - clamp(1.5rem,3vw,4rem)));z-index:2147483000;min-height:94px;display:flex;align-items:center;justify-content:space-between;gap:clamp(1.1rem,2.2vw,2.75rem);padding:clamp(.55rem,.9vw,.9rem) clamp(1rem,1.6vw,1.7rem);border-radius:28px;border:1px solid rgba(150,170,215,.32);background:radial-gradient(135% 210% at 97% 24%,rgba(150,101,255,.36),transparent 45%),linear-gradient(100deg,rgba(20,26,52,.95),rgba(13,18,40,.96) 44%,rgba(23,20,54,.95) 80%,rgba(40,29,82,.95));backdrop-filter:blur(30px) saturate(1.4);-webkit-backdrop-filter:blur(30px) saturate(1.4);box-shadow:0 24px 70px rgba(10,14,35,.5),0 10px 30px rgba(70,50,140,.26),inset 0 1px 0 rgba(255,255,255,.26),inset 0 -1px 0 rgba(150,110,220,.32),inset 0 0 0 1px rgba(120,140,190,.1);font-family:Urbanist,Inter,system-ui,sans-serif;isolation:isolate;overflow:visible}",
    ".cg-topnav:before{content:'';position:absolute;inset:6px;border-radius:22px;z-index:-1;pointer-events:none;background:linear-gradient(180deg,rgba(255,255,255,.09),transparent 42%),repeating-linear-gradient(90deg,transparent 0 150px,rgba(150,180,240,.09) 151px,transparent 153px);border:1px solid rgba(130,150,205,.14);box-shadow:inset 0 0 44px rgba(78,58,158,.34)}",
    ".cg-topnav:after{content:'';position:absolute;left:41%;right:34px;top:6px;height:2px;border-radius:999px;pointer-events:none;background:linear-gradient(90deg,transparent,rgba(150,120,255,.45) 38%,rgba(214,140,255,.95) 74%,rgba(150,170,255,.35));box-shadow:0 0 14px rgba(196,120,255,.7),0 0 30px rgba(120,110,255,.28)}",
    ".cg-topnav *{box-sizing:border-box}.cg-brand{position:relative;display:flex;align-items:center;gap:clamp(14px,1.6vw,24px);min-width:max-content;color:#eef2ff;text-decoration:none}.cg-brand:after{display:none}",
    ".cg-mark{position:relative;width:80px;height:80px;border-radius:50%;display:grid;place-items:center;background:radial-gradient(circle at 34% 26%,#ffffff,#dde4f0 24%,#9aa2b6 52%,#2b3150 82%);border:2px solid rgba(232,240,254,.9);box-shadow:0 0 0 4px rgba(120,140,205,.16),0 0 24px rgba(150,120,240,.45),0 8px 22px rgba(0,0,0,.5),inset 0 4px 12px rgba(255,255,255,.72),inset 0 -10px 22px rgba(0,0,0,.4);flex:0 0 auto}.cg-mark:before{content:'';position:absolute;inset:0;border-radius:50%;background:conic-gradient(from 210deg,transparent,rgba(255,255,255,.6),transparent 24%,rgba(180,140,250,.32),transparent 50%);mix-blend-mode:screen}.cg-mark img{position:relative;width:94%;height:94%;object-fit:contain;border-radius:50%;filter:grayscale(.12) contrast(1.16) saturate(.7) drop-shadow(0 8px 14px rgba(0,0,0,.32))}",
    ".cg-name{font-family:'Cormorant Garamond',Georgia,serif;font-size:clamp(1.5rem,2.15vw,2.5rem);font-weight:600;letter-spacing:-.02em;line-height:1;white-space:nowrap;color:#f4f6ff}.cg-name em{font-family:'Cormorant Garamond',Georgia,serif;font-style:italic;font-weight:400;color:#cbb8ff;letter-spacing:.005em;margin-left:.34rem;text-shadow:0 0 16px rgba(190,160,255,.55)}",
    ".cg-links{display:flex;align-items:center;gap:clamp(.35rem,.95vw,1.1rem);margin-left:auto}.cg-links a,.cg-dropbtn{position:relative;color:rgba(228,234,252,.85);text-decoration:none;font-size:clamp(.96rem,1vw,1.14rem);font-weight:500;letter-spacing:.01em;padding:14px 12px 16px;border-radius:12px;border:0;background:transparent;cursor:pointer;display:inline-flex;align-items:center;gap:5px}.cg-links a:after,.cg-dropbtn:after{content:'';position:absolute;left:50%;bottom:8px;width:0;height:2px;border-radius:999px;transform:translateX(-50%);background:linear-gradient(90deg,transparent,#a68cff,#d68cff,transparent);box-shadow:0 0 12px rgba(200,130,255,.85);opacity:0;transition:width .22s,opacity .22s}.cg-links a:hover,.cg-dropbtn:hover{color:#fff}.cg-links a:hover:after,.cg-dropbtn:hover:after,.cg-drop:focus-within .cg-dropbtn:after{width:62%;opacity:.9}",
    ".cg-cta{display:inline-flex!important;align-items:center;gap:12px;background:linear-gradient(180deg,rgba(24,29,54,.72),rgba(12,15,32,.74))!important;color:#eef2ff!important;margin-left:clamp(.45rem,1vw,1.1rem);padding:13px 22px!important;border:1px solid rgba(166,150,224,.5)!important;border-radius:18px!important;box-shadow:0 8px 24px rgba(0,0,0,.36),0 0 20px rgba(150,110,235,.22),inset 0 1px 0 rgba(255,255,255,.12)!important;line-height:1.15;transition:border-color .2s,box-shadow .2s,transform .2s}.cg-cta:hover{transform:translateY(-1px);border-color:rgba(196,160,255,.75)!important;box-shadow:0 12px 30px rgba(0,0,0,.42),0 0 28px rgba(176,110,255,.4),inset 0 1px 0 rgba(255,255,255,.16)!important}.cg-cta svg{width:30px;height:30px;flex:0 0 auto;color:#bd93f4;filter:drop-shadow(0 0 8px rgba(180,120,255,.7))}.cg-cta:after{display:none}",
    ".cg-drop{position:relative}.cg-menu{position:absolute;top:calc(100% + 16px);left:50%;transform:translateX(-50%) translateY(-6px);width:min(980px,92vw);max-height:min(72vh,720px);overflow:auto;display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:7px;padding:10px;background:rgba(15,20,44,.97);border:1px solid rgba(170,150,240,.32);border-radius:22px;box-shadow:0 22px 70px rgba(6,10,30,.5),0 0 34px rgba(150,100,240,.2);opacity:0;pointer-events:none;transition:.18s;backdrop-filter:blur(24px)}.cg-drop:hover .cg-menu,.cg-drop:focus-within .cg-menu{opacity:1;pointer-events:auto;transform:translateX(-50%) translateY(0)}.cg-prod{display:flex!important;gap:10px!important;align-items:center!important;padding:10px!important;border-radius:14px!important;color:#eef4ff!important;background:transparent!important}.cg-prod:hover{background:rgba(255,255,255,.07)!important}.cg-ic{width:30px;height:30px;border-radius:10px;background:rgba(150,120,235,.16);display:grid;place-items:center;flex:0 0 auto}.cg-prod b{display:block;font-size:13px;line-height:1.15}.cg-prod small{display:block;margin-top:3px;font-family:'IBM Plex Mono',monospace;font-size:9px;letter-spacing:.06em;text-transform:uppercase;color:#a9b4d4}",
    ".cg-toggle{display:none;border:1px solid rgba(180,150,235,.5);background:rgba(12,16,34,.7);color:#fff;border-radius:14px;padding:10px}.cg-mobile{position:fixed;top:120px;left:.75rem;right:.75rem;z-index:2147482999;display:none;grid-template-columns:1fr;gap:4px;max-height:calc(100vh - 136px);overflow:auto;padding:10px;background:rgba(15,20,44,.98);border:1px solid rgba(170,150,240,.32);border-radius:22px;box-shadow:0 12px 48px rgba(8,10,26,.4)}.cg-mobile.open{display:grid}.cg-mobile a{padding:12px 14px;border-radius:12px;text-decoration:none;color:#eef4ff;font-weight:600}.cg-mobile a:hover{background:rgba(255,255,255,.08)}.cg-label{font-family:'IBM Plex Mono',monospace;font-size:10px;letter-spacing:.15em;text-transform:uppercase;color:#a9b4d4;padding:10px 14px 4px}",
    ".cg-topnav+main,.cg-topnav~main{scroll-margin-top:140px}.cg-topnav~:is(main,.page,.wrap){padding-top:max(140px,env(safe-area-inset-top))}.cg-unified-page :is(section,.section,.panel,.card){border-radius:clamp(16px,2vw,24px)}body{--cg-home-rhythm:clamp(80px,12vw,140px)}main :is(h1,h2){letter-spacing:-.025em}main :is(.eyebrow,.kicker,.label,.mono){letter-spacing:.12em;text-transform:uppercase}.btn,.button,a[class*=cta],button[class*=cta]{border-radius:999px}@media(max-width:1240px){.cg-links{display:none}.cg-toggle{display:block}.cg-topnav{min-height:78px}.cg-mark{width:58px;height:58px}.cg-menu{grid-template-columns:1fr}}@media(max-width:760px){.cg-topnav{top:8px;width:calc(100% - 1rem);min-height:64px;padding:.45rem .75rem}.cg-name{font-size:19px}.cg-name em{display:none}.cg-mark{width:50px;height:50px}.cg-mobile{top:82px;max-height:calc(100vh - 98px)}}"
  ].join("");
  function isNativePrimaryNav(el){
    if (!el || el.id === 'cg-global-nav' || el.id === 'cg-mobile-nav') return false;
    if (el.closest('#cg-related,footer,.footer,.site-footer,.gov-footer,.cgr-box,.cg-topnav,.cg-mobile')) return false;
    var label = (el.getAttribute('aria-label') || '').toLowerCase();
    var role = (el.getAttribute('role') || '').toLowerCase();
    var cls = (' ' + (el.className || '') + ' ').toLowerCase();
    var id = (' ' + (el.id || '') + ' ').toLowerCase();
    if (/related|footer|breadcrumb|pagination/.test(label + cls + id)) return false;
    if (/primary|main|navigation/.test(label) || role === 'navigation') return true;
    return /( nav | navbar | topbar | header-nav | ag-nav | site-nav )/.test(cls) || /( navbar | nav )/.test(id);
  }
  function hideNativeNavigation(){
    Array.prototype.forEach.call(document.querySelectorAll('nav,[role="navigation"]'), function(el){
      if (isNativePrimaryNav(el)) el.classList.add('cg-native-nav-hidden');
    });
    document.body.classList.add('cg-global-nav-enabled');
  }
  function build(){
    if (document.getElementById('cg-global-nav')) return;
    // On non-home pages the design-system top bar (cg-design-system.js) owns the
    // global nav, so defer to it and avoid a duplicate bar. This bar still builds
    // on the homepage and on any page that does not load the design system.
    var isIndex = (here === '' || here === 'index.html');
    var tbOptOut = document.documentElement.hasAttribute('data-cg-no-topbar') ||
      (document.body && document.body.hasAttribute('data-cg-no-topbar'));
    if (window.__cgDesignSystem && !isIndex && !tbOptOut) return;
    var st=document.createElement('style'); st.textContent=css; document.head.appendChild(st);
    hideNativeNavigation();
    var nav=document.createElement('nav'); nav.id='cg-global-nav'; nav.className='cg-topnav'; nav.setAttribute('aria-label','Primary navigation');
    var menu=PRODUCTS.map(function(p){return '<a class="cg-prod" href="'+href(p[1])+'"><span class="cg-ic">'+p[3]+'</span><span><b>'+esc(p[0])+'</b><small>'+esc(p[2])+'</small></span></a>';}).join('');
    nav.innerHTML='<a class="cg-brand" href="'+href('index.html')+'"><span class="cg-mark" aria-hidden="true"><img src="'+href('assets/images/clearglass-logo.png')+'" alt=""></span><span class="cg-name">ClearGlassInc. <em>2040</em></span></a><div class="cg-links">'+TOP.map(function(t){return t[0]==='Products'?'<span class="cg-drop"><a class="cg-dropbtn" href="'+href('products.html')+'" aria-haspopup="true">Products⌄</a><span class="cg-menu" role="menu"><a class="cg-prod" href="'+href('products.html')+'"><span class="cg-ic">▨</span><span><b>All Products</b><small>Unified catalog</small></span></a>'+menu+'</span></span>':'<a href="'+href(t[1])+'">'+t[0]+'</a>';}).join('')+'<a class="cg-cta" href="'+href('store.html')+'"><svg viewBox="0 0 32 32" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M16 3.5l10 3.8v7.2c0 6.2-4 11.6-10 14-6-2.4-10-7.8-10-14V7.3l10-3.8z"/><path d="M12.2 15.7l2.5 2.5 5.5-6"/></svg>Book a Security Engagement</a></div><button class="cg-toggle" aria-label="Open navigation" aria-expanded="false">☰</button>';
    var mob=document.createElement('div'); mob.className='cg-mobile'; mob.id='cg-mobile-nav'; mob.innerHTML='<div class="cg-label">Navigation</div>'+TOP.map(function(t){return '<a href="'+href(t[1])+'">'+t[0]+'</a>';}).join('')+'<a href="'+href('store.html')+'">Book a Security Engagement</a><div class="cg-label">Products</div>'+PRODUCTS.map(function(p){return '<a href="'+href(p[1])+'">'+esc(p[0])+'</a>';}).join('');
    document.body.appendChild(nav); document.body.appendChild(mob);
    var btn=nav.querySelector('.cg-toggle'); btn.addEventListener('click',function(){var open=mob.classList.toggle('open');btn.setAttribute('aria-expanded',open?'true':'false');});
  }
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',build);else build();
})();

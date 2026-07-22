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
    ["Pricing", "pricing.html", "Plans and engagements", "₵"]
  ];
  var TOP = [["Vision","index.html#vision"],["Services","index.html#services"],["Products","#products"],["Government","government.html"],["Insights","blog/"],["Contact","index.html#contact"]];
  var script = document.currentScript || Array.prototype.slice.call(document.scripts).filter(function(s){return /nav\.js(?:\?|$)/.test(s.src);}).pop();
  var base = script ? new URL('.', script.src).href : new URL('.', location.href).href;
  function href(path){ return /^https?:|^mailto:|^#/.test(path) ? path : new URL(path, base).href; }
  var here = (location.pathname.split('/').pop() || 'index.html').toLowerCase();
  function esc(s){return String(s).replace(/[&<>"]/g,function(c){return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c];});}
  var css = ".cg-topnav{position:fixed;top:14px;left:50%;transform:translateX(-50%);width:min(1280px,calc(100% - 2rem));z-index:2147483000;height:72px;display:flex;align-items:center;justify-content:space-between;padding:0 clamp(1rem,2.5vw,1.75rem);background:rgba(250,251,252,.78);backdrop-filter:blur(28px) saturate(1.5);-webkit-backdrop-filter:blur(28px) saturate(1.5);border:1px solid rgba(255,255,255,.84);border-radius:22px;box-shadow:0 6px 28px rgba(10,12,16,.07);font-family:Inter,system-ui,sans-serif}.cg-topnav *{box-sizing:border-box}.cg-brand{display:flex;align-items:center;gap:12px;color:#0a0c10;text-decoration:none}.cg-mark{width:40px;height:40px;border-radius:11px;display:grid;place-items:center;background:radial-gradient(circle at 35% 30%,#fff,#bcd4ff 35%,#60a5fa 64%,#161038);box-shadow:0 2px 10px rgba(0,0,0,.10);overflow:hidden}.cg-name{font-family:Georgia,serif;font-size:20px;font-weight:700;letter-spacing:-.03em}.cg-name em{font-style:italic;font-weight:300;color:#6b7280}.cg-links{display:flex;align-items:center;gap:2px}.cg-links a,.cg-dropbtn{color:#4b5563;text-decoration:none;font-size:13.5px;font-weight:650;padding:9px 15px;border-radius:10px;border:0;background:transparent;cursor:pointer}.cg-links a:hover,.cg-dropbtn:hover{background:rgba(10,12,16,.055);color:#0a0c10}.cg-cta{background:#0a0c10!important;color:#fff!important;margin-left:8px}.cg-drop{position:relative}.cg-menu{position:absolute;top:calc(100% + 10px);left:50%;transform:translateX(-50%) translateY(-6px);width:min(760px,92vw);max-height:min(70vh,680px);overflow:auto;display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:7px;padding:10px;background:rgba(252,253,254,.98);border:1px solid rgba(0,0,0,.07);border-radius:18px;box-shadow:0 18px 60px rgba(10,12,16,.13);opacity:0;pointer-events:none;transition:.18s}.cg-drop:hover .cg-menu,.cg-drop:focus-within .cg-menu{opacity:1;pointer-events:auto;transform:translateX(-50%) translateY(0)}.cg-prod{display:flex!important;gap:10px!important;align-items:center!important;padding:10px!important;border-radius:12px!important;color:#111827!important;background:transparent!important}.cg-prod:hover{background:rgba(10,12,16,.055)!important}.cg-ic{width:30px;height:30px;border-radius:9px;background:rgba(10,12,16,.055);display:grid;place-items:center;flex:0 0 auto}.cg-prod b{display:block;font-size:13px;line-height:1.15}.cg-prod small{display:block;margin-top:3px;font-family:'IBM Plex Mono',monospace;font-size:9px;letter-spacing:.06em;text-transform:uppercase;color:#8a93a3}.cg-toggle{display:none;border:1px solid rgba(0,0,0,.09);background:rgba(255,255,255,.5);border-radius:11px;padding:8px}.cg-mobile{position:fixed;top:96px;left:.75rem;right:.75rem;z-index:2147482999;display:none;grid-template-columns:1fr;gap:4px;max-height:calc(100vh - 112px);overflow:auto;padding:10px;background:rgba(252,253,254,.98);border:1px solid rgba(255,255,255,.88);border-radius:20px;box-shadow:0 12px 48px rgba(10,12,16,.10)}.cg-mobile.open{display:grid}.cg-mobile a{padding:12px 14px;border-radius:12px;text-decoration:none;color:#0a0c10;font-weight:650}.cg-mobile a:hover{background:rgba(10,12,16,.055)}.cg-label{font-family:'IBM Plex Mono',monospace;font-size:10px;letter-spacing:.15em;text-transform:uppercase;color:#8a93a3;padding:10px 14px 4px}@media(max-width:1040px){.cg-links{display:none}.cg-toggle{display:block}.cg-menu{grid-template-columns:1fr}}@media(max-width:760px){.cg-topnav{top:8px;width:calc(100% - 1rem);height:64px}.cg-name{font-size:17px}.cg-mobile{top:84px}}";
  function build(){
    if (document.getElementById('cg-global-nav')) return;
    var st=document.createElement('style'); st.textContent=css; document.head.appendChild(st);
    var nav=document.createElement('nav'); nav.id='cg-global-nav'; nav.className='cg-topnav'; nav.setAttribute('aria-label','Primary navigation');
    var menu=PRODUCTS.map(function(p){return '<a class="cg-prod" href="'+href(p[1])+'"><span class="cg-ic">'+p[3]+'</span><span><b>'+esc(p[0])+'</b><small>'+esc(p[2])+'</small></span></a>';}).join('');
    nav.innerHTML='<a class="cg-brand" href="'+href('index.html')+'"><span class="cg-mark" aria-hidden="true"></span><span class="cg-name">ClearGlassInc. <em>2040</em></span></a><div class="cg-links">'+TOP.map(function(t){return t[0]==='Products'?'<span class="cg-drop"><button class="cg-dropbtn" aria-haspopup="true">Products ▾</button><span class="cg-menu" role="menu">'+menu+'</span></span>':'<a href="'+href(t[1])+'">'+t[0]+'</a>';}).join('')+'<a class="cg-cta" href="'+href('store.html')+'">Book a Security Engagement</a></div><button class="cg-toggle" aria-label="Open navigation" aria-expanded="false">☰</button>';
    var mob=document.createElement('div'); mob.className='cg-mobile'; mob.id='cg-mobile-nav'; mob.innerHTML='<div class="cg-label">Navigation</div>'+TOP.filter(function(t){return t[0]!=='Products';}).map(function(t){return '<a href="'+href(t[1])+'">'+t[0]+'</a>';}).join('')+'<a href="'+href('store.html')+'">Book a Security Engagement</a><div class="cg-label">Products</div>'+PRODUCTS.map(function(p){return '<a href="'+href(p[1])+'">'+esc(p[0])+'</a>';}).join('');
    document.body.appendChild(nav); document.body.appendChild(mob);
    var btn=nav.querySelector('.cg-toggle'); btn.addEventListener('click',function(){var open=mob.classList.toggle('open');btn.setAttribute('aria-expanded',open?'true':'false');});
  }
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',build);else build();
})();

/* ClearGlass · premium neon navigation layer for every GitHub Pages view.
   Drop in with <script defer src="/nav.js"></script> (or relative path). The
   script preserves page markup and injects a fixed, accessible command navbar
   with a responsive hamburger menu. No dependencies. */
(function () {
  "use strict";
  if (window.__cgNavLoaded) return;
  window.__cgNavLoaded = true;

  var GROUPS = [
    ["Command", [
      ["AVALON", "artemis-percival.html", "A⊕P"],
      ["PERCIVAL", "percival-os.html", "◐"],
      ["SENTINEL", "sentinel.html", "◉"],
      ["AEGIS", "aegis.html", "⚖"],
      ["Agent Mesh", "agentmesh.html", "⌗"],
      ["CONDUIT", "conduit.html", "⟿"],
      ["AI Operator", "ai-operator.html", "🜂"],
      ["Console", "command-console.html", "▤"]
    ]],
    ["Platforms", [
      ["Architecture", "platform-architecture.html", "▧"],
      ["Artemis IV", "artemis-iv.html", "🧭"],
      ["ZEPHYR", "air-control.html", "🜁"],
      ["Artemis VI", "artemis.html", "🛰"],
      ["Guardian", "guardian.html", "🌐"],
      ["NEXUS", "clearglass-nexus.html", "🛡"],
      ["Government", "government.html", "🏛"],
      ["ClearPulse", "clearpulse.html", "📡"]
    ]],
    ["Intelligence", [
      ["Intelligence", "intelligence.html", "🧠"],
      ["Command Surface", "intelligence-command-surface.html", "🗺"],
      ["Interface", "intelligence-interface.html", "🖥"],
      ["Flow Intelligence", "clearglass.html", "🕸"],
      ["Flowsint", "flowsint.html", "🕸"],
      ["Ontario OSINT", "Ontario-osint.html", "🛰"],
      ["Revenue Engine", "revenue-engine.html", "💹"]
    ]],
    ["Company", [
      ["Home", "index.html", "⌂"],
      ["Web Design", "web-design.html", "💻"],
      ["Store", "store.html", "🛒"],
      ["Pricing", "pricing.html", "₵"],
      ["Offers", "offers/", "🎯"],
      ["SMB Kit", "smb-cyber-trust-kit.html", "🔐"]
    ]]
  ];

  var PRIMARY = [
    ["Home", "index.html"],
    ["Platforms", "platform-architecture.html"],
    ["Intelligence", "intelligence.html"],
    ["Guardian", "guardian.html"],
    ["Pricing", "pricing.html"]
  ];

  var here = (location.pathname.split("/").pop() || "index.html").toLowerCase();
  function localHref(path) { return /^https?:/i.test(path) ? path : "/" + path.replace(/^\/+/, ""); }
  function isCurrent(path) {
    var target = path.replace(/\/$/, "index.html").split("/").pop().toLowerCase();
    return target === here;
  }

  var css = [
    ":root{--cg-nav-h:72px}",
    "#cg-nav{position:fixed;top:max(10px,env(safe-area-inset-top));left:50%;transform:translateX(-50%);width:min(1180px,calc(100vw - 28px));z-index:2147483600;font-family:Inter,Urbanist,system-ui,-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;pointer-events:none;color:#eaf1ff}",
    "#cg-nav *{box-sizing:border-box}",
    "#cg-nav .cg-shell{pointer-events:auto;position:relative;display:flex;align-items:center;gap:18px;min-height:var(--cg-nav-h);padding:10px 12px 10px 14px;border:1px solid rgba(124,150,255,.38);border-radius:22px;background:linear-gradient(135deg,rgba(5,8,22,.84),rgba(13,18,42,.66));box-shadow:0 18px 60px rgba(0,0,0,.38),0 0 34px rgba(96,165,250,.16),inset 0 1px 0 rgba(255,255,255,.12);backdrop-filter:blur(18px) saturate(1.35);transition:border-color .22s ease,box-shadow .22s ease,transform .22s ease}",
    "#cg-nav .cg-shell::before{content:'';position:absolute;inset:0;border-radius:22px;pointer-events:none;background:linear-gradient(90deg,transparent,rgba(96,165,250,.18),rgba(167,139,250,.16),transparent);opacity:.58;mask:linear-gradient(#000 0 0) content-box,linear-gradient(#000 0 0);-webkit-mask:linear-gradient(#000 0 0) content-box,linear-gradient(#000 0 0);padding:1px;-webkit-mask-composite:xor;mask-composite:exclude}",
    "#cg-nav.scrolled .cg-shell{min-height:64px;border-color:rgba(96,165,250,.58);box-shadow:0 16px 48px rgba(0,0,0,.45),0 0 42px rgba(96,165,250,.22)}",
    "#cg-nav a{color:inherit;text-decoration:none}",
    "#cg-nav .cg-brand{display:flex;align-items:center;gap:11px;min-width:max-content;padding:8px 10px;border-radius:16px}",
    "#cg-nav .cg-mark{width:38px;height:38px;border-radius:12px;background:radial-gradient(circle at 35% 25%,#eaf6ff,#60a5fa 38%,#6d5cf0 72%,#100924);box-shadow:0 0 18px rgba(96,165,250,.58),inset 0 0 14px rgba(255,255,255,.35)}",
    "#cg-nav .cg-title{font-weight:850;letter-spacing:.06em;font-size:14px;line-height:1;text-transform:uppercase}#cg-nav .cg-title b{color:#a78bfa;text-shadow:0 0 12px rgba(167,139,250,.75)}#cg-nav .cg-sub{margin-top:4px;font-family:'IBM Plex Mono',ui-monospace,monospace;font-size:9px;letter-spacing:.22em;color:#9fb2ff;text-transform:uppercase}",
    "#cg-nav .cg-links{margin-left:auto;display:flex;align-items:center;gap:4px;padding:5px;border:1px solid rgba(124,150,255,.18);border-radius:999px;background:rgba(255,255,255,.045)}",
    "#cg-nav .cg-link{position:relative;display:inline-flex;align-items:center;padding:10px 13px;border-radius:999px;color:#cbd7ff;font-size:13px;font-weight:750;letter-spacing:.01em;transition:color .18s ease,background .18s ease,text-shadow .18s ease}",
    "#cg-nav .cg-link::after{content:'';position:absolute;left:14px;right:14px;bottom:5px;height:2px;border-radius:999px;background:linear-gradient(90deg,#60a5fa,#a78bfa,#5eead4);transform:scaleX(0);transform-origin:left;opacity:.9;box-shadow:0 0 14px rgba(96,165,250,.78);transition:transform .2s cubic-bezier(.16,1,.3,1)}",
    "#cg-nav .cg-link:hover,#cg-nav .cg-link:focus-visible,#cg-nav .cg-link.cur{color:#fff;background:rgba(96,165,250,.13);text-shadow:0 0 16px rgba(96,165,250,.55);outline:none}#cg-nav .cg-link:hover::after,#cg-nav .cg-link:focus-visible::after,#cg-nav .cg-link.cur::after{transform:scaleX(1)}",
    "#cg-nav .cg-cta{display:inline-flex;align-items:center;gap:8px;margin-left:4px;padding:10px 14px;border-radius:999px;color:#fff;font-size:12px;font-weight:850;letter-spacing:.08em;text-transform:uppercase;background:linear-gradient(135deg,rgba(96,165,250,.9),rgba(167,139,250,.9));box-shadow:0 0 22px rgba(96,165,250,.28);border:1px solid rgba(255,255,255,.16);transition:transform .18s ease,box-shadow .18s ease}",
    "#cg-nav .cg-cta:hover,#cg-nav .cg-cta:focus-visible{transform:translateY(-1px);box-shadow:0 0 30px rgba(96,165,250,.42);outline:none}",
    "#cg-nav .cg-toggle{display:grid;margin-left:0;width:44px;height:44px;border:1px solid rgba(124,150,255,.34);border-radius:14px;background:rgba(255,255,255,.06);color:#eaf1ff;cursor:pointer;place-items:center;box-shadow:inset 0 1px 0 rgba(255,255,255,.09)}#cg-nav .cg-toggle span,#cg-nav .cg-toggle span::before,#cg-nav .cg-toggle span::after{display:block;width:18px;height:2px;border-radius:9px;background:currentColor;box-shadow:0 0 10px rgba(96,165,250,.8);transition:transform .2s ease,opacity .2s ease}#cg-nav .cg-toggle span::before,#cg-nav .cg-toggle span::after{content:'';position:relative}#cg-nav .cg-toggle span::before{top:-6px}#cg-nav .cg-toggle span::after{top:4px}#cg-nav.open .cg-toggle span{transform:rotate(45deg)}#cg-nav.open .cg-toggle span::before{transform:translateY(6px) rotate(90deg)}#cg-nav.open .cg-toggle span::after{opacity:0}",
    "#cg-nav .cg-panel{pointer-events:auto;position:absolute;top:calc(100% + 10px);right:0;width:min(760px,calc(100vw - 28px));max-height:min(72vh,680px);overflow:auto;padding:16px;border:1px solid rgba(124,150,255,.32);border-radius:22px;background:linear-gradient(180deg,rgba(7,10,26,.96),rgba(12,16,38,.94));box-shadow:0 30px 90px rgba(0,0,0,.58),0 0 44px rgba(96,165,250,.16);backdrop-filter:blur(20px);opacity:0;transform:translateY(-10px) scale(.985);pointer-events:none;transition:opacity .2s ease,transform .2s ease}",
    "#cg-nav.open .cg-panel{opacity:1;transform:translateY(0) scale(1);pointer-events:auto}",
    "#cg-nav .cg-grid{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:10px}#cg-nav .cg-grp{padding:10px;border-radius:16px;background:rgba(255,255,255,.035);border:1px solid rgba(124,150,255,.12)}#cg-nav .cg-grp-title{font-family:'IBM Plex Mono',ui-monospace,monospace;font-size:10px;letter-spacing:.18em;text-transform:uppercase;color:#8ea4ff;margin:2px 4px 8px}#cg-nav .cg-item{display:flex;align-items:center;gap:9px;padding:9px 8px;border-radius:11px;color:#ccd7ff;font-size:13px;font-weight:700;transition:background .16s ease,color .16s ease}#cg-nav .cg-item:hover,#cg-nav .cg-item:focus-visible,#cg-nav .cg-item.cur{background:rgba(96,165,250,.14);color:#fff;outline:none}#cg-nav .cg-ic{width:25px;height:25px;border-radius:8px;display:grid;place-items:center;background:rgba(124,150,255,.12);border:1px solid rgba(124,150,255,.18);font-size:11px;color:#dce7ff}",
    "#cg-nav .cg-foot{display:flex;justify-content:space-between;gap:12px;margin-top:12px;padding:11px 12px;border-top:1px solid rgba(124,150,255,.16);font-family:'IBM Plex Mono',ui-monospace,monospace;font-size:9px;letter-spacing:.14em;color:#7f8bc7;text-transform:uppercase}",
    "@media(max-width:860px){#cg-nav{width:min(680px,calc(100vw - 20px));top:max(8px,env(safe-area-inset-top))}#cg-nav .cg-shell{min-height:62px;padding:8px 10px}#cg-nav .cg-links,#cg-nav .cg-cta{display:none}#cg-nav .cg-toggle{margin-left:auto}#cg-nav .cg-grid{grid-template-columns:1fr 1fr}#cg-nav .cg-title{font-size:13px}#cg-nav .cg-sub{font-size:8px}}",
    "@media(max-width:540px){#cg-nav .cg-grid{grid-template-columns:1fr}#cg-nav .cg-panel{left:0;right:auto;width:100%;max-height:76vh}#cg-nav .cg-brand{padding-left:4px}#cg-nav .cg-mark{width:34px;height:34px}#cg-nav .cg-foot{display:block;line-height:1.8}}",
    "@media(prefers-reduced-motion:reduce){#cg-nav *,#cg-nav *::before,#cg-nav *::after{transition:none!important;animation:none!important}}"
  ].join("");

  function build() {
    var style = document.createElement("style");
    style.textContent = css;
    document.head.appendChild(style);

    var root = document.createElement("nav");
    root.id = "cg-nav";
    root.setAttribute("aria-label", "ClearGlass primary navigation");

    var primaryHtml = PRIMARY.map(function (it) {
      var cur = isCurrent(it[1]) ? " cur" : "";
      return '<a class="cg-link' + cur + '" href="' + localHref(it[1]) + '">' + it[0] + '</a>';
    }).join("");

    var panelHtml = '<div class="cg-grid">';
    GROUPS.forEach(function (g) {
      panelHtml += '<div class="cg-grp"><div class="cg-grp-title">' + g[0] + '</div>';
      g[1].forEach(function (it) {
        var ext = /^https?:/i.test(it[1]);
        var cur = isCurrent(it[1]) ? " cur" : "";
        panelHtml += '<a class="cg-item' + cur + '" href="' + localHref(it[1]) + '"' + (ext ? ' target="_blank" rel="noopener noreferrer"' : '') + '><span class="cg-ic">' + it[2] + '</span><span>' + it[0] + '</span></a>';
      });
      panelHtml += '</div>';
    });
    panelHtml += '</div><div class="cg-foot"><span>ClearGlass Inc. · command navigation</span><span>clarity is power</span></div>';

    root.innerHTML = '<div class="cg-shell"><a class="cg-brand" href="' + localHref("index.html") + '" aria-label="ClearGlass home"><span class="cg-mark" aria-hidden="true"></span><span><span class="cg-title">ClearGlass<b>·</b>OS</span><span class="cg-sub">Neon Command Layer</span></span></a><div class="cg-links">' + primaryHtml + '</div><a class="cg-cta" href="' + localHref("offers/") + '">Engage</a><button class="cg-toggle" type="button" aria-label="Open navigation menu" aria-expanded="false" aria-controls="cg-nav-panel"><span></span></button></div><div class="cg-panel" id="cg-nav-panel">' + panelHtml + '</div>';
    document.body.appendChild(root);

    var toggle = root.querySelector(".cg-toggle");
    var panel = root.querySelector(".cg-panel");
    function setOpen(v) {
      root.classList.toggle("open", v);
      toggle.setAttribute("aria-expanded", v ? "true" : "false");
      toggle.setAttribute("aria-label", v ? "Close navigation menu" : "Open navigation menu");
    }
    toggle.addEventListener("click", function () { setOpen(!root.classList.contains("open")); });
    root.querySelector(".cg-brand").addEventListener("focus", function () { setOpen(false); });
    panel.addEventListener("click", function (e) { if (e.target.closest("a")) setOpen(false); });
    document.addEventListener("click", function (e) { if (!root.contains(e.target)) setOpen(false); });
    document.addEventListener("keydown", function (e) { if (e.key === "Escape") setOpen(false); });
    window.addEventListener("scroll", function () { root.classList.toggle("scrolled", window.scrollY > 12); }, { passive: true });
  }

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", build);
  else build();
})();

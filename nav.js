/* ClearGlass · shared site navigation — one self-contained hover menu for every
   page. Drop in with <script defer src="nav.js"></script>. No dependencies; a
   fixed right-edge tab expands a grouped menu on hover/focus/click. Indigo glass
   tuned to the homepage's sky-blue → violet accent, high z-index, collision-free,
   so it reads on both light and dark pages. */
(function () {
  "use strict";
  if (window.__cgNavLoaded) return;
  window.__cgNavLoaded = true;

  var GROUPS = [
    ["Command", [
      ["PERCIVAL OS", "percival-os.html", "◐"],
      ["SENTINEL · Live", "sentinel.html", "◉"],
      ["AEGIS · Legal Shield", "aegis.html", "⚖"],
      ["Agent Mesh", "agentmesh.html", "⌗"],
      ["AI Operator", "ai-operator.html", "🜂"],
      ["Command Console", "command-console.html", "▤"]
    ]],
    ["Platforms", [
      ["Artemis IV Core", "artemis-iv.html", "🧭"],
      ["Artemis VI", "artemis.html", "🛰"],
      ["Guardian", "guardian.html", "🌐"],
      ["ClearGlass NEXUS", "clearglass-nexus.html", "🛡"],
      ["Government", "government.html", "🏛"],
      ["ClearPulse", "clearpulse.html", "📡"]
    ]],
    ["Intelligence", [
      ["Intelligence", "intelligence.html", "🧠"],
      ["Command Surface", "intelligence-command-surface.html", "🗺"],
      ["Interface", "intelligence-interface.html", "🖥"],
      ["Revenue Engine", "revenue-engine.html", "💹"]
    ]],
    ["Legal & Finance", [
      ["Corporate Legal", "corporate-legal-advisor.html", "§"],
      ["Banking Law", "banking-law-advisor.html", "🏦"],
      ["ClearTax", "tax.html", "🧾"]
    ]],
    ["Company", [
      ["Home", "index.html", "⌂"]
    ]]
  ];

  var here = (location.pathname.split("/").pop() || "index.html").toLowerCase();

  var css = [
    "#cg-nav{position:fixed;top:0;right:0;height:100%;z-index:2147483600;font-family:'IBM Plex Mono',ui-monospace,monospace;pointer-events:none}",
    "#cg-nav *{box-sizing:border-box}",
    "#cg-nav .cg-tab{pointer-events:auto;position:absolute;top:50%;right:0;transform:translateY(-50%);writing-mode:vertical-rl;text-orientation:mixed;",
    "background:linear-gradient(180deg,rgba(18,20,42,.92),rgba(11,12,28,.92));color:#dbe4ff;border:1px solid rgba(124,150,255,.42);border-right:0;",
    "border-radius:10px 0 0 10px;padding:14px 7px;font-size:11px;letter-spacing:.28em;cursor:pointer;box-shadow:-6px 0 22px rgba(0,0,0,.4);backdrop-filter:blur(6px);user-select:none}",
    "#cg-nav .cg-tab:hover{color:#fff;border-color:rgba(124,150,255,.85);box-shadow:-6px 0 26px rgba(96,165,250,.32)}",
    "#cg-nav .cg-tab b{color:#a78bfa}",
    "#cg-nav .cg-panel{pointer-events:auto;position:absolute;top:0;right:0;height:100%;width:min(330px,86vw);overflow-y:auto;",
    "background:linear-gradient(180deg,rgba(15,17,34,.985),rgba(9,10,24,.985));border-left:1px solid rgba(124,150,255,.32);box-shadow:-24px 0 60px rgba(0,0,0,.6);",
    "transform:translateX(100%);transition:transform .26s cubic-bezier(.16,1,.3,1);padding:16px 14px 26px;color:#e7ecff}",
    "#cg-nav.open .cg-panel{transform:translateX(0)}",
    "#cg-nav .cg-head{display:flex;align-items:center;gap:10px;padding:4px 6px 12px;border-bottom:1px solid rgba(124,150,255,.18);margin-bottom:10px}",
    "#cg-nav .cg-mk{width:26px;height:26px;border-radius:7px;background:radial-gradient(circle at 40% 35%,#bcd4ff,#6d5cf0 58%,#161038);box-shadow:0 0 12px rgba(124,150,255,.6);flex:0 0 auto}",
    "#cg-nav .cg-title{font-weight:800;letter-spacing:.16em;font-size:13px}#cg-nav .cg-title b{background:linear-gradient(90deg,#60a5fa,#a78bfa);-webkit-background-clip:text;background-clip:text;-webkit-text-fill-color:transparent}",
    "#cg-nav .cg-sub{font-size:8.5px;letter-spacing:.18em;color:#8a90c4;text-transform:uppercase}",
    "#cg-nav .cg-x{margin-left:auto;cursor:pointer;color:#9aa0d4;background:none;border:0;font-size:18px;line-height:1}",
    "#cg-nav .cg-grp{font-size:9px;letter-spacing:.18em;text-transform:uppercase;color:#6f74a8;padding:10px 8px 4px}",
    "#cg-nav a.cg-link{display:flex;align-items:center;gap:11px;padding:9px 10px;border-radius:9px;color:#cdd6f5;text-decoration:none;font-size:13px;font-family:'Inter',system-ui,sans-serif;border:1px solid transparent;transition:.13s}",
    "#cg-nav a.cg-link:hover{background:rgba(124,150,255,.12);color:#fff;border-color:rgba(124,150,255,.28)}",
    "#cg-nav a.cg-link .ic{width:24px;height:24px;border-radius:6px;display:grid;place-items:center;font-size:13px;background:rgba(124,150,255,.1);border:1px solid rgba(124,150,255,.2);flex:0 0 auto}",
    "#cg-nav a.cg-link.cur{background:linear-gradient(100deg,rgba(96,165,250,.2),rgba(167,139,250,.06));border-color:rgba(124,150,255,.5);color:#fff}",
    "#cg-nav a.cg-link.cur .ic{background:rgba(124,150,255,.24)}",
    "#cg-nav .cg-foot{font-size:8.5px;letter-spacing:.1em;color:#595e8c;text-align:center;padding:14px 0 2px}",
    "@media(max-width:640px){#cg-nav .cg-tab{padding:11px 6px;font-size:10px;letter-spacing:.2em}}"
  ].join("");

  function build() {
    var style = document.createElement("style");
    style.textContent = css;
    document.head.appendChild(style);

    var root = document.createElement("div");
    root.id = "cg-nav";

    var tab = document.createElement("div");
    tab.className = "cg-tab";
    tab.setAttribute("role", "button");
    tab.setAttribute("tabindex", "0");
    tab.setAttribute("aria-label", "Open ClearGlass navigation");
    tab.innerHTML = "☰&nbsp; <b>MENU</b>";

    var panel = document.createElement("div");
    panel.className = "cg-panel";

    var html = '<div class="cg-head"><div class="cg-mk"></div>' +
      '<div><div class="cg-title">ClearGlass<b>·</b>OS</div><div class="cg-sub">Navigation</div></div>' +
      '<button class="cg-x" aria-label="Close">✕</button></div>';
    GROUPS.forEach(function (g) {
      html += '<div class="cg-grp">' + g[0] + "</div>";
      g[1].forEach(function (it) {
        var cur = it[1].toLowerCase() === here ? " cur" : "";
        html += '<a class="cg-link' + cur + '" href="' + it[1] + '">' +
          '<span class="ic">' + it[2] + "</span>" + it[0] +
          (cur ? ' <span style="margin-left:auto;font-family:monospace;font-size:9px;color:#8a90c4">● here</span>' : "") +
          "</a>";
      });
    });
    html += '<div class="cg-foot">ClearGlass Inc. · Clarity Is Power</div>';
    panel.innerHTML = html;

    root.appendChild(tab);
    root.appendChild(panel);
    document.body.appendChild(root);

    var openT;
    function open() { clearTimeout(openT); root.classList.add("open"); }
    function close() { root.classList.remove("open"); }
    tab.addEventListener("mouseenter", open);
    tab.addEventListener("click", open);
    tab.addEventListener("keydown", function (e) { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); open(); } });
    panel.addEventListener("mouseenter", open);
    root.addEventListener("mouseleave", function () { openT = setTimeout(close, 220); });
    panel.querySelector(".cg-x").addEventListener("click", close);
    document.addEventListener("keydown", function (e) { if (e.key === "Escape") close(); });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", build);
  } else {
    build();
  }
})();

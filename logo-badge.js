/* ClearGlass · adaptive company logo badge — a fixed, self-contained brand mark
   for every page except the homepage. Drop in with <script defer src="/logo-badge.js"></script>.
   It uses the official company logo, adapts to dense/mobile pages, accounts for
   safe-area insets, and coordinates with stealth-glass.js via shared CSS vars. */
(function () {
  "use strict";
  if (window.__cgLogoBadge) return;
  window.__cgLogoBadge = true;

  var path = location.pathname.replace(/\/+$/, "/");
  var last = (location.pathname.split("/").pop() || "").toLowerCase();
  var isHome = path === "/" || (last === "index.html" && location.pathname.toLowerCase() === "/index.html");
  if (isHome) return;

  var LOGO = "/assets/images/clearglass-logo.png";
  var HOME = "/index.html";

  function build() {
    if (document.getElementById("cg-logo-badge")) return;

    var css = [
      ":root{--cg-floating-left:max(14px,calc(env(safe-area-inset-left,0px) + 14px));",
      "--cg-floating-bottom:max(14px,calc(env(safe-area-inset-bottom,0px) + 14px));",
      "--cg-logo-size:54px;--cg-logo-gap:12px;--cg-stealth-bottom:calc(var(--cg-floating-bottom) + var(--cg-logo-size) + var(--cg-logo-gap));}",
      "#cg-logo-badge{position:fixed;left:var(--cg-floating-left);bottom:var(--cg-floating-bottom);z-index:2147483000;",
      "min-width:var(--cg-logo-size);height:var(--cg-logo-size);border-radius:999px;display:inline-flex;align-items:center;gap:10px;overflow:hidden;",
      "padding:5px 14px 5px 5px;text-decoration:none;color:#eef5ff;",
      "background:linear-gradient(135deg,rgba(18,23,44,.88),rgba(8,12,26,.82));",
      "border:1px solid rgba(124,150,255,.42);box-shadow:0 10px 30px rgba(0,0,0,.38),0 0 18px rgba(124,150,255,.24),inset 0 1px 0 rgba(255,255,255,.13);",
      "backdrop-filter:blur(12px) saturate(1.35);-webkit-backdrop-filter:blur(12px) saturate(1.35);",
      "transition:transform .18s cubic-bezier(.16,1,.3,1),box-shadow .18s ease,border-color .18s ease;line-height:1;max-width:min(270px,calc(100vw - 28px - env(safe-area-inset-left,0px) - env(safe-area-inset-right,0px)))}",
      "#cg-logo-badge:hover{transform:translateY(-2px) scale(1.025);border-color:rgba(124,150,255,.85);box-shadow:0 12px 34px rgba(0,0,0,.44),0 0 24px rgba(96,165,250,.38),inset 0 1px 0 rgba(255,255,255,.16)}",
      "#cg-logo-badge img{width:calc(var(--cg-logo-size) - 10px);height:calc(var(--cg-logo-size) - 10px);border-radius:50%;object-fit:cover;display:block;flex:0 0 auto}",
      "#cg-logo-badge .cg-lb-text{display:flex;flex-direction:column;gap:3px;min-width:0;white-space:nowrap}",
      "#cg-logo-badge .cg-lb-name{font:800 11px/1 'Urbanist',system-ui,sans-serif;letter-spacing:.14em;text-transform:uppercase;color:#fff}",
      "#cg-logo-badge .cg-lb-sub{font:600 9px/1 'IBM Plex Mono',ui-monospace,monospace;letter-spacing:.12em;text-transform:uppercase;color:#aab8d4}",
      "#cg-logo-badge:focus-visible{outline:2px solid #a78bfa;outline-offset:3px}",
      "@media(max-width:720px){:root{--cg-logo-size:46px;--cg-logo-gap:10px}#cg-logo-badge{padding:4px;width:var(--cg-logo-size);max-width:var(--cg-logo-size);border-radius:50%;gap:0}#cg-logo-badge .cg-lb-text{position:absolute;width:1px;height:1px;overflow:hidden;clip:rect(0 0 0 0);white-space:nowrap}}",
      "@media(print){#cg-logo-badge{display:none}}"
    ].join("");

    var style = document.createElement("style");
    style.textContent = css;
    document.head.appendChild(style);

    var a = document.createElement("a");
    a.id = "cg-logo-badge";
    a.href = HOME;
    a.setAttribute("aria-label", "ClearGlass Inc. — home");
    a.title = "ClearGlass Inc. — home";

    var img = document.createElement("img");
    img.src = LOGO;
    img.alt = "ClearGlass Inc. company logo";
    img.decoding = "async";
    img.loading = "lazy";

    var text = document.createElement("span");
    text.className = "cg-lb-text";
    text.innerHTML = '<span class="cg-lb-name">ClearGlassInc</span><span class="cg-lb-sub">Home</span>';

    a.appendChild(img);
    a.appendChild(text);
    document.body.appendChild(a);
  }

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", build);
  else build();
})();

/* ClearGlass · corner logo badge — a fixed, self-contained brand mark for every
   page EXCEPT the homepage. Drop in with <script defer src="/logo-badge.js"></script>.
   No dependencies. Sits in the bottom-RIGHT corner and never collides with page
   navbars (top). Self-guards the homepage: it returns early on "/" or
   "/index.html", so it physically cannot render there even if mistakenly
   included. Idempotent — a second include is a no-op.

   The badge lives inside a shared corner "dock" (#cg-dock, a flex row anchored to
   the bottom-right). On its own the dock holds just the coin. On pages that also
   load the Writing-help control, that control docks its pill into the SAME row,
   to the LEFT of the coin, so the two read as one continuous, glowing control
   cluster instead of two elements stacked on top of each other.

   Advanced treatment: a single clip-safe NEON HALO is painted behind the whole
   dock (via #cg-dock::before), so it wraps whatever the cluster currently is —
   coin alone, or pill + coin — as one aura. It breathes on an opacity-only loop
   and is frozen under prefers-reduced-motion. The badge keeps overflow:hidden to
   mask the logo to the circle; the halo lives on the dock, not the badge, so the
   clip can't touch it. */
(function () {
  "use strict";
  if (window.__cgLogoBadge) return;
  window.__cgLogoBadge = true;

  // Homepage guard: skip the site root and root index.html.
  var path = location.pathname.replace(/\/+$/, "/");
  var last = (location.pathname.split("/").pop() || "").toLowerCase();
  var isHome = path === "/" || (last === "index.html" && location.pathname.toLowerCase() === "/index.html");
  if (isHome) return;

  var LOGO = "/assets/images/clearglass-logo.png";
  var HOME = "/index.html";

  function build() {
    if (document.getElementById("cg-dock")) return;

    var css = [
      /* shared corner dock — a flex row other corner controls can join */
      "#cg-dock{position:fixed;right:18px;bottom:18px;z-index:2147483000;",
      "display:inline-flex;align-items:center;pointer-events:none}",
      "#cg-dock>*{pointer-events:auto}",
      /* one neon halo wrapping the whole cluster (coin alone, or pill + coin) */
      "#cg-dock::before{content:'';position:absolute;inset:-16px -16px -16px -22px;",
      "border-radius:999px;pointer-events:none;z-index:-1;will-change:opacity;",
      "background:radial-gradient(120% 130% at 82% 50%,rgba(96,165,250,.42) 0%,rgba(167,139,250,.28) 42%,rgba(57,216,255,.12) 60%,transparent 74%);",
      "filter:blur(9px);opacity:.72;animation:cgDockGlow 3.6s ease-in-out infinite}",
      "@keyframes cgDockGlow{0%,100%{opacity:.5}50%{opacity:.96}}",

      "#cg-logo-badge{position:relative;flex:0 0 auto;",
      "width:54px;height:54px;border-radius:50%;display:block;overflow:hidden;",
      "background:linear-gradient(180deg,rgba(18,20,42,.92),rgba(11,12,28,.92));",
      /* neon ring on the border + outer bloom, matched to the pill it docks with */
      "border:1px solid rgba(124,150,255,.55);",
      "box-shadow:0 6px 22px rgba(0,0,0,.4),0 0 16px rgba(96,165,250,.45),0 0 28px rgba(167,139,250,.3);",
      "backdrop-filter:blur(6px);-webkit-backdrop-filter:blur(6px);",
      "transition:transform .18s cubic-bezier(.16,1,.3,1),box-shadow .18s ease;line-height:0}",
      /* scale only (no lift) so the coin never detaches from the pill beside it */
      "#cg-logo-badge:hover{transform:scale(1.06);border-color:rgba(150,180,255,.95);",
      "box-shadow:0 8px 26px rgba(0,0,0,.46),0 0 26px rgba(96,165,250,.6),0 0 44px rgba(167,139,250,.45)}",
      "#cg-logo-badge img{width:100%;height:100%;object-fit:cover;display:block}",
      "#cg-logo-badge:focus-visible{outline:2px solid #a78bfa;outline-offset:3px}",
      "@media(max-width:640px){#cg-dock{right:14px;bottom:14px}#cg-logo-badge{width:46px;height:46px}}",
      /* honour reduced motion — freeze the halo at a steady mid glow */
      "@media (prefers-reduced-motion:reduce){#cg-dock::before{animation:none;opacity:.7}}"
    ].join("");

    var style = document.createElement("style");
    style.textContent = css;
    document.head.appendChild(style);

    var dock = document.createElement("div");
    dock.id = "cg-dock";
    document.body.appendChild(dock);

    var a = document.createElement("a");
    a.id = "cg-logo-badge";
    a.href = HOME;
    a.setAttribute("aria-label", "ClearGlass — home");
    a.title = "ClearGlass — home";

    var img = document.createElement("img");
    img.src = LOGO;
    img.alt = "ClearGlass logo";
    img.decoding = "async";
    img.loading = "lazy";

    a.appendChild(img);
    dock.appendChild(a);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", build);
  } else {
    build();
  }
})();

/* ClearGlass · corner logo badge — a fixed, self-contained brand mark for every
   page EXCEPT the homepage. Drop in with <script defer src="/logo-badge.js"></script>.
   No dependencies. Sits in the bottom-RIGHT corner (paired directly under the
   stealth-glass control, which anchors the same corner) so the two form one
   coherent control cluster and never collide with page navbars (top). Self-guards
   the homepage: it returns early on "/" or "/index.html", so it physically cannot
   render there even if mistakenly included. Idempotent — a second include is a no-op.

   Advanced treatment: a clip-safe, separately-layered NEON HALO sits behind the
   badge (the badge itself keeps overflow:hidden to mask the logo to the circle,
   so the halo cannot live in a pseudo-element — it is its own element). The halo
   breathes on an opacity-only loop and is killed under prefers-reduced-motion. */
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
    if (document.getElementById("cg-logo-badge")) return;

    var css = [
      /* neon halo — its own layer so overflow:hidden on the badge can't clip it */
      "#cg-logo-badge-glow{position:fixed;right:6px;bottom:6px;z-index:2147482999;",
      "width:78px;height:78px;border-radius:50%;pointer-events:none;",
      "background:radial-gradient(circle,rgba(96,165,250,.42) 0%,rgba(167,139,250,.28) 45%,transparent 72%);",
      "filter:blur(2px);opacity:.7;will-change:opacity;animation:cgBadgeNeon 3.6s ease-in-out infinite}",
      "@keyframes cgBadgeNeon{0%,100%{opacity:.5}50%{opacity:1}}",

      "#cg-logo-badge{position:fixed;right:18px;bottom:18px;z-index:2147483000;",
      "width:54px;height:54px;border-radius:50%;display:block;overflow:hidden;",
      "background:linear-gradient(180deg,rgba(18,20,42,.92),rgba(11,12,28,.92));",
      /* intensified neon ring on the border + outer bloom */
      "border:1px solid rgba(124,150,255,.55);",
      "box-shadow:0 6px 22px rgba(0,0,0,.4),0 0 16px rgba(96,165,250,.45),0 0 28px rgba(167,139,250,.3);",
      "backdrop-filter:blur(6px);-webkit-backdrop-filter:blur(6px);",
      "transition:transform .18s cubic-bezier(.16,1,.3,1),box-shadow .18s ease;line-height:0}",
      "#cg-logo-badge:hover{transform:translateY(-2px) scale(1.05);border-color:rgba(150,180,255,.95);",
      "box-shadow:0 8px 26px rgba(0,0,0,.46),0 0 26px rgba(96,165,250,.6),0 0 44px rgba(167,139,250,.45)}",
      "#cg-logo-badge img{width:100%;height:100%;object-fit:cover;display:block}",
      "#cg-logo-badge:focus-visible{outline:2px solid #a78bfa;outline-offset:3px}",
      "@media(max-width:640px){#cg-logo-badge{width:46px;height:46px;right:14px;bottom:14px}",
      "#cg-logo-badge-glow{width:68px;height:68px;right:3px;bottom:3px}}",
      /* honour reduced motion — freeze the halo at a steady mid glow */
      "@media (prefers-reduced-motion:reduce){#cg-logo-badge-glow{animation:none;opacity:.7}}"
    ].join("");

    var style = document.createElement("style");
    style.textContent = css;
    document.head.appendChild(style);

    var glow = document.createElement("div");
    glow.id = "cg-logo-badge-glow";
    glow.setAttribute("aria-hidden", "true");
    document.body.appendChild(glow);

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
    document.body.appendChild(a);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", build);
  } else {
    build();
  }
})();

/* ClearGlass · corner logo badge — a fixed, self-contained brand mark for every
   page EXCEPT the homepage. Drop in with <script defer src="/logo-badge.js"></script>.
   No dependencies. Sits in the bottom-left corner so it never collides with page
   navbars (top) or the shared nav menu tab (right edge). Self-guards the homepage:
   it returns early on "/" or "/index.html", so it physically cannot render there
   even if mistakenly included. Idempotent — a second include is a no-op. */
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
      "#cg-logo-badge{position:fixed;left:18px;bottom:18px;z-index:2147483000;",
      "width:54px;height:54px;border-radius:50%;display:block;overflow:hidden;",
      "background:linear-gradient(180deg,rgba(18,20,42,.92),rgba(11,12,28,.92));",
      "border:1px solid rgba(124,150,255,.42);box-shadow:0 6px 22px rgba(0,0,0,.4),0 0 14px rgba(124,150,255,.28);",
      "backdrop-filter:blur(6px);-webkit-backdrop-filter:blur(6px);",
      "transition:transform .18s cubic-bezier(.16,1,.3,1),box-shadow .18s ease;line-height:0}",
      "#cg-logo-badge:hover{transform:translateY(-2px) scale(1.05);border-color:rgba(124,150,255,.85);",
      "box-shadow:0 8px 26px rgba(0,0,0,.46),0 0 20px rgba(96,165,250,.42)}",
      "#cg-logo-badge img{width:100%;height:100%;object-fit:cover;display:block}",
      "#cg-logo-badge:focus-visible{outline:2px solid #a78bfa;outline-offset:3px}",
      "@media(max-width:640px){#cg-logo-badge{width:46px;height:46px;left:14px;bottom:14px}}"
    ].join("");

    var style = document.createElement("style");
    style.textContent = css;
    document.head.appendChild(style);

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

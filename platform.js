/* ClearGlass · platform layer — progressive enhancement with real, shipping
   browser technology. Drop in with <script defer src="platform.js"></script>.

     1) PWA: registers the service worker (offline shell + fast repeat visits)
        and injects the web-app manifest link where a page lacks it, making the
        site installable.
     2) Instant navigation: injects a Speculation Rules script so Chromium
        prefetches (and prerenders on hover) same-origin pages — typical
        click→render drops to near-zero. Other engines ignore it harmlessly.
     3) Cross-document View Transitions: opts the site into smooth page-to-page
        fades (Chromium 126+), disabled under prefers-reduced-motion.

   Everything is feature-detected; on unsupported browsers this file is inert. */
(function () {
  "use strict";
  if (window.__cgPlatform) return;
  window.__cgPlatform = true;

  /* ── 1) PWA: manifest link + service worker ─────────────────────────────── */
  if (!document.querySelector('link[rel="manifest"]')) {
    var mf = document.createElement("link");
    mf.rel = "manifest";
    mf.href = "manifest.webmanifest";
    document.head.appendChild(mf);
  }
  if (!document.querySelector('meta[name="theme-color"]')) {
    var tc = document.createElement("meta");
    tc.name = "theme-color";
    tc.content = "#0b0f1e";
    document.head.appendChild(tc);
  }
  // first-class icons (vector favicon + iOS home-screen icon) where a page lacks them
  function addLink(sel, attrs) {
    if (document.querySelector(sel)) return;
    var l = document.createElement("link");
    Object.keys(attrs).forEach(function (k) { l.setAttribute(k, attrs[k]); });
    document.head.appendChild(l);
  }
  addLink('link[rel="icon"][type="image/svg+xml"]', { rel: "icon", type: "image/svg+xml", href: "icon.svg" });
  addLink('link[rel="apple-touch-icon"]', { rel: "apple-touch-icon", href: "logo.png" });

  /* ── advanced motion layer (fx.css + fx.js) — progressive enhancement ───── */
  addLink('link[href="fx.css"]', { rel: "stylesheet", href: "fx.css" });
  if (!document.querySelector('script[src="fx.js"]')) {
    var fx = document.createElement("script");
    fx.src = "fx.js"; fx.defer = true;
    document.body.appendChild(fx);
  }
  if ("serviceWorker" in navigator) {
    window.addEventListener("load", function () {
      navigator.serviceWorker.register("sw.js").catch(function () {
        /* registration is best-effort; never break the page */
      });
    });
  }

  /* ── 2) instant navigation: Speculation Rules (Chromium) ────────────────── */
  try {
    if (HTMLScriptElement.supports && HTMLScriptElement.supports("speculationrules")) {
      var rules = document.createElement("script");
      rules.type = "speculationrules";
      rules.textContent = JSON.stringify({
        prefetch: [{ where: { href_matches: "/*" }, eagerness: "moderate" }],
        prerender: [{ where: { href_matches: "/*" }, eagerness: "moderate" }]
      });
      document.head.appendChild(rules);
    }
  } catch (e) { /* inert on unsupported engines */ }

  /* ── 3) cross-document view transitions (motion-pref aware) ─────────────── */
  try {
    var reduce = matchMedia("(prefers-reduced-motion: reduce)").matches;
    if (!reduce && "CSSViewTransitionRule" in window === false) {
      // @view-transition is pure CSS; inject it regardless — engines without
      // support ignore the rule, and we skip it entirely under reduced motion.
    }
    if (!reduce) {
      var st = document.createElement("style");
      st.textContent = "@view-transition{navigation:auto}" +
        "::view-transition-old(root),::view-transition-new(root){animation-duration:.22s}";
      document.head.appendChild(st);
    }
  } catch (e) { /* inert */ }
})();

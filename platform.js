/* ClearGlass performance platform.
   Purpose: keep shared pages installable and fast without attaching a second
   animation stack, speculative prerenders, smooth-scroll engines, or pointer loops. */
(function () {
  "use strict";
  if (window.__cgPlatform) return;
  window.__cgPlatform = true;

  var doc = document;
  var root = doc.documentElement;
  var reduce = false;
  var coarse = false;
  var lowMemory = false;

  try {
    reduce = matchMedia("(prefers-reduced-motion: reduce)").matches;
    coarse = matchMedia("(hover: none), (pointer: coarse), (max-width: 768px)").matches;
    lowMemory = typeof navigator.deviceMemory === "number" && navigator.deviceMemory <= 4;
  } catch (e) {}

  root.classList.add("cg-performance-runtime");
  if (reduce || coarse || lowMemory) root.classList.add("cg-performance-lite");

  function addLink(selector, attrs) {
    if (doc.querySelector(selector)) return;
    var node = doc.createElement("link");
    Object.keys(attrs).forEach(function (key) { node.setAttribute(key, attrs[key]); });
    doc.head.appendChild(node);
  }

  addLink('link[rel="manifest"]', { rel: "manifest", href: "/manifest.webmanifest" });
  addLink('link[rel="icon"][type="image/svg+xml"]', { rel: "icon", type: "image/svg+xml", href: "/icon.svg" });
  addLink('link[rel="apple-touch-icon"]', { rel: "apple-touch-icon", href: "/logo.png" });

  if (!doc.querySelector('meta[name="theme-color"]')) {
    var theme = doc.createElement("meta");
    theme.name = "theme-color";
    theme.content = "#07111f";
    doc.head.appendChild(theme);
  }

  var style = doc.createElement("style");
  style.id = "cg-performance-guardrails";
  style.textContent = [
    "html.cg-performance-runtime{scroll-behavior:auto!important}",
    ".cg-performance-runtime main>section:not(:first-child),.cg-performance-runtime body>section:not(:first-of-type){content-visibility:auto;contain-intrinsic-size:auto 900px}",
    ".cg-performance-runtime [data-cg-offscreen],.cg-performance-runtime [data-cg-offscreen] *{animation-play-state:paused!important}",
    ".cg-performance-runtime.cg-page-hidden *{animation-play-state:paused!important}",
    ".cg-performance-runtime .rv{opacity:1!important;transform:none!important;filter:none!important;visibility:visible!important}",
    ".cg-performance-runtime [data-reveal]{opacity:1!important;transform:none!important;filter:none!important;visibility:visible!important;transition-delay:0s!important}",
    ".cg-performance-lite .cursor-glow,.cg-performance-lite #cg-spotlight,.cg-performance-lite #cg-neon-aura,.cg-performance-lite .artemis-reticle{display:none!important}",
    ".cg-performance-lite .hero-prism,.cg-performance-lite .hero-line,.cg-performance-lite .scroll-line,.cg-performance-lite .artemis-grid::after,.cg-performance-lite .artemis-grid span,.cg-performance-lite .artemis-toggle__signal,.cg-performance-lite #cg-related .cgr-box::before{animation:none!important}",
    ".cg-performance-lite .nav,.cg-performance-lite .mobile-menu,.cg-performance-lite .cg-topnav,.cg-performance-lite #cg-stealth-btn{backdrop-filter:none!important;-webkit-backdrop-filter:none!important}",
    "@media(max-width:768px){.cg-performance-runtime *{scroll-behavior:auto!important}.cg-performance-runtime video[autoplay]{display:none!important}.cg-performance-runtime .hero-prism{opacity:.45!important}.cg-performance-runtime .artemis-grid{opacity:.22!important}}",
    "@media(prefers-reduced-motion:reduce){.cg-performance-runtime *, .cg-performance-runtime *::before, .cg-performance-runtime *::after{animation-duration:.001ms!important;animation-iteration-count:1!important;transition-duration:.001ms!important;scroll-behavior:auto!important}}"
  ].join("");
  doc.head.appendChild(style);

  function revealStaticContent() {
    try {
      if (window.rvObs && typeof window.rvObs.disconnect === "function") window.rvObs.disconnect();
      if (window.sectionObserver && typeof window.sectionObserver.disconnect === "function" && (coarse || lowMemory)) {
        window.sectionObserver.disconnect();
      }
    } catch (e) {}

    doc.querySelectorAll(".rv").forEach(function (el) { el.classList.add("vis"); });
    doc.querySelectorAll("[data-reveal]").forEach(function (el) {
      el.classList.add("cg-in");
      el.removeAttribute("data-reveal-delay");
    });
  }

  function prioritizeLcp() {
    var hero = doc.querySelector("main, .hero, header");
    if (!hero) return;
    var media = hero.querySelector("img,video");
    if (!media) return;
    media.setAttribute("fetchpriority", "high");
    if (media.tagName === "IMG") {
      media.loading = "eager";
      media.decoding = "async";
    } else {
      media.preload = "metadata";
      if (coarse || lowMemory) {
        try { media.pause(); } catch (e) {}
        media.removeAttribute("autoplay");
      }
    }
  }

  function installOffscreenPause() {
    if (!("IntersectionObserver" in window) || reduce) return;
    var animated = doc.querySelectorAll("section,footer,aside#cg-related");
    var observer = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        entry.target.toggleAttribute("data-cg-offscreen", !entry.isIntersecting);
      });
    }, { rootMargin: "160px 0px", threshold: 0.01 });
    animated.forEach(function (node) { observer.observe(node); });
  }

  function disableScriptedSmoothScroll() {
    doc.addEventListener("click", function (event) {
      var link = event.target.closest && event.target.closest('a[href^="#"]');
      if (!link) return;
      var href = link.getAttribute("href");
      if (!href || href === "#") return;
      var target;
      try { target = doc.querySelector(href); } catch (e) { return; }
      if (!target) return;
      event.preventDefault();
      event.stopImmediatePropagation();
      target.scrollIntoView({ behavior: "auto", block: "start" });
      try { history.replaceState(null, "", href); } catch (e) {}
    }, true);
  }

  function addFounderLink() {
    var actions = doc.querySelector("#founder .founder-actions");
    if (!actions || actions.querySelector("[data-founder-linkedin]")) return;
    var link = doc.createElement("a");
    link.href = "https://www.linkedin.com/in/desmondotieno";
    link.className = "btn btn-glass";
    link.target = "_blank";
    link.rel = "noopener noreferrer me";
    link.setAttribute("data-founder-linkedin", "true");
    link.textContent = "LinkedIn Profile ↗";
    actions.appendChild(link);
  }

  function ready() {
    revealStaticContent();
    prioritizeLcp();
    installOffscreenPause();
    disableScriptedSmoothScroll();
    addFounderLink();
  }

  if (doc.readyState === "loading") doc.addEventListener("DOMContentLoaded", ready, { once: true });
  else ready();

  doc.addEventListener("visibilitychange", function () {
    root.classList.toggle("cg-page-hidden", doc.hidden);
  }, { passive: true });

  if ("serviceWorker" in navigator) {
    window.addEventListener("load", function () {
      var register = function () {
        navigator.serviceWorker.register("/sw.js").catch(function () {});
      };
      if ("requestIdleCallback" in window) requestIdleCallback(register, { timeout: 3000 });
      else setTimeout(register, 1200);
    }, { once: true });
  }
})();

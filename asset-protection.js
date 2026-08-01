/* ClearGlass · asset protection — labels the page with the ClearGlass copyright
   and deters casual copying of brand imagery. Drop in with
   <script defer src="/asset-protection.js"></script>. No dependencies.
   Idempotent — a second include is a no-op.

   What it does:
   - Injects a <meta name="copyright"> tag if the page doesn't already have one.
   - Marks every <img> (including ones added later) as non-draggable.
   - Blocks the context menu and drag-start on images only — text selection,
     links, and everything else on the page behave normally.
   - Adds an unobtrusive ClearGlass watermark to opt-in
     [data-cg-watermark] regions.
   - Adds casual-copy friction to opt-in [data-cg-protected] regions while
     preserving forms, editable content, keyboard navigation, and global UX.
   - Stamps a machine-readable ownership notice on window.__cgAssetNotice.

   This is a deterrent for casual right-click/drag copying; the authoritative
   ownership record is the copyright metadata embedded in the image files
   themselves and the LICENSE at the repo root. */
(function () {
  "use strict";
  if (window.__cgAssetProtection) return;
  window.__cgAssetProtection = true;

  var NOTICE = "© 2026 ClearGlass Inc. All Rights Reserved.";
  window.__cgAssetNotice =
    NOTICE + " Images and brand assets on this site are the property of " +
    "ClearGlass Inc. and may not be reproduced without written permission.";

  function isImage(el) {
    return !!el && (el.tagName === "IMG" || el.tagName === "PICTURE" ||
      (el.tagName === "SVG" || el.tagName === "svg"));
  }

  function shield(img) {
    if (img.__cgShielded) return;
    img.__cgShielded = true;
    img.setAttribute("draggable", "false");
  }

  function shieldAll(root) {
    var imgs = (root || document).querySelectorAll("img");
    for (var i = 0; i < imgs.length; i++) shield(imgs[i]);
  }

  function installProtectionStyles() {
    if (document.getElementById("cg-asset-protection-styles")) return;
    var style = document.createElement("style");
    style.id = "cg-asset-protection-styles";
    style.textContent =
      "[data-cg-watermark]{position:relative;isolation:isolate}" +
      "[data-cg-watermark]::after{" +
        "content:attr(data-cg-watermark);position:absolute;right:1rem;bottom:.75rem;" +
        "z-index:20;pointer-events:none;color:rgba(220,245,255,.38);" +
        "font:700 10px/1.2 Inter,system-ui,sans-serif;letter-spacing:.16em;" +
        "text-transform:uppercase;text-shadow:0 0 12px rgba(34,211,238,.45)" +
      "}" +
      "[data-cg-protected],[data-cg-protected] *{-webkit-user-select:none;user-select:none}" +
      "[data-cg-protected] input,[data-cg-protected] textarea," +
      "[data-cg-protected] select,[data-cg-protected] [contenteditable=true]{" +
        "-webkit-user-select:text;user-select:text" +
      "}" +
      ".protected,.protected *{-webkit-user-select:none;-moz-user-select:none;" +
        "-ms-user-select:none;user-select:none;-webkit-touch-callout:none}" +
      ".protected input,.protected textarea,.protected select," +
      ".protected [contenteditable=true]{-webkit-user-select:text;user-select:text}" +
      ".protected-watermark{position:relative;overflow:hidden;isolation:isolate}" +
      ".protected-watermark::after{content:\"ClearGlassInc. • Confidential • © 2026\";" +
        "position:absolute;inset:0;z-index:20;display:grid;place-items:center;" +
        "font-size:clamp(14px,2vw,28px);font-weight:700;letter-spacing:.35em;" +
        "text-transform:uppercase;color:rgba(255,255,255,.08);" +
        "transform:rotate(-18deg);pointer-events:none;white-space:nowrap}" +
      ".protected-watermark::before{content:\"\";position:absolute;inset:0;z-index:19;" +
        "background-image:linear-gradient(135deg,transparent 0%," +
        "rgba(255,255,255,.03) 50%,transparent 100%);background-size:120px 120px;" +
        "opacity:.7;pointer-events:none}" +
      ".blur-preview{filter:blur(6px);transition:filter 180ms ease}" +
      ".blur-preview:hover,.blur-preview:focus-within{filter:blur(0)}" +
      "@media (prefers-reduced-motion:reduce){.blur-preview{transition:none}}" +
      "@media print{[data-cg-watermark]::after{position:fixed;right:1cm;bottom:1cm;color:#777}}";
    document.head.appendChild(style);
  }

  function closestProtected(el) {
    return el && el.closest ? el.closest("[data-cg-protected]") : null;
  }

  function closestClassProtected(el) {
    return el && el.closest ? el.closest(".protected") : null;
  }

  function isEditable(el) {
    return !!(el && el.closest &&
      el.closest("input,textarea,select,[contenteditable=true]"));
  }

  function loadCyberEditorialVisual() {
    var last = (location.pathname.split("/").pop() || "").toLowerCase();
    if (last !== "cyber-defense-console.html" ||
        document.getElementById("cg-editorial-visuals-script")) return;
    var script = document.createElement("script");
    script.id = "cg-editorial-visuals-script";
    script.src = "/editorial-visuals.js";
    script.defer = true;
    document.head.appendChild(script);
  }

  function init() {
    if (!document.querySelector('meta[name="copyright"]')) {
      var meta = document.createElement("meta");
      meta.name = "copyright";
      meta.content = NOTICE;
      document.head.appendChild(meta);
    }

    installProtectionStyles();
    shieldAll(document);
    loadCyberEditorialVisual();

    // A non-identifying, per-page token helps correlate an authorized preview
    // with client-side diagnostics without fingerprinting the visitor.
    var sessionToken;
    if (window.crypto && window.crypto.getRandomValues) {
      var randomBytes = new Uint8Array(8);
      window.crypto.getRandomValues(randomBytes);
      sessionToken = Array.prototype.map.call(randomBytes, function (byte) {
        return byte.toString(16).padStart(2, "0");
      }).join("").toUpperCase();
    } else {
      sessionToken = Math.random().toString(36).slice(2, 10).toUpperCase();
    }
    document.documentElement.dataset.sessionWatermark = sessionToken;
    if (!document.querySelector('meta[name="session-watermark"]')) {
      var sessionMeta = document.createElement("meta");
      sessionMeta.name = "session-watermark";
      sessionMeta.content = sessionToken;
      document.head.appendChild(sessionMeta);
    }

    // Cover images that arrive after load (badges, carousels, lazy content).
    if (window.MutationObserver) {
      new MutationObserver(function () { shieldAll(document); })
        .observe(document.body, { childList: true, subtree: true });
    }

    document.addEventListener("contextmenu", function (e) {
      var el = e.target;
      while (el && el !== document.body) {
        if (isImage(el) || (closestProtected(el) && !isEditable(el))) {
          e.preventDefault();
          return;
        }
        el = el.parentElement;
      }
    });

    document.addEventListener("dragstart", function (e) {
      if (isImage(e.target)) e.preventDefault();
    });

    document.addEventListener("contextmenu", function (e) {
      if (closestClassProtected(e.target) && !isEditable(e.target)) e.preventDefault();
    });

    document.addEventListener("dragstart", function (e) {
      if (e.target.closest && e.target.closest(".protected .drag-block")) e.preventDefault();
    });

    document.addEventListener("keydown", function (e) {
      var key = String(e.key || "").toLowerCase();
      var isCopyShortcut = (e.ctrlKey || e.metaKey) &&
        ["c", "u", "s", "p"].indexOf(key) !== -1;
      if (!isCopyShortcut || isEditable(e.target)) return;

      var protectedTarget = closestProtected(e.target) || closestClassProtected(e.target) ||
        document.querySelector("[data-cg-protected]:hover,.protected:hover");
      if (protectedTarget) e.preventDefault();
    });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();

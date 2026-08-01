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
      "@media print{[data-cg-watermark]::after{position:fixed;right:1cm;bottom:1cm;color:#777}}";
    document.head.appendChild(style);
  }

  function closestProtected(el) {
    return el && el.closest ? el.closest("[data-cg-protected]") : null;
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
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();

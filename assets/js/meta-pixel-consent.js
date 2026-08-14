/* ClearGlass Meta Pixel consent gate.
 * This module never loads Meta or sends an event until the site's consent UI
 * calls ClearGlassMetaPixel.grant(pixelId). Do not place email addresses or
 * other customer-list data in this file, browser storage, or page markup.
 */
(function (window, document) {
  "use strict";
  var loaded = false;
  var pixelPattern = /^\d{5,20}$/;

  function grant(pixelId) {
    var id = String(pixelId || "").trim();
    if (!pixelPattern.test(id)) throw new Error("A valid numeric Meta Pixel ID is required");
    if (loaded) return;
    loaded = true;
    window.fbq = window.fbq || function () { (window.fbq.q = window.fbq.q || []).push(arguments); };
    window._fbq = window.fbq;
    window.fbq.loaded = true;
    window.fbq.version = "2.0";
    var script = document.createElement("script");
    script.async = true;
    script.src = "https://connect.facebook.net/en_US/fbevents.js";
    script.referrerPolicy = "strict-origin-when-cross-origin";
    document.head.appendChild(script);
    window.fbq("init", id);
    window.fbq("track", "PageView");
  }

  function revoke() {
    if (window.fbq) window.fbq("consent", "revoke");
  }

  window.ClearGlassMetaPixel = Object.freeze({ grant: grant, revoke: revoke });
})(window, document);

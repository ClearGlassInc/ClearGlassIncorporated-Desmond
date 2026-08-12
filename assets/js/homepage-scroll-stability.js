/* ClearGlass homepage scroll stability guard.
   Keeps decorative/floating layers from turning the dense footer into a
   continuous layout-measurement hot path on mobile Safari. */
(function () {
  "use strict";

  if (window.__cgHomepageScrollStability) return;
  window.__cgHomepageScrollStability = true;

  var root = document.documentElement;
  var body = document.body;
  if (!root || !body) return;

  var raf = 0;
  var lastY = -1;
  var footer = document.querySelector("footer");
  var assistant = null;

  function clampScrollState() {
    raf = 0;
    var y = Math.max(0, window.scrollY || window.pageYOffset || 0);
    if (Math.abs(y - lastY) < 2) return;
    lastY = y;

    var viewport = window.innerHeight || root.clientHeight || 0;
    var max = Math.max(0, root.scrollHeight - viewport);
    var nearBottom = max > 0 && y >= Math.max(0, max - Math.min(320, viewport * 0.45));
    body.classList.toggle("cg-near-page-bottom", nearBottom);

    if (!assistant) assistant = document.getElementById("cg-security-stack");
    if (assistant && nearBottom && assistant.classList.contains("is-expanded")) {
      var launcher = document.getElementById("cg-assistant-launcher");
      var panel = document.getElementById("cg-assistant-panel");
      assistant.classList.remove("is-expanded");
      if (launcher) launcher.setAttribute("aria-expanded", "false");
      if (panel) panel.setAttribute("aria-hidden", "true");
    }
  }

  function schedule() {
    if (raf) return;
    raf = window.requestAnimationFrame(clampScrollState);
  }

  window.addEventListener("scroll", schedule, { passive: true });
  window.addEventListener("resize", schedule, { passive: true });
  window.addEventListener("orientationchange", schedule, { passive: true });
  document.addEventListener("visibilitychange", function () {
    if (!document.hidden) schedule();
  });

  if (footer && "IntersectionObserver" in window) {
    var footerObserver = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        body.classList.toggle("cg-footer-visible", entry.isIntersecting);
      });
    }, { rootMargin: "240px 0px 0px 0px", threshold: 0.01 });
    footerObserver.observe(footer);
  }

  schedule();
})();

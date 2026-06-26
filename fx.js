/* ClearGlass · FX behaviors. Loaded by platform.js. Progressive enhancement:
   inert under prefers-reduced-motion; never hides content if IO is unavailable. */
(function () {
  "use strict";
  if (window.__cgFx) return;
  window.__cgFx = true;

  var reduce = false;
  try { reduce = matchMedia("(prefers-reduced-motion: reduce)").matches; } catch (e) {}
  // Only mark cg-fx when motion is allowed — the hiding rules in fx.css key off it,
  // so reduced-motion users (and no-JS) always see fully-visible content.
  if (!reduce) document.documentElement.classList.add("cg-fx");

  function ready(fn) {
    if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", fn);
    else fn();
  }

  ready(function () {
    /* ── scroll progress bar ─────────────────────────────────────────────── */
    var bar = document.createElement("div");
    bar.id = "cg-progress";
    document.body.appendChild(bar);

    /* ── back-to-top ─────────────────────────────────────────────────────── */
    var top = document.createElement("button");
    top.id = "cg-top";
    top.type = "button";
    top.setAttribute("aria-label", "Back to top");
    top.innerHTML = "↑";
    top.addEventListener("click", function () {
      window.scrollTo({ top: 0, behavior: reduce ? "auto" : "smooth" });
    });
    document.body.appendChild(top);

    var ticking = false;
    function onScroll() {
      if (ticking) return;
      ticking = true;
      requestAnimationFrame(function () {
        var h = document.documentElement;
        var max = (h.scrollHeight - h.clientHeight) || 1;
        var pct = Math.min(100, Math.max(0, (h.scrollTop || window.pageYOffset) / max * 100));
        bar.style.width = pct + "%";
        top.classList.toggle("show", (h.scrollTop || window.pageYOffset) > 480);
        ticking = false;
      });
    }
    window.addEventListener("scroll", onScroll, { passive: true });
    onScroll();

    if (reduce) return; // ambient bar/top stay; skip reveal + tilt

    /* ── scroll reveal (opt-in [data-reveal]) ────────────────────────────── */
    var reveals = [].slice.call(document.querySelectorAll("[data-reveal]"));
    if (reveals.length) {
      if ("IntersectionObserver" in window) {
        var io = new IntersectionObserver(function (entries) {
          entries.forEach(function (en) {
            if (en.isIntersecting) {
              var el = en.target, d = parseFloat(el.getAttribute("data-reveal-delay")) || 0;
              if (d) el.style.transitionDelay = d + "ms";
              el.classList.add("cg-in");
              io.unobserve(el);
            }
          });
        }, { threshold: 0.12, rootMargin: "0px 0px -8% 0px" });
        reveals.forEach(function (el) { io.observe(el); });
        // failsafe: if anything is still hidden after 1.6s, reveal it
        setTimeout(function () { reveals.forEach(function (el) { el.classList.add("cg-in"); }); }, 1600);
      } else {
        reveals.forEach(function (el) { el.classList.add("cg-in"); });
      }
    }

    /* ── pointer tilt (opt-in [data-tilt], fine pointers only) ───────────── */
    var fine = true;
    try { fine = matchMedia("(hover: hover) and (pointer: fine)").matches; } catch (e) {}
    if (fine) {
      [].slice.call(document.querySelectorAll("[data-tilt]")).forEach(function (el) {
        var raf = 0, rx = 0, ry = 0;
        var MAX = parseFloat(el.getAttribute("data-tilt")) || 6;
        function apply() { raf = 0; el.style.transform = "perspective(800px) rotateX(" + rx + "deg) rotateY(" + ry + "deg) translateY(-2px)"; }
        el.addEventListener("pointermove", function (e) {
          var r = el.getBoundingClientRect();
          ry = ((e.clientX - (r.left + r.width / 2)) / (r.width / 2)) * MAX;
          rx = -((e.clientY - (r.top + r.height / 2)) / (r.height / 2)) * MAX;
          if (!raf) raf = requestAnimationFrame(apply);
        });
        el.addEventListener("pointerleave", function () {
          if (raf) { cancelAnimationFrame(raf); raf = 0; }
          el.style.transform = "";
        });
      });
    }
  });
})();

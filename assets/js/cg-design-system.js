/* ═══════════════════════════════════════════════════════════════════
   CLEARGLASS GLOBAL DESIGN SYSTEM — behavior layer
   Mounts the ambient FX defined in assets/css/cg-design-system.css:
   aurora background, floating depth orbs with parallax, scan-line
   sweep, cursor-reactive glow, and scroll-reveal motion.
   Idempotent; respects prefers-reduced-motion; opt out per page with
   <body data-cg-no-fx> or <html data-cg-no-fx>.
═══════════════════════════════════════════════════════════════════ */
(function () {
  'use strict';
  if (window.__cgDesignSystem) return;
  window.__cgDesignSystem = true;

  var reduceMotion = false;
  try {
    reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  } catch (e) { /* ignore */ }

  function optedOut() {
    return document.documentElement.hasAttribute('data-cg-no-fx') ||
      (document.body && document.body.hasAttribute('data-cg-no-fx'));
  }

  function ensureFonts() {
    // The design system's typography (Cormorant Garamond / Urbanist /
    // IBM Plex Mono) — only add the stylesheet if the page doesn't
    // already load Urbanist.
    var links = document.querySelectorAll('link[href*="fonts.googleapis.com"]');
    for (var i = 0; i < links.length; i++) {
      if (/Urbanist/.test(links[i].href)) return;
    }
    var l = document.createElement('link');
    l.rel = 'stylesheet';
    l.href = 'https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,300;0,400;0,500;0,600;0,700;1,300;1,400&family=Urbanist:wght@300;400;500;600;700;800&family=IBM+Plex+Mono:wght@400;500;600&display=swap';
    document.head.appendChild(l);
  }

  function el(tag, className) {
    var n = document.createElement(tag);
    n.className = className;
    n.setAttribute('aria-hidden', 'true');
    return n;
  }

  function mountAmbient() {
    var frag = document.createDocumentFragment();
    frag.appendChild(el('div', 'cg-fx-aurora'));
    frag.appendChild(el('div', 'cg-fx-orb o1'));
    frag.appendChild(el('div', 'cg-fx-orb o2'));
    frag.appendChild(el('div', 'cg-fx-orb o3'));
    if (!reduceMotion) frag.appendChild(el('div', 'cg-fx-scan'));
    document.body.appendChild(frag);
  }

  function mountCursorGlow() {
    if (reduceMotion) return;
    // Pages that already ship the homepage cursor glow keep their own.
    if (document.querySelector('.cursor-glow')) return;
    var glow = el('div', 'cg-fx-cursor');
    document.body.appendChild(glow);
    var x = -500, y = -500, raf = null;
    document.addEventListener('pointermove', function (e) {
      x = e.clientX; y = e.clientY;
      if (raf) return;
      raf = requestAnimationFrame(function () {
        glow.style.left = x + 'px';
        glow.style.top = y + 'px';
        raf = null;
      });
    }, { passive: true });
  }

  function bindParallax() {
    if (reduceMotion) return;
    var orbs = document.querySelectorAll('.cg-fx-orb');
    if (!orbs.length) return;
    var ticking = false;
    window.addEventListener('scroll', function () {
      if (ticking) return;
      ticking = true;
      requestAnimationFrame(function () {
        var s = window.scrollY || 0;
        for (var i = 0; i < orbs.length; i++) {
          orbs[i].style.setProperty('--cg-par', String(-(s * (0.03 + i * 0.025))));
        }
        ticking = false;
      });
    }, { passive: true });
  }

  function bindReveal() {
    if (reduceMotion || !('IntersectionObserver' in window)) return;
    try {
      var targets = document.querySelectorAll(
        'main > section, body > section, article, .card, .product-card, .tech-card, .connect-card, .value-card, .offer-card, .cg-glass-card'
      );
      if (!targets.length) return;
      var io = new IntersectionObserver(function (entries) {
        entries.forEach(function (en) {
          if (en.isIntersecting) {
            en.target.classList.add('cg-vis');
            io.unobserve(en.target);
          }
        });
      }, { threshold: 0.08, rootMargin: '0px 0px -6% 0px' });
      for (var i = 0; i < targets.length && i < 80; i++) {
        var t = targets[i];
        var r = t.getBoundingClientRect();
        // Never hide content already in the first viewport.
        if (r.top < window.innerHeight * 0.9) continue;
        t.classList.add('cg-rv');
        io.observe(t);
      }
    } catch (e) { /* reveal is progressive enhancement only */ }
  }

  function init() {
    if (optedOut()) return;
    ensureFonts();
    mountAmbient();
    mountCursorGlow();
    bindParallax();
    bindReveal();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();

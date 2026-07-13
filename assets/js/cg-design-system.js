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
    frag.appendChild(el('div', 'cg-fx-neon-grid'));
    frag.appendChild(el('div', 'cg-fx-aurora'));
    frag.appendChild(el('div', 'cg-fx-orb o1'));
    frag.appendChild(el('div', 'cg-fx-orb o2'));
    frag.appendChild(el('div', 'cg-fx-orb o3'));
    if (!reduceMotion) {
      frag.appendChild(el('div', 'cg-fx-scan'));
      frag.appendChild(el('div', 'cg-fx-neon-thread'));
    }
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

  /* ── Global top bar — the ClearGlassInc. 2040 identity and menu on every page.
     It is additive: existing page navigation remains intact and is nudged below
     the global bar when necessary. Opt out only with data-cg-no-topbar on
     <html> or <body>. Pages can dock their own controls into the bar with
     [data-cg-topbar-slot], and rebrand the left side with
     data-cg-topbar-title / data-cg-topbar-sub on <body>. ── */
  function mountTopbar() {
    if (document.querySelector('.cg-topbar')) return;
    if (document.documentElement.hasAttribute('data-cg-no-topbar') ||
        (document.body && document.body.hasAttribute('data-cg-no-topbar'))) return;

    var PRODUCTS = [
      ['Guardian', '/guardian.html', '🌐', 'ClearGlassInc. Intelligence'],
      ['BLUEDESK', '/bluedesk.html', '🛡️', 'CISO Risk & Blue Team'],
      ['Government Solutions', '/government.html', '🏛️', 'Federal & Defence'],
      ['Web Design & Dev', '/web-design.html', '💻', 'Design & Development'],
      ['SMB Cyber Trust Kit', '/smb-cyber-trust-kit.html', '🔐', 'Small Business Security'],
      ['Side Store', '/side-store.html', '🔌', 'Cheap Wires & Electronics'],
      null,
      ['Insights', '/blog/', '📡', 'Blog & Field Notes']
    ];
    var LINKS = [
      ['Vision', '/index.html#vision'],
      ['Technology', '/index.html#technology'],
      ['PRODUCTS'],
      ['Services', '/offers/index.html'],
      ['Founder', '/index.html#founder']
    ];

    var path = location.pathname.toLowerCase();
    function isHere(href) {
      var p = href.split('#')[0].toLowerCase();
      if (!p || p === '/index.html') return false;
      return path === p || (p.slice(-1) === '/' && path.indexOf(p) === 0);
    }
    function esc(s) {
      return String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
    }

    var body = document.body;
    var title = body.getAttribute('data-cg-topbar-title');
    var sub = body.getAttribute('data-cg-topbar-sub') || 'Clarity is Power';
    var nameHtml = title ? esc(title) : 'ClearGlassInc. <em>2040</em>';

    var chev = '<svg class="cg-tb-chev" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M4 6l4 4 4-4"/></svg>';
    var productActive = false;
    var ddHtml = '';
    PRODUCTS.forEach(function (p) {
      if (!p) { ddHtml += '<div class="cg-tb-dd-sep" role="separator"></div>'; return; }
      var cur = isHere(p[1]);
      if (cur) productActive = true;
      ddHtml += '<a href="' + p[1] + '" role="menuitem"' + (cur ? ' class="is-active" aria-current="page"' : '') + '>' +
        '<div class="cg-tb-dd-icon">' + p[2] + '</div>' +
        '<div class="cg-tb-dd-meta"><span class="cg-tb-dd-label">' + esc(p[0]) + '</span>' +
        '<span class="cg-tb-dd-sub">' + esc(p[3]).toUpperCase() + '</span></div></a>';
    });

    var linksHtml = '';
    LINKS.forEach(function (l) {
      if (l[0] === 'PRODUCTS') {
        linksHtml += '<div class="cg-tb-dropwrap">' +
          '<button type="button" class="cg-tb-dropbtn' + (productActive ? ' is-active' : '') + '" aria-haspopup="true" aria-expanded="false">Products' + chev + '</button>' +
          '<div class="cg-tb-dropdown" role="menu">' + ddHtml + '</div></div>';
      } else {
        linksHtml += '<a href="' + l[1] + '"' + (isHere(l[1]) ? ' class="is-active" aria-current="page"' : '') + '>' + l[0] + '</a>';
      }
    });

    var mobHtml = '<a href="/index.html#vision">Vision</a><a href="/index.html#technology">Technology</a>' +
      '<div class="cg-tb-mob-sep"></div><div class="cg-tb-mob-label">Products</div>';
    PRODUCTS.forEach(function (p) {
      if (!p) return;
      mobHtml += '<a href="' + p[1] + '">' + esc(p[0]) + ' <span class="arr">→</span></a>';
    });
    mobHtml += '<div class="cg-tb-mob-sep"></div>' +
      '<a href="/offers/index.html">Services <span class="arr">→</span></a>' +
      '<a href="/index.html#founder">Founder</a>' +
      '<a class="cg-tb-mob-cta" href="/index.html#contact">Contact →</a>';

    var bar = document.createElement('div');
    bar.className = 'cg-topbar';
    bar.innerHTML =
      '<div class="cg-topbar-in">' +
        '<a class="cg-tb-brand" href="/index.html">' +
          '<span class="cg-tb-mark"><img src="/assets/images/clearglass-logo.png" alt="ClearGlass logo"><i class="cg-tb-ring" aria-hidden="true"></i></span>' +
          '<span class="cg-tb-id"><span class="cg-tb-name">' + nameHtml + '</span>' +
          '<span class="cg-tb-sub">' + esc(sub) + '</span></span>' +
        '</a>' +
        '<nav class="cg-tb-links" aria-label="Primary navigation">' + linksHtml + '</nav>' +
        '<div class="cg-tb-actions">' +
          '<span class="cg-tb-status"><i class="cg-pulse ok"></i>SYS · LIVE</span>' +
          '<a class="cg-tb-cta" href="/index.html#contact">Contact →</a>' +
          '<button type="button" class="cg-tb-toggle" aria-label="Open menu" aria-expanded="false">' +
            '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M4 12h16M4 6h16M4 18h16"/></svg>' +
          '</button>' +
        '</div>' +
      '</div>' +
      '<div class="cg-tb-mobile" role="dialog" aria-label="Navigation menu">' + mobHtml + '</div>';

    var spacer = document.createElement('div');
    spacer.className = 'cg-topbar-spacer';
    spacer.setAttribute('aria-hidden', 'true');
    body.insertBefore(spacer, body.firstChild);
    body.insertBefore(bar, spacer);

    // Adopt page-provided controls (e.g. the store's cart button) into
    // the action cluster, ahead of the CTA.
    var cta = bar.querySelector('.cg-tb-cta');
    var slots = document.querySelectorAll('[data-cg-topbar-slot]');
    for (var i = 0; i < slots.length; i++) {
      if (!bar.contains(slots[i])) cta.parentNode.insertBefore(slots[i], cta);
    }

    // Nudge existing fixed navigation and compact top widgets below the
    // global bar without deleting, restyling, or replacing page content.
    function nudgeFixedWidgets() {
      var barH = bar.offsetHeight || 64;
      var cands = document.querySelectorAll('body > *, body > * > *');
      for (var j = 0; j < cands.length && j < 600; j++) {
        var item = cands[j];
        if (item === bar || bar.contains(item) || item.id === 'cg-nav') continue;
        if (item.hasAttribute('data-cg-tb-nudged')) continue;
        var cs = getComputedStyle(item);
        if (cs.position !== 'fixed' && cs.position !== 'sticky') continue;
        var r = item.getBoundingClientRect();
        if (r.height < 18 || r.height > 170 || r.width < 1) continue;
        if (r.top >= barH || r.bottom <= 0) continue;
        item.setAttribute('data-cg-tb-nudged', '1');
        item.style.top = (r.top + barH) + 'px';
      }
    }
    nudgeFixedWidgets();
    window.addEventListener('load', nudgeFixedWidgets);

    // Mobile menu + touch dropdown toggles.
    var toggle = bar.querySelector('.cg-tb-toggle');
    var mobile = bar.querySelector('.cg-tb-mobile');
    toggle.addEventListener('click', function (e) {
      e.stopPropagation();
      var open = mobile.classList.toggle('open');
      toggle.setAttribute('aria-expanded', open ? 'true' : 'false');
    });
    var dropwrap = bar.querySelector('.cg-tb-dropwrap');
    var dropbtn = bar.querySelector('.cg-tb-dropbtn');
    dropbtn.addEventListener('click', function (e) {
      e.stopPropagation();
      var open = dropwrap.classList.toggle('open');
      dropbtn.setAttribute('aria-expanded', open ? 'true' : 'false');
    });
    document.addEventListener('click', function (e) {
      if (!bar.contains(e.target)) {
        mobile.classList.remove('open');
        dropwrap.classList.remove('open');
        toggle.setAttribute('aria-expanded', 'false');
        dropbtn.setAttribute('aria-expanded', 'false');
      }
    });
    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape') {
        mobile.classList.remove('open');
        dropwrap.classList.remove('open');
        toggle.setAttribute('aria-expanded', 'false');
        dropbtn.setAttribute('aria-expanded', 'false');
      }
    });

    // Condense on scroll.
    var ticking = false;
    function onScroll() {
      if (ticking) return;
      ticking = true;
      requestAnimationFrame(function () {
        bar.classList.toggle('scrolled', (window.scrollY || 0) > 12);
        ticking = false;
      });
    }
    window.addEventListener('scroll', onScroll, { passive: true });
    onScroll();
  }

  function init() {
    if (optedOut()) return;
    if (document.body) document.body.classList.add('cg-neon-ready');
    ensureFonts();
    mountTopbar();
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

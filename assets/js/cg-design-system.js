/* ClearGlass design-system loader.
   Preserves the existing behavior layer in cg-design-system-core.js and
   adds the Business Productivity Suite to product navigation/catalog. */
(function () {
  'use strict';

  var PRODUCT_PAGE = '/business-productivity-suite.html';
  var PRODUCT_URL = 'https://turbo-fishstick-jg11zep.pages.github.io/';

  function isProductPage() {
    return location.pathname.toLowerCase() === PRODUCT_PAGE;
  }

  function addCatalogCard() {
    var pagePath = location.pathname.replace(/\/+$/, '').toLowerCase();
    if (pagePath !== '/products' && pagePath !== '/products.html') return true;
    if (document.getElementById('cg-business-productivity-suite-card')) return true;

    var container = document.querySelector('.cg-page .cg-container');
    var hero = container && container.querySelector('.cg-hero');
    if (!container || !hero) return false;

    var section = document.createElement('section');
    section.className = 'cg-product-section';
    section.id = 'business-productivity-suite';
    section.innerHTML =
      '<div class="cg-section-head">' +
        '<p class="cg-eyebrow">Business productivity systems</p>' +
        '<h2>Business productivity systems</h2>' +
        '<p>Canadian-first plan comparison and subscription-readiness experiences connected to the ClearGlass product ecosystem.</p>' +
      '</div>' +
      '<div class="cg-product-grid">' +
        '<article class="cg-product-card" id="cg-business-productivity-suite-card">' +
          '<span class="cg-card-icon" aria-hidden="true">▦</span>' +
          '<p class="cg-card-meta">Business productivity systems</p>' +
          '<h3>Business Productivity Suite</h3>' +
          '<p>CAD-oriented productivity plan comparison, seat configuration, and subscription lifecycle architecture.</p>' +
          '<div class="cg-card-actions">' +
            '<a class="btn btn-dark" href="' + PRODUCT_PAGE + '">View Product</a>' +
            '<a class="btn btn-glass" href="' + PRODUCT_URL + '" target="_blank" rel="noopener noreferrer">Launch Live App ↗</a>' +
          '</div>' +
        '</article>' +
      '</div>';

    hero.insertAdjacentElement('afterend', section);
    return true;
  }

  function addDesktopProductLink() {
    var menu = document.querySelector('.cg-tb-dropdown');
    if (!menu) return false;
    if (menu.querySelector('a[href="' + PRODUCT_PAGE + '"]')) return true;

    var link = document.createElement('a');
    link.href = PRODUCT_PAGE;
    link.setAttribute('role', 'menuitem');
    if (isProductPage()) {
      link.className = 'is-active';
      link.setAttribute('aria-current', 'page');
    }
    link.innerHTML =
      '<div class="cg-tb-dd-icon">▦</div>' +
      '<div class="cg-tb-dd-meta">' +
        '<span class="cg-tb-dd-label">Business Productivity Suite</span>' +
        '<span class="cg-tb-dd-sub">CAD PRODUCTIVITY PLANS</span>' +
      '</div>';
    menu.appendChild(link);
    return true;
  }

  function addMobileProductLink() {
    var menu = document.querySelector('.cg-tb-mobile');
    if (!menu) return false;
    if (menu.querySelector('a[href="' + PRODUCT_PAGE + '"]')) return true;

    var link = document.createElement('a');
    link.href = PRODUCT_PAGE;
    link.innerHTML = 'Business Productivity Suite <span class="arr">→</span>';
    var government = menu.querySelector('a[href="/government.html"]');
    if (government) menu.insertBefore(link, government.previousElementSibling || government);
    else menu.appendChild(link);
    return true;
  }

  function integrate() {
    var catalogDone = addCatalogCard();
    var desktopDone = addDesktopProductLink();
    var mobileDone = addMobileProductLink();
    return catalogDone && desktopDone && mobileDone;
  }

  function retryIntegration() {
    var attempts = 0;
    function run() {
      attempts += 1;
      if (integrate() || attempts >= 40) return;
      setTimeout(run, 100);
    }
    run();
  }

  var core = document.createElement('script');
  core.src = '/assets/js/cg-design-system-core.js';
  core.async = false;
  core.onload = retryIntegration;
  core.onerror = retryIntegration;
  document.head.appendChild(core);

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', retryIntegration, { once: true });
  } else {
    retryIntegration();
  }
})();

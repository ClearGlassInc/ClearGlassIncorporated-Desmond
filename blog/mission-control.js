(function () {
  'use strict';
  var root = document.querySelector('.cg-blog-mission');
  if (!root) return;

  var reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)');
  var desktopMotion = window.matchMedia('(min-width: 701px) and (hover: hover) and (pointer: fine)');
  var particleField = root.querySelector('[data-mission-particles]');
  var observer;
  var readyTimer;
  var sessionKey = 'cg.blog.mission.initialized';
  var cleanup = [];

  function listen(target, eventName, handler, options) {
    target.addEventListener(eventName, handler, options);
    cleanup.push(function () { target.removeEventListener(eventName, handler, options); });
  }

  if (!reducedMotion.matches && desktopMotion.matches && particleField) {
    var particleCount = 12;
    var fragment = document.createDocumentFragment();
    for (var index = 0; index < particleCount; index += 1) {
      var particle = document.createElement('span');
      particle.style.left = ((index * 37 + 11) % 97) + '%';
      particle.style.top = ((index * 53 + 7) % 100) + '%';
      particle.style.setProperty('--particle-speed', (16 + index % 7) + 's');
      particle.style.setProperty('--particle-delay', (-index * 1.7) + 's');
      fragment.appendChild(particle);
    }
    particleField.appendChild(fragment);
  }

  var revealTargets = root.querySelectorAll('main .section-head, main .article-card');
  if (!reducedMotion.matches && 'IntersectionObserver' in window) {
    revealTargets.forEach(function (target) { target.classList.add('cg-mission-reveal'); });
    observer = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (!entry.isIntersecting) return;
        entry.target.classList.add('cg-mission-visible');
        observer.unobserve(entry.target);
      });
    }, { rootMargin: '0px 0px -8% 0px', threshold: 0.08 });
    revealTargets.forEach(function (target) { observer.observe(target); });
  }

  function syncVisibility() {
    root.classList.toggle('cg-mission-paused', document.hidden);
  }
  listen(document, 'visibilitychange', syncVisibility);

  if (!reducedMotion.matches && desktopMotion.matches) {
    var spotlightFrame = 0;
    var pointerX = 0;
    var pointerY = 0;
    listen(window, 'pointermove', function (event) {
      pointerX = event.clientX; pointerY = event.clientY;
      if (spotlightFrame) return;
      spotlightFrame = window.requestAnimationFrame(function () {
        root.style.setProperty('--cg-spot-x', pointerX + 'px');
        root.style.setProperty('--cg-spot-y', pointerY + 'px');
        spotlightFrame = 0;
      });
    }, { passive: true });
    cleanup.push(function () { if (spotlightFrame) window.cancelAnimationFrame(spotlightFrame); });
  }

  root.querySelectorAll('.article-card[href]').forEach(function (card) {
    listen(card, 'click', function (event) {
      if (event.defaultPrevented || event.button > 0 || event.metaKey || event.ctrlKey || event.shiftKey || event.altKey || reducedMotion.matches) return;
      card.classList.add('cg-mission-confirm');
    });
  });

  var initialized = false;
  try { initialized = window.sessionStorage.getItem(sessionKey) === '1'; } catch (error) { initialized = true; }
  if (reducedMotion.matches || initialized) {
    root.classList.add('cg-mission-ready');
  } else {
    try { window.sessionStorage.setItem(sessionKey, '1'); } catch (error) { /* storage can be unavailable */ }
    readyTimer = window.setTimeout(function () { root.classList.add('cg-mission-ready'); }, 1050);
  }

  listen(window, 'pagehide', function () {
    if (observer) observer.disconnect();
    if (readyTimer) window.clearTimeout(readyTimer);
    cleanup.splice(0).forEach(function (dispose) { dispose(); });
  }, { once: true });
}());

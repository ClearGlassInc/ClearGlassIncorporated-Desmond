(function () {
  'use strict';
  var root = document.querySelector('.cg-blog-mission');
  if (!root) return;

  var reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)');
  var particleField = root.querySelector('[data-mission-particles]');

  if (!reducedMotion.matches && particleField) {
    var particleCount = window.matchMedia('(max-width: 700px)').matches ? 6 : 12;
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
    var observer = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (!entry.isIntersecting) return;
        entry.target.classList.add('cg-mission-visible');
        observer.unobserve(entry.target);
      });
    }, { rootMargin: '0px 0px -8% 0px', threshold: 0.08 });
    revealTargets.forEach(function (target) { observer.observe(target); });
  }

  document.addEventListener('visibilitychange', function () {
    root.classList.toggle('cg-mission-paused', document.hidden);
  });

  if (reducedMotion.matches) {
    root.classList.add('cg-mission-ready');
  } else {
    window.requestAnimationFrame(function () {
      window.requestAnimationFrame(function () { root.classList.add('cg-mission-ready'); });
    });
  }
}());

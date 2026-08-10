/* ClearGlass Inc. — Cinematic Motion System
 * Progressive enhancement only. Static layout remains authoritative.
 */
(function () {
  'use strict';

  var reduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  var coarse = window.matchMedia('(pointer: coarse)').matches;
  if (reduced || !window.gsap || !window.ScrollTrigger) return;

  gsap.registerPlugin(ScrollTrigger);

  var EASE = {
    cinematic: 'power3.out',
    settle: 'power2.out',
    reveal: 'expo.out',
    precision: 'power1.inOut',
    elasticSoft: 'back.out(1.35)'
  };

  var DURATION = {
    micro: 0.42,
    standard: 0.82,
    hero: 1.18,
    long: 1.45
  };

  gsap.config({ nullTargetWarn: false });
  gsap.defaults({ ease: EASE.cinematic });

  function q(sel, root) { return Array.prototype.slice.call((root || document).querySelectorAll(sel)); }
  function exists(sel) { return !!document.querySelector(sel); }

  function revealText(targets, opts) {
    opts = opts || {};
    q(targets).forEach(function (el) {
      gsap.fromTo(el,
        { autoAlpha: 0, yPercent: opts.yPercent || 24, filter: 'blur(10px)' },
        {
          autoAlpha: 1,
          yPercent: 0,
          filter: 'blur(0px)',
          duration: opts.duration || DURATION.hero,
          ease: opts.ease || EASE.reveal,
          scrollTrigger: opts.scrollTrigger || undefined,
          clearProps: 'filter'
        }
      );
    });
  }

  function buildHero() {
    if (!exists('.hero')) return;
    var tl = gsap.timeline({ defaults: { ease: EASE.reveal } });

    tl.fromTo('.hero-video',
      { autoAlpha: 0, scale: 1.045, y: 26 },
      { autoAlpha: 1, scale: 1, y: 0, duration: 1.35 }, 0)
      .fromTo('.hero-seal',
      { autoAlpha: 0, scale: 0.72, rotateZ: -10 },
      { autoAlpha: 1, scale: 1, rotateZ: 0, duration: 1.05, ease: EASE.elasticSoft }, 0.18)
      .fromTo('.hero-year',
      { autoAlpha: 0, y: 18, letterSpacing: '0.28em' },
      { autoAlpha: 1, y: 0, letterSpacing: '0.15em', duration: 0.72 }, 0.34)
      .fromTo('.hero h1',
      { autoAlpha: 0, y: 42, scale: 0.985, filter: 'blur(12px)' },
      { autoAlpha: 1, y: 0, scale: 1, filter: 'blur(0px)', duration: 1.15, clearProps: 'filter' }, 0.42)
      .fromTo('.hero-sub',
      { autoAlpha: 0, y: 26 },
      { autoAlpha: 1, y: 0, duration: 0.82 }, 0.66)
      .fromTo('.hero-domain-line',
      { autoAlpha: 0, y: 18, scale: 0.98 },
      { autoAlpha: 1, y: 0, scale: 1, duration: 0.68 }, 0.77)
      .fromTo('.hero-actions > *',
      { autoAlpha: 0, y: 20, scale: 0.97 },
      { autoAlpha: 1, y: 0, scale: 1, duration: 0.62, stagger: 0.08 }, 0.84)
      .fromTo('.sentinel-hero',
      { autoAlpha: 0, y: 36, scale: 0.985 },
      { autoAlpha: 1, y: 0, scale: 1, duration: 0.92 }, 0.98)
      .fromTo('.artemis-controls > *, .hero-command-rail > *, .hero-options > *',
      { autoAlpha: 0, y: 18 },
      { autoAlpha: 1, y: 0, duration: 0.58, stagger: 0.055 }, 1.08);

    gsap.to('.hero-prism', {
      scale: 1.18,
      rotation: 18,
      ease: 'none',
      scrollTrigger: {
        trigger: '.hero',
        start: 'top top',
        end: 'bottom top',
        scrub: 1.4
      }
    });

    gsap.to('.hero-video', {
      yPercent: 10,
      scale: 0.965,
      ease: 'none',
      scrollTrigger: {
        trigger: '.hero',
        start: 'top top',
        end: 'bottom top',
        scrub: 1.2
      }
    });

    gsap.to('.hero-seal', {
      yPercent: -14,
      rotation: 8,
      ease: 'none',
      scrollTrigger: {
        trigger: '.hero',
        start: 'top top',
        end: 'bottom top',
        scrub: 1.6
      }
    });
  }

  function buildSectionReveals() {
    q('main section:not(.hero)').forEach(function (section) {
      var headers = q('.sh-tag, .sh h2, .sh p, blockquote, cite', section);
      var cards = q('.value-card, .service-card, .hero-option, .project-card, article, .mission-inner', section)
        .filter(function (el) { return !el.closest('.sentinel-hero'); });

      if (headers.length) {
        gsap.fromTo(headers,
          { autoAlpha: 0, y: 34, filter: 'blur(8px)' },
          {
            autoAlpha: 1,
            y: 0,
            filter: 'blur(0px)',
            duration: DURATION.standard,
            stagger: 0.075,
            ease: EASE.reveal,
            clearProps: 'filter',
            scrollTrigger: {
              trigger: section,
              start: 'top 78%',
              toggleActions: 'play none none reverse'
            }
          }
        );
      }

      if (cards.length) {
        gsap.fromTo(cards,
          { autoAlpha: 0, y: 42, scale: 0.985, rotateX: coarse ? 0 : 4, transformPerspective: 900 },
          {
            autoAlpha: 1,
            y: 0,
            scale: 1,
            rotateX: 0,
            duration: 0.78,
            stagger: 0.075,
            ease: EASE.cinematic,
            scrollTrigger: {
              trigger: section,
              start: 'top 80%',
              toggleActions: 'play none none reverse'
            }
          }
        );
      }
    });
  }

  function buildLegacyRevealUpgrade() {
    q('.rv').forEach(function (el) {
      gsap.fromTo(el,
        { autoAlpha: 0, y: 30 },
        {
          autoAlpha: 1,
          y: 0,
          duration: 0.76,
          ease: EASE.cinematic,
          scrollTrigger: {
            trigger: el,
            start: 'top 86%',
            toggleActions: 'play none none reverse'
          }
        }
      );
    });
  }

  function buildDepthMotion() {
    if (coarse) return;
    q('.value-card, .service-card, .project-card, .hero-option').forEach(function (card) {
      card.addEventListener('pointermove', function (event) {
        var r = card.getBoundingClientRect();
        var px = (event.clientX - r.left) / r.width - 0.5;
        var py = (event.clientY - r.top) / r.height - 0.5;
        gsap.to(card, {
          rotateY: px * 5,
          rotateX: py * -4,
          y: -4,
          transformPerspective: 900,
          transformOrigin: 'center',
          duration: 0.45,
          ease: EASE.settle,
          overwrite: 'auto'
        });
      });
      card.addEventListener('pointerleave', function () {
        gsap.to(card, { rotateX: 0, rotateY: 0, y: 0, duration: 0.6, ease: EASE.cinematic, overwrite: 'auto' });
      });
    });
  }

  function buildSceneTransitions() {
    q('main section').forEach(function (section, index) {
      if (index === 0) return;
      gsap.fromTo(section,
        { '--cg-scene-progress': 0 },
        {
          '--cg-scene-progress': 1,
          ease: 'none',
          scrollTrigger: {
            trigger: section,
            start: 'top bottom',
            end: 'top 35%',
            scrub: 0.8
          }
        }
      );
    });
  }

  function refreshAfterAssets() {
    var refresh = function () { ScrollTrigger.refresh(); };
    window.addEventListener('load', refresh, { once: true });
    if (document.fonts && document.fonts.ready) document.fonts.ready.then(refresh);
  }

  document.documentElement.classList.add('cg-motion-enabled');
  buildHero();
  buildSectionReveals();
  buildLegacyRevealUpgrade();
  buildDepthMotion();
  buildSceneTransitions();
  refreshAfterAssets();
})();

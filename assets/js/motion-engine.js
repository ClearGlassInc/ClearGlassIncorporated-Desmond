(() => {
  "use strict";

  const doc = document;
  const root = doc.documentElement;
  const body = doc.body;

  root.classList.remove("no-js");
  root.classList.add("js");

  const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  const supportsIntersectionObserver = "IntersectionObserver" in window;
  const clamp = (value, min, max) => Math.min(Math.max(value, min), max);

  function markReady() {
    body?.classList.add("is-ready");
    root.dataset.ready = "true";
  }

  function initRevealAnimations() {
    const targets = [...doc.querySelectorAll("[data-animate]"), ...doc.querySelectorAll("[data-stagger]")];
    if (!targets.length) return;
    if (reduceMotion || !supportsIntersectionObserver) {
      targets.forEach((el) => el.classList.add("is-visible"));
      return;
    }
    const observer = new IntersectionObserver((entries, obs) => {
      entries.forEach((entry) => {
        if (!entry.isIntersecting) return;
        entry.target.classList.add("is-visible");
        obs.unobserve(entry.target);
      });
    }, { root: null, threshold: 0.14, rootMargin: "0px 0px -8% 0px" });
    targets.forEach((el) => observer.observe(el));
  }

  function initPointerCards() {
    if (reduceMotion) return;
    const cards = doc.querySelectorAll(".motion-card, .card, .product-card, .tech-card, .value-card, .connect-card, .founder-card, .credentials-card, .signup-card");
    cards.forEach((card) => {
      card.addEventListener("pointermove", (event) => {
        if (event.pointerType === "touch") return;
        const rect = card.getBoundingClientRect();
        const x = ((event.clientX - rect.left) / rect.width) * 100;
        const y = ((event.clientY - rect.top) / rect.height) * 100;
        card.style.setProperty("--pointer-x", `${x}%`);
        card.style.setProperty("--pointer-y", `${y}%`);
      }, { passive: true });
    });
  }

  function initMagneticButtons() {
    if (reduceMotion) return;
    const buttons = doc.querySelectorAll(".magnetic");
    buttons.forEach((button) => {
      let frame = null;
      const reset = () => {
        if (frame) cancelAnimationFrame(frame);
        button.style.transform = "translate3d(0, 0, 0)";
      };
      const move = (event) => {
        if (event.pointerType === "touch") return;
        const rect = button.getBoundingClientRect();
        const relX = event.clientX - rect.left - rect.width / 2;
        const relY = event.clientY - rect.top - rect.height / 2;
        const moveX = clamp(relX * 0.16, -10, 10);
        const moveY = clamp(relY * 0.16, -8, 8);
        if (frame) cancelAnimationFrame(frame);
        frame = requestAnimationFrame(() => {
          button.style.transform = `translate3d(${moveX}px, ${moveY}px, 0)`;
        });
      };
      button.addEventListener("pointermove", move, { passive: true });
      button.addEventListener("pointerleave", reset, { passive: true });
      button.addEventListener("blur", reset);
    });
  }

  function initParallax() {
    if (reduceMotion) return;
    const items = [...doc.querySelectorAll("[data-parallax]")];
    if (!items.length) return;
    let ticking = false;
    let active = true;
    const update = () => {
      if (!active) return;
      const viewportHeight = window.innerHeight || 1;
      items.forEach((item) => {
        const rect = item.getBoundingClientRect();
        if (rect.bottom < 0 || rect.top > viewportHeight) return;
        const speed = Number.parseFloat(item.dataset.parallaxSpeed || "0.12");
        const centerOffset = rect.top + rect.height / 2 - viewportHeight / 2;
        const movement = clamp(centerOffset * speed * -1, -36, 36);
        item.style.transform = `translate3d(0, ${movement}px, 0)`;
      });
      ticking = false;
    };
    const requestTick = () => {
      if (ticking) return;
      ticking = true;
      requestAnimationFrame(update);
    };
    window.addEventListener("scroll", requestTick, { passive: true });
    window.addEventListener("resize", requestTick, { passive: true });
    document.addEventListener("visibilitychange", () => {
      active = !document.hidden;
      if (active) requestTick();
    });
    requestTick();
  }

  function initAnchorOffset() {
    const links = doc.querySelectorAll('a[href^="#"]:not([href="#"])');
    links.forEach((link) => {
      link.addEventListener("click", (event) => {
        const id = link.getAttribute("href");
        const target = id ? doc.getElementById(decodeURIComponent(id.slice(1))) : null;
        if (!target) return;
        event.preventDefault();
        target.scrollIntoView({ behavior: reduceMotion ? "auto" : "smooth", block: "start" });
        history.pushState(null, "", id);
      });
    });
  }

  function hardenExternalLinks() {
    doc.querySelectorAll('a[target="_blank"]').forEach((link) => {
      const rel = new Set((link.getAttribute("rel") || "").split(/\s+/).filter(Boolean));
      rel.add("noopener");
      rel.add("noreferrer");
      link.setAttribute("rel", [...rel].join(" "));
    });
  }

  function optimizeImages() {
    doc.querySelectorAll("img").forEach((img, index) => {
      if (!img.hasAttribute("decoding")) img.setAttribute("decoding", "async");
      const isLikelyHero = index === 0 || img.closest("[data-hero], .hero, header");
      if (!isLikelyHero && !img.hasAttribute("loading")) img.setAttribute("loading", "lazy");
      if (!img.hasAttribute("alt")) img.setAttribute("alt", "");
    });
  }

  function init() {
    markReady();
    optimizeImages();
    hardenExternalLinks();
    initRevealAnimations();
    initPointerCards();
    initMagneticButtons();
    initParallax();
    initAnchorOffset();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init, { once: true });
  } else {
    init();
  }
})();

/* ClearGlass Inc. — Cinematic Motion Runtime
 * Dependency-free progressive enhancement. Static HTML/SVG is authoritative.
 * Performance observations stay browser-local and are never transmitted.
 */
(function () {
  "use strict";
  if (window.__cgCinematicMotion) return;
  window.__cgCinematicMotion = true;

  var doc = document;
  var root = doc.documentElement;
  var reduced = false;
  var saveData = false;
  var lowMemory = false;
  var emergencyOff = false;

  try { reduced = matchMedia("(prefers-reduced-motion: reduce)").matches; } catch (e) {}
  try { saveData = !!(navigator.connection && navigator.connection.saveData); } catch (e) {}
  try { lowMemory = typeof navigator.deviceMemory === "number" && navigator.deviceMemory <= 4; } catch (e) {}
  try {
    var params = new URLSearchParams(location.search);
    emergencyOff = params.get("cg_motion") === "off" || localStorage.getItem("cg-motion") === "off";
  } catch (e) {}

  var lowPower = saveData || lowMemory;
  var metrics = {
    disabled: emergencyOff,
    reducedMotion: reduced,
    lowPower: lowPower,
    lcp: null,
    cls: 0,
    inp: null,
    motionFps: null,
    longTasks: 0,
    animationTargetFps: lowPower ? 12 : 24
  };
  window.__cgMotionMetrics = metrics;
  window.getClearGlassMotionMetrics = function () { return Object.assign({}, metrics); };

  if (emergencyOff) {
    root.classList.add("cg-motion-disabled");
    return;
  }

  root.classList.add("cg-cinematic-ready");
  if (lowPower) root.classList.add("cg-low-power");
  if (navigator.gpu) root.classList.add("cg-webgpu-capable");
  try { performance.mark("cg-cinematic-ready"); } catch (e) {}

  function emitMetrics() {
    try {
      window.dispatchEvent(new CustomEvent("cg:motion-metrics", { detail: Object.assign({}, metrics) }));
    } catch (e) {}
  }

  function observePerformance() {
    if (!("PerformanceObserver" in window)) return;
    var interactions = new Map();
    function updateInp() {
      var values = Array.from(interactions.values()).sort(function (a, b) { return a - b; });
      if (!values.length) return;
      var index = Math.min(values.length - 1, Math.max(0, Math.ceil(values.length * .98) - 1));
      metrics.inp = Math.round(values[index]);
    }
    try {
      new PerformanceObserver(function (list) {
        var entries = list.getEntries();
        if (entries.length) metrics.lcp = Math.round(entries[entries.length - 1].startTime);
      }).observe({ type: "largest-contentful-paint", buffered: true });
    } catch (e) {}
    try {
      new PerformanceObserver(function (list) {
        list.getEntries().forEach(function (entry) {
          if (!entry.hadRecentInput) metrics.cls = Math.round((metrics.cls + entry.value) * 10000) / 10000;
        });
      }).observe({ type: "layout-shift", buffered: true });
    } catch (e) {}
    try {
      new PerformanceObserver(function (list) {
        list.getEntries().forEach(function (entry) {
          if (!entry.interactionId) return;
          var prior = interactions.get(entry.interactionId) || 0;
          if (entry.duration > prior) interactions.set(entry.interactionId, entry.duration);
        });
        updateInp();
      }).observe({ type: "event", buffered: true, durationThreshold: 40 });
    } catch (e) {}
    try {
      new PerformanceObserver(function (list) { metrics.longTasks += list.getEntries().length; })
        .observe({ type: "longtask", buffered: true });
    } catch (e) {}
    doc.addEventListener("visibilitychange", function () {
      if (doc.hidden) { updateInp(); emitMetrics(); }
    });
    window.addEventListener("pagehide", emitMetrics, { once: true });
    window.setTimeout(emitMetrics, 5000);
  }
  observePerformance();

  function ready(fn) {
    if (doc.readyState === "loading") doc.addEventListener("DOMContentLoaded", fn, { once: true });
    else fn();
  }

  function element(tag, className, text) {
    var node = doc.createElement(tag);
    if (className) node.className = className;
    if (typeof text === "string") node.textContent = text;
    return node;
  }

  function buildNetwork(hero) {
    if (hero.querySelector(".cg-growth-network")) return;
    hero.classList.add("cg-growth-hero");
    var network = element("div", "cg-growth-network");
    network.setAttribute("aria-hidden", "true");
    network.innerHTML =
      '<svg viewBox="0 0 1200 700" preserveAspectRatio="xMidYMid meet" role="presentation" focusable="false">' +
        '<defs><linearGradient id="cgSignalGradient" x1="0" y1="0" x2="1" y2="1">' +
          '<stop offset="0" stop-color="#67e8f9" stop-opacity=".16"/>' +
          '<stop offset=".48" stop-color="#60a5fa" stop-opacity=".72"/>' +
          '<stop offset="1" stop-color="#a78bfa" stop-opacity=".18"/>' +
        '</linearGradient></defs>' +
        '<ellipse class="cg-net-ring" cx="600" cy="320" rx="350" ry="205"/>' +
        '<ellipse class="cg-net-ring" cx="600" cy="320" rx="235" ry="138"/>' +
        '<path class="cg-net-path" d="M180 175 C350 70 435 245 600 320 S875 530 1020 185"/>' +
        '<path class="cg-net-path" d="M160 455 C330 540 440 410 600 320 S850 95 1040 470"/>' +
        '<path class="cg-net-path" d="M255 80 C360 230 480 205 600 320 S780 420 930 105"/>' +
        '<path class="cg-net-path" d="M250 585 C380 430 490 455 600 320 S790 250 945 585"/>' +
        '<circle class="cg-net-node" cx="180" cy="175" r="4"/><circle class="cg-net-node-secondary" cx="1020" cy="185" r="4"/>' +
        '<circle class="cg-net-node-secondary" cx="160" cy="455" r="4"/><circle class="cg-net-node" cx="1040" cy="470" r="4"/>' +
        '<circle class="cg-net-node" cx="255" cy="80" r="3.5"/><circle class="cg-net-node-secondary" cx="930" cy="105" r="3.5"/>' +
        '<circle class="cg-net-node-secondary" cx="250" cy="585" r="3.5"/><circle class="cg-net-node" cx="945" cy="585" r="3.5"/>' +
      '</svg>';
    network.appendChild(element("span", "cg-signal-core"));
    var anchor = hero.querySelector(".hero-intel-layer, .hero-prism");
    if (anchor && anchor.parentNode) anchor.parentNode.insertBefore(network, anchor.nextSibling);
    else hero.insertBefore(network, hero.firstChild);
  }

  var capabilities = [
    ["ATTENTION", "Clarifies hierarchy so the most important decision receives attention first."],
    ["TRUST", "Makes governance, evidence, and human approval boundaries visible instead of implied."],
    ["CONVERSION", "Directs visitors toward a clear next action without sacrificing comprehension."],
    ["PERFORMANCE", "Keeps motion GPU-friendly, bounded, observable, and secondary to page speed."],
    ["SEARCH", "Preserves semantic HTML and readable content so motion never becomes the information layer."],
    ["AUTOMATION", "Shows how governed workflows connect tools, approvals, and repeatable execution."],
    ["SECURITY", "Reinforces explicit control states, least privilege, and auditable operating boundaries."],
    ["LEARNING", "Uses interaction to explain relationships progressively rather than dumping visual noise."]
  ];

  function buildCapabilityInterface(hero) {
    if (hero.querySelector(".cg-capability-interface")) return;
    var wrap = element("section", "cg-capability-interface");
    wrap.setAttribute("aria-label", "ClearGlass growth infrastructure capabilities");
    var eyebrow = element("div", "cg-capability-interface__eyebrow", "Growth infrastructure interface");
    var grid = element("div", "cg-capability-nodes");
    var detail = element("div", "cg-capability-detail");
    detail.id = "cg-capability-detail";
    detail.setAttribute("aria-live", "polite");
    detail.innerHTML = "<strong>ATTENTION</strong> — " + capabilities[0][1];

    capabilities.forEach(function (item, index) {
      var button = element("button", "cg-motion-node", item[0]);
      button.type = "button";
      button.setAttribute("aria-pressed", index === 0 ? "true" : "false");
      button.setAttribute("aria-controls", detail.id);
      button.setAttribute("data-cg-capability", item[0]);
      function select() {
        grid.querySelectorAll(".cg-motion-node").forEach(function (candidate) {
          candidate.setAttribute("aria-pressed", String(candidate === button));
        });
        detail.innerHTML = "<strong>" + item[0] + "</strong> — " + item[1];
      }
      button.addEventListener("click", select);
      button.addEventListener("focus", select);
      button.addEventListener("mouseenter", select, { passive: true });
      grid.appendChild(button);
    });

    wrap.append(eyebrow, grid, detail);
    var actions = hero.querySelector(".hero-actions");
    if (actions && actions.parentNode) actions.insertAdjacentElement("afterend", wrap);
    else hero.appendChild(wrap);
  }

  function configureHeroMotion(hero) {
    var visible = true;
    var pageVisible = !doc.hidden;
    var last = 0;
    var raf = 0;
    var fpsInterval = lowPower ? 1000 / 12 : 1000 / 24;
    var measuredFrames = 0;
    var measuredStart = 0;

    function setLive() { hero.classList.toggle("cg-motion-live", visible && pageVisible && !reduced); }
    if ("IntersectionObserver" in window) {
      var heroObserver = new IntersectionObserver(function (entries) {
        visible = !!entries[0].isIntersecting;
        setLive();
      }, { rootMargin: "120px 0px 120px 0px", threshold: 0.01 });
      heroObserver.observe(hero);
    }
    doc.addEventListener("visibilitychange", function () { pageVisible = !doc.hidden; setLive(); });
    setLive();
    if (reduced || lowPower) return;

    function tick(now) {
      raf = requestAnimationFrame(tick);
      if (!visible || !pageVisible || now - last < fpsInterval) return;
      last = now;
      if (!measuredStart) measuredStart = now;
      measuredFrames += 1;
      if (now - measuredStart >= 2000) {
        var measuredFps = measuredFrames * 1000 / (now - measuredStart);
        metrics.motionFps = Math.round(measuredFps * 10) / 10;
        measuredFrames = 0;
        measuredStart = now;
      }
      var seconds = now / 1000;
      var phase = (seconds * 2.2) % 360;
      var glow = .72 + Math.sin(seconds * .48) * .12;
      hero.style.setProperty("--cg-motion-phase", phase.toFixed(2));
      hero.style.setProperty("--cg-motion-glow", glow.toFixed(3));
    }
    raf = requestAnimationFrame(tick);
    window.addEventListener("pagehide", function () { if (raf) cancelAnimationFrame(raf); }, { once: true });
  }

  function configureSectionTransitions() {
    if (reduced || !("IntersectionObserver" in window)) return;
    var sections = [].slice.call(doc.querySelectorAll("main > section:not(.hero)"));
    if (!sections.length) return;
    var observer = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (!entry.isIntersecting) return;
        entry.target.classList.remove("cg-motion-section-pending");
        entry.target.classList.add("cg-motion-section-visible");
        observer.unobserve(entry.target);
      });
    }, { threshold: .06, rootMargin: "0px 0px -8% 0px" });
    sections.forEach(function (section, index) {
      if (index > 0 && section.getBoundingClientRect().top > innerHeight * .82) section.classList.add("cg-motion-section-pending");
      else section.classList.add("cg-motion-section-visible");
      observer.observe(section);
    });
    setTimeout(function () {
      sections.forEach(function (section) {
        section.classList.remove("cg-motion-section-pending");
        section.classList.add("cg-motion-section-visible");
      });
    }, 1800);
  }

  ready(function () {
    var hero = doc.getElementById("hero") || doc.querySelector(".hero");
    if (hero) {
      buildNetwork(hero);
      buildCapabilityInterface(hero);
      configureHeroMotion(hero);
    }
    configureSectionTransitions();
  });
})();

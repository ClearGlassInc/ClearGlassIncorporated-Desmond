/* ClearGlass Inc. — Homepage Cinematic Motion Runtime
 * Dependency-free progressive enhancement. Static HTML remains authoritative.
 * Decorative motion is bounded, user-controllable, visibility-aware, and
 * disabled automatically on constrained touch-first layouts.
 */
(function () {
  "use strict";

  var doc = document;
  var root = doc.documentElement;

  function isHomepage() {
    var canonical = doc.querySelector('link[rel="canonical"]');
    if (canonical) {
      try {
        if (new URL(canonical.href, location.href).pathname === "/") return true;
      } catch (e) {}
    }
    return location.pathname === "/" || /\/index\.html$/i.test(location.pathname);
  }

  if (!isHomepage() || window.__cgCinematicMotion) return;
  window.__cgCinematicMotion = true;

  var STORAGE_KEY = "cgVisualEffects";
  var motionQuery = window.matchMedia("(prefers-reduced-motion: reduce)");
  var touchFirstQuery = window.matchMedia("(hover: none) and (pointer: coarse)");
  var explicitPreference = readPreference();
  var saveData = false;
  var touchFirstSmall = false;
  var lowPower = false;
  var reduced = false;
  var motionControl = null;
  var controller = null;
  var suspensionCleanup = null;
  var sectionObserver = null;

  try {
    saveData = !!(navigator.connection && navigator.connection.saveData);
  } catch (e) {}

  function readPreference() {
    try {
      var value = localStorage.getItem(STORAGE_KEY);
      return value === "standard" || value === "reduced" ? value : null;
    } catch (e) {
      return null;
    }
  }

  function writePreference(value) {
    try { localStorage.setItem(STORAGE_KEY, value); } catch (e) {}
  }

  function refreshCapabilityState() {
    touchFirstSmall = touchFirstQuery.matches && window.innerWidth <= 820;
    lowPower = saveData || touchFirstSmall;
    root.classList.toggle("cg-low-power", lowPower);
    root.setAttribute("data-cg-performance", lowPower ? "reduced" : "standard");
  }

  function resolveMotionLevel() {
    if (explicitPreference === "reduced") return "minimal";
    if (explicitPreference === "standard") return "standard";
    if (motionQuery.matches) return "minimal";
    if (lowPower) return "minimal";
    return "standard";
  }

  function updateControl() {
    if (!motionControl) return;
    motionControl.textContent = "Visual effects: " + (reduced ? "Reduced" : "Standard");
    motionControl.setAttribute("aria-pressed", String(reduced));
    motionControl.setAttribute("data-cg-motion-control-state", reduced ? "reduced" : "standard");
  }

  function applyMotionLevel() {
    var level = resolveMotionLevel();
    reduced = level !== "standard";
    root.setAttribute("data-cg-motion-level", level);
    root.classList.toggle("cg-motion-reduced", reduced);
    updateControl();

    if (controller) {
      if (!reduced && !touchFirstSmall && !saveData) {
        var hero = doc.getElementById("hero") || doc.querySelector(".hero");
        if (hero) buildNetwork(hero);
        controller.start();
      } else {
        controller.pause();
      }
    }
  }

  function injectMotionTokens() {
    if (doc.getElementById("cg-cinematic-governance-tokens")) return;
    var style = doc.createElement("style");
    style.id = "cg-cinematic-governance-tokens";
    style.textContent =
      ":root{" +
        "--cg-ease-standard:cubic-bezier(0.22,1,0.36,1);" +
        "--cg-ease-emphasized:cubic-bezier(0.16,1,0.3,1);" +
        "--cg-duration-micro:140ms;" +
        "--cg-duration-fast:180ms;" +
        "--cg-duration-section:360ms;" +
        "--cg-duration-scene:560ms;" +
        "--cg-distance-micro:4px;" +
        "--cg-distance-section:12px;" +
        "--cg-distance-route:10px;" +
        "--cg-glow-cyan:rgba(70,225,255,.24);" +
        "--cg-glow-violet:rgba(150,105,255,.18);" +
        "--cg-glow-success:rgba(86,220,150,.18);" +
        "--cg-glow-warning:rgba(255,185,78,.20);" +
        "--cg-glow-error:rgba(255,102,118,.18);" +
        "--cg-motion-fast:var(--cg-duration-fast);" +
        "--cg-motion-section:var(--cg-duration-section);" +
        "--cg-motion-ease:var(--cg-ease-standard);" +
        "--cg-motion-soft:var(--cg-ease-emphasized);" +
      "}" +
      ".cg-visual-effects-wrap{position:relative;z-index:5;display:flex;justify-content:center;margin:14px auto 0}" +
      ".cg-visual-effects-control{min-height:44px;padding:9px 14px;border-radius:999px;border:1px solid rgba(103,232,249,.26);background:rgba(7,17,31,.72);color:#dffaff;box-shadow:inset 0 1px 0 rgba(255,255,255,.06),0 8px 24px rgba(7,17,31,.14);font:700 9px/1 var(--mono,monospace);letter-spacing:.09em;text-transform:uppercase;cursor:pointer}" +
      ".cg-visual-effects-control:hover{border-color:rgba(103,232,249,.55)}" +
      ".cg-visual-effects-control:focus-visible{outline:3px solid #67e8f9;outline-offset:3px}" +
      "html[data-cg-motion-level=\"minimal\"] .cg-net-path," +
      "html[data-cg-motion-level=\"minimal\"] .cg-signal-core," +
      "html[data-cg-motion-level=\"minimal\"] .hero-prism," +
      "html[data-cg-motion-level=\"minimal\"] .hero-line," +
      "html[data-cg-motion-level=\"minimal\"] .artemis-grid::after," +
      "html[data-cg-motion-level=\"minimal\"] .artemis-grid span," +
      "html[data-cg-motion-level=\"minimal\"] .artemis-reticle," +
      "html[data-cg-motion-level=\"minimal\"] .artemis-elite-status i{animation:none!important;transition:none!important}" +
      "html[data-cg-motion-level=\"minimal\"] .cg-motion-section-pending{opacity:1!important;transform:none!important}" +
      "html.cg-motion-suspended .cg-net-path," +
      "html.cg-motion-suspended .cg-signal-core," +
      "html.cg-motion-suspended .hero-prism," +
      "html.cg-motion-suspended .hero-line," +
      "html.cg-motion-suspended .artemis-grid::after," +
      "html.cg-motion-suspended .artemis-grid span," +
      "html.cg-motion-suspended .artemis-reticle," +
      "html.cg-motion-suspended .artemis-elite-status i{animation-play-state:paused!important}" +
      "@media(max-width:820px),(hover:none),(pointer:coarse){.cg-growth-network{display:none!important}.cg-signal-core{display:none!important}}" +
      "@media(forced-colors:active){.cg-visual-effects-control{forced-color-adjust:auto;border:1px solid ButtonText;background:ButtonFace;color:ButtonText;box-shadow:none}}";
    doc.head.appendChild(style);
  }

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

  function buildMotionControl(hero) {
    if (doc.querySelector(".cg-visual-effects-control")) {
      motionControl = doc.querySelector(".cg-visual-effects-control");
      updateControl();
      return;
    }

    var wrap = element("div", "cg-visual-effects-wrap");
    var button = element("button", "cg-visual-effects-control");
    button.type = "button";
    button.setAttribute("aria-label", "Toggle decorative visual effects between Standard and Reduced");
    button.setAttribute("title", "Controls decorative motion only. Core content and controls remain unchanged.");
    wrap.appendChild(button);
    motionControl = button;
    updateControl();

    button.addEventListener("click", function () {
      explicitPreference = reduced ? "standard" : "reduced";
      writePreference(explicitPreference);
      applyMotionLevel();
    });

    var controls = hero.querySelector(".artemis-controls");
    if (controls) controls.appendChild(button);
    else {
      var actions = hero.querySelector(".hero-actions");
      if (actions && actions.parentNode) actions.insertAdjacentElement("afterend", wrap);
      else hero.appendChild(wrap);
    }
  }

  function buildNetwork(hero) {
    if (hero.querySelector(".cg-growth-network") || touchFirstSmall || saveData) return;
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

  function PerformanceModeController(hero) {
    this.hero = hero;
    this.visible = true;
    this.pageVisible = !doc.hidden;
    this.enabled = false;
    this.initialized = false;
    this.downgraded = false;
    this.fps = 30;
    this.raf = 0;
    this.lastRender = 0;
    this.samples = [];
    this.observer = null;
    this.onVisibility = null;
    this.onSuspension = null;
  }

  PerformanceModeController.prototype.setLive = function () {
    var live = this.enabled && this.visible && this.pageVisible && !root.classList.contains("cg-motion-suspended");
    this.hero.classList.toggle("cg-motion-live", live);
  };

  PerformanceModeController.prototype.initialize = function () {
    var self = this;
    if (self.initialized) return;
    self.initialized = true;

    if ("IntersectionObserver" in window) {
      self.observer = new IntersectionObserver(function (entries) {
        self.visible = !!entries[0].isIntersecting;
        self.setLive();
      }, { rootMargin: "120px 0px 120px 0px", threshold: 0.01 });
      self.observer.observe(self.hero);
    }

    self.onVisibility = function () {
      self.pageVisible = !doc.hidden;
      self.setLive();
    };
    self.onSuspension = function () { self.setLive(); };
    doc.addEventListener("visibilitychange", self.onVisibility);
    doc.addEventListener("cg-motion-suspension-change", self.onSuspension);
  };

  PerformanceModeController.prototype.start = function () {
    var self = this;
    if (self.enabled || reduced || touchFirstSmall || saveData) return;
    self.initialize();
    self.enabled = true;
    self.setLive();
    if (!self.raf) self.raf = requestAnimationFrame(function tick(now) { self.tick(now, tick); });
  };

  PerformanceModeController.prototype.tick = function (now, tick) {
    var self = this;
    if (!self.enabled) {
      self.raf = 0;
      return;
    }
    self.raf = requestAnimationFrame(function (next) { self.tick(next, tick); });
    if (!self.visible || !self.pageVisible || root.classList.contains("cg-motion-suspended")) return;

    var interval = 1000 / self.fps;
    if (self.lastRender && now - self.lastRender < interval) return;

    if (self.lastRender) {
      var delta = now - self.lastRender;
      if (delta > 0 && delta < 250) {
        self.samples.push(delta);
        if (self.samples.length > 20) self.samples.shift();
        if (!self.downgraded && self.samples.length === 20) {
          var average = self.samples.reduce(function (sum, value) { return sum + value; }, 0) / self.samples.length;
          if (average > 50) {
            self.downgraded = true;
            self.fps = 15;
            root.classList.add("cg-low-power");
            root.setAttribute("data-cg-performance", "downgraded");
          }
        }
      }
    }

    self.lastRender = now;
    var seconds = now / 1000;
    var phase = (seconds * 2.2) % 360;
    var glow = .72 + Math.sin(seconds * .48) * .12;
    self.hero.style.setProperty("--cg-motion-phase", phase.toFixed(2));
    self.hero.style.setProperty("--cg-motion-glow", glow.toFixed(3));
  };

  PerformanceModeController.prototype.pause = function () {
    this.enabled = false;
    this.setLive();
    if (this.raf) cancelAnimationFrame(this.raf);
    this.raf = 0;
  };

  PerformanceModeController.prototype.stop = function () {
    this.pause();
    if (this.observer) this.observer.disconnect();
    if (this.onVisibility) doc.removeEventListener("visibilitychange", this.onVisibility);
    if (this.onSuspension) doc.removeEventListener("cg-motion-suspension-change", this.onSuspension);
    this.hero.style.removeProperty("--cg-motion-phase");
    this.hero.style.removeProperty("--cg-motion-glow");
  };

  function configureSectionTransitions() {
    var sections = [].slice.call(doc.querySelectorAll("main > section:not(.hero)"));
    if (!sections.length || reduced || !("IntersectionObserver" in window)) return;

    sectionObserver = new IntersectionObserver(function (entries, observer) {
      entries.forEach(function (entry) {
        if (!entry.isIntersecting) return;
        entry.target.classList.remove("cg-motion-section-pending");
        entry.target.classList.add("cg-motion-section-visible");
        observer.unobserve(entry.target);
      });
    }, { threshold: .06, rootMargin: "0px 0px -8% 0px" });

    sections.forEach(function (section, index) {
      if (index > 0 && section.getBoundingClientRect().top > window.innerHeight * .82) {
        section.classList.add("cg-motion-section-pending");
      } else {
        section.classList.add("cg-motion-section-visible");
      }
      sectionObserver.observe(section);
    });

    window.setTimeout(function () {
      sections.forEach(function (section) {
        section.classList.remove("cg-motion-section-pending");
        section.classList.add("cg-motion-section-visible");
      });
    }, 1800);
  }

  function configureSuspension() {
    var sentinelShell = doc.getElementById("sentinelShell");
    var mobileMenu = doc.getElementById("mobileMenu");
    var observers = [];
    var formFocus = false;

    function hasOpenDialog() {
      var dialogs = [].slice.call(doc.querySelectorAll('[role="dialog"][aria-modal="true"]'));
      return dialogs.some(function (dialog) {
        var hiddenParent = dialog.closest("[hidden]");
        return !hiddenParent;
      });
    }

    function update() {
      var sentinelOpen = !!(sentinelShell && !sentinelShell.hidden);
      var menuOpen = !!(mobileMenu && mobileMenu.classList.contains("open"));
      var suspended = sentinelOpen || menuOpen || formFocus || hasOpenDialog();
      root.classList.toggle("cg-motion-suspended", suspended);
      doc.dispatchEvent(new CustomEvent("cg-motion-suspension-change", { detail: { suspended: suspended } }));
    }

    function isFormField(node) {
      return !!(node && node.matches && node.matches('input,textarea,select,[contenteditable="true"]'));
    }

    function onFocusIn(event) {
      if (isFormField(event.target)) {
        formFocus = true;
        update();
      }
    }

    function onFocusOut() {
      window.setTimeout(function () {
        formFocus = isFormField(doc.activeElement);
        update();
      }, 0);
    }

    doc.addEventListener("focusin", onFocusIn);
    doc.addEventListener("focusout", onFocusOut);

    if ("MutationObserver" in window) {
      if (sentinelShell) {
        var sentinelObserver = new MutationObserver(update);
        sentinelObserver.observe(sentinelShell, { attributes: true, attributeFilter: ["hidden", "aria-hidden"] });
        observers.push(sentinelObserver);
      }
      if (mobileMenu) {
        var menuObserver = new MutationObserver(update);
        menuObserver.observe(mobileMenu, { attributes: true, attributeFilter: ["class", "aria-hidden"] });
        observers.push(menuObserver);
      }
    }

    update();
    return function () {
      observers.forEach(function (observer) { observer.disconnect(); });
      doc.removeEventListener("focusin", onFocusIn);
      doc.removeEventListener("focusout", onFocusOut);
      root.classList.remove("cg-motion-suspended");
    };
  }

  function onSystemMotionChange() {
    if (explicitPreference) return;
    applyMotionLevel();
  }

  function onCapabilityChange() {
    refreshCapabilityState();
    if (!explicitPreference) applyMotionLevel();
    if (controller && (touchFirstSmall || saveData)) controller.pause();
  }

  refreshCapabilityState();
  root.classList.add("cg-cinematic-ready");
  injectMotionTokens();
  applyMotionLevel();

  if (motionQuery.addEventListener) motionQuery.addEventListener("change", onSystemMotionChange);
  else if (motionQuery.addListener) motionQuery.addListener(onSystemMotionChange);
  if (touchFirstQuery.addEventListener) touchFirstQuery.addEventListener("change", onCapabilityChange);
  else if (touchFirstQuery.addListener) touchFirstQuery.addListener(onCapabilityChange);
  window.addEventListener("resize", onCapabilityChange, { passive: true });

  ready(function () {
    var hero = doc.getElementById("hero") || doc.querySelector(".hero");
    if (hero) {
      buildMotionControl(hero);
      controller = new PerformanceModeController(hero);
      if (!reduced && !touchFirstSmall && !saveData) {
        buildNetwork(hero);
        controller.start();
      }
    }
    suspensionCleanup = configureSuspension();
    configureSectionTransitions();
  });

  window.addEventListener("pagehide", function () {
    if (controller) controller.stop();
    if (sectionObserver) sectionObserver.disconnect();
    if (suspensionCleanup) suspensionCleanup();
    window.removeEventListener("resize", onCapabilityChange);
    if (motionQuery.removeEventListener) motionQuery.removeEventListener("change", onSystemMotionChange);
    else if (motionQuery.removeListener) motionQuery.removeListener(onSystemMotionChange);
    if (touchFirstQuery.removeEventListener) touchFirstQuery.removeEventListener("change", onCapabilityChange);
    else if (touchFirstQuery.removeListener) touchFirstQuery.removeListener(onCapabilityChange);
  }, { once: true });
})();

/* ClearGlass · Unified Assistant Fixture
   Additive replacement for overlapping Sentinel / Stealth Glass floating controls.
   Preserves Stealth Glass state + capability events while presenting one accessible fixture. */
(function () {
  "use strict";
  if (window.__cgStealthGlass) return;
  window.__cgStealthGlass = true;

  var KEY = "cg-stealth";
  var ON = "on";
  var OFF = "off";
  var reduce = false;
  var collisionRaf = 0;
  var legacyObserver = null;

  try { reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches; } catch (e) {}

  function stored() { try { return localStorage.getItem(KEY); } catch (e) { return null; } }
  function save(v) { try { localStorage.setItem(KEY, v); } catch (e) {}
  }

  function ready(fn) {
    if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", fn, { once: true });
    else fn();
  }

  function loadOnce(selector, tagName, attrs) {
    if (document.querySelector(selector)) return;
    var el = document.createElement(tagName);
    Object.keys(attrs).forEach(function (key) { el.setAttribute(key, attrs[key]); });
    (tagName === "script" ? document.body : document.head).appendChild(el);
  }

  loadOnce('link[href="/security-stack-fusion.css"],link[href="security-stack-fusion.css"]', "link", {
    rel: "stylesheet",
    href: "/security-stack-fusion.css",
    "data-security-stack-fusion": "true"
  });

  if (!window.__cgAnalytics && !document.querySelector("script[data-cg-analytics]")) {
    var analytics = document.createElement("script");
    analytics.src = "/analytics.js";
    analytics.defer = true;
    analytics.setAttribute("data-cg-analytics", "");
    (document.head || document.documentElement).appendChild(analytics);
  }

  var FX_CSS = [
    "#cg-neon-aura{position:fixed;inset:0;z-index:1;pointer-events:none;box-shadow:inset 0 0 110px rgba(96,165,250,.07),inset 0 0 34px rgba(167,139,250,.055);animation:cgNeonAura 6s ease-in-out infinite}",
    "@keyframes cgNeonAura{0%,100%{opacity:.58}50%{opacity:.92}}",
    "[data-skin='stealth'] #cg-neon-aura{box-shadow:inset 0 0 130px rgba(120,224,200,.09),inset 0 0 42px rgba(96,165,250,.06)}",
    "#cg-stealth-veil{position:fixed;inset:0;z-index:9700;pointer-events:none;background:rgba(5,8,12,.26);-webkit-backdrop-filter:saturate(.6) brightness(.86);backdrop-filter:saturate(.6) brightness(.86);opacity:0;animation:cgSgVeil .3s cubic-bezier(.16,1,.3,1) forwards}",
    "@keyframes cgSgVeil{to{opacity:1}}",
    "@media(prefers-reduced-motion:reduce){#cg-neon-aura{animation:none;opacity:.8}#cg-stealth-veil{animation:none;opacity:1}}"
  ].join("");

  function injectStyle() {
    if (document.getElementById("cg-stealth-style")) return;
    var style = document.createElement("style");
    style.id = "cg-stealth-style";
    style.textContent = FX_CSS;
    document.head.appendChild(style);
  }

  function getStack() {
    var stack = document.getElementById("cg-security-stack");
    if (!stack) {
      stack = document.createElement("div");
      stack.id = "cg-security-stack";
      document.body.appendChild(stack);
    }
    stack.setAttribute("role", "region");
    stack.setAttribute("aria-label", "ClearGlass assistant");
    document.body.classList.add("cg-security-dock-mounted");
    return stack;
  }

  function veil(on) {
    var el = document.getElementById("cg-stealth-veil");
    if (on) {
      if (!el && document.body) {
        el = document.createElement("div");
        el.id = "cg-stealth-veil";
        el.setAttribute("aria-hidden", "true");
        document.body.appendChild(el);
      }
    } else if (el && el.parentNode) {
      el.parentNode.removeChild(el);
    }
  }

  function apply(on, btn, status) {
    [document.documentElement, document.body].forEach(function (node) {
      if (!node) return;
      if (on) node.setAttribute("data-skin", "stealth");
      else if (node.getAttribute("data-skin") === "stealth") node.removeAttribute("data-skin");
    });
    veil(on);
    if (btn) {
      btn.setAttribute("aria-pressed", String(on));
      btn.classList.toggle("is-on", on);
      btn.title = on ? "Stealth Glass ON · tap to restore signal" : "Stealth Glass · dim and desaturate";
      var state = btn.querySelector(".cg-action-state");
      if (state) state.textContent = on ? "On" : "Off";
    }
    if (status) {
      status.classList.toggle("is-on", on);
      status.setAttribute("aria-label", "Stealth Glass " + (on ? "on" : "off"));
      var statusText = status.querySelector(".cg-stealth-status-text");
      if (statusText) statusText.textContent = on ? "Stealth On" : "Stealth Glass";
    }
  }

  function dispatchCapability(action, source) {
    window.dispatchEvent(new CustomEvent("clearglass:capability-control", {
      detail: { action: action, source: source || "unified-assistant" }
    }));
  }

  function setExpanded(stack, launcher, panel, expanded, focusFirst) {
    stack.classList.toggle("is-expanded", expanded);
    launcher.setAttribute("aria-expanded", String(expanded));
    panel.setAttribute("aria-hidden", String(!expanded));
    if (expanded && focusFirst) {
      var first = panel.querySelector("a[href],button:not([disabled])");
      if (first) window.setTimeout(function () { first.focus(); }, reduce ? 0 : 120);
    }
    scheduleCollisionCheck();
  }

  function buildPanel(stack) {
    var panel = document.getElementById("cg-assistant-panel");
    if (panel) return panel;

    panel = document.createElement("div");
    panel.id = "cg-assistant-panel";
    panel.className = "cg-assistant-panel";
    panel.setAttribute("aria-hidden", "true");
    panel.innerHTML =
      '<div class="cg-assistant-head">' +
        '<div class="cg-assistant-brand"><span class="cg-assistant-live" aria-hidden="true"></span><strong>ClearGlass</strong></div>' +
        '<span id="cg-stealth-status" class="cg-stealth-status" aria-label="Stealth Glass off"><span class="cg-stealth-status-dot" aria-hidden="true"></span><span class="cg-stealth-status-text">Stealth Glass</span></span>' +
      '</div>' +
      '<nav class="cg-assistant-actions" aria-label="ClearGlass assistant actions">' +
        '<a class="cg-assistant-action cg-assistant-action--primary" href="/sentinel.html" data-cg-action="ask" aria-label="Ask a question with Sentinel">' +
          '<span class="cg-action-icon" aria-hidden="true">💬</span><span class="cg-action-copy"><strong>Ask a question</strong><small>Open Sentinel</small></span><span class="cg-action-arrow" aria-hidden="true">↗</span>' +
        '</a>' +
        '<button type="button" id="cg-stealth-btn" class="cg-assistant-action" data-cg-action="stealth" aria-label="Toggle Stealth Glass visual mode" aria-pressed="false">' +
          '<span class="cg-action-icon cg-action-icon--moon" aria-hidden="true">◐</span><span class="cg-action-copy"><strong>Stealth Glass</strong><small>Privacy visual mode</small></span><span class="cg-action-state">Off</span>' +
        '</button>' +
        '<a class="cg-assistant-action cg-capability-control" href="/web-design.html" data-action="action-1" data-cg-action="web-design" aria-label="Action 1, Web Design and Development">' +
          '<span class="cg-action-index" aria-hidden="true">01</span><span class="cg-action-copy"><strong>Action 1</strong><small>Web Design &amp; Development</small></span><span class="cg-action-arrow" aria-hidden="true">↗</span>' +
        '</a>' +
        '<a class="cg-assistant-action cg-capability-control" href="/blog/" data-action="action-2" data-cg-action="insights" aria-label="Action 2, ClearGlass Insights">' +
          '<span class="cg-action-index" aria-hidden="true">02</span><span class="cg-action-copy"><strong>Action 2</strong><small>ClearGlass Insights</small></span><span class="cg-action-arrow" aria-hidden="true">↗</span>' +
        '</a>' +
      '</nav>' +
      '<div class="cg-assistant-status-slot" aria-live="polite"></div>';

    stack.appendChild(panel);
    return panel;
  }

  function buildLauncher(stack) {
    var launcher = document.getElementById("cg-assistant-launcher");
    if (launcher) return launcher;

    launcher = document.createElement("button");
    launcher.id = "cg-assistant-launcher";
    launcher.type = "button";
    launcher.setAttribute("aria-label", "Open ClearGlass assistant");
    launcher.setAttribute("aria-controls", "cg-assistant-panel");
    launcher.setAttribute("aria-expanded", "false");
    launcher.innerHTML =
      '<span class="cg-launcher-icon" aria-hidden="true"><span class="cg-launcher-pulse"></span>💬</span>' +
      '<span class="cg-launcher-copy"><strong>Ask Sentinel</strong><small>ClearGlass</small></span>' +
      '<span class="cg-launcher-chevron" aria-hidden="true">⌃</span>';
    stack.appendChild(launcher);
    return launcher;
  }

  function adoptAegisStatus(panel) {
    var status = document.getElementById("aegis-glass-status");
    var slot = panel && panel.querySelector(".cg-assistant-status-slot");
    if (status && slot && status.parentNode !== slot) slot.appendChild(status);
  }

  function hideLegacyAssistantControls(stack) {
    if (!document.body) return;
    var nodes = document.querySelectorAll("button,a,[role='button'],iframe");
    var w = window.innerWidth || document.documentElement.clientWidth;
    var h = window.innerHeight || document.documentElement.clientHeight;

    Array.prototype.forEach.call(nodes, function (node) {
      if (!node || stack.contains(node) || node.classList.contains("cg-legacy-assistant-hidden")) return;
      var label = [node.textContent || "", node.getAttribute("aria-label") || "", node.getAttribute("title") || "", node.id || "", node.className || ""].join(" ").toLowerCase();
      if (!/(ask\s*sentinel|sentinel.*chat|chat.*sentinel|open.*chat|chat.*widget|assistant.*chat|chat.*assistant)/i.test(label)) return;

      var cs;
      try { cs = window.getComputedStyle(node); } catch (e) { return; }
      if (!cs || (cs.position !== "fixed" && cs.position !== "sticky")) return;

      var rect;
      try { rect = node.getBoundingClientRect(); } catch (e2) { return; }
      if (!rect || rect.width < 20 || rect.height < 20) return;
      if (rect.right < w * 0.55 || rect.bottom < h * 0.55) return;

      node.classList.add("cg-legacy-assistant-hidden");
      node.setAttribute("data-cg-legacy-assistant", "hidden-by-unified-fixture");
      node.setAttribute("aria-hidden", "true");
      if (node.tagName !== "IFRAME") node.setAttribute("tabindex", "-1");
    });
  }

  function updateModalState() {
    var modal = document.querySelector('dialog[open],[role="dialog"][aria-modal="true"],[aria-modal="true"]');
    document.body.classList.toggle("cg-assistant-modal-active", !!modal);
  }

  function isVisible(node) {
    if (!node || !node.getBoundingClientRect) return false;
    var rect = node.getBoundingClientRect();
    if (rect.width < 2 || rect.height < 2) return false;
    var cs = window.getComputedStyle(node);
    return cs.display !== "none" && cs.visibility !== "hidden" && Number(cs.opacity || 1) > 0;
  }

  function avoidCTAOverlap() {
    collisionRaf = 0;
    var stack = document.getElementById("cg-security-stack");
    var launcher = document.getElementById("cg-assistant-launcher");
    if (!stack || !launcher || stack.classList.contains("is-expanded")) {
      if (stack) stack.style.setProperty("--cg-assistant-lift", "0px");
      return;
    }

    stack.style.setProperty("--cg-assistant-lift", "0px");
    var base = launcher.getBoundingClientRect();
    var candidates = document.querySelectorAll('a,button,[role="button"]');
    var maxLift = Math.min((window.innerHeight || 800) * 0.38, window.innerWidth <= 720 ? 190 : 280);
    var lift = 0;

    Array.prototype.forEach.call(candidates, function (node) {
      if (stack.contains(node) || node.classList.contains("cg-legacy-assistant-hidden") || !isVisible(node)) return;
      var label = [node.textContent || "", node.id || "", node.className || "", node.getAttribute("aria-label") || ""].join(" ").toLowerCase();
      if (!/(cta|book|pricing|plans|contact|demo|get started|request|schedule|checkout|buy now|start now|security engagement)/i.test(label)) return;
      var r = node.getBoundingClientRect();
      var horizontal = r.right > base.left - 10 && r.left < base.right + 10;
      var vertical = r.bottom > base.top - 10 && r.top < base.bottom + 10;
      if (!horizontal || !vertical) return;
      lift = Math.max(lift, base.bottom - r.top + 14);
    });

    stack.style.setProperty("--cg-assistant-lift", Math.max(0, Math.min(maxLift, lift)) + "px");
  }

  function scheduleCollisionCheck() {
    if (collisionRaf) cancelAnimationFrame(collisionRaf);
    collisionRaf = requestAnimationFrame(avoidCTAOverlap);
  }

  function build() {
    if (!document.body) return;
    injectStyle();

    if (!document.getElementById("cg-neon-aura")) {
      var aura = document.createElement("div");
      aura.id = "cg-neon-aura";
      aura.setAttribute("aria-hidden", "true");
      document.body.appendChild(aura);
    }

    var stack = getStack();
    var panel = buildPanel(stack);
    var launcher = buildLauncher(stack);
    var stealthButton = document.getElementById("cg-stealth-btn");
    var stealthStatus = document.getElementById("cg-stealth-status");
    var active = stored() === ON;

    apply(active, stealthButton, stealthStatus);
    adoptAegisStatus(panel);
    hideLegacyAssistantControls(stack);
    updateModalState();

    launcher.addEventListener("click", function () {
      var expanded = launcher.getAttribute("aria-expanded") !== "true";
      setExpanded(stack, launcher, panel, expanded, false);
      launcher.setAttribute("aria-label", expanded ? "Close ClearGlass assistant" : "Open ClearGlass assistant");
    });

    if (stealthButton) {
      stealthButton.addEventListener("click", function () {
        active = !(stealthButton.getAttribute("aria-pressed") === "true");
        save(active ? ON : OFF);
        apply(active, stealthButton, stealthStatus);
        window.dispatchEvent(new CustomEvent("clearglass:stealth", { detail: { active: active } }));
      });
    }

    Array.prototype.forEach.call(panel.querySelectorAll("[data-action^='action-']"), function (control) {
      control.addEventListener("click", function () {
        dispatchCapability(control.getAttribute("data-action"), "unified-assistant");
      });
    });

    panel.addEventListener("click", function (event) {
      var link = event.target.closest && event.target.closest("a[href]");
      if (link) setExpanded(stack, launcher, panel, false, false);
    });

    document.addEventListener("keydown", function (event) {
      if (event.key !== "Escape" || launcher.getAttribute("aria-expanded") !== "true") return;
      setExpanded(stack, launcher, panel, false, false);
      launcher.focus();
    });

    document.addEventListener("pointerdown", function (event) {
      if (launcher.getAttribute("aria-expanded") !== "true") return;
      if (stack.contains(event.target)) return;
      setExpanded(stack, launcher, panel, false, false);
    }, { passive: true });

    window.addEventListener("resize", scheduleCollisionCheck, { passive: true });
    window.addEventListener("orientationchange", scheduleCollisionCheck, { passive: true });
    window.addEventListener("scroll", scheduleCollisionCheck, { passive: true });

    legacyObserver = new MutationObserver(function () {
      adoptAegisStatus(panel);
      hideLegacyAssistantControls(stack);
      updateModalState();
      scheduleCollisionCheck();
    });
    legacyObserver.observe(document.body, { childList: true, subtree: true, attributes: true, attributeFilter: ["open", "aria-modal", "class", "style"] });

    scheduleCollisionCheck();
  }

  window.__cgRefreshSecurityStack = function () {
    var stack = getStack();
    var panel = document.getElementById("cg-assistant-panel");
    if (panel) adoptAegisStatus(panel);
    hideLegacyAssistantControls(stack);
    updateModalState();
    scheduleCollisionCheck();
  };

  ready(build);
})();
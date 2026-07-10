/* ClearGlass · stealth-glass toggle — one self-contained, premium glass button for
   every page. Drop in with <script defer src="/stealth-glass.js"></script>. No
   dependencies. This is the single source of truth: every page consumes this file,
   so the control stays identical site-wide and there are no per-page variants.

   Design: a future-forward, compact glass *secondary* chip — translucent frosted
   surface, hairline gradient ring, soft inner highlight + outer glow, a restrained
   shimmer sweep on hover/focus, a slow ambient pulse, and a subtle magnetic drift
   toward the pointer. It is deliberately SMALLER and lighter in visual weight than
   the primary CTA (≈26px tall vs. the ~34px btn--sm / 54px logo badge) so it never
   competes with the main action.

   Engineering guarantees:
   - Animates only compositor-friendly properties (transform / opacity / shadow);
     pointer tracking is rAF-throttled and clamped to a few px.
   - Small-area backdrop blur on the chip; the optional stealth veil uses a single
     light saturate/brightness pass (no full-screen blur).
   - Real <button> with aria-pressed / aria-label, visible focus ring, honours
     prefers-reduced-motion (kills sweep, pulse and drift), and degrades gracefully
     where backdrop-filter is unsupported (solid frosted fallback via @supports).
   - Idempotent; choice persists across pages via localStorage. */
(function () {
  "use strict";
  if (window.__cgStealthGlass) return;
  window.__cgStealthGlass = true;

  /* Load the site-wide analytics loader once. It is config-gated in
     /analytics.js and does nothing (no network, no cookies) until a provider is
     set there, so this is safe to ship on every page. */
  if (!window.__cgAnalytics && !document.querySelector("script[data-cg-analytics]")) {
    var _cgA = document.createElement("script");
    _cgA.src = "/analytics.js";
    _cgA.defer = true;
    _cgA.setAttribute("data-cg-analytics", "");
    (document.head || document.documentElement).appendChild(_cgA);
  }

  var KEY = "cg-stealth"; // localStorage flag: "on" | "off"
  var ON = "on", OFF = "off";
  var reduce = false;
  try { reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches; } catch (e) {}

  function stored() { try { return localStorage.getItem(KEY); } catch (e) { return null; } }
  function save(v) { try { localStorage.setItem(KEY, v); } catch (e) {} }

  var CSS = [
    /* ── universal NEON AURA: a soft edge-glow + corner bloom on every page ──── */
    "#cg-neon-aura{position:fixed;inset:0;z-index:2147483000;pointer-events:none;will-change:opacity;",
    "box-shadow:inset 0 0 130px rgba(96,165,250,.10),inset 0 0 46px rgba(167,139,250,.08);",
    "animation:cgNeonAura 6s ease-in-out infinite}",
    /* the bloom sits at the bottom-right, anchoring the control cluster */
    "#cg-neon-aura::after{content:'';position:absolute;right:-46px;bottom:-46px;width:340px;height:340px;",
    "border-radius:50%;background:radial-gradient(circle,rgba(96,165,250,.16),rgba(167,139,250,.09) 46%,transparent 72%);",
    "filter:blur(6px)}",
    "@keyframes cgNeonAura{0%,100%{opacity:.65}50%{opacity:1}}",
    "@media(max-width:640px){#cg-neon-aura::after{width:240px;height:240px;right:-40px;bottom:-40px}}",
    "@media (prefers-reduced-motion:reduce){#cg-neon-aura{animation:none;opacity:.8}}",
    /* stealth ON deepens the aura toward teal to match the engaged control */
    "[data-skin='stealth'] #cg-neon-aura{box-shadow:inset 0 0 150px rgba(120,224,200,.12),inset 0 0 50px rgba(96,165,250,.08)}",
    "[data-skin='stealth'] #cg-neon-aura::after{background:radial-gradient(circle,rgba(120,224,200,.18),rgba(96,165,250,.08) 46%,transparent 72%)}",

    /* ── universal stealth veil: one light, blur-free desaturate pass ───────── */
    "#cg-stealth-veil{position:fixed;inset:0;z-index:2147483646;pointer-events:none;",
    "background:rgba(5,8,12,.26);will-change:opacity;",
    "-webkit-backdrop-filter:saturate(.6) brightness(.86);backdrop-filter:saturate(.6) brightness(.86);",
    "opacity:0;animation:cgSgVeil .4s cubic-bezier(.16,1,.3,1) forwards}",
    "@keyframes cgSgVeil{to{opacity:1}}",

    /* ── the chip: a compact, premium glass secondary button ────────────────── */
    "#cg-stealth-btn{--cg-mx:0px;--cg-my:0px;",
    "position:fixed;right:18px;bottom:84px;z-index:2147483647;",
    "display:inline-flex;align-items:center;gap:6px;height:26px;padding:0 11px 0 9px;",
    "margin:0;border:0;border-radius:999px;cursor:pointer;white-space:nowrap;line-height:1;",
    "overflow:hidden;isolation:isolate;-webkit-tap-highlight-color:transparent;",
    "font-family:'IBM Plex Mono',ui-monospace,SFMono-Regular,Menlo,monospace;",
    "font-size:9.5px;font-weight:600;letter-spacing:.14em;text-transform:uppercase;color:#e7eeff;",
    "background:linear-gradient(165deg,rgba(30,34,58,.55),rgba(12,14,28,.62));",
    "-webkit-backdrop-filter:blur(10px) saturate(1.5);backdrop-filter:blur(10px) saturate(1.5);",
    "box-shadow:0 4px 18px rgba(0,0,0,.38),0 0 0 .5px rgba(150,170,255,.30),",
    "inset 0 1px 0 rgba(255,255,255,.14),inset 0 -1px 0 rgba(0,0,0,.25);",
    "transform:translate3d(var(--cg-mx),var(--cg-my),0);will-change:transform;",
    "transition:transform .22s cubic-bezier(.16,1,.3,1),box-shadow .22s ease,color .22s ease,background .22s ease}",

    /* hairline gradient ring (1px, masked) */
    "#cg-stealth-btn::after{content:'';position:absolute;inset:0;border-radius:inherit;padding:1px;pointer-events:none;",
    "background:linear-gradient(150deg,rgba(180,200,255,.55),rgba(150,170,255,.06) 42%,rgba(120,224,200,.14));",
    "-webkit-mask:linear-gradient(#000 0 0) content-box,linear-gradient(#000 0 0);-webkit-mask-composite:xor;",
    "mask:linear-gradient(#000 0 0) content-box,linear-gradient(#000 0 0);mask-composite:exclude;",
    "opacity:.7;transition:opacity .22s ease;z-index:3}",

    /* micro-reflection shimmer sweep */
    "#cg-stealth-btn::before{content:'';position:absolute;inset:0;border-radius:inherit;pointer-events:none;z-index:1;",
    "background:linear-gradient(115deg,transparent 30%,rgba(255,255,255,.16) 48%,rgba(255,255,255,.04) 54%,transparent 70%);",
    "transform:translateX(-130%);transition:transform .7s cubic-bezier(.16,1,.3,1)}",
    "#cg-stealth-btn:hover::before,#cg-stealth-btn:focus-visible::before{transform:translateX(130%)}",

    /* restrained, alive hover / press / focus */
    "#cg-stealth-btn:hover{color:#fff;transform:translate3d(var(--cg-mx),calc(var(--cg-my) - 1.5px),0) scale(1.04);",
    "box-shadow:0 8px 26px rgba(0,0,0,.46),0 0 0 .5px rgba(170,190,255,.5),0 0 22px -2px rgba(120,160,255,.5),",
    "inset 0 1px 0 rgba(255,255,255,.2),inset 0 -1px 0 rgba(0,0,0,.28)}",
    "#cg-stealth-btn:hover::after{opacity:1}",
    "#cg-stealth-btn:active{transform:translate3d(var(--cg-mx),var(--cg-my),0) scale(.975)}",
    "#cg-stealth-btn:focus-visible{outline:2px solid #a9b8ff;outline-offset:3px}",

    /* icon + label sit above the sweep */
    "#cg-stealth-btn .cg-sg-ic{width:13px;height:13px;display:block;flex:0 0 auto;position:relative;z-index:2;",
    "filter:drop-shadow(0 0 4px rgba(140,170,255,.45))}",
    "#cg-stealth-btn .cg-sg-ic svg{width:100%;height:100%;display:block}",
    "#cg-stealth-btn .cg-sg-tx{position:relative;z-index:2}",

    /* slow ambient pulse (opacity only) */
    "#cg-stealth-btn .cg-sg-glow{position:absolute;inset:0;border-radius:inherit;z-index:0;pointer-events:none;",
    "background:radial-gradient(60% 120% at 18% 50%,rgba(130,160,255,.22),transparent 70%);",
    "opacity:.5;animation:cgSgPulse 4.2s ease-in-out infinite}",
    "@keyframes cgSgPulse{0%,100%{opacity:.4}50%{opacity:.85}}",

    /* engaged state (stealth ON) — teal glass */
    "#cg-stealth-btn.is-on{color:#c9fbf2;background:linear-gradient(165deg,rgba(10,26,26,.6),rgba(4,14,14,.66));",
    "box-shadow:0 4px 18px rgba(0,0,0,.5),0 0 0 .5px rgba(120,224,200,.5),0 0 20px -3px rgba(120,224,200,.5),",
    "inset 0 1px 0 rgba(190,255,240,.16),inset 0 -1px 0 rgba(0,0,0,.3)}",
    "#cg-stealth-btn.is-on .cg-sg-ic{filter:drop-shadow(0 0 5px rgba(120,224,200,.7))}",
    "#cg-stealth-btn.is-on .cg-sg-glow{background:radial-gradient(60% 120% at 18% 50%,rgba(120,224,200,.28),transparent 70%)}",
    "#cg-stealth-btn.is-on::after{background:linear-gradient(150deg,rgba(160,255,238,.6),rgba(120,224,200,.06) 45%,rgba(120,224,200,.2))}",

    /* mobile — a touch smaller, still ≥24px (WCAG 2.2 target size) */
    "@media(max-width:640px){#cg-stealth-btn{right:14px;bottom:72px;height:25px;font-size:9px;padding:0 10px 0 8px}}",

    /* reduced motion — drop loops, sweep & drift; keep instant states */
    "@media (prefers-reduced-motion:reduce){#cg-stealth-btn,#cg-stealth-btn:hover,#cg-stealth-btn:active{transition:none}",
    "#cg-stealth-btn::before{display:none}#cg-stealth-btn .cg-sg-glow{animation:none}",
    "#cg-stealth-veil{animation:none;opacity:1}}",

    /* graceful degradation — no backdrop-filter → solid frosted fallback */
    "@supports not ((backdrop-filter:blur(1px)) or (-webkit-backdrop-filter:blur(1px))){",
    "#cg-stealth-btn{background:linear-gradient(165deg,rgba(26,30,52,.96),rgba(10,12,24,.97))}",
    "#cg-stealth-veil{background:rgba(6,9,13,.5)}}"
  ].join("");

  /* paint or remove the universal desaturating veil */
  function veil(on) {
    var el = document.getElementById("cg-stealth-veil");
    if (on) {
      if (!el && document.body) {
        el = document.createElement("div");
        el.id = "cg-stealth-veil";
        el.setAttribute("aria-hidden", "true");
        document.body.appendChild(el);
      }
    } else if (el) {
      el.parentNode.removeChild(el);
    }
  }

  /* apply state to the document + reflect it on the button */
  function apply(on, btn) {
    [document.documentElement, document.body].forEach(function (n) {
      if (!n) return;
      if (on) n.setAttribute("data-skin", "stealth");
      else if (n.getAttribute("data-skin") === "stealth") n.removeAttribute("data-skin");
    });
    veil(on);
    if (btn) {
      btn.setAttribute("aria-pressed", String(on));
      btn.classList.toggle("is-on", on);
      btn.title = on ? "Stealth glass ON · tap to restore signal" : "Stealth glass · dim & desaturate";
    }
  }

  /* subtle magnetic drift — rAF-throttled, clamped, compositor-only */
  function magnetize(btn) {
    if (reduce) return;
    var raf = 0, mx = 0, my = 0;
    function flush() {
      raf = 0;
      btn.style.setProperty("--cg-mx", mx.toFixed(2) + "px");
      btn.style.setProperty("--cg-my", my.toFixed(2) + "px");
    }
    btn.addEventListener("pointermove", function (e) {
      var r = btn.getBoundingClientRect();
      var dx = (e.clientX - (r.left + r.width / 2)) / (r.width / 2);
      var dy = (e.clientY - (r.top + r.height / 2)) / (r.height / 2);
      mx = Math.max(-1, Math.min(1, dx)) * 2.5;
      my = Math.max(-1, Math.min(1, dy)) * 2.5;
      if (!raf) raf = requestAnimationFrame(flush);
    });
    btn.addEventListener("pointerleave", function () {
      if (raf) { cancelAnimationFrame(raf); raf = 0; }
      mx = my = 0;
      btn.style.setProperty("--cg-mx", "0px");
      btn.style.setProperty("--cg-my", "0px");
    });
  }

  function build() {
    if (document.getElementById("cg-stealth-btn")) return;

    var style = document.createElement("style");
    style.textContent = CSS;
    document.head.appendChild(style);

    /* site-wide neon aura — one element, present on every page (incl. home) */
    if (!document.getElementById("cg-neon-aura")) {
      var aura = document.createElement("div");
      aura.id = "cg-neon-aura";
      aura.setAttribute("aria-hidden", "true");
      document.body.appendChild(aura);
    }

    var btn = document.createElement("button");
    btn.id = "cg-stealth-btn";
    btn.type = "button";
    btn.setAttribute("aria-label", "Toggle stealth glass appearance");
    btn.setAttribute("aria-pressed", "false");
    btn.innerHTML =
      '<span class="cg-sg-glow" aria-hidden="true"></span>' +
      '<span class="cg-sg-ic" aria-hidden="true">' +
      '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" ' +
      'stroke-linecap="round" stroke-linejoin="round"><path d="M12 3a9 9 0 109 9 7 7 0 01-9-9z"/></svg>' +
      '</span><span class="cg-sg-tx">Stealth Glass</span>';

    document.body.appendChild(btn);

    var on = stored() === ON;
    apply(on, btn);
    magnetize(btn);

    btn.addEventListener("click", function () {
      on = !on;
      save(on ? ON : OFF);
      apply(on, btn);
    });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", build);
  } else {
    build();
  }
})();

/* ClearGlass · stealth-glass toggle — a fixed, self-contained "Stealth Glass"
   button for every page. Drop in with <script defer src="/stealth-glass.js"></script>.
   No dependencies. It is deliberately SMALLER than the standard action button: a
   compact glass chip (~26px tall) rather than the full ~34px `btn--sm` / 54px logo
   badge. Sits in the bottom-left, stacked just above the corner logo badge, so it
   never collides with page navbars (top), the shared nav tab (right edge), or the
   badge itself (bottom-left). Idempotent — a second include is a no-op.

   Clicking it toggles a site-wide "stealth" skin: it sets data-skin="stealth" on
   <html>/<body> (so pages with a native stealth skin, e.g. the command console,
   respond), and paints a universal desaturating glass veil so the dimmed look is
   visible on ANY page regardless of that page's own CSS. The choice is saved in
   localStorage, so stealth mode follows the visitor from page to page. */
(function () {
  "use strict";
  if (window.__cgStealthGlass) return;
  window.__cgStealthGlass = true;

  var KEY = "cg-stealth"; // localStorage flag: "on" | "off"
  var ON = "on", OFF = "off";

  function stored() {
    try { return localStorage.getItem(KEY); } catch (e) { return null; }
  }
  function save(v) {
    try { localStorage.setItem(KEY, v); } catch (e) {}
  }

  var CSS = [
    /* universal stealth veil: desaturate + dim everything painted behind it */
    "#cg-stealth-veil{position:fixed;inset:0;z-index:2147483646;pointer-events:none;",
    "background:rgba(5,8,12,.30);",
    "-webkit-backdrop-filter:grayscale(.5) saturate(.55) brightness(.84) contrast(1.04);",
    "backdrop-filter:grayscale(.5) saturate(.55) brightness(.84) contrast(1.04);",
    "animation:cgStealthFade .35s ease both}",
    "@keyframes cgStealthFade{from{opacity:0}to{opacity:1}}",

    /* the chip — a compact glass pill, smaller than the standard button */
    "#cg-stealth-btn{position:fixed;left:18px;bottom:84px;z-index:2147483647;",
    "display:inline-flex;align-items:center;gap:6px;height:26px;padding:0 11px;",
    "border-radius:999px;white-space:nowrap;line-height:1;cursor:pointer;",
    "font-family:'IBM Plex Mono',ui-monospace,SFMono-Regular,Menlo,monospace;",
    "font-size:9.5px;font-weight:600;letter-spacing:.14em;text-transform:uppercase;color:#dbe4ff;",
    "background:linear-gradient(180deg,rgba(18,20,42,.92),rgba(11,12,28,.92));",
    "border:1px solid rgba(124,150,255,.42);",
    "box-shadow:0 6px 22px rgba(0,0,0,.4),0 0 14px rgba(124,150,255,.22);",
    "-webkit-backdrop-filter:blur(6px);backdrop-filter:blur(6px);",
    "transition:transform .18s cubic-bezier(.16,1,.3,1),box-shadow .18s ease,border-color .18s ease,color .18s ease}",
    "#cg-stealth-btn:hover{transform:translateY(-2px);border-color:rgba(124,150,255,.85);color:#fff;",
    "box-shadow:0 8px 26px rgba(0,0,0,.46),0 0 20px rgba(96,165,250,.4)}",
    "#cg-stealth-btn:focus-visible{outline:2px solid #a78bfa;outline-offset:3px}",
    "#cg-stealth-btn:active{transform:translateY(0) scale(.97)}",
    "#cg-stealth-btn .cg-sg-ic{width:13px;height:13px;display:block;flex:0 0 auto}",
    "#cg-stealth-btn .cg-sg-ic svg{width:100%;height:100%;display:block}",
    /* active / engaged state — teal glass glow */
    "#cg-stealth-btn.is-on{color:#bff3ef;border-color:rgba(120,224,200,.6);",
    "background:linear-gradient(180deg,rgba(10,22,24,.94),rgba(6,14,16,.94));",
    "box-shadow:0 6px 22px rgba(0,0,0,.5),0 0 16px rgba(120,224,200,.34),inset 0 0 0 1px rgba(120,224,200,.14)}",
    "@media(max-width:640px){#cg-stealth-btn{left:14px;bottom:70px;height:24px;font-size:9px;padding:0 10px}}",
    "@media (prefers-reduced-motion:reduce){#cg-stealth-btn{transition:none}#cg-stealth-veil{animation:none}}"
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

  function build() {
    if (document.getElementById("cg-stealth-btn")) return;

    var style = document.createElement("style");
    style.textContent = CSS;
    document.head.appendChild(style);

    var btn = document.createElement("button");
    btn.id = "cg-stealth-btn";
    btn.type = "button";
    btn.setAttribute("aria-label", "Toggle stealth glass appearance");
    btn.setAttribute("aria-pressed", "false");
    btn.innerHTML =
      '<span class="cg-sg-ic" aria-hidden="true">' +
      '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" ' +
      'stroke-linecap="round" stroke-linejoin="round"><path d="M12 3a9 9 0 109 9 7 7 0 01-9-9z"/></svg>' +
      "</span><span class=\"cg-sg-tx\">Stealth Glass</span>";

    document.body.appendChild(btn);

    var on = stored() === ON;
    apply(on, btn);

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

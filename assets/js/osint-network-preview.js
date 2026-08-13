/**
 * Ontario OSINT -> Network Flow Intelligence bridge.
 * Page-scoped, dependency-free, lazy initialized, and safe to remove independently.
 */
(() => {
  "use strict";

  const PAGE_RE = /\/Ontario-osint\.html$/i;
  if (!PAGE_RE.test(location.pathname)) return;

  const SECTION_ID = "cg-network-intel-preview";
  const STYLE_ID = "cg-network-intel-preview-style";
  const EMBED_URL = "/clearglass.html?skipboot=1&embed=1";
  const FULL_URL = "/clearglass.html";
  let frameObserver = null;
  let mountFrame = 0;

  function isNetworkRoute() {
    return location.hash.replace(/^#/, "").toLowerCase() === "network";
  }

  function addStyles() {
    if (document.getElementById(STYLE_ID)) return;
    const style = document.createElement("style");
    style.id = STYLE_ID;
    style.textContent = `
      #${SECTION_ID}{
        margin-top:16px;
        border:1px solid var(--line-2,rgba(10,12,16,.14));
        border-radius:14px;
        overflow:hidden;
        background:linear-gradient(145deg,rgba(56,189,248,.08),rgba(167,139,250,.06) 48%,rgba(255,255,255,.5));
        box-shadow:0 18px 50px rgba(15,23,42,.08);
        content-visibility:auto;
        contain:layout paint;
        contain-intrinsic-size:680px;
      }
      body.theme-dark #${SECTION_ID}{
        background:linear-gradient(145deg,rgba(34,211,238,.08),rgba(124,58,237,.08) 48%,rgba(14,22,34,.94));
        box-shadow:0 18px 50px rgba(0,0,0,.28);
      }
      #${SECTION_ID} .cg-nfi-head{
        display:flex;gap:14px;align-items:flex-start;justify-content:space-between;
        padding:16px 18px;border-bottom:1px solid var(--line,rgba(10,12,16,.08));
      }
      #${SECTION_ID} .cg-nfi-kicker{
        font-family:var(--mono,'IBM Plex Mono',monospace);font-size:10px;font-weight:700;
        letter-spacing:.13em;text-transform:uppercase;color:var(--cyan,#0e9bbd);margin-bottom:5px;
      }
      #${SECTION_ID} .cg-nfi-title{font-size:17px;font-weight:800;letter-spacing:.01em}
      #${SECTION_ID} .cg-nfi-copy{margin-top:5px;max-width:760px;font-size:12px;line-height:1.6;color:var(--text-2,#3a3f4a)}
      #${SECTION_ID} .cg-nfi-actions{display:flex;gap:8px;flex-wrap:wrap;justify-content:flex-end}
      #${SECTION_ID} .cg-nfi-launch{
        display:inline-flex;align-items:center;justify-content:center;min-height:38px;padding:8px 13px;
        border-radius:9px;background:var(--cyan,#0e9bbd);border:1px solid var(--cyan,#0e9bbd);
        color:#fff!important;font:700 11px var(--mono,'IBM Plex Mono',monospace);letter-spacing:.035em;text-decoration:none!important;
      }
      #${SECTION_ID} .cg-nfi-launch:hover{filter:brightness(1.06)}
      #${SECTION_ID} .cg-nfi-init{
        min-height:38px;padding:8px 12px;border-radius:9px;border:1px solid var(--line-2,rgba(10,12,16,.14));
        background:var(--panel-2,rgba(255,255,255,.9));color:var(--text,#0a0c10);
        font:600 11px var(--mono,'IBM Plex Mono',monospace);cursor:pointer;
      }
      #${SECTION_ID} .cg-nfi-status{
        display:flex;align-items:center;gap:8px;padding:9px 18px;border-bottom:1px solid var(--line,rgba(10,12,16,.08));
        color:var(--text-2,#3a3f4a);font:600 10px var(--mono,'IBM Plex Mono',monospace);letter-spacing:.05em;
      }
      #${SECTION_ID} .cg-nfi-dot{width:7px;height:7px;border-radius:50%;background:var(--amber,#d97706);box-shadow:0 0 9px currentColor;flex:0 0 auto}
      #${SECTION_ID}[data-state="ready"] .cg-nfi-dot{background:var(--green,#0f9d6b)}
      #${SECTION_ID}[data-state="error"] .cg-nfi-dot{background:var(--red,#e11d48)}
      #${SECTION_ID} .cg-nfi-framewrap{position:relative;background:#070912;min-height:520px}
      #${SECTION_ID} iframe{display:block;width:100%;height:520px;border:0;background:#070912}
      #${SECTION_ID} .cg-nfi-noscript{padding:16px 18px;color:var(--text-2,#3a3f4a);font-size:12px}
      @media(max-width:820px){
        #${SECTION_ID} .cg-nfi-head{flex-direction:column}
        #${SECTION_ID} .cg-nfi-actions{width:100%;justify-content:flex-start}
        #${SECTION_ID} .cg-nfi-framewrap,#${SECTION_ID} iframe{min-height:430px;height:430px}
      }
      @media(max-width:560px){
        #${SECTION_ID} .cg-nfi-actions>*{width:100%}
        #${SECTION_ID} .cg-nfi-framewrap,#${SECTION_ID} iframe{min-height:390px;height:390px}
      }
    `;
    document.head.appendChild(style);
  }

  function setState(section, state, label) {
    section.dataset.state = state;
    const status = section.querySelector("[data-cg-nfi-status]");
    if (status) status.textContent = label;
  }

  function mount() {
    if (!isNetworkRoute() || document.getElementById(SECTION_ID)) return;
    const content = document.querySelector(".main .content");
    if (!content) return;

    addStyles();

    const section = document.createElement("section");
    section.id = SECTION_ID;
    section.dataset.state = "idle";
    section.setAttribute("aria-labelledby", "cg-nfi-preview-title");
    section.innerHTML = `
      <div class="cg-nfi-head">
        <div>
          <div class="cg-nfi-kicker">Network intelligence bridge</div>
          <div class="cg-nfi-title" id="cg-nfi-preview-title">Network Flow Intelligence</div>
          <div class="cg-nfi-copy">The institutional OSINT graph above remains the public-record context layer. This preview initializes the dedicated flow workstation for domain, IP, connection, and entity-relationship exploration without turning the control deck into a second full application.</div>
        </div>
        <div class="cg-nfi-actions">
          <button type="button" class="cg-nfi-init" data-cg-nfi-init>Initialize preview</button>
          <a class="cg-nfi-launch" href="${FULL_URL}">Launch Full Network Intelligence ↗</a>
        </div>
      </div>
      <div class="cg-nfi-status"><span class="cg-nfi-dot" aria-hidden="true"></span><span data-cg-nfi-status>Preview queued · lazy initialization</span></div>
      <div class="cg-nfi-framewrap">
        <iframe
          title="ClearGlass Network Flow Intelligence preview"
          loading="lazy"
          referrerpolicy="same-origin"
          fetchpriority="low"
          data-cg-nfi-frame
        ></iframe>
      </div>
      <noscript><div class="cg-nfi-noscript">JavaScript is required for the embedded preview. Use “Launch Full Network Intelligence” to open the standalone workstation.</div></noscript>
    `;

    content.appendChild(section);

    const frame = section.querySelector("[data-cg-nfi-frame]");
    const initButton = section.querySelector("[data-cg-nfi-init]");

    const initialize = () => {
      if (!frame || frame.dataset.initialized === "true") return;
      frame.dataset.initialized = "true";
      setState(section, "loading", "Initializing Network Flow Intelligence…");
      frame.src = EMBED_URL;
    };

    frame?.addEventListener("load", () => {
      setState(section, "ready", "Preview ready · standalone workstation available");
      if (initButton) {
        initButton.textContent = "Preview initialized";
        initButton.disabled = true;
        initButton.setAttribute("aria-disabled", "true");
      }
    }, { once: true });

    frame?.addEventListener("error", () => {
      setState(section, "error", "Preview unavailable · launch the standalone workstation");
      if (initButton) initButton.textContent = "Retry preview";
      if (frame) frame.dataset.initialized = "false";
    });

    initButton?.addEventListener("click", initialize);

    if ("IntersectionObserver" in window) {
      frameObserver?.disconnect();
      frameObserver = new IntersectionObserver(entries => {
        if (entries.some(entry => entry.isIntersecting)) {
          initialize();
          frameObserver?.disconnect();
          frameObserver = null;
        }
      }, { rootMargin: "280px 0px" });
      frameObserver.observe(section);
    } else {
      initialize();
    }
  }

  function scheduleMount() {
    if (mountFrame) cancelAnimationFrame(mountFrame);
    mountFrame = requestAnimationFrame(() => {
      mountFrame = 0;
      mount();
    });
  }

  const domObserver = new MutationObserver(scheduleMount);

  function init() {
    domObserver.observe(document.body, { childList: true, subtree: true });
    window.addEventListener("hashchange", scheduleMount, { passive: true });
    scheduleMount();
  }

  window.__cgOsintNetworkPreview = Object.freeze({ mount: scheduleMount });

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", init, { once: true });
  else init();
})();

/* ClearGlass · governed editorial visuals
   Contextually places reviewed concept artwork on approved pages.
   The module is additive, idempotent, dependency-free, and fail-quiet.
   Embedded artwork text is never promoted to machine-readable factual copy. */
(function () {
  "use strict";

  if (window.__cgEditorialVisuals) return;
  window.__cgEditorialVisuals = true;

  var page = (location.pathname.split("/").pop() || "").toLowerCase();
  var ITEMS = {
    "cyber-defense-console.html": {
      signal: "Incident simulation lens",
      title: "See the breach as an operating system problem.",
      copy: "A useful incident visual should move the reader from alarm to architecture: exposed identity, disrupted services, containment decisions, evidence preservation, recovery sequencing, and accountable human command.",
      src: "/assets/images/editorial/municipal-cyber-tabletop-concept.webp",
      width: 240,
      height: 360,
      alt: "Concept artwork showing a municipal cyber incident command interface over an aerial city map",
      disclosure: "Illustrative municipal ransomware tabletop scenario. It is not a report of an actual City of Burlington incident; dates, actors, records, and impacts shown in the artwork are fictional unless separately verified.",
      links: [
        ["Continuous threat-modeling framework", "/blog/autonomous-threat-modeling-2026.html"],
        ["Autonomous threat-modeling service", "/offers/autonomous-threat-modeling.html"]
      ],
      tone: "orange"
    },
    "advanced-features-tools-systems.html": {
      signal: "System decomposition",
      title: "Architecture becomes manageable when the layers are visible.",
      copy: "ClearGlass models systems as connected layers—interface, compute, storage, network, power, telemetry, policy, and recovery—so dependencies and failure boundaries can be reviewed before automation acts.",
      src: "/assets/images/editorial/laptop-system-decomposition-concept.webp",
      width: 240,
      height: 360,
      alt: "Conceptual exploded view of a laptop separated into display, chassis, thermal, compute, storage, wireless, battery, and expansion layers",
      disclosure: "Conceptual system-decomposition graphic. Component layout, numbering, and labels are illustrative and are not repair, safety, or service documentation.",
      links: [
        ["Map system relationships with AutoMap", "/automap.html"],
        ["Review governed autonomous operations", "/percival-os.html"]
      ],
      tone: "cyan"
    },
    "revenue-engine.html": {
      signal: "Growth operations concept",
      title: "Treat acquisition as an instrumented decision system.",
      copy: "The useful pattern is not visual spectacle. It is a controlled loop connecting audience hypotheses, creative tests, attribution, unit economics, approval gates, and post-campaign evidence.",
      src: "/assets/images/editorial/marketing-command-center-concept.webp",
      width: 400,
      height: 273,
      alt: "Concept artwork of a futuristic marketing command center with campaign, audience, funnel, and unit-economics panels",
      disclosure: "Concept artwork for a paid-growth operations interface. Names, seals, dashboards, metrics, people, and campaign claims in the artwork are not certifications, affiliations, customers, or measured results.",
      links: [
        ["Ethical sales-system playbook", "/blog/ethical-sales-system-100k-revenue-prompt.html"],
        ["Review ClearGlass engagements", "/offers/index.html"]
      ],
      tone: "gold"
    },
    "button-lab.html": {
      signal: "Trust-interface prototype",
      title: "Proof design must never outrun proof itself.",
      copy: "A premium testimonial treatment can establish hierarchy and confidence, but publication governance matters more than typography: attribution, permission, exact wording, role, organization, and evidence must be verified before an endorsement is presented as real.",
      src: "/assets/images/editorial/verified-trust-layout-concept.webp",
      width: 864,
      height: 1080,
      alt: "Sample dark testimonial layout with large quotation typography and a blue circuit-board motif",
      disclosure: "Sample testimonial-layout design. The displayed name, title, quotation, and endorsement are placeholder creative and are not presented as a verified customer testimonial.",
      links: [
        ["Explore web design and development", "/web-design.html"],
        ["Begin governed client onboarding", "/operations/client-onboarding.html"]
      ],
      tone: "violet"
    }
  };

  var item = ITEMS[page];
  if (!item) return;

  function el(tag, className, text) {
    var node = document.createElement(tag);
    if (className) node.className = className;
    if (text) node.textContent = text;
    return node;
  }

  function addStyles() {
    if (document.getElementById("cg-editorial-visual-styles")) return;
    var style = document.createElement("style");
    style.id = "cg-editorial-visual-styles";
    style.textContent = [
      ".cgev{--cgev-a:#56e7ff;--cgev-b:#9b8cff;position:relative;z-index:1;width:min(1120px,92vw);margin:clamp(54px,8vw,100px) auto;padding:clamp(18px,3vw,32px);border:1px solid rgba(120,190,255,.25);border-radius:20px;background:linear-gradient(145deg,rgba(7,14,28,.94),rgba(11,18,38,.88));box-shadow:0 32px 86px -48px rgba(0,0,0,.95),0 0 34px rgba(70,190,255,.08);color:#edf7ff;font-family:Inter,system-ui,-apple-system,sans-serif;overflow:hidden}",
      ".cgev[data-tone='orange']{--cgev-a:#ff9a52;--cgev-b:#ff5e39}.cgev[data-tone='gold']{--cgev-a:#ffd66b;--cgev-b:#ff9a52}.cgev[data-tone='violet']{--cgev-a:#bba5ff;--cgev-b:#54d9ff}",
      ".cgev:before{content:'';position:absolute;inset:0 0 auto;height:2px;background:linear-gradient(90deg,transparent,var(--cgev-a),var(--cgev-b),transparent)}",
      ".cgev__grid{display:grid;grid-template-columns:minmax(220px,.78fr) minmax(0,1.22fr);gap:clamp(24px,5vw,64px);align-items:center}",
      ".cgev__media{margin:0;position:relative}.cgev__frame{padding:8px;border:1px solid rgba(140,205,255,.28);border-radius:16px;background:rgba(2,7,16,.72);box-shadow:inset 0 0 30px rgba(80,200,255,.06),0 24px 54px -34px rgba(0,0,0,.95)}",
      ".cgev__frame img{display:block;width:100%;height:auto;max-height:620px;object-fit:contain;border-radius:11px;background:#030711}",
      ".cgev__caption{margin-top:11px;color:#91a6c2;font:500 .72rem/1.55 ui-monospace,SFMono-Regular,Consolas,monospace}",
      ".cgev__signal{display:inline-flex;align-items:center;gap:9px;color:var(--cgev-a);font:700 .7rem/1.3 ui-monospace,SFMono-Regular,Consolas,monospace;letter-spacing:.16em;text-transform:uppercase}",
      ".cgev__signal:before{content:'';width:24px;height:1px;background:var(--cgev-a);box-shadow:0 0 10px var(--cgev-a)}",
      ".cgev h2{margin:15px 0 17px;color:#f5fbff;font-size:clamp(1.8rem,3.7vw,3.25rem);line-height:1.03;letter-spacing:-.035em;font-weight:760}",
      ".cgev__copy{margin:0;color:#aec0d6;font-size:clamp(.98rem,1.35vw,1.12rem);line-height:1.72;max-width:64ch}",
      ".cgev__notice{margin:20px 0 0;padding:13px 15px;border-left:3px solid var(--cgev-a);border-radius:0 9px 9px 0;background:rgba(116,155,205,.08);color:#c7d7e8;font-size:.84rem;line-height:1.55}",
      ".cgev__notice strong{color:var(--cgev-a);letter-spacing:.04em}",
      ".cgev__links{display:flex;flex-wrap:wrap;gap:10px;margin-top:22px}.cgev__links a{display:inline-flex;align-items:center;text-decoration:none;color:#eaf7ff;font-weight:700;font-size:.84rem;padding:10px 13px;border:1px solid rgba(130,200,255,.28);border-radius:999px;background:rgba(47,93,145,.13);transition:transform .18s,border-color .18s,box-shadow .18s}",
      ".cgev__links a:hover{transform:translateY(-1px);border-color:var(--cgev-a);box-shadow:0 0 22px rgba(80,205,255,.12)}.cgev__links a:focus-visible{outline:2px solid var(--cgev-a);outline-offset:3px}",
      ".cg-holo-seal{--holo-blue:#27d9ff;--holo-cyan:#6ff7ff;--holo-violet:#9b7cff;position:relative;width:min(100%,520px);aspect-ratio:1/1;margin-inline:auto;display:grid;place-items:center;isolation:isolate;border-radius:50%;overflow:hidden;background:radial-gradient(circle at 50% 45%,rgba(35,220,255,.11),rgba(24,12,65,.16) 38%,rgba(2,5,15,.82) 72%,#01030a 100%);border:1px solid rgba(171,239,255,.34);box-shadow:inset 0 0 80px rgba(77,210,255,.1),0 0 70px rgba(43,178,255,.14),0 0 110px rgba(132,89,255,.1)}",
      ".cg-holo-seal:before{content:'';position:absolute;inset:5%;border-radius:50%;background:repeating-radial-gradient(circle,transparent 0 24px,rgba(76,224,255,.055) 25px 26px),linear-gradient(rgba(74,215,255,.05) 1px,transparent 1px),linear-gradient(90deg,rgba(74,215,255,.05) 1px,transparent 1px);background-size:auto,34px 34px,34px 34px;mask-image:radial-gradient(circle,#000 45%,transparent 86%);-webkit-mask-image:radial-gradient(circle,#000 45%,transparent 86%);pointer-events:none}",
      ".cg-holo-seal:after{content:'';position:absolute;inset:11%;border-radius:50%;border:1px solid rgba(111,247,255,.28);box-shadow:0 0 25px rgba(39,217,255,.12),inset 0 0 25px rgba(155,124,255,.09);animation:cgHoloSpin 22s linear infinite;pointer-events:none}",
      ".cg-holo-ring{position:absolute;border-radius:50%;pointer-events:none;box-sizing:border-box}.cg-holo-ring.r1{inset:7%;border:1px solid rgba(111,247,255,.45);box-shadow:0 0 18px rgba(39,217,255,.16)}.cg-holo-ring.r2{inset:14%;border:1px dashed rgba(155,124,255,.42);animation:cgHoloSpin 18s linear infinite reverse}.cg-holo-ring.r3{inset:22%;border:1px solid rgba(255,255,255,.18);box-shadow:0 0 20px rgba(155,124,255,.12)}",
      ".cg-holo-logo{position:relative;z-index:4;width:48%;height:48%;object-fit:contain;filter:grayscale(1) brightness(1.75) contrast(1.12) drop-shadow(0 0 8px rgba(220,250,255,.75)) drop-shadow(0 0 24px rgba(39,217,255,.46)) drop-shadow(0 0 36px rgba(155,124,255,.28));opacity:.94;mix-blend-mode:screen}",
      ".cg-holo-glass{position:absolute;z-index:5;inset:28%;border-radius:50%;background:radial-gradient(circle at 35% 25%,rgba(255,255,255,.16),transparent 22%),radial-gradient(circle at 65% 75%,rgba(39,217,255,.08),transparent 38%);border:1px solid rgba(255,255,255,.16);box-shadow:inset 7px 8px 24px rgba(255,255,255,.08),inset -12px -16px 30px rgba(0,0,0,.2);pointer-events:none;mix-blend-mode:screen}",
      ".cg-holo-scan{position:absolute;z-index:6;left:9%;right:9%;height:1px;background:linear-gradient(90deg,transparent,var(--holo-cyan),var(--holo-violet),transparent);box-shadow:0 0 12px var(--holo-blue);opacity:.58;animation:cgHoloScan 5s ease-in-out infinite;pointer-events:none}",
      ".cg-holo-label{position:absolute;z-index:7;font:600 8px/1.2 'IBM Plex Mono',monospace;letter-spacing:.22em;color:rgba(224,250,255,.68);text-transform:uppercase}.cg-holo-label.top{top:12%;left:50%;transform:translateX(-50%)}.cg-holo-label.bottom{bottom:12%;left:50%;transform:translateX(-50%)}.cg-holo-label.left{left:8%;top:50%;transform:translateY(-50%) rotate(-90deg)}.cg-holo-label.right{right:8%;top:50%;transform:translateY(-50%) rotate(90deg)}",
      ".cg-holo-tick{position:absolute;z-index:7;width:10px;height:10px;border-top:1px solid var(--holo-cyan);border-left:1px solid var(--holo-cyan);opacity:.62}.cg-holo-tick.tl{top:19%;left:19%}.cg-holo-tick.tr{top:19%;right:19%;transform:rotate(90deg)}.cg-holo-tick.br{bottom:19%;right:19%;transform:rotate(180deg)}.cg-holo-tick.bl{bottom:19%;left:19%;transform:rotate(270deg)}",
      "@keyframes cgHoloSpin{to{transform:rotate(360deg)}}@keyframes cgHoloScan{0%,100%{top:22%;opacity:.15}50%{top:78%;opacity:.72}}",
      "@media(max-width:760px){.cgev__grid{grid-template-columns:1fr}.cgev__media{max-width:520px;margin-inline:auto}.cgev{width:min(94vw,1120px)}.cg-holo-seal{width:min(88vw,520px)}}",
      "@media(prefers-reduced-motion:reduce){.cgev__links a{transition:none}.cg-holo-ring.r2,.cg-holo-seal:after,.cg-holo-scan{animation:none}.cg-holo-scan{top:50%;opacity:.45}}"
    ].join("");
    document.head.appendChild(style);
  }

  function buildHolographicSeal() {
    if (page !== "advanced-features-tools-systems.html") return;
    if (document.getElementById("cg-holo-seal")) return;
    var target = document.querySelector(".afx-term");
    if (!target) return;

    var seal = el("div", "cg-holo-seal");
    seal.id = "cg-holo-seal";
    seal.setAttribute("role", "img");
    seal.setAttribute("aria-label", "ClearGlass holographic crystal seal with eagle emblem");
    seal.innerHTML =
      '<span class="cg-holo-ring r1" aria-hidden="true"></span>' +
      '<span class="cg-holo-ring r2" aria-hidden="true"></span>' +
      '<span class="cg-holo-ring r3" aria-hidden="true"></span>' +
      '<span class="cg-holo-tick tl" aria-hidden="true"></span><span class="cg-holo-tick tr" aria-hidden="true"></span>' +
      '<span class="cg-holo-tick br" aria-hidden="true"></span><span class="cg-holo-tick bl" aria-hidden="true"></span>' +
      '<span class="cg-holo-label top">CLEARGLASS INTELLIGENCE</span>' +
      '<span class="cg-holo-label bottom">TRANSPARENCY IS INFRASTRUCTURE</span>' +
      '<span class="cg-holo-label left">PROVENANCE</span><span class="cg-holo-label right">GOVERNANCE</span>' +
      '<img class="cg-holo-logo" src="/assets/clearglass-logo.png" alt="ClearGlass eagle emblem" width="1024" height="1024" decoding="async" fetchpriority="high">' +
      '<span class="cg-holo-glass" aria-hidden="true"></span><span class="cg-holo-scan" aria-hidden="true"></span>';

    target.replaceWith(seal);
  }

  function build() {
    addStyles();
    buildHolographicSeal();
    if (page === "advanced-features-tools-systems.html") return;
    if (document.getElementById("cg-editorial-visual")) return;

    var section = el("section", "cgev");
    section.id = "cg-editorial-visual";
    section.dataset.tone = item.tone;
    section.setAttribute("aria-labelledby", "cgev-title");

    var grid = el("div", "cgev__grid");
    var figure = el("figure", "cgev__media");
    var frame = el("div", "cgev__frame");
    var image = document.createElement("img");
    image.src = item.src;
    image.width = item.width;
    image.height = item.height;
    image.alt = item.alt;
    image.loading = "lazy";
    image.decoding = "async";
    image.fetchPriority = "low";
    frame.appendChild(image);
    figure.appendChild(frame);
    figure.appendChild(el("figcaption", "cgev__caption", "Concept visualization · editorial context only"));

    var body = el("div", "cgev__body");
    body.appendChild(el("span", "cgev__signal", item.signal));
    var heading = el("h2", "", item.title);
    heading.id = "cgev-title";
    body.appendChild(heading);
    body.appendChild(el("p", "cgev__copy", item.copy));

    var notice = el("p", "cgev__notice");
    var noticeLabel = el("strong", "", "Disclosure — ");
    notice.appendChild(noticeLabel);
    notice.appendChild(document.createTextNode(item.disclosure));
    body.appendChild(notice);

    var links = el("nav", "cgev__links");
    links.setAttribute("aria-label", "Related ClearGlass resources");
    item.links.forEach(function (entry) {
      var anchor = el("a", "", entry[0]);
      anchor.href = entry[1];
      links.appendChild(anchor);
    });
    body.appendChild(links);

    grid.appendChild(figure);
    grid.appendChild(body);
    section.appendChild(grid);

    var related = document.getElementById("cg-related");
    if (related && related.parentNode) {
      related.parentNode.insertBefore(section, related);
      return;
    }
    var footer = document.querySelector("footer");
    if (footer && footer.parentNode) {
      footer.parentNode.insertBefore(section, footer);
      return;
    }
    (document.querySelector("main") || document.body).appendChild(section);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", build, { once: true });
  } else {
    build();
  }
})();

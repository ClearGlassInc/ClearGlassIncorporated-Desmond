(() => {
  "use strict";
  const root = "data/minerals/";
  const state = { minerals: [], feeds: {}, limit: 12, industry: "all" };
  const $ = (selector) => document.querySelector(selector);
  const escapeText = (value) => String(value ?? "");
  const fetchJSON = async (path, timeout = 8000) => {
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), timeout);
    try {
      const response = await fetch(root + path, { signal: controller.signal, cache: "no-cache" });
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      return await response.json();
    } finally { clearTimeout(timer); }
  };
  const badgeClass = (status) => ["OFFLINE", "STALE", "DEGRADED"].includes(status) ? "warning" : "neutral";
  const setFeedState = (id, status) => { const el = $(id); if (el) { el.textContent = status; el.dataset.status = status; } };

  function renderMinerals() {
    const query = $("#mineral-search").value.trim().toLowerCase();
    const filtered = state.minerals.filter((m) => (!query || `${m.name} ${m.symbol} ${m.uses.join(" ")}`.toLowerCase().includes(query)) && (state.industry === "all" || m.industries.includes(state.industry)));
    const visible = filtered.slice(0, query ? filtered.length : state.limit);
    const fragment = document.createDocumentFragment();
    for (const mineral of visible) {
      const button = document.createElement("button");
      button.className = "mineral-card"; button.type = "button"; button.dataset.id = mineral.id;
      const name = document.createElement("b"); name.textContent = mineral.name;
      const symbol = document.createElement("span"); symbol.textContent = mineral.symbol;
      const uses = document.createElement("small"); uses.textContent = mineral.uses.join(" · ");
      button.append(name, symbol, uses); fragment.append(button);
    }
    $("#mineral-grid").replaceChildren(fragment);
    $("#show-more").hidden = Boolean(query) || state.limit >= filtered.length;
    if (!visible.length) $("#mineral-grid").textContent = "No configured mineral matches this search and industry filter.";
  }
  function showProfile(id) {
    const mineral = state.minerals.find((item) => item.id === id); if (!mineral) return;
    $("#profile-name").textContent = `${mineral.name} · ${mineral.symbol}`;
    $("#profile-copy").textContent = mineral.importance;
    const fields = [["Major uses", mineral.uses.join(", ")],["Industry dependencies", mineral.industries.join(", ")],["Market data", "DATA UNAVAILABLE"],["Production / reserves", "Awaiting normalized official data"],["Supply / processing concentration", "NOT CALCULATED"],["Canada / U.S. / EU exposure", "Not inferred"],["Compliance", "Entity and chain-of-custody review required"],["Confidence", "UNVERIFIED"]];
    const fragment = document.createDocumentFragment();
    fields.forEach(([term, value]) => { const dl=document.createElement("dl"),dt=document.createElement("dt"),dd=document.createElement("dd");dt.textContent=term;dd.textContent=value;dl.append(dt,dd);fragment.append(dl); });
    $("#profile-fields").replaceChildren(fragment); $("#profile-detail").focus({preventScroll:true});
  }
  function renderFilters() {
    const industries = ["all", ...new Set(state.minerals.flatMap((m) => m.industries))];
    const fragment = document.createDocumentFragment();
    industries.forEach((industry) => { const b=document.createElement("button");b.type="button";b.dataset.industry=industry;b.setAttribute("aria-pressed",String(industry==="all"));b.textContent=industry;fragment.append(b); });
    $("#industry-filters").replaceChildren(fragment);
  }
  function renderRisk() {
    const fragment = document.createDocumentFragment();
    state.minerals.slice(0, 10).forEach((m) => { const tr=document.createElement("tr"); [m.name,"UNAVAILABLE","UNAVAILABLE","UNAVAILABLE","UNAVAILABLE","UNAVAILABLE"].forEach((v,i)=>{const cell=document.createElement(i?"td":"th");if(!i)cell.scope="row";cell.textContent=v;if(i)cell.className="unknown";tr.append(cell);});fragment.append(tr); });
    $("#risk-body").replaceChildren(fragment);
  }
  async function load() {
    try {
      const manifest = await fetchJSON("manifest.json");
      const [minerals, sources, ...feeds] = await Promise.all([fetchJSON(manifest.minerals_path), fetchJSON(manifest.sources_path), ...manifest.feeds.map((feed) => fetchJSON(feed.path).then((data) => ({ id: feed.id, data })))]);
      state.minerals = minerals.minerals; feeds.forEach(({id,data}) => state.feeds[id]=data);
      const available = feeds.filter(({data}) => Array.isArray(data.records) && data.records.length > 0).length;
      $("#feed-count").textContent = `${available} / ${feeds.length}`;
      $("#sync-time").textContent = new Date(manifest.generated_at).toLocaleString("en-CA", { timeZone:"UTC",dateStyle:"medium",timeStyle:"short" }) + " UTC";
      setFeedState("#market-status", state.feeds.prices.metadata.status); setFeedState("#trade-status", state.feeds.trade.metadata.status); setFeedState("#policy-status", state.feeds.policy.metadata.status); setFeedState("#trade-panel-status", state.feeds.trade.metadata.status);
      $("#market-state").textContent=state.feeds.prices.metadata.status; $("#market-state").className=`state ${badgeClass(state.feeds.prices.metadata.status)}`;
      $("#market-panel").innerHTML=""; const message=document.createElement("div"),heading=document.createElement("strong"),copy=document.createElement("p");heading.textContent="DATA UNAVAILABLE";copy.textContent=state.feeds.prices.message;message.append(heading,copy);$("#market-panel").append(message);
      $("#mineral-total").textContent=`${state.minerals.length} MINERALS`; renderFilters();renderMinerals();renderRisk();renderSources(sources.sources);
    } catch (error) {
      $("#feed-count").textContent="OFFLINE"; ["#market-status","#trade-status","#policy-status"].forEach((id)=>setFeedState(id,"OFFLINE"));
      $("#market-panel").textContent=`Unable to load the static intelligence manifest (${escapeText(error.name)}). Check connectivity or retry.`;
      $("#source-list").textContent="Source registry unavailable. No data claims are displayed.";
    }
  }
  function renderSources(sources) {
    const fragment=document.createDocumentFragment(); sources.forEach((s)=>{const row=document.createElement("article");row.className="source-row";const provider=document.createElement("b"),dataset=document.createElement("span"),coverage=document.createElement("span"),cadence=document.createElement("span"),link=document.createElement("a");provider.textContent=s.provider;dataset.textContent=s.dataset;coverage.textContent=s.coverage;cadence.textContent=s.frequency.toUpperCase();link.href=s.source_url;link.target="_blank";link.rel="noopener noreferrer";link.textContent="Official source ↗";row.append(provider,dataset,coverage,cadence,link);fragment.append(row);});$("#source-list").replaceChildren(fragment);
  }
  let debounce; $("#mineral-search").addEventListener("input",()=>{clearTimeout(debounce);debounce=setTimeout(renderMinerals,120);});
  $("#mineral-grid").addEventListener("click",(event)=>{const card=event.target.closest("[data-id]");if(card)showProfile(card.dataset.id);});
  $("#industry-filters").addEventListener("click",(event)=>{const button=event.target.closest("[data-industry]");if(!button)return;state.industry=button.dataset.industry;document.querySelectorAll("[data-industry]").forEach((b)=>b.setAttribute("aria-pressed",String(b===button)));renderMinerals();});
  $("#show-more").addEventListener("click",()=>{state.limit=state.minerals.length;renderMinerals();});
  const provinces=["Ontario","Quebec","British Columbia","Alberta","Saskatchewan","Manitoba","New Brunswick","Nova Scotia","Newfoundland and Labrador","Prince Edward Island","Yukon","Northwest Territories","Nunavut"];
  provinces.forEach((p,i)=>{const b=document.createElement("button");b.type="button";b.textContent=p;b.setAttribute("aria-pressed",String(i===0));b.addEventListener("click",()=>{document.querySelectorAll("#province-filters button").forEach(x=>x.setAttribute("aria-pressed",String(x===b)));$("#province-label").textContent=`${p} intelligence view`;});$("#province-filters").append(b);});
  function scenario(){const shock=Number($("#shock").value),dep=Number($("#dependency").value);$("#shock-output").textContent=`${shock}%`;$("#dependency-output").textContent=`${dep}%`;$("#scenario-result").textContent=`${(shock*dep/100).toFixed(1)}%`;}
  $("#scenario").addEventListener("input",scenario); $(".nav-toggle").addEventListener("click",()=>{const open=$("#site-nav").classList.toggle("open");$(".nav-toggle").setAttribute("aria-expanded",String(open));});
  document.addEventListener("keydown",(e)=>{if(e.key==="/"&&!/input|select|textarea/i.test(document.activeElement.tagName)){e.preventDefault();$("#mineral-search").focus();}});
  load();
})();

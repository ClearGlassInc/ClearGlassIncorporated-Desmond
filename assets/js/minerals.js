(() => {
  "use strict";

  const STATUS_VALUES = new Set(["LIVE", "NEAR LIVE", "DELAYED", "DAILY", "WEEKLY", "MONTHLY", "ANNUAL", "STATIC REFERENCE", "STALE", "DEGRADED", "OFFLINE", "UNAVAILABLE"]);
  const CONFIDENCE_VALUES = new Set(["HIGH", "MEDIUM", "LOW", "UNKNOWN"]);

  async function fetchJson(path, timeoutMs = 8000) {
    const controller = new AbortController();
    const timer = window.setTimeout(() => controller.abort(), timeoutMs);
    try {
      const response = await fetch(path, {headers: {Accept: "application/json"}, cache: "no-cache", signal: controller.signal});
      if (!response.ok) throw new Error(`${path} returned HTTP ${response.status}`);
      const contentType = response.headers.get("content-type") || "";
      if (!contentType.includes("json")) throw new Error(`${path} returned an unexpected content type`);
      return await response.json();
    } finally {
      window.clearTimeout(timer);
    }
  }

  function isIsoTimestamp(value) {
    return value === null || (typeof value === "string" && !Number.isNaN(Date.parse(value)) && /(?:Z|[+-]\d\d:\d\d)$/.test(value));
  }

  function validateManifest(value) {
    if (!value || !Array.isArray(value.feeds) || typeof value.generated_at !== "string") throw new Error("Manifest has an invalid root schema");
    if (!isIsoTimestamp(value.generated_at)) throw new Error("Manifest generated_at is not an ISO UTC timestamp");
    const ids = new Set();
    value.feeds.forEach((feed) => {
      if (!feed || typeof feed.id !== "string" || ids.has(feed.id)) throw new Error("Manifest contains a missing or duplicate feed id");
      ids.add(feed.id);
      if (!STATUS_VALUES.has(feed.status) || !CONFIDENCE_VALUES.has(feed.confidence)) throw new Error(`Feed ${feed.id} contains an unsupported status or confidence`);
      if (!Number.isInteger(feed.record_count) || feed.record_count < 0 || !isIsoTimestamp(feed.retrieved_at) || !isIsoTimestamp(feed.source_updated_at)) throw new Error(`Feed ${feed.id} contains invalid metrics`);
    });
    return value;
  }

  function validateMinerals(value) {
    if (!value || !Array.isArray(value.records) || value.records.length === 0) throw new Error("Mineral reference data is empty or invalid");
    const ids = new Set();
    value.records.forEach((record) => {
      if (!record || !/^[a-z0-9]+(?:-[a-z0-9]+)*$/.test(record.id) || ids.has(record.id) || typeof record.name !== "string" || !Array.isArray(record.uses)) throw new Error("Mineral reference data contains an invalid or duplicate record");
      ids.add(record.id);
    });
    return value.records;
  }

  function formatTimestamp(value) {
    if (!value) return "Never retrieved";
    return new Intl.DateTimeFormat("en-CA", {dateStyle: "medium", timeStyle: "short", timeZone: "UTC"}).format(new Date(value)) + " UTC";
  }

  function safeSourceLink(feed) {
    if (!feed.source_url) return document.createTextNode(feed.source);
    try {
      const url = new URL(feed.source_url);
      if (url.protocol !== "https:") throw new Error("non-HTTPS source URL");
      const link = document.createElement("a");
      link.href = url.href;
      link.textContent = feed.source;
      link.target = "_blank";
      link.rel = "noopener noreferrer";
      return link;
    } catch {
      return document.createTextNode(feed.source);
    }
  }

  function renderManifest(manifest) {
    const unavailable = new Set(["STALE", "DEGRADED", "OFFLINE", "UNAVAILABLE"]);
    const availableCount = manifest.feeds.filter((feed) => !unavailable.has(feed.status)).length;
    const degradedCount = manifest.feeds.length - availableCount;
    document.querySelector("#system-status").textContent = manifest.overall_status;
    document.querySelector("#feeds-healthy").textContent = `${availableCount} / ${manifest.feeds.length}`;
    document.querySelector("#feeds-degraded").textContent = String(degradedCount);
    document.querySelector("#last-sync").textContent = formatTimestamp(manifest.generated_at);
    document.querySelector("#pipeline-status").textContent = degradedCount ? "DEGRADED" : "HEALTHY";
    document.querySelector("#status-message").textContent = degradedCount ? "Some datasets are unavailable. Available reference data remains usable and unavailable feeds are not substituted with estimates." : "All configured feeds are within their declared operating state.";
    document.querySelector(".status-panel").dataset.state = degradedCount ? "degraded" : "ready";

    const body = document.querySelector("#feed-table");
    body.replaceChildren(...manifest.feeds.map((feed) => {
      const row = document.createElement("tr");
      const values = [feed.name, null, feed.expected_frequency, feed.status, formatTimestamp(feed.retrieved_at), feed.confidence];
      values.forEach((value, index) => {
        const cell = document.createElement("td");
        if (index === 1) cell.append(safeSourceLink(feed)); else cell.textContent = value;
        row.append(cell);
      });
      return row;
    }));
  }

  function renderMinerals(records) {
    const grid = document.querySelector("#mineral-grid");
    const count = document.querySelector("#result-count");
    grid.replaceChildren(...records.map((record) => {
      const card = document.createElement("article");
      card.className = "mineral-card";
      card.dataset.mineralId = record.id;
      const symbol = document.createElement("span"); symbol.className = "symbol"; symbol.textContent = record.symbol;
      const heading = document.createElement("h3"); heading.textContent = record.name;
      const category = document.createElement("p"); category.textContent = record.category;
      const list = document.createElement("ul");
      record.uses.forEach((use) => { const item = document.createElement("li"); item.textContent = use; list.append(item); });
      card.append(symbol, heading, category, list);
      return card;
    }));
    grid.setAttribute("aria-busy", "false");
    count.textContent = `${records.length} mineral${records.length === 1 ? "" : "s"} shown`;
  }

  function showError(message) {
    const panel = document.querySelector(".status-panel");
    panel.dataset.state = "error";
    document.querySelector("#system-status").textContent = navigator.onLine ? "OFFLINE" : "OFFLINE";
    document.querySelector("#pipeline-status").textContent = "UNAVAILABLE";
    document.querySelector("#status-message").textContent = message;
    document.querySelector("#feed-table").innerHTML = '<tr><td colspan="6">Feed manifest unavailable. No operating state can be verified.</td></tr>';
  }

  async function initialize() {
    const search = document.querySelector("#mineral-search");
    const grid = document.querySelector("#mineral-grid");
    if (!search || !grid) return;
    try {
      const [manifestValue, mineralsValue] = await Promise.all([fetchJson("/data/minerals/manifest.json"), fetchJson("/data/minerals/metadata/minerals.json")]);
      const manifest = validateManifest(manifestValue);
      const records = validateMinerals(mineralsValue);
      renderManifest(manifest);
      renderMinerals(records);
      search.addEventListener("input", () => {
        const query = search.value.trim().toLocaleLowerCase("en-CA");
        renderMinerals(records.filter((record) => `${record.id} ${record.name} ${record.symbol} ${record.category} ${record.uses.join(" ")}`.toLocaleLowerCase("en-CA").includes(query)));
      });
    } catch (error) {
      const detail = error instanceof Error ? error.message : "Unknown data error";
      showError(`Minerals data could not be validated: ${detail}. Retry later; no fallback values were invented.`);
      grid.innerHTML = '<div class="empty-state"><strong>REFERENCE DATA UNAVAILABLE</strong><p>The mineral directory could not be loaded or did not pass schema checks.</p></div>';
      grid.setAttribute("aria-busy", "false");
    }
  }

  window.addEventListener("offline", () => showError("The browser is offline. Previously rendered information may remain visible, but feed health cannot be refreshed."));
  initialize();
})();

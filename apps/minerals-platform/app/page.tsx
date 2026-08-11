import GlobalMap from "@/components/GlobalMap";
import MarketChart from "@/components/MarketChart";

const modules = [
  ["Command Center", "Executive operational picture"],
  ["Global Map", "PostGIS-backed project, mine, facility, and logistics features"],
  ["Mineral Markets", "Observed and licensed price series only"],
  ["Mines & Projects", "Ownership, permits, production, reserves, and provenance"],
  ["Supply Chains", "Verified dependencies and explicit inferred relationships"],
  ["Trade Intelligence", "Origin/destination flows with classification transparency"],
  ["Risk Radar", "Configurable 0–100 methodology with coverage and overrides"],
  ["Exploration", "Discoveries, permits, expansions, and project-stage monitoring"],
  ["Alerts", "Deduplication, assignment, acknowledgement, comments, resolution"],
  ["Reports", "Human-reviewed analyst and AI-assisted report workflows"],
  ["Data Sources", "Cadence, TTL, license, freshness, ingestion, provenance"],
  ["Administration", "Organization-scoped RBAC, audit and integration readiness"]
];

export const dynamic = "force-dynamic";

export default function Page() {
  return (
    <main className="cg-shell">
      <aside className="cg-rail" aria-label="Minerals platform navigation">
        <a className="cg-brand" href="/" aria-label="Minerals Intelligence home"><span className="cg-orb">CG</span><span>MINERALS<br/><small className="text-slate-500">INTELLIGENCE</small></span></a>
        <nav className="cg-nav">
          {modules.map(([name]) => <a key={name} href={`#${name.toLowerCase().replaceAll(/[^a-z0-9]+/g, "-")}`}>{name}</a>)}
        </nav>
      </aside>
      <section className="cg-main">
        <header className="cg-topbar">
          <div className="cg-search" role="search"><span aria-hidden="true">⌕</span><span>Search via <code>/api/v1/search?q=…</code></span><kbd className="ml-auto text-xs">API v1</kbd></div>
          <span className="cg-status"><i className="cg-dot"/>SOURCE-GROUNDED MODE</span>
        </header>

        <section className="cg-hero" id="command-center">
          <article className="cg-panel cg-hero-copy">
            <p className="cg-kicker">ClearGlass · Enterprise Intelligence Service</p>
            <h1>Critical minerals.<br/>One operational picture.</h1>
            <p className="cg-lede">Authenticated command infrastructure for mineral markets, mine and project intelligence, trade, supply-chain exposure, risk, alerts, provenance, and governed analyst workflows. Missing evidence remains unknown.</p>
            <div className="cg-actions">
              <a className="cg-button primary" href="/api/v1/sources">Inspect source health</a>
              <a className="cg-button" href="/api/v1/minerals">Open API</a>
              <a className="cg-button" href="https://www.clearglassinc.com/minerals-platform.html">Public command surface</a>
            </div>
          </article>
          <aside className="cg-panel cg-metrics" aria-label="Architecture status">
            <div className="cg-metric"><span>API</span><strong>v1</strong></div>
            <div className="cg-metric"><span>Spatial</span><strong>PostGIS</strong></div>
            <div className="cg-metric"><span>Queue</span><strong>BullMQ</strong></div>
            <div className="cg-metric"><span>Cache</span><strong>Redis</strong></div>
            <div className="cg-metric"><span>Auth</span><strong>RBAC</strong></div>
            <div className="cg-metric"><span>Data rule</span><strong>Provenance</strong></div>
          </aside>
        </section>

        <section className="cg-grid">
          <article className="cg-panel cg-map-card" id="global-map"><div className="cg-card-head"><div><h2>Global Mineral Map</h2><p>Clustered geospatial features from authenticated source records</p></div><span className="cg-kicker">MapLibre + PostGIS</span></div><GlobalMap/></article>
          <article className="cg-panel cg-chart-card" id="mineral-markets"><div className="cg-card-head"><div><h2>Market Series</h2><p>Observed benchmark records; no invented prices</p></div><span className="cg-kicker">ECharts</span></div><MarketChart/></article>
        </section>

        <section className="cg-footer-grid" aria-label="Platform modules">
          {modules.slice(3).map(([name, description]) => {
            const id = name.toLowerCase().replaceAll(/[^a-z0-9]+/g, "-");
            return <article key={name} className="cg-panel cg-module" id={id}><h3>{name}</h3><p>{description}</p><code>/api/v1/{id === "mines-projects" ? "projects" : id === "data-sources" ? "sources" : id}</code></article>;
          })}
        </section>
      </section>
    </main>
  );
}

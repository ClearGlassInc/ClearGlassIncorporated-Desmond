import { agents, claims, sources } from "../lib/research";
import { NextStepCTA } from "../components/navigation/NextStepCTA";
import { RelatedLinks } from "../components/navigation/RelatedLinks";
import { routeFlow } from "../lib/navigation";

const metrics = ["Local-first vault", "Cited summaries", "RBAC + audit", "Public OSINT only"];

export default function Page() {
  return (
    <main id="main-content" className="stage">
      <div className="aurora" />
      <section className="hero">
        <p className="eyebrow"><span /> ClearGlassInc Artemis · Browser Security AI</p>
        <h1>Neon-glass browser intelligence for lawful defensive research.</h1>
        <p className="lede">Capture tabs, notes, public sources, and AI summaries in one hardened workflow where every claim is cited, every significant action is approval-gated, and every decision is audit-ready.</p>
        <div className="actions"><a href="#architecture">View architecture</a><a href="#agents" className="secondary">Explore agents</a></div>
        <div className="metrics">{metrics.map((metric) => <b key={metric}>{metric}</b>)}</div>
      </section>

      <section className="console" aria-label="Artemis browser intelligence console screenshot mockup">
        <div className="browser"><div className="tabs"><span className="active">Vendor advisory</span><span>CVE record</span><span>Detection note</span></div><div className="capture"><span className="glyph">🛡</span><div><b>Secure capture</b><p>Public URL validated · DOM snapshot hashed · source lineage attached</p></div></div></div>
        <div className="panel"><h2>AI summary with citations</h2>{claims.map((claim) => <p key={claim.text}>{claim.text} <small>{claim.sourceIds.map((id) => `[${id}]`).join(" ")}</small></p>)}</div>
        <div className="panel"><h2>Source ledger</h2>{sources.map((source) => <p key={source.id}><b>{source.id}</b> · {source.title}<br /><small>{source.url}</small></p>)}</div>
      </section>

      <section id="agents" className="grid">{agents.map((agent) => <article className="card" key={agent.name}><span className="glyph">🧠</span><h3>{agent.name}</h3><p>{agent.purpose}</p><small>{agent.guardrail}</small><em>{agent.status}</em></article>)}</section>

      <section id="architecture" className="architecture">
        <h2>Production architecture</h2>
        <div className="layers">
          <p><span className="glyph">✦</span> Next.js premium UI for tab intelligence, notes, source capture, and analyst review.</p>
          <p><span className="glyph">🔐</span> Local encrypted vault for secrets; model prompts receive only redacted source excerpts and stable IDs.</p>
          <p><span className="glyph">◎</span> API gateway, event bus, search, model router, and ontology adapters for Foundry/Gotham/AIP deployments.</p>
          <p><span className="glyph">▣</span> Immutable audit chain, RBAC, policy-as-code, eval dashboards, Apollo rollback, and hardening runbooks.</p>
        </div>
      </section>
      <RelatedLinks hrefs={routeFlow["/"].related} />
      <NextStepCTA href={routeFlow["/"].next} />
    </main>
  );
}

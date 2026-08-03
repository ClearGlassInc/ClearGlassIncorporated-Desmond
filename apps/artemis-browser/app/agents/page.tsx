import { PageFlow } from "../../components/layout/PageFlow";
import { SystemSection } from "../../components/layout/SystemSection";
export const metadata = { title: "AI & Agents | ClearGlassInc Artemis", description: "Human-governed multi-agent intelligence workflows." };
export default function AgentsPage() { return <PageFlow route="/agents" eyebrow="AI and agent design" title="Fast machine reasoning. Explicit human authority." summary="Artemis agents are bounded decision-support workers: typed inputs, allowlisted evidence, short-lived credentials, finite budgets, structured outputs, and approval gates enforced outside the model.">
  <nav className="section-nav" aria-label="On this page"><a href="#roles">Agent roles</a><a href="#workflow">Workflow state</a><a href="#tools">Tool boundaries</a></nav>
  <SystemSection id="roles" title="Agent roles" intro="Specialized agents reduce context sprawl and make every handoff observable." items={[
    { title: "Triage agent", text: "Validates event type, urgency evidence, duplication, and routing; it may abstain but cannot declare operational truth." },
    { title: "Enrichment agent", text: "Queries authorized ontology views and public or approved sources, attaching lineage to every returned field." },
    { title: "Correlation agent", text: "Builds hypotheses from temporal and graph patterns while preserving contradictory evidence and alternatives." },
    { title: "Briefing agent", text: "Produces audience-scoped, citation-complete summaries with confidence, gaps, and explicit unknowns." },
    { title: "Recommendation agent", text: "Prepares reversible courses of action and expected effects; it cannot approve or execute them." },
    { title: "Assurance agent", text: "Checks provenance, policy decisions, prompt injection signals, tool scope, and package completeness independently." },
  ]} />
  <SystemSection id="workflow" title="Governed workflow state" intro="A deterministic service owns transitions; agents can propose outputs but cannot manufacture authority." items={[
    { title: "Observe → Draft", text: "Read-only tools build an evidence packet and draft hypothesis under mission-scoped authorization." },
    { title: "Draft → Review", text: "Schema, citation, policy, uncertainty, and independent assurance checks must all pass." },
    { title: "Review → Approved", text: "A named, authorized human signs the immutable package before its expiry; rejection records rationale." },
    { title: "Approved → Execute", text: "A separate executor re-authorizes the principal, package, target, policy version, and idempotency key." },
  ]} />
  <SystemSection id="tools" title="Tool boundaries" intro="Every call is narrow, authenticated, rate-limited, time-bounded, and audit-emitting." items={[
    { title: "Query", text: "Parameterized ontology and search operations constrained by row, column, entity, purpose, and coalition policy." },
    { title: "Prepare", text: "Agents may create cases, intel-product drafts, and action-package drafts in a non-executable state." },
    { title: "Act", text: "Operationally significant tools reject model credentials and require a valid human approval artifact at execution time." },
  ]} />
</PageFlow>; }

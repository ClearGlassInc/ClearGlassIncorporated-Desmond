import { PageFlow } from "../../components/layout/PageFlow";
import { SystemSection } from "../../components/layout/SystemSection";

export const metadata = { title: "System Architecture | ClearGlassInc Artemis", description: "The governed full-stack architecture for ClearGlassInc Artemis." };

export default function ArchitecturePage() {
  return <PageFlow route="/architecture" eyebrow="System architecture" title="One intelligence fabric. Four controlled planes." summary="A target-state architecture that separates experience, data, intelligence, and deployment concerns so every decision remains attributable, policy-bound, and reversible.">
    <nav className="section-nav" aria-label="On this page"><a href="#platform">Platform roles</a><a href="#runtime">Runtime flow</a><a href="#assurance">Mission assurance</a></nav>
    <SystemSection id="platform" title="Platform roles" intro="Palantir capabilities are integrated through narrow, authenticated contracts; this design does not presume that any target-state service is already provisioned." items={[
      { title: "Gotham · Operations", text: "Investigations, entity tracking, link analysis, mission workspaces, and operator-facing operational context.", meta: "Operational plane" },
      { title: "Foundry · Data", text: "Live and historical ingestion, quality gates, transforms, ontology objects, lineage, and application logic.", meta: "Data plane" },
      { title: "AIP · Intelligence", text: "Cited copilots, bounded agents, model routing, prompt registry, evaluations, and approval-aware automation.", meta: "Decision-support plane" },
      { title: "Apollo · Runtime", text: "Environment-aware releases, policy-constrained updates, health observation, staged promotion, and known-good rollback.", meta: "Management plane" },
    ]} />
    <SystemSection id="runtime" title="Runtime flow" intro="Events move forward through explicit contracts while evidence, policy decisions, and audit records move alongside them." items={[
      { title: "1 · Sense", text: "Connectors validate schemas, classification, source identity, timestamps, and content hashes before durable ingestion." },
      { title: "2 · Fuse", text: "Foundry pipelines resolve candidates into temporal ontology objects without erasing conflicting observations." },
      { title: "3 · Reason", text: "AIP workflows retrieve only policy-authorized context, call allowlisted tools, and return evidence-linked proposals." },
      { title: "4 · Decide", text: "Operators inspect confidence, provenance, alternatives, and policy rationale before approving consequential action packages." },
      { title: "5 · Observe", text: "Outcomes, corrections, latency, abstentions, and approval decisions feed evaluation datasets—not autonomous authority." },
      { title: "6 · Improve", text: "Candidate changes pass offline evals, security review, human approval, canary release, and deterministic rollback gates." },
    ]} />
    <SystemSection id="assurance" title="Mission assurance" intro="The architecture fails closed at every consequential boundary and degrades to read-only evidence access when dependent controls are unhealthy." items={[
      { title: "Separated trust domains", text: "Control, data, model, execution, and audit planes use audience-scoped workload identity and default-deny communication." },
      { title: "Bounded performance", text: "Deadlines, queue limits, circuit breakers, idempotency keys, and cancellation keep latency failures from becoming unsafe retries." },
      { title: "Recovery by design", text: "Immutable version identities bind data, ontology, prompt, model, policy, approval, and deployment records for replay and rollback." },
    ]} />
  </PageFlow>;
}

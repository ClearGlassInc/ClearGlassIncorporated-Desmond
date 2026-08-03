import { PageFlow } from "../../components/layout/PageFlow";
import { SystemSection } from "../../components/layout/SystemSection";

export const metadata = { title: "Data & Ontology | ClearGlassInc Artemis", description: "Temporal, provenance-rich intelligence ontology design." };
export default function OntologyPage() { return <PageFlow route="/ontology" eyebrow="Data and ontology" title="Evidence first. Context always. Confidence never hidden." summary="The ontology is the shared contract between analysts, applications, policies, and agents—preserving time, source lineage, uncertainty, and coalition permissions at object level.">
  <nav className="section-nav" aria-label="On this page"><a href="#objects">Core objects</a><a href="#relationships">Relationships</a><a href="#invariants">Data invariants</a></nav>
  <SystemSection id="objects" title="Core objects" intro="Stable identifiers represent concepts; append-only observations represent what a source asserted at a specific time." items={[
    { title: "Entity", text: "A person, organization, asset, location, account, device, event, indicator, case, mission, or intelligence product." },
    { title: "Observation", text: "Source-bound assertion with observed time, valid time, ingestion time, content hash, classification, and releasability." },
    { title: "Claim", text: "A normalized proposition linked to supporting and contradicting evidence, calibration cohort, and confidence rationale." },
    { title: "Mission context", text: "Purpose, scope, authority, compartments, coalition caveats, retention, time window, and accountable owner." },
    { title: "Decision package", text: "Recommendation, alternatives, predicted effects, evidence set, policy result, required approvers, and expiry." },
    { title: "Outcome", text: "Observed result tied to a decision, operator correction, mission metric, and evaluation eligibility label." },
  ]} />
  <SystemSection id="relationships" title="Temporal relationships" intro="Edges are first-class, permissioned claims rather than permanent facts." items={[
    { title: "Attributed to", text: "Links a claim to the exact source artifact, extraction method, transform version, and responsible ingestion principal." },
    { title: "Observed near", text: "Expresses time-bounded co-occurrence without automatically asserting causality or identity." },
    { title: "Corroborates / contradicts", text: "Preserves competing evidence and lets confidence services explain rather than conceal disagreement." },
    { title: "Derived from", text: "Creates a traversable lineage graph from raw record through transforms, retrieval, model output, and analyst product." },
  ]} />
  <SystemSection id="invariants" title="Data invariants" intro="Conventional validation—not model judgment—enforces these constraints." items={[
    { title: "Bitemporal truth", text: "Valid time and system time are retained so operators can reconstruct both what was believed and when it was known." },
    { title: "Monotonic provenance", text: "Derivation adds lineage; no transform may detach a claim from its original evidence or classification." },
    { title: "Policy inheritance", text: "Derived objects inherit the most restrictive applicable markings until an authorized release decision is recorded." },
  ]} />
</PageFlow>; }

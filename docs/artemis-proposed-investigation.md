# ARTEMIS — Proposed Investigation Framework

**System:** ARTEMIS  
**Organization:** ClearGlass Inc.  
**Document Status:** PROPOSED / NOT ACTIVE  
**Research Status:** BLOCKED pending exact mission question and approval  
**Purpose:** Establish a defensible investigation methodology only.  

> Copyright © ClearGlass Inc. All rights reserved.  
> Original Author and Systems Architect: Desmond Otieno Odhiambo.  
> Powered by ARTEMIS — A ClearGlass Inc. Intelligence System.

---

## 1. Mission Scope

**Status:** Mission question/deliverable not yet provided.

**Current Scope Definition:** Establish a research framework only.

This document defines the methodology, evidence standards, agent responsibilities, information flow, and acceptance criteria for a future ARTEMIS investigation.

No evidence collection, source review, substantive analysis, findings, conclusions, or solution generation begins until the exact mission question is supplied and explicitly approved.

### Activation Gate

Research may begin only when all of the following are explicitly defined and approved:

- Exact mission question
- Intended deliverable
- Time scope
- Geographic scope, where applicable
- Required depth
- Stakeholders / decision audience
- Investigation-specific success criteria
- Applicable legal, privacy, access, and handling constraints

---

## 2. Definitions

### Verified Fact

A statement directly supported by an authoritative or primary source and independently checked where feasible.

### Inference

A conclusion logically derived from verified facts but not explicitly stated by the source. Inferences must be labeled as such.

### Assumption

A working premise temporarily adopted because required evidence is missing. An assumption is not evidence and must be disclosed.

### Unknown

Information required to answer the mission that is currently unavailable. Unknowns must be documented without speculation.

### Authoritative Source

A source with direct responsibility, ownership, publication authority, or official stewardship over the information.

### Primary Source

Original evidence such as official documents, datasets, filings, records, technical documentation, transcripts, direct observations, or first-party statements.

### Secondary Source

Analysis, reporting, interpretation, or commentary derived from primary sources.

### Independent Verification

Confirmation of a claim through a separate authoritative or primary source that is not merely repeating the same underlying assertion.

### UNVERIFIED Claim

Any claim that cannot be confirmed through independent authoritative evidence. Such claims must never be presented as verified facts.

---

## 3. Research Subquestions

Because the mission question has not yet been provided, the following generic structure will be refined after activation:

1. What exactly is being asked?
2. What decision or deliverable will the answer support?
3. What claims must be validated?
4. What evidence exists?
5. Which sources are primary versus secondary?
6. Where do sources disagree?
7. What uncertainty remains?
8. What conclusions are supported by evidence?
9. What conclusions remain UNVERIFIED?
10. What information gaps materially affect confidence?

---

## 4. Required Source Types

Research should prioritize source quality in the following order.

### Tier 1 — Primary / Authoritative

- Official records
- Regulatory filings
- Government publications
- Court documents
- Standards bodies
- Original datasets
- Technical specifications
- Product documentation
- Organization-issued statements
- Verifiable first-party evidence

### Tier 2 — Independent Expert Sources

- Peer-reviewed literature
- Academic institutions
- Professional associations
- Independent research organizations

### Tier 3 — Secondary Sources

- Reputable news organizations
- Industry analysis
- Market research publications

### Tier 4 — Supplemental Sources

- Public archives
- Historical repositories
- Specialist publications

### Excluded as Standalone Evidence

The following may be used only as leads or contextual material and cannot, by themselves, establish a material fact:

- Anonymous claims
- Unsourced assertions
- AI-generated content
- Unverified social media claims
- Circular citations

---

## 5. Agent Roles

### 1. Lead Investigator

- Manages scope
- Maintains the hypothesis register
- Controls evidence standards
- Produces the final synthesis

### 2. Source Discovery Agent

- Identifies candidate sources
- Maps source hierarchy
- Detects source provenance
- Records publication and ownership context

### 3. Verification Agent

- Independently validates claims
- Confirms citations
- Flags inconsistencies
- Tests whether cited material actually supports the claim

### 4. Evidence Extraction Agent

- Extracts relevant facts
- Preserves source context
- Records exact source references
- Avoids stripping qualifiers, dates, or limitations from evidence

### 5. Contradiction Agent

- Searches for disconfirming evidence
- Challenges prevailing interpretations
- Identifies conflicting sources
- Preserves contradictions rather than discarding them

### 6. Uncertainty Agent

- Tracks confidence levels
- Documents limitations
- Identifies unresolved questions
- Maintains the information-gap register

### 7. Synthesis Agent

- Integrates validated findings only
- Separates evidence from interpretation
- Drafts evidence-backed conclusions
- Does not promote inference into fact

### 8. Quality Assurance Agent

- Audits methodology
- Checks citation integrity
- Tests evidence-to-claim traceability
- Ensures compliance with mission rules

---

## 6. Information-Flow Rules

### Evidence Flow

```text
SOURCE
  ↓
SOURCE VALIDATION
  ↓
FACT EXTRACTION
  ↓
INDEPENDENT VERIFICATION
  ↓
EVIDENCE REGISTER
  ↓
ANALYSIS
  ↓
CONCLUSIONS
```

### Mandatory Rules

- No agent may treat another agent's output as evidence.
- Every material claim requires source attribution.
- Important claims require independent confirmation when possible.
- Unsupported claims must be labeled **UNVERIFIED**.
- Evidence and interpretation must remain separate.
- Contradictory evidence must be preserved rather than discarded.
- Missing evidence must be explicitly documented.
- Confidence assessments must be justified by the available evidence.
- Citation presence is not sufficient; the cited source must actually support the claim.
- Source duplication, syndication, and circular reporting must not be mistaken for independent corroboration.

---

## 7. Evidence Classification Framework

### Verified Facts

A claim qualifies as a verified fact only when:

- Directly supported by authoritative or primary evidence
- Citation is available
- Source provenance is known
- Evidence has been checked for consistency
- Independent confirmation has been obtained when materially necessary and feasible

### Inferences

A claim qualifies as an inference when:

- It is logically derived from verified facts
- It is not explicitly stated by the source
- The reasoning is defensible
- The output explicitly labels it as an inference

### Assumptions

A statement qualifies as an assumption when:

- Required data is missing
- The premise is temporarily necessary for workflow continuity
- The premise is clearly disclosed as non-evidence
- The assumption is tracked for later validation or removal

### Unknowns

An item qualifies as an unknown when:

- The information is necessary to answer the mission
- The information is currently unavailable or unresolved
- A concrete research gap can be identified
- No speculation is used to fill the gap

---

## 8. Evidence Register Requirements

Every material claim should be traceable through an evidence register containing, at minimum:

| Field | Requirement |
|---|---|
| Claim ID | Stable identifier |
| Claim | Exact normalized claim |
| Classification | Verified Fact / Inference / Assumption / Unknown / UNVERIFIED |
| Source ID | Stable source reference |
| Source Tier | Tier 1–4 |
| Source Type | Primary / Authoritative / Expert / Secondary / Supplemental |
| Provenance | Ownership, publisher, or stewardship context |
| Citation | Exact retrievable source reference |
| Verification | Independent confirmation status |
| Contradictions | Conflicting evidence, if any |
| Confidence | Justified confidence assessment |
| Notes | Qualifications, caveats, or limitations |

No material claim should enter final synthesis without an evidence-register entry.

---

## 9. Hypothesis and Contradiction Control

ARTEMIS must maintain an explicit hypothesis register during active investigations.

For each hypothesis, record:

- Hypothesis ID
- Statement
- Supporting evidence
- Disconfirming evidence
- Alternative explanations
- Key assumptions
- Known unknowns
- Current confidence
- Verification status
- Disposition

The contradiction workflow must actively seek evidence that could falsify or weaken the working interpretation. Absence of contradiction is not proof of correctness.

---

## 10. Confidence and Uncertainty

Confidence must be evidence-based and explained.

ARTEMIS should distinguish at minimum among:

- High confidence: strong, direct, corroborated evidence
- Moderate confidence: meaningful evidence with residual uncertainty or limited corroboration
- Low confidence: partial or indirect evidence
- UNVERIFIED: insufficient evidence to support the claim

Confidence must not be increased merely because multiple sources repeat the same underlying report.

Where a numerical confidence score is used, the scoring rubric must be documented and consistently applied.

---

## 11. Acceptance Criteria

An investigation is accepted only if all applicable criteria below are satisfied.

### Evidence Standards

- Every important claim has a source.
- Sources are cited.
- Source provenance is documented.
- Claims are traceable to the evidence register.
- Material source qualifiers are preserved.

### Verification Standards

- Key claims are independently checked where possible.
- Contradictions are evaluated and preserved.
- Unsupported assertions are removed or labeled UNVERIFIED.
- Circular reporting is identified.

### Transparency Standards

- Verified facts are clearly separated from inferences.
- Assumptions are identified.
- Unknowns are listed.
- Information gaps affecting confidence are disclosed.

### Output Standards

- Conclusions are evidence-backed.
- Uncertainty is explicit.
- No fabricated information is included.
- No unsupported claim is presented as fact.
- The final product accurately states what was and was not established.

---

## 12. Risks and Likely Failure Modes

### Source Risks

- Low-quality sources
- Circular reporting
- Outdated information
- Misattributed citations
- Broken or inaccessible source records
- Selective sourcing

### Analysis Risks

- Confirmation bias
- Overgeneralization
- Causation inferred from correlation
- Selective evidence use
- Base-rate neglect
- Premature closure

### Process Risks

- Scope creep
- Ambiguous definitions
- Incomplete source coverage
- Failure to independently verify claims
- Uncontrolled research drift
- Agent-to-agent citation laundering

### Output Risks

- Mixing facts and interpretations
- Unmarked assumptions
- Unreported uncertainty
- Accidental presentation of UNVERIFIED claims as facts
- Citation mismatch between claim and source
- Overstating confidence

---

## 13. Research Activation Protocol

When an exact mission question is supplied and approved, ARTEMIS should create a mission-specific investigation record before substantive research begins.

Minimum activation record:

```yaml
mission:
  question: null
  deliverable: null
  status: proposed
  approval_status: pending
  time_scope: null
  geographic_scope: null
  depth: null
  stakeholders: []
  success_criteria: []
  constraints: []

research:
  enabled: false
  source_review_started: false
  evidence_collection_started: false
  synthesis_started: false

controls:
  independent_verification_required: true
  preserve_contradictions: true
  label_unverified_claims: true
  prohibit_speculation: true
```

`research.enabled` must remain `false` until the mission question and required scope fields are supplied and approved.

---

## 14. Output Structure for an Activated Investigation

Once activated, the final investigation should use this order unless the mission requires another structure:

1. Mission Question
2. Scope and Constraints
3. Executive Finding
4. Verified Facts
5. Evidence Register
6. Independent Verification Results
7. Contradictions and Alternative Explanations
8. Inferences
9. Assumptions
10. Unknowns / Information Gaps
11. Confidence Assessment
12. Evidence-Backed Conclusions
13. Limitations
14. Source List / Citation Record
15. Audit and QA Status

The final synthesis must never conceal material disagreement or uncertainty for narrative simplicity.

---

## 15. Current Status

### Verified Facts

- A research methodology has been requested.
- No mission question has been provided.
- This document establishes a research framework only.

### Inferences

None.

### Assumptions

None.

### Unknowns

- Exact mission question
- Intended deliverable
- Time scope
- Geographic scope
- Required depth
- Stakeholders
- Investigation-specific success criteria
- Any mission-specific legal, privacy, access, or handling constraints

### Operational State

**AWAITING MISSION QUESTION AND APPROVAL BEFORE ANY RESEARCH BEGINS.**

---

## 16. Non-Negotiable Investigation Directive

ARTEMIS must not manufacture evidence, fill information gaps with speculation, convert repeated reporting into independent verification, or present an inference as a verified fact.

The purpose of this framework is to make future investigations reproducible, auditable, source-grounded, contradiction-aware, and explicit about uncertainty.

# ClearGlass Inc. Neon Command Grid Internal Linking Strategy

This document defines the maintainable authority network implemented by `tools/internal_links.py`. The goal is a precise neon command grid: every crawlable page contributes signal to a pillar, every supporting page has lateral paths, and every discovery path resolves toward trust and conversion without noisy overlinking.

## 1. Full site linking strategy

- **Home hub:** `index.html` remains the global authority hub and links outward to every pillar through the generated network block.
- **Pillars:** each cluster has one central page that receives cluster equity and explains the category: cyber defense, intelligence, Artemis, autonomous operations, legal/compliance, healthcare, government, services, design, Opal-Koboi assets, insights, and company operations.
- **Clusters:** supporting pages link back to their pillar, forward to rotated siblings, and laterally to curated cross-cluster pages only when the intent is strong.
- **Conversion routes:** service and product pages route to `store.html`, `pricing.html`, or `offers/index.html`; trust pages route toward proof pages before conversion.
- **Generated consistency:** internal-link blocks are regenerated from the canonical graph using `python3 tools/internal_links.py`, preventing drift and accidental hand edits.

## 2. Page hierarchy map

| Tier | Role | Canonical pages |
| --- | --- | --- |
| Authority hub | Brand, navigation, crawl center | `index.html` |
| Pillars | Major topical categories | `cyber-defense-console.html`, `intelligence.html`, `artemis-os.html`, `percival-os.html`, `legal/index.html`, `clearpulse.html`, `government.html`, `offers/index.html`, `web-design.html`, `opal/index.html`, `blog/index.html` |
| Clusters | Product, proof, service, and education depth | Members listed in `CLUSTERS` inside `tools/internal_links.py` |
| Conversion | Intake and offer paths | `store.html`, `pricing.html`, `offers/index.html`, individual offer pages |
| Proof and expansion | Specs, docs, blogs, runbooks | `docs/guardian_command_nexus_spec.html`, blog posts, operations handoffs |

## 3. Pillar-to-cluster matrix

| Pillar | Cluster purpose | Strategic CTA |
| --- | --- | --- |
| Cyber Defense Console | Defensive operations, GUARDIAN, SENTINEL, BLUEDESK, blue-team workflows | Book a security engagement; start a Security Quick-Audit |
| Intelligence | OSINT, NEXUS, flow intelligence, investigation surfaces | Book a security engagement; see pricing |
| Artemis OS | Self-evolving intelligence platform and air-control surfaces | See pricing; book engagement |
| PERCIVAL OS | Governed command and autonomous operations | Browse services; see pricing |
| Legal Infrastructure | Corporate, tax, procurement, privacy, AI liability | Book engagement; browse services |
| ClearPulse | Healthcare and PHIPA readiness | Get PHIPA checklist; book engagement |
| Government Solutions | Procurement readiness, public-sector systems, Counter-UAS, transit twins | Book engagement; procurement readiness |
| Services & Engagements | Offers, pricing, store, SMB package, hardening sprint | Store; pricing |
| Web Design & Development | Premium UI and design system studies | Store; pricing |
| Opal-Koboi | Productized automation assets | Store; pricing |
| ClearGlass Intelligence | Essays and educational topical expansion | Store; pricing |

## 4. Recommended anchor text for major pages

- `cyber-defense-console.html`: **Cyber Defense Console — defensive operations command center**
- `guardian.html`: **GUARDIAN intelligence command interface**
- `docs/guardian_command_nexus_spec.html`: **GUARDIAN command nexus technical specification**
- `intelligence.html`: **ClearGlass intelligence practice**
- `artemis-os.html`: **Artemis intelligence operating system**
- `artemis-self-evolving-platform.html`: **Artemis self-evolving improvement loop**
- `percival-os.html`: **PERCIVAL governed command center**
- `agentmesh.html`: **Agent Mesh multi-agent orchestration**
- `offers/index.html`: **ClearGlass services and engagements**
- `store.html`: **book a ClearGlass security engagement**
- `pricing.html`: **ClearGlass pricing and engagement models**

## 5. Suggested internal links for the home page

The home page should prioritize pillar links, not individual long-tail pages. Link to the cyber-defense, intelligence, Artemis, command, legal, healthcare, government, services, design, Opal-Koboi, and insights pillars. Keep direct conversion links to services, pricing, and store visible in navigation and CTA areas.

## 6. Suggested internal links for major service pages

- `offers/index.html` should link to `store.html`, `pricing.html`, `offers/security-quick-audit.html`, `offers/hardening-sprint.html`, `smb-cyber-trust-kit.html`, and `cyber-defense-console.html`.
- `store.html` should link to the SMB trust kit, security quick audit, hardening sprint, pricing, and the cyber-defense pillar.
- `pricing.html` should link back to services, store, and proof pages that justify trust: cyber defense, BLUEDESK, GUARDIAN spec, and AI agent governance.

## 7. Suggested internal links for blog pillar pages

`blog/index.html` should behave as the editorial pillar. Each post should link back to the blog index, its product or platform pillar, one sibling post, and one conversion page where relevant. Avoid generic “read more” anchors; use topic-specific anchors such as “agentic software security architecture” or “governed deployment approvals.”

## 8. Suggested internal links for cluster articles

Cluster articles should use a four-link ceiling unless the page is a pillar: one pillar link, two sibling links, and one conversion or proof bridge. This keeps the signal tight and prevents interface clutter.

## 9. Suggested footer link structure

Recommended footer groups:

1. **Command Systems:** Cyber Defense Console, GUARDIAN, SENTINEL, BLUEDESK, PERCIVAL.
2. **Intelligence Platforms:** Intelligence, NEXUS, Artemis OS, Agent Mesh, ClearPulse.
3. **Services:** Services & Engagements, Store, Pricing, Security Quick-Audit, Hardening Sprint.
4. **Governance:** Legal Infrastructure, Privacy, Terms, AI Liability, Procurement Readiness.
5. **Insights:** Blog index plus three flagship essays.

## 10. Suggested CTA link structure

- Top-of-page CTA: primary commercial action (`store.html` or `offers/index.html`).
- Mid-page CTA: proof path (`docs/guardian_command_nexus_spec.html`, `blog/...`, or architecture page).
- End-of-page CTA: direct conversion (`store.html`, `pricing.html`, intake/contact action).
- Generated related block CTA: two links only, selected by cluster.

## 11. Prioritized implementation order

1. Keep `tools/internal_links.py` as the canonical graph and regenerate all marked blocks.
2. Strengthen the generated block visual language into a premium neon command grid.
3. Add or refine only high-intent contextual links on critical pages such as GUARDIAN, Cyber Defense Console, services, and blog pillars.
4. Update footer groups after reviewing global navigation patterns.
5. Run `python3 tools/internal_links.py --check` and a link crawl before release.

## Maintenance rule

Do not hand-edit generated `cg-related` blocks. Add pages to `PAGES`, place them in a cluster, add curated bridges to `EXTRA_LINKS`, and regenerate.

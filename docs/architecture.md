# ClearGlass Burlington Cyber Market Growth Engine Architecture

## Repository audit

This monorepo already contains a GitHub Pages marketing site, `artemis` Python architecture code, existing agent definitions, data feeds, and governed commerce systems. The safe merge approach is additive: keep the homepage and commerce approval model intact, add a Burlington growth-engine control layer, and avoid live integrations until operators provide credentials and approval workflows.

## Architecture plan

The system is a human-gated growth operating system: agents draft and validate market intelligence, leads, campaign assets, local SEO plans, outreach, partnerships, conversion experiments, revenue operations, analytics, and compliance findings. Deterministic Python controls enforce duplicate prevention, suppression, approval, claim evidence, budget ceilings, geographic targeting, attribution links, prompt-injection resistance, and audit-log integrity.

## Runtime components

- `artemis.growth_engine`: dependency-light policy, scoring, campaign validation, suppression, and immutable audit controls.
- `config/*.yaml`: brand, markets, offers, campaigns, approval policies, suppression rules, and scoring model.
- `agents/*`: scoped agent definitions with draft/analyze/export permissions only.
- `data/*`: schemas and draft campaign packages; no invented performance or customer data.
- `apps/command-center`: static command-centre surface with safe zero states.
- `workflows/*.yml`: local workflow specifications for planning, content, qualification, approvals, reviews, and rollback.

## Campaign generation workflow

Market signal → opportunity qualification → audience selection → offer selection → campaign brief → content and ad generation → claim verification → compliance review → human approval → publication/export → performance collection → attribution → optimization recommendation → human-approved adjustment.

External actions fail closed when approval is missing or dry-run mode is active.

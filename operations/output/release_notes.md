# Release Notes — 2026-06-12

*112 commit(s) since repository start*

## New Features

- **nexus:** v12.3 — CG loader splash + live patch + intel expansion (#414) (`ac30b77`)
- **percival:** PERCIVAL BUILD — orbital spatial workspace (#413) (`7bb48c8`)
- **percival:** rename agent to PERCIVAL + Systems Control Surface console (#411) (`ba9650d`)
- **percival:** STEWARD — governed autonomous website-steward agent (#409) (`330e944`)
- **pwa:** install-grade vector icon + first-class icon links (`58b1991`)
- **platform:** PWA + instant navigation + view transitions (#406) (`be2835d`)
- **platform:** PWA + instant navigation + view transitions (`e61ab44`)
- **prompts:** add ClearGlassInc Revenue Agent system prompt (`3e36220`)
- **web-design:** add comparison table, FAQ, and animated metric counters (#399) (`18151ad`)
- **web-design:** add comparison table, FAQ, and animated metric counters (`1789be3`)
- **outreach:** add personalized top-5 outreach drafts (`5e2fac0`)
- **outreach:** add real Oakville/Burlington lead list (public sources) (`05555b2`)
- **outreach:** add CASL-compliant outreach templates and lead-list framework (`eceed0a`)
- **site:** premium Website Design & Development landing page (#396) (`a3be1a1`)
- **offers:** add revenue/offer assets and read-only audit tool (`9f60093`)
- **ci:** optimize workflow_doctor.py — add timeout enforcement + expanded stable actions [P0 milestone] (`5cbfd1c`)
- **design:** shared design-token system (Control Surface v3.3) (#385) (`0e699a6`)
- **ci:** add Cert Bot TLS expiry monitor (script + workflow + tests) (`12f4631`)
- **nav:** ClearGlass Control Surface v3.1 — command-palette-first nav (#382) (`d759fa2`)
- **buttons:** MACHINED GLASS button system + live Button Lab (#381) (`0f87bf0`)
- **ui:** finish site-wide blue-violet recolor + advanced interaction behaviors (#379) (`903ec71`)
- **ui:** deep-clean next-tier pages + advanced button/link interaction layer (#378) (`ac2c95d`)
- **theme:** unify all pages on homepage blue-violet identity (#377) (`cd55882`)
- **nav:** site-wide hover menu for easy navigation across all pages (#374) (`75eb9d9`)
- **mesh:** OSINT collector (24 sources) + entity/topic graph + orchestration dashboard (#373) (`dca9cda`)
- **percival:** org-scoped Agent Mesh — ClearGlass-only OSINT orchestration (#372) (`bd6af99`)
- **autostore:** risk scoring + read-only advisor + idempotency + metrics (#371) (`a7a2f58`)
- **aegis:** legal-process register + transparency report + intake UI + shared audit (#370) (`b21ecdc`)
- **percival:** AEGIS — lawful-access compliance & rights-protection agent (#369) (`6eb223a`)
- **bots:** self-evolving wealth engine (revenue-first ladder + fleet evolution) (`e175e8a`)
- **autostore:** PostgresStore + migrations, Redis worker, role auth, write cockpit (#366) (`ebe82b9`)
- **autostore:** PERCIVAL control-plane monorepo (Postgres + FastAPI + Next.js) (#365) (`be2aac8`)
- **autostore:** PERCIVAL control-plane monorepo (Postgres + FastAPI + Next.js) (`9d04576`)
- **percival·pfas:** evidence-pack exporter + text-PDF profile + in-browser download (#364) (`b784662`)
- **percival·pfas:** lab CSV ingester + SENTINEL map layer (#362) (`1ab16f8`)
- **percival:** purple-team detection-engineering engine + PFAS agent (#361) (`91c0c25`)
- **percival:** purple-team detection-engineering engine + PFAS agent (`dc85d5e`)
- **home:** live USGS/NWS LIVE OPS ribbon linking to SENTINEL (#359) (`ce95436`)
- live USGS/NWS in PERCIVAL + live airspace (OpenSky) in SENTINEL (#358) (`2729bb6`)
- **sentinel:** live geospatial mode — real location + USGS/NWS feeds + camera (#357) (`9d3c537`)
- **sentinel:** live geospatial mode — real location + USGS/NWS feeds + camera (`e8f6d19`)
- **percival:** link SENTINEL command center into the PERCIVAL HUD (#355) (`ac00ffe`)
- **sentinel:** privacy-preserving vision ops + visual command center (#354) (`8a3b779`)
- **sentinel:** privacy-preserving vision ops + visual command center (`4caf7dd`)
- **sentinel:** add Exploit-DB as approved defensive threat-intel source (#352) (`aec99cd`)
- **sentinel:** add Exploit-DB as approved defensive threat-intel source (`6cca8a4`)
- **sentinel:** charter v2.1 — geospatial + OSINT extension (#350) (`9be32d5`)
- **sentinel:** geospatial+OSINT charter + enforced hard rules (#349) (`bf288b4`)
- **sentinel:** privacy-first SENTINEL charter + enforced policy gate (#348) (`5988604`)
- **percival:** red/black mission-ready HUD reskin (#344) (`434aec1`)
- **sentinel:** Phase-One Governance Shell + RBAC retrieval (#343) (`14ca6d4`)
- **sentinel:** add Pinecone+Milvus adapters and recall harness (`193a832`)
- **sentinel:** Phase-One fail-closed Governance Shell + RBAC retrieval (`5c9a5e7`)

## Bug Fixes

- **seo,a11y:** apply PERCIVAL's auto-fix queue + calibrate scanner (#412) (`73a8d5b`)
- **steward:** calibrate link/sitemap scanners from first live run (#410) (`5e19664`)
- **seo:** repair malformed sitemap entries and drop dead URL (#402) (`799b436`)
- **pages:** retire flaky legacy pages-build-deployment (`9819626`)
- **ci:** make needs_fix advisory (CI green, repair applies fixes) [patch + run] (`687898f`)
- **ci:** make timeout enforcement --fix only (unblock dry-run CI) [patch] (`309d776`)
- **pages:** move permissions to deploy job for GitHub Pages [workflow-doctor] (`be77431`)
- **ci:** pin actions/checkout to v6 in cert-bot.yml [workflow-doctor] (`a8a66d7`)
- **live:** keep crypto panels live after CoinCap v2 retirement (#376) (`fcece3d`)
- **sitemap:** index remaining content pages; exempt non-indexable (#347) (`e895f24`)
- **health-bot:** treat sitemap drift as warning, not a health failure (#346) (`23fcd32`)
- **ci:** Health Monitor label crash + SENTINEL demo runner (#345) (`2eacb13`)

## Documentation

- **repo:** add Code of Conduct, issue/PR templates, deployment runbook (#397) (`0fc8153`)
- **offers:** add ClearGlass ARTEMIS Service Agent specification (`5634704`)

## Tests

- **sentinel:** drop unused import (ruff clean) (`db363ee`)

## Maintenance

- Add Control Surface event contract: n8n envelope spec + JSON Schema (`0dd3b21`)
- Add Event-Driven Control Surface dashboard (`99519eb`)
- Add Artemis OS — cinematic intelligence operating system page (`aabb04e`)
- Rebuild saas-platform as event-driven Control Surface in brand palette (`be11e06`)
- Fix dependency-updater: missing label must not abort PR creation (`72f9e16`)
- update Python test dependencies (`48c0e24`)
- Patch all workflows: per-job timeouts + align doctor rules with proven versions (`29dc96f`)
- Site health: index saas-platform + button-lab, add missing page metadata (`836252e`)
- Create saas-platform.html for live dashboard (`e5297e1`)
- Update header comment in control-surface.js (`89cfb43`)
- Update title in hover-menu.html (`204d1d4`)
- Update aria-label in icon.svg (`e45cae3`)
- Update branding from CLEARGLASS to CLEARGLASSINC (`cbacd52`)
- Update title and comments in ai-operator.html (`932bf6d`)
- Add AVALON fusion core to schema.json structured data (`9298861`)
- Add AVALON — ARTEMIS ⊕ PERCIVAL unified fusion core (`1afda34`)
- Wire up revenue funnel: live lead capture, working CTAs, pricing links (`fabb22d`)
- Update founder and chairman profile picture (`2322177`)
- Update small corner logo to new crystal seal across site (`0f47f4e`)
- Build premium offers page and add ARTEMIS Service Agent (`407cd9e`)
- Match offers page palette to main site (`eb1bf6f`)
- Sharpen offers page copy with hardening/PHIPA language (`ddbae4a`)
- Add ARTEMIS edge-native AI command system prompt (`38000f9`)
- Swap homepage hero video for updated clip (#390) (`3912032`)
- Trim homepage Products menu to Guardian and Government only (`09f2673`)
- Replace homepage hero image with autoplay video (`03032f3`)
- **ci:** trigger all workflows [pages + doctor] 2026-06-08 (`05d7a8f`)
- **deps:** bump the actions group across 1 directory with 3 updates (`16a1516`)
- Update documentation structure: add docs/index.md as central hub linking AI TTS and future sections (`3a49de8`)
- Add open-source TTS models guide for AI voice agents and custom cloning (Aria integration) (`4b9e961`)
- Add CPA / fractional CFO partner outreach automation bot (`2d99d1d`)

## Automation

- update generated outputs — 2026-06-11 23:45 UTC [skip ci] (`c850adb`)
- update generated outputs — 2026-06-11 11:21 UTC [skip ci] (`389c6d3`)
- update generated outputs — 2026-06-10 10:55 UTC [skip ci] (`ddf8bae`)
- update generated outputs — 2026-06-09 10:33 UTC [skip ci] (`82617c6`)
- update generated outputs — 2026-06-08 11:57 UTC [skip ci] (`0f54742`)
- update generated outputs — 2026-06-07 09:59 UTC [skip ci] (`6277431`)
- update generated outputs — 2026-06-06 09:24 UTC [skip ci] (`6e77f2c`)
- update generated outputs — 2026-06-05 10:45 UTC [skip ci] (`27a8de2`)
- update generated outputs — 2026-06-04 19:41 UTC [skip ci] (`5deec71`)
- update generated outputs — 2026-06-04 10:38 UTC [skip ci] (`eb007c4`)

## Style

- **nav:** recolor hover menu to homepage blue-violet theme (#375) (`4821656`)
- **nav:** recolor hover menu to homepage blue-violet theme (`44ed956`)

## Other

- **sitemap:** add offers/ landing pages to sitemap (`7a6a3c7`)

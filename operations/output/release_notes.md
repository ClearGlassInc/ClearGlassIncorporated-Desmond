# Release Notes — 2026-06-13

*112 commit(s) since repository start*

## New Features

- **revenue:** add live Interac e-Transfer payment rail to pricing (#429) (`b84d484`)
- **revenue:** live pricing storefront — book-ready conversion surface (#423) (`abf8a61`)
- **bluedesk:** CISO risk & blue-team defensive console (#422) (`0a13c60`)
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

## Bug Fixes

- **seo:** PERCIVAL sitemap sweep — index artemis-os + control-surface (#424) (`ee3a1c8`)
- **live:** replace dead open-notify ISS feed with wheretheiss.at (#421) (`a84f742`)
- **seo,a11y:** apply PERCIVAL's auto-fix queue + calibrate scanner (#412) (`73a8d5b`)
- **steward:** calibrate link/sitemap scanners from first live run (#410) (`5e19664`)
- **seo:** repair malformed sitemap entries and drop dead URL (#402) (`799b436`)
- **pages:** retire flaky legacy pages-build-deployment (`9819626`)
- **ci:** make needs_fix advisory (CI green, repair applies fixes) [patch + run] (`687898f`)
- **ci:** make timeout enforcement --fix only (unblock dry-run CI) [patch] (`309d776`)
- **pages:** move permissions to deploy job for GitHub Pages [workflow-doctor] (`be77431`)
- **ci:** pin actions/checkout to v6 in cert-bot.yml [workflow-doctor] (`a8a66d7`)
- **live:** keep crypto panels live after CoinCap v2 retirement (#376) (`fcece3d`)

## Documentation

- **repo:** add Code of Conduct, issue/PR templates, deployment runbook (#397) (`0fc8153`)
- **offers:** add ClearGlass ARTEMIS Service Agent specification (`5634704`)

## Maintenance

- Apply suggested fix to claude_agent_sdk from Copilot Autofix (`ef5c74b`)
- Add async main function for querying directory files (`60f20da`)
- Fix missing newline at end of icon.svg (`8fd1ad9`)
- Update icon.svg to use SVG logo format (`70a0190`)
- Add navigation bar and logo styling (`c2903db`)
- Replace 'jarvisSay' with 'CGSay' in HTML file (`32b1637`)
- Update title and meta description for branding (`8b8ec63`)
- Rename JARVIS OS to CG OS in HTML file (`c0d2085`)
- Retire legacy pages-build-deployment by pinning Pages source to GitHub Actions (`c47d3a4`)
- Remove broken threads.html footer link in artemis-os (`0aac777`)
- Rebuild control-surface command dropdown with crystal-glass styling and live page links (`0fc45dd`)
- Fix broken footer link in artemis-os.html (`e55d800`)
- Add UNCLASSIFIED classification banner to homepage (`9911afb`)
- Add AEGIS-ML-Defense.ps1 - advanced adversarial ML input sanitization and entropy-based defense function (`acbebfb`)
- Add scripts/Invoke-AegisMLDefense.ps1 - Production-ready adversarial ML input defense function with entropy analysis (`843124d`)
- Add OSINT-Methodologies.md documenting gathering techniques and advanced automation (`05a2697`)
- Go live: real data plane for the Control Surface (all six streams) (`5e65972`)
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

- refresh control-surface data feeds [skip ci] (`d056de8`)
- refresh control-surface data feeds [skip ci] (`9b2b1a6`)
- refresh control-surface data feeds [skip ci] (`4d0c801`)
- update generated outputs — 2026-06-13 09:56 UTC [skip ci] (`a20d4a2`)
- refresh control-surface data feeds [skip ci] (`3944583`)
- refresh control-surface data feeds [skip ci] (`b1420c8`)
- refresh control-surface data feeds [skip ci] (`5ad6ebf`)
- update generated outputs — 2026-06-12 11:00 UTC [skip ci] (`67ba8fb`)
- update generated outputs — 2026-06-11 23:45 UTC [skip ci] (`c850adb`)
- update generated outputs — 2026-06-11 11:21 UTC [skip ci] (`389c6d3`)
- update generated outputs — 2026-06-10 10:55 UTC [skip ci] (`ddf8bae`)
- update generated outputs — 2026-06-09 10:33 UTC [skip ci] (`82617c6`)
- update generated outputs — 2026-06-08 11:57 UTC [skip ci] (`0f54742`)
- update generated outputs — 2026-06-07 09:59 UTC [skip ci] (`6277431`)
- update generated outputs — 2026-06-06 09:24 UTC [skip ci] (`6e77f2c`)
- update generated outputs — 2026-06-05 10:45 UTC [skip ci] (`27a8de2`)

## Style

- **nav:** recolor hover menu to homepage blue-violet theme (#375) (`4821656`)
- **nav:** recolor hover menu to homepage blue-violet theme (`44ed956`)

## Build

- **deps:** bump next from 14.2.5 to 15.5.18 in /apps/autostore/cockpit (`a45fd83`)

## Other

- **sitemap:** add offers/ landing pages to sitemap (`7a6a3c7`)

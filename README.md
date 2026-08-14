# ClearGlass Inc.

**Transparency is infrastructure.**

ClearGlass Inc. is an Ontario-focused cybersecurity, AI-governance, OSINT, automation, and intelligence-platform company. This repository is the primary engineering and web platform for ClearGlassInc.com, including the public website, product surfaces, research systems, operational data, automation, and platform architecture.

## Live Platform

- Website: https://www.clearglassinc.com
- Intelligence Platform: https://www.clearglassinc.com/intelligence-platform.html
- Governed Data Fabric Diagnostics: https://www.clearglassinc.com/data-fabric.html
- Ontario OSINT: https://www.clearglassinc.com/Ontario-osint.html
- Products: https://www.clearglassinc.com/products.html
- Store: https://www.clearglassinc.com/store.html

## Core Systems

- **ClearGlass Nexus** — central intelligence and orchestration layer
- **Artemis** — AI/cyber intelligence product family
- **Guardian / Sentinel** — defensive cybersecurity and monitoring surfaces
- **Ontario OSINT** — public-source intelligence and regional analysis
- **XENOLITH** — sovereign intelligence-lattice research platform
- **ClearGlass Data Fabric** — governed same-origin repository data layer
- **Growth / SEO / Commerce** — revenue, marketing, search, and product systems

## Governed Data Fabric

Repository-backed operational data is cataloged through `data/catalog.json` and accessed through `assets/js/clearglass-data-fabric.js`.

The fabric provides:

- same-origin loading
- parent-traversal blocking
- JSON and CSV decoding
- module and root-dataset discovery
- browser health checks
- restricted browser access for sensitive workflow boundaries such as `data/leads`

Run the offline validator when a local checkout is available:

```bash
python3 scripts/validate_data_fabric.py
node --check assets/js/clearglass-data-fabric.js
```

## Actions-Independent Release Path

GitHub Pages is configured from `main` and can publish through the repository's legacy Pages build path. The site also includes browser-based data-fabric diagnostics so the public runtime can be checked without depending on a GitHub-hosted Actions runner.

See `docs/ACTIONS_BILLING_FALLBACK.md` for the operational fallback and recovery procedure.

## Repository Safety

- No credentials or private API keys belong in source control.
- Production secrets must remain in approved external secret stores or platform configuration.
- Public OSINT and cybersecurity functions are defensive, lawful, and evidence-oriented.
- Counter-UAS material in this repository is a component/research area; it is **not** the identity or primary purpose of this repository.

## Company

**ClearGlass Inc.**  
Ontario, Canada  
https://www.clearglassinc.com

© 2026 ClearGlass Inc. All rights reserved except where a file or third-party component states otherwise.

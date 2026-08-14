#!/usr/bin/env python3
"""Apply the canonical ClearGlass public identity to static-site source.

The operation is intentionally narrow: exact legacy contact strings and known
role variants are replaced in public HTML, JavaScript and JSON. It never edits
generated operational reports, tests, dependencies or backend systems.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
IDENTITY_PATH = ROOT / "data" / "corporate-identity.json"
SKIP_TOP_LEVEL = {
    ".git",
    ".github",
    "apps",
    "clearglass-commerce",
    "data",
    "dist",
    "node_modules",
    "operations",
    "projects",
    "tests",
    "tools",
}
PUBLIC_SUFFIXES = {".html", ".js", ".json"}
MANAGED_DOCUMENTS = {
    ".github/workflows/cloudflare-email-routing-diagnostic.yml",
    ".github/workflows/cloudflare-email-routing.yml",
    "4D_DOMINANCE_ACTIVATION.md",
    "CLEARGLASSINC_EMAIL_SETUP.md",
    "CLEARGLASS_SECURE_DEPLOYMENT_AGENT_PROMPT.md",
    "agents/positioning_credibility_architect/README.md",
    "agents/positioning_credibility_architect/agent.json",
    "agents/positioning_credibility_architect/system_prompt.md",
    "docs/SEO_STRATEGY.md",
    "docs/STRIPE_LIVE_READINESS.md",
    "enterprise-profile/README.md",
    "enterprise-profile/VERIFICATION_REPORT.md",
    "humans.txt",
    "llms.txt",
    "legal/CONTENT_THEFT_RESPONSE_PLAN.md",
    "operations/email/README.md",
    "operations/seo/SEO_STRATEGY.md",
    "prompts/sales_guardian_artemis_system_prompt.md",
    "tools/priority_alpha_engine.py",
}


def identity() -> dict:
    return json.loads(IDENTITY_PATH.read_text(encoding="utf-8"))


def replacements() -> dict[str, str]:
    canonical = identity()
    email = canonical["organization"]["email"]
    role = canonical["founder"]["jobTitle"]
    return {
        "desmondotieno@icloud.com": email,
        "dezzy.231@gmail.com": email,
        "Desmond@clearglassinc.com": email,
        "https://www.linkedin.com/company/clearglassinc": canonical["organization"]["sameAs"][1],
        "Software Architect & COO · Founder": role,
        "Software Architect & COO, ClearGlass Inc.": f"{role}, ClearGlass Inc.",
        "Software Architect & COO": role,
        "SOFTWARE ARCHITECT & COO": role.upper(),
        "Software Architect &amp; COO": role.replace("&", "&amp;"),
        "Software Architect and COO": role,
        "Software Architect + COO": role,
        "Founder, Software Architect, and COO": role,
        "Founder & Chairman, Software Architect": role,
        "Software Architect, Founder & Chairman": role,
        "Founder &amp; Chairman": role.replace("&", "&amp;"),
        "Founder and Chairman": role,
        "COO & Founder": role,
        "Founder & Chairman": role,
    }


def public_files() -> list[Path]:
    site_files = {
        path
        for path in ROOT.rglob("*")
        if path.is_file()
        and path.suffix.lower() in PUBLIC_SUFFIXES
        and path.relative_to(ROOT).parts[0] not in SKIP_TOP_LEVEL
    }
    managed = {ROOT / path for path in MANAGED_DOCUMENTS if (ROOT / path).is_file()}
    return sorted(site_files | managed)


def transformed(text: str) -> str:
    for old, new in replacements().items():
        text = text.replace(old, new)
    return text


def stale_files() -> list[Path]:
    return [
        path
        for path in public_files()
        if transformed(path.read_text(encoding="utf-8", errors="replace"))
        != path.read_text(encoding="utf-8", errors="replace")
    ]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    stale = stale_files()
    if args.check:
        for path in stale:
            print(path.relative_to(ROOT).as_posix())
        return 1 if stale else 0
    for path in stale:
        original = path.read_text(encoding="utf-8", errors="replace")
        path.write_text(transformed(original), encoding="utf-8")
        print(path.relative_to(ROOT).as_posix())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Deterministic, dependency-free SEO governance validator."""
from __future__ import annotations
import json
import re
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "config/seo/seo-governance.json"
REQUIRED = ["services/ai-automation-services.html", "services/cybersecurity-consulting.html", "services/osint-automation.html", "services/ai-governance.html"]

def fail(message: str) -> None:
    print(f"FAIL: {message}")
    raise SystemExit(1)

def main() -> int:
    if not CONFIG.is_file(): fail(f"missing {CONFIG.relative_to(ROOT)}")
    policy = json.loads(CONFIG.read_text(encoding="utf-8"))
    if policy.get("status") != "ACTIVE": fail("SEO policy is not ACTIVE")
    if "NSA" not in policy.get("assurance_note", "") or "DARPA" not in policy.get("assurance_note", ""): fail("assurance disclaimer is incomplete")
    if set(policy.get("canonical_service_routes", [])) != {"/" + p for p in REQUIRED}: fail("canonical service route set does not match required pages")
    for rel in REQUIRED:
        path = ROOT / rel
        if not path.is_file(): fail(f"missing canonical service page: {rel}")
        html = path.read_text(encoding="utf-8")
        checks = {
            "title": r"<title>[^<]+</title>",
            "description": r'<meta\s+name=["\']description["\']\s+content=["\'][^"\']+["\']',
            "canonical": r'<link\s+rel=["\']canonical["\']\s+href=["\']https://www\.clearglassinc\.com/[^"\']+["\']',
            "organization_schema": r'"@type"\s*:\s*"Organization"',
            "breadcrumb_schema": r'"@type"\s*:\s*"BreadcrumbList"',
            "service_schema": r'"@type"\s*:\s*"Service"',
            "evidence": r"Evidence status",
            "cta": r"Request an assessment",
        }
        for name, pattern in checks.items():
            if not re.search(pattern, html, re.IGNORECASE | re.DOTALL): fail(f"{rel}: missing {name}")
        if re.search(r"NSA[- ](?:certified|grade certification)|DARPA[- ]certified|government-certified", html, re.I): fail(f"{rel}: unsupported certification claim detected")
    robots = (ROOT / "robots.txt").read_text(encoding="utf-8")
    for sitemap_ref in ("Sitemap: https://www.clearglassinc.com/sitemap.xml", "Sitemap: https://www.clearglassinc.com/sitemap-services.xml"):
        if sitemap_ref not in robots: fail(f"robots.txt missing {sitemap_ref}")
    service_sitemap = (ROOT / "sitemap-services.xml").read_text(encoding="utf-8")
    for rel in REQUIRED:
        route = rel.replace("\\", "/")
        if f"https://www.clearglassinc.com/{route}" not in service_sitemap: fail(f"sitemap-services.xml missing {route}")
    print(f"PASS: SEO governance validated for {len(REQUIRED)} canonical service pages")
    return 0
if __name__ == "__main__": raise SystemExit(main())

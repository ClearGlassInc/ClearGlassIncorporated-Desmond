#!/usr/bin/env python3
"""Validate the sitemap ping script and the ClearGlassInc sitemap reference.

The check is intentionally offline-friendly: it verifies that sitemap.xml exists,
that robots.txt advertises it, and that the PowerShell script contains only the
approved Bing ping endpoint rather than black-hat submission targets.
"""
from __future__ import annotations

import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SITEMAP = ROOT / "sitemap.xml"
ROBOTS = ROOT / "robots.txt"
PING_SCRIPT = ROOT / "scripts" / "Invoke-SitemapPing.ps1"
SITEMAP_URL = "https://www.clearglassinc.com/sitemap.xml"
BING_ENDPOINT = "https://www.bing.com/ping?sitemap="
PROHIBITED_TERMS = ("forum", "comment", "directory", "backlink", "blast", "spam")


def fail(message: str) -> None:
    print(f"FAIL: {message}")
    sys.exit(1)


def main() -> None:
    if not SITEMAP.exists():
        fail("sitemap.xml is missing")
    if not ROBOTS.exists():
        fail("robots.txt is missing")
    if not PING_SCRIPT.exists():
        fail("scripts/Invoke-SitemapPing.ps1 is missing")

    ET.parse(SITEMAP)
    robots_text = ROBOTS.read_text(encoding="utf-8", errors="replace")
    script_text = PING_SCRIPT.read_text(encoding="utf-8", errors="replace")

    if f"Sitemap: {SITEMAP_URL}" not in robots_text:
        fail("robots.txt does not advertise the canonical sitemap URL")
    if SITEMAP_URL not in script_text:
        fail("PowerShell script does not use the canonical sitemap URL")
    if BING_ENDPOINT not in script_text:
        fail("PowerShell script does not target the approved Bing sitemap endpoint")
    if "google.com/ping" in script_text.lower():
        fail("PowerShell script references Google's retired ping endpoint")

    executable_section = re.sub(r"<#.*?#>", "", script_text, flags=re.DOTALL).lower()
    for term in PROHIBITED_TERMS:
        if re.search(rf"\b{re.escape(term)}\b", executable_section):
            fail(f"PowerShell script contains prohibited SEO automation term: {term}")

    print("OK: sitemap ping script and sitemap references are valid")


if __name__ == "__main__":
    main()

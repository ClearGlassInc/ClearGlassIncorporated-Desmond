#!/usr/bin/env python3
"""Idempotently wire the Minerals Intelligence Platform into static site registries."""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def write(path: str, text: str) -> None:
    (ROOT / path).write_text(text, encoding="utf-8")


def insert_once(text: str, marker: str, insertion: str, *, before: bool = True) -> str:
    if insertion.strip() in text:
        return text
    if marker not in text:
        raise RuntimeError(f"Required marker not found: {marker[:120]}")
    return text.replace(marker, insertion + marker if before else marker + insertion, 1)


def wire_product_catalog() -> None:
    path = ROOT / "data/products.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    products = data.setdefault("products", [])
    if any(p.get("slug") == "minerals-intelligence-platform" for p in products):
        return
    ids = []
    for p in products:
        m = re.fullmatch(r"cg-(\d+)", str(p.get("id", "")))
        if m:
            ids.append(int(m.group(1)))
    next_id = max(ids, default=0) + 1
    products.append(
        {
            "id": f"cg-{next_id:03d}",
            "slug": "minerals-intelligence-platform",
            "name": "Minerals Intelligence Platform",
            "description": "Source-transparent global critical-minerals command center.",
            "shortDescription": "Global critical-minerals command center.",
            "category": "Intelligence and command platforms",
            "tags": [
                "critical minerals",
                "commodities",
                "geospatial",
                "intelligence",
                "mining",
                "provenance",
                "risk",
                "supply chain",
                "trade",
            ],
            "status": "available",
            "featured": True,
            "bestseller": False,
            "new": True,
            "recommended": True,
            "productUrl": "/minerals-platform.html",
            "icon": "⛏",
        }
    )
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def wire_nav() -> None:
    text = read("nav.js")
    entry = '    ["Minerals Intelligence Platform", "minerals-platform.html", "Critical-minerals command center", "⛏"],\n'
    marker = '    ["Intelligence Platform", "intelligence-platform.html", "Full-stack intel architecture", "✦"],\n'
    write("nav.js", insert_once(text, marker, entry))


def wire_sitemap() -> None:
    text = read("sitemap.xml")
    if "https://www.clearglassinc.com/minerals-platform.html" in text:
        return
    entry = "  <url>\n    <loc>https://www.clearglassinc.com/minerals-platform.html</loc>\n    <lastmod>2026-08-10</lastmod>\n  </url>\n"
    write("sitemap.xml", insert_once(text, "</urlset>", entry))


def wire_pages_builder() -> None:
    text = read("tools/build_pages.py")
    additions = (
        '    "data/minerals/platform/config.json",\n'
        '    "data/minerals/platform/demo.json",\n'
    )
    marker = '    "data/minerals/manifest.json",\n'
    if '"data/minerals/platform/config.json"' not in text:
        text = insert_once(text, marker, additions, before=False)
    write("tools/build_pages.py", text)


def wire_reference_page() -> None:
    text = read("minerals.html")
    if 'href="/minerals-platform.html"' in text:
        return
    marker = '        <a class="button primary" href="#mineral-search">Search minerals</a>\n'
    insertion = '        <a class="button primary" href="/minerals-platform.html">Open Intelligence Platform</a>\n'
    write("minerals.html", insert_once(text, marker, insertion, before=False))


def wire_store_discovery() -> None:
    text = read("store.html")
    if 'id="minerals-intelligence-platform"' in text:
        return
    marker = '<article class="card"><span class="tag">Free guide</span><h3>Second Brain System</h3>'
    card = (
        '<article class="card feat" id="minerals-intelligence-platform">'
        '<span class="tag">Intelligence platform · new</span>'
        '<h3>Minerals Intelligence Platform</h3>'
        '<p class="desc">Source-transparent command center for critical-minerals markets, projects, trade, supply chains, risk, exploration and data-source health.</p>'
        '<div class="price">Enterprise <small>· deployment scoped to data and licensing</small></div>'
        '<ul class="feats"><li>Global mineral command center</li><li>Geospatial project and facility workspace</li><li>Risk, trade and supply-chain intelligence</li><li>Per-widget provenance and freshness</li><li>Explicit source vs demo data separation</li></ul>'
        '<a class="buy" href="minerals-platform.html">Open platform →</a>'
        '</article>\n'
    )
    write("store.html", insert_once(text, marker, card))


def wire_internal_links() -> None:
    text = read("tools/internal_links.py")
    if '"minerals-platform.html"' in text:
        return
    page_marker = '    "minerals.html": ("Critical Minerals Intelligence", "public-data mineral supply-chain, policy, provenance and compliance intelligence"),\n'
    page_entry = '    "minerals-platform.html": ("Minerals Intelligence Platform", "source-transparent global critical-minerals command center"),\n'
    text = insert_once(text, page_marker, page_entry, before=False)
    write("tools/internal_links.py", text)


def main() -> int:
    wire_product_catalog()
    wire_nav()
    wire_sitemap()
    wire_pages_builder()
    wire_reference_page()
    wire_store_discovery()
    wire_internal_links()
    print("Minerals Intelligence Platform wiring complete.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

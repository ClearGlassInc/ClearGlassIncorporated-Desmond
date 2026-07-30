#!/usr/bin/env python3
"""ClearGlass Advanced SEO Growth Engine.

Audits every indexable static HTML page against search-intent, content-cluster,
internal-link, trust, freshness, schema, crawlability, and Core Web Vitals proxy
rules. It produces a deterministic JSON/Markdown growth backlog and can fail CI
when material sitewide SEO defects are introduced.

Usage:
    python3 tools/advanced_seo_growth.py
    python3 tools/advanced_seo_growth.py --write
    python3 tools/advanced_seo_growth.py --strict

Standard-library only. No page content is modified automatically; recommendations
remain evidence-based and auditable.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import sys
from collections import Counter, defaultdict
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent.parent
SITE = "https://www.clearglassinc.com"
OUT_DIR = ROOT / "data" / "seo"
SKIP_DIRS = {".git", ".github", "assets", "apps", "bots", "clearglass-commerce", "docs", "node_modules", "tools"}
UTILITY = {"404.html", "offline.html", "loader.html", "cg-loader.html", "header-mockup-2040.html", "button-lab.html"}
INTENT_TERMS = {
    "commercial": {"services", "solutions", "pricing", "audit", "consulting", "readiness", "assessment", "platform", "product", "store", "buy"},
    "informational": {"guide", "how", "what", "why", "article", "blog", "research", "explained", "checklist"},
    "navigational": {"about", "contact", "privacy", "terms", "accessibility", "legal", "login", "dashboard"},
}
TRUST_PATHS = {"legal/privacy.html", "legal/terms.html", "legal/accessibility.html"}


class PageParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.title = ""
        self.description = ""
        self.canonical = ""
        self.robots = ""
        self.headings: list[tuple[int, str]] = []
        self.links: list[tuple[str, str]] = []
        self.images: list[dict[str, str]] = []
        self.scripts: list[dict[str, str]] = []
        self.schema: list[str] = []
        self.text: list[str] = []
        self.author = ""
        self.modified = ""
        self._capture = ""
        self._buf: list[str] = []
        self._link_href = ""

    def handle_starttag(self, tag: str, attrs_list: list[tuple[str, str | None]]) -> None:
        attrs = {k.lower(): (v or "") for k, v in attrs_list}
        if tag == "title":
            self._capture, self._buf = "title", []
        elif tag == "meta":
            name = attrs.get("name", "").lower()
            prop = attrs.get("property", "").lower()
            content = attrs.get("content", "").strip()
            if name == "description": self.description = content
            elif name == "robots": self.robots = content.lower()
            elif name in {"author", "article:author"} or prop == "article:author": self.author = content
            elif name in {"last-modified", "date", "article:modified_time"} or prop == "article:modified_time": self.modified = content
        elif tag == "link" and "canonical" in attrs.get("rel", "").lower().split():
            self.canonical = attrs.get("href", "").strip()
        elif re.fullmatch(r"h[1-6]", tag):
            self._capture, self._buf = tag, []
        elif tag == "a":
            self._capture, self._buf = "a", []
            self._link_href = attrs.get("href", "").strip()
        elif tag == "img":
            self.images.append({"src": attrs.get("src", ""), "alt": attrs.get("alt", ""), "width": attrs.get("width", ""), "height": attrs.get("height", ""), "loading": attrs.get("loading", "")})
        elif tag == "script":
            typ = attrs.get("type", "").lower()
            if typ == "application/ld+json": self._capture, self._buf = "jsonld", []
            else: self.scripts.append({"src": attrs.get("src", ""), "defer": attrs.get("defer", ""), "async": attrs.get("async", "")})

    def handle_endtag(self, tag: str) -> None:
        if self._capture == "title" and tag == "title": self.title = " ".join("".join(self._buf).split())
        elif self._capture == "jsonld" and tag == "script": self.schema.append("".join(self._buf))
        elif self._capture == "a" and tag == "a":
            self.links.append((self._link_href, " ".join("".join(self._buf).split())))
            self._link_href = ""
        elif self._capture == tag and re.fullmatch(r"h[1-6]", tag):
            self.headings.append((int(tag[1]), " ".join("".join(self._buf).split())))
        else: return
        self._capture, self._buf = "", []

    def handle_data(self, data: str) -> None:
        if self._capture: self._buf.append(data)
        else:
            clean = " ".join(data.split())
            if clean: self.text.append(clean)


def pages() -> list[Path]:
    result = []
    for p in ROOT.rglob("*.html"):
        rel = p.relative_to(ROOT)
        if rel.parts[0] in SKIP_DIRS or "node_modules" in rel.parts: continue
        result.append(p)
    return sorted(result)


def normalize_internal(href: str, source: str) -> str | None:
    if not href or href.startswith(("#", "mailto:", "tel:", "javascript:", "data:")): return None
    parsed = urlparse(href)
    if parsed.netloc and parsed.netloc not in {"www.clearglassinc.com", "clearglassinc.com"}: return None
    target = parsed.path
    if not target: return "index.html"
    if target.startswith("/"): target = target[1:]
    else:
        parent = Path(source).parent
        target = (parent / target).as_posix()
    target = re.sub(r"(^|/)\./", r"\1", target)
    while "/../" in f"/{target}":
        target = str(Path(target))
        break
    if target.endswith("/"): target += "index.html"
    elif not Path(target).suffix: target += ".html"
    return target


def infer_intent(rel: str, title: str, h1: str) -> str:
    corpus = f"{rel} {title} {h1}".lower()
    scores = {kind: sum(1 for term in terms if term in corpus) for kind, terms in INTENT_TERMS.items()}
    if rel.startswith("blog/"): scores["informational"] += 3
    if rel.startswith("offers/"): scores["commercial"] += 3
    return max(scores, key=scores.get) if max(scores.values()) else "informational"


def cluster_for(rel: str) -> str:
    stem = Path(rel).stem.lower()
    if rel.startswith("blog/"): return "blog"
    if rel.startswith("offers/"): return "services"
    if rel.startswith("legal/"): return "trust-legal"
    for key in ("artemis", "guardian", "cyber", "security", "government", "procurement", "ai", "automation", "smb", "business", "crypto", "banking"):
        if key in rel.lower() or key in stem: return key
    return "corporate"


def add(findings: list[dict], page: str, level: str, check: str, message: str, action: str) -> None:
    findings.append({"page": page, "level": level, "check": check, "message": message, "action": action})


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--strict", action="store_true")
    args = ap.parse_args()

    inventory = {p.relative_to(ROOT).as_posix(): p for p in pages()}
    findings: list[dict] = []
    records: dict[str, dict] = {}
    incoming: Counter[str] = Counter()
    clusters: defaultdict[str, list[str]] = defaultdict(list)

    for rel, path in inventory.items():
        raw = path.read_text(encoding="utf-8", errors="ignore")
        parser = PageParser(); parser.feed(raw)
        noindex = "noindex" in parser.robots
        utility = rel in UTILITY or noindex
        h1s = [t for lvl, t in parser.headings if lvl == 1]
        words = len(re.findall(r"\b[\w'-]+\b", " ".join(parser.text)))
        schema_types: list[str] = []
        for block in parser.schema:
            try:
                data = json.loads(block)
            except json.JSONDecodeError:
                add(findings, rel, "error", "schema.parse", "Invalid JSON-LD prevents machine interpretation.", "Repair or remove the malformed JSON-LD block.")
                continue
            stack = [data]
            while stack:
                node = stack.pop()
                if isinstance(node, dict):
                    typ = node.get("@type")
                    schema_types.extend(typ if isinstance(typ, list) else ([typ] if isinstance(typ, str) else []))
                    stack.extend(node.values())
                elif isinstance(node, list): stack.extend(node)

        intent = infer_intent(rel, parser.title, h1s[0] if h1s else "")
        cluster = cluster_for(rel); clusters[cluster].append(rel)
        internal = []
        weak_anchors = 0
        for href, anchor in parser.links:
            target = normalize_internal(href, rel)
            if target:
                internal.append(target)
                incoming[target] += 1
                if anchor.lower().strip() in {"click here", "learn more", "read more", "here", "more"}: weak_anchors += 1

        records[rel] = {"url": f"{SITE}/" + ("" if rel == "index.html" else rel), "indexable": not noindex, "intent": intent, "cluster": cluster, "title": parser.title, "description": parser.description, "canonical": parser.canonical, "h1_count": len(h1s), "words": words, "schema_types": sorted(set(schema_types)), "internal_links": len(internal), "incoming_links": 0, "images": len(parser.images), "scripts": len(parser.scripts), "bytes": len(raw.encode()), "author": parser.author, "modified": parser.modified}

        if utility: continue
        expected = f"{SITE}/" + ("" if rel == "index.html" else rel)
        if not parser.canonical: add(findings, rel, "error", "canonical.missing", "Indexable page has no canonical URL.", f"Add <link rel=\"canonical\" href=\"{expected}\">.")
        elif parser.canonical.rstrip("/") != expected.rstrip("/"): add(findings, rel, "warn", "canonical.target", f"Canonical points to {parser.canonical}.", "Confirm this consolidation is intentional; otherwise self-canonicalize.")
        if len(h1s) != 1: add(findings, rel, "error", "heading.h1", f"Expected exactly one H1; found {len(h1s)}.", "Give the page one descriptive H1 matching its primary intent.")
        if not parser.title or len(parser.title) < 25 or len(parser.title) > 62: add(findings, rel, "warn", "metadata.title", f"Title length is {len(parser.title)}.", "Write a unique 25–62 character title aligned with the page intent.")
        if not parser.description or len(parser.description) < 70 or len(parser.description) > 165: add(findings, rel, "warn", "metadata.description", f"Description length is {len(parser.description)}.", "Write a unique 70–165 character benefit-led meta description.")
        if words < 180: add(findings, rel, "warn", "content.thin", f"Only about {words} crawlable words were detected.", "Expand with original evidence, examples, comparisons, FAQs, and a decisive next step—or noindex/remove the page.")
        if len(internal) < 2: add(findings, rel, "warn", "links.outbound", f"Only {len(internal)} internal links detected.", "Link to the pillar, one adjacent answer, and the relevant conversion page using descriptive anchors.")
        if weak_anchors: add(findings, rel, "info", "links.anchor", f"Found {weak_anchors} generic internal-link anchors.", "Replace generic anchors with text describing the destination topic.")
        if intent == "informational" and not ({"Article", "TechArticle", "FAQPage"} & set(schema_types)): add(findings, rel, "warn", "schema.intent", "Informational page lacks Article, TechArticle, or FAQPage schema.", "Add accurate structured data matching visible content.")
        if intent == "commercial" and not ({"Product", "Service", "ProfessionalService"} & set(schema_types)): add(findings, rel, "warn", "schema.intent", "Commercial page lacks Product or Service schema.", "Add accurate Product/Service schema with visible offer details.")
        if rel.startswith("blog/") and not parser.author: add(findings, rel, "warn", "trust.author", "Article has no machine-readable author signal.", "Add an author meta tag and visible byline linked to a real author profile.")
        if rel.startswith("blog/") and not parser.modified: add(findings, rel, "info", "freshness.modified", "Article has no machine-readable modified date.", "Expose dateModified when materially updating the article.")
        for img in parser.images:
            if not img["width"] or not img["height"]: add(findings, rel, "info", "cwv.cls", f"Image {img['src'] or '[inline]'} has no width/height attributes.", "Reserve image dimensions or an aspect-ratio box to reduce CLS.")
            if img["src"].lower().endswith((".png", ".jpg", ".jpeg")) and not img["src"].lower().startswith("data:"): add(findings, rel, "info", "cwv.image", f"Legacy image format used: {img['src']}.", "Generate AVIF/WebP variants and use responsive srcset while keeping a fallback.")
        blocking = [s for s in parser.scripts if s["src"] and not s["defer"] and not s["async"]]
        if blocking: add(findings, rel, "info", "cwv.inp", f"{len(blocking)} external scripts are not deferred.", "Defer non-critical JavaScript and remove unused interaction code.")

    for rel, record in records.items(): record["incoming_links"] = incoming[rel]
    for rel, record in records.items():
        if record["indexable"] and rel not in UTILITY and incoming[rel] == 0 and rel != "index.html":
            add(findings, rel, "error", "links.orphan", "No internal page links to this indexable URL.", "Link it from its pillar or remove/noindex it if it has no strategic purpose.")
    for cluster, members in clusters.items():
        indexable = [m for m in members if records[m]["indexable"] and m not in UTILITY]
        if len(indexable) >= 3 and not any(records[m]["internal_links"] >= 4 for m in indexable):
            add(findings, indexable[0], "warn", "cluster.pillar", f"Cluster '{cluster}' has {len(indexable)} pages but no obvious internally linked pillar.", "Designate one comprehensive pillar and link supporting pages bidirectionally.")

    missing_trust = sorted(TRUST_PATHS - set(inventory))
    if missing_trust: add(findings, "sitewide", "error", "trust.pages", f"Missing trust pages: {', '.join(missing_trust)}.", "Publish and link the required legal/trust pages.")

    counts = Counter(f["level"] for f in findings)
    score = max(0, 100 - counts["error"] * 4 - counts["warn"] - min(counts["info"] // 10, 10))
    report = {"generated_at": dt.datetime.now(dt.timezone.utc).isoformat(), "site": SITE, "score": score, "totals": {"pages": len(records), "errors": counts["error"], "warnings": counts["warn"], "info": counts["info"]}, "clusters": {k: sorted(v) for k, v in sorted(clusters.items())}, "pages": records, "findings": findings}

    print(f"Advanced SEO Growth: {score}/100 | {len(records)} pages | {counts['error']} errors | {counts['warn']} warnings | {counts['info']} info")
    for f in findings[:80]: print(f"[{f['level'].upper()}] {f['page']} {f['check']}: {f['message']}")
    if len(findings) > 80: print(f"... {len(findings)-80} additional findings; use --write for the complete backlog.")

    if args.write:
        OUT_DIR.mkdir(parents=True, exist_ok=True)
        (OUT_DIR / "advanced-growth.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        lines = ["# Advanced SEO Growth Backlog", "", f"Generated: {report['generated_at']}", "", f"**Score:** {score}/100 — {counts['error']} errors, {counts['warn']} warnings, {counts['info']} informational findings.", "", "## Priority Actions", ""]
        order = {"error": 0, "warn": 1, "info": 2}
        for f in sorted(findings, key=lambda x: (order[x["level"]], x["page"], x["check"])):
            lines.append(f"- **{f['level'].upper()} · `{f['page']}` · {f['check']}** — {f['message']} **Action:** {f['action']}")
        (OUT_DIR / "advanced-growth.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    return 1 if counts["error"] or (args.strict and counts["warn"]) else 0


if __name__ == "__main__":
    sys.exit(main())

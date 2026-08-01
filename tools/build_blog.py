#!/usr/bin/env python3
"""Build the ClearGlass Intelligence hub and feeds from the canonical post index."""

from __future__ import annotations

import argparse
import base64
import hashlib
import html
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from xml.etree import ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
BLOG = ROOT / "blog"
BASE = "https://www.clearglassinc.com"
STATUSES = ("LATEST INTELLIGENCE", "FIELD REPORT", "CYBER BRIEF", "STRATEGIC ANALYSIS")
REQUIRED_FIELDS = ("slug", "url", "title", "description", "date", "author", "category", "tags")
SLUG_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


def esc(value: object) -> str:
    return html.escape(str(value), quote=True)


def load_posts() -> list[dict]:
    payload = json.loads((BLOG / "posts.json").read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or not isinstance(payload.get("posts"), list):
        raise ValueError("blog/posts.json must contain a posts array")
    posts = []
    seen: set[str] = set()
    errors: list[str] = []
    for index, post in enumerate(payload["posts"]):
        if not isinstance(post, dict):
            errors.append(f"record {index}: expected object")
            continue
        missing = [field for field in REQUIRED_FIELDS if not post.get(field)]
        slug = post.get("slug", "")
        if missing:
            errors.append(f"record {index} ({slug or 'unknown'}): missing {', '.join(missing)}")
        elif not SLUG_PATTERN.fullmatch(slug) or slug in seen:
            errors.append(f"record {index}: invalid or duplicate slug {slug!r}")
        elif post["url"] != f"/blog/{slug}.html":
            errors.append(f"record {index} ({slug}): URL does not match canonical slug")
        else:
            try:
                datetime.fromisoformat(post["date"])
            except (TypeError, ValueError):
                errors.append(f"record {index} ({slug}): invalid ISO-8601 date")
                continue
            if not isinstance(post["tags"], list) or not all(isinstance(tag, str) and tag for tag in post["tags"]):
                errors.append(f"record {index} ({slug}): tags must be non-empty strings")
                continue
            seen.add(slug)
            if post.get("status", "published") == "published":
                posts.append(post)
    if errors:
        raise ValueError("Malformed blog records:\n- " + "\n- ".join(errors))
    return sorted(posts, key=lambda post: (post.get("date", ""), post["slug"]), reverse=True)


def label(post: dict, index: int) -> str:
    category = post.get("category", "").lower()
    if "cyber" in category or "security" in category:
        return "CYBER BRIEF"
    if post.get("featured") and index == 0:
        return "LATEST INTELLIGENCE"
    if "architecture" in category or post.get("readMinutes", 0) >= 20:
        return "STRATEGIC ANALYSIS"
    return "FIELD REPORT"


def card(post: dict, index: int) -> str:
    tags = " ".join(post.get("tags", []))
    topics = " ".join(post.get("topics", []))
    return f'''<article class="mission-card" data-article-card data-title="{esc(post['title'])}" data-summary="{esc(post.get('description', ''))}" data-category="{esc(post.get('category', 'Intelligence'))}" data-tags="{esc(tags)}" data-topics="{esc(topics)}" data-author="{esc(post.get('author', 'ClearGlass Inc.'))}" data-date="{esc(post.get('date', ''))}" data-minutes="{int(post.get('readMinutes') or 1)}" data-slug="{esc(post['slug'])}">
  <div class="mission-card__edge" aria-hidden="true"></div>
  <div class="mission-card__meta"><span class="mission-status">{label(post, index)}</span><time datetime="{esc(post.get('date', ''))}">{esc(post.get('date', 'Date unavailable'))}</time><span>{int(post.get('readMinutes') or 1)} min read</span></div>
  <h3><a href="{esc(post['url'])}">{esc(post['title'])}</a></h3>
  <p>{esc(post.get('description', ''))}</p>
  <div class="mission-card__tags"><button type="button" data-category-filter="{esc(post.get('category', 'Intelligence'))}">{esc(post.get('category', 'Intelligence'))}</button>{''.join(f'<button type="button" data-tag-filter="{esc(tag)}">#{esc(tag)}</button>' for tag in post.get('tags', [])[:3])}</div>
  <div class="mission-card__tools"><button type="button" data-bookmark>☆ Bookmark</button><button type="button" data-copy-link>Copy link</button><button type="button" data-share>Share</button></div>
  <details><summary>Expand preview</summary><p>By {esc(post.get('author', 'ClearGlass Inc.'))} · {esc(post.get('series', 'ClearGlass Intelligence'))}. Explore this briefing for the complete analysis, evidence, and implementation guidance.</p><a class="mission-action" href="{esc(post['url'])}">Open briefing <span aria-hidden="true">→</span></a></details>
</article>'''


def build_index(posts: list[dict]) -> str:
    featured = next((post for post in posts if post.get("featured")), posts[0])
    categories = sorted({post.get("category", "Intelligence") for post in posts})
    tags = sorted({tag for post in posts for tag in post.get("tags", [])})
    item_list = [{"@type": "ListItem", "position": i + 1, "url": BASE + post["url"]} for i, post in enumerate(posts)]
    schema = {"@context": "https://schema.org", "@graph": [
        {"@type": "Blog", "@id": f"{BASE}/blog/#blog", "name": "ClearGlass Intelligence", "url": f"{BASE}/blog/", "publisher": {"@type": "Organization", "name": "ClearGlass Inc."}},
        {"@type": "BreadcrumbList", "itemListElement": [{"@type": "ListItem", "position": 1, "name": "Home", "item": f"{BASE}/"}, {"@type": "ListItem", "position": 2, "name": "Intelligence", "item": f"{BASE}/blog/"}]},
        {"@type": "ItemList", "itemListOrder": "https://schema.org/ItemListOrderDescending", "itemListElement": item_list},
    ]}
    schema_json = json.dumps(schema, ensure_ascii=False).replace("</", "<\\/")
    schema_hash = base64.b64encode(hashlib.sha256(schema_json.encode("utf-8")).digest()).decode("ascii")
    related = ""
    current = BLOG / "index.html"
    if current.exists():
        text = current.read_text(encoding="utf-8")
        start = text.find("<!-- cg-related:start -->")
        end = text.find("<!-- cg-related:end -->")
        if start >= 0 and end >= start:
            related = text[start : end + len("<!-- cg-related:end -->")]
    return f'''<!doctype html>
<html lang="en"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>ClearGlass Intelligence | Cyber Defense, Governed AI &amp; OSINT</title>
<meta name="description" content="Mission-ready cyber intelligence, governed AI architecture, OSINT tradecraft, and strategic analysis from ClearGlass Inc.">
<meta name="robots" content="index,follow,max-image-preview:large"><meta name="author" content="ClearGlass Inc.">
<meta http-equiv="Content-Security-Policy" content="default-src 'self'; script-src 'self' 'sha256-{schema_hash}'; style-src 'self'; img-src 'self' data:; font-src 'self'; connect-src 'self'; object-src 'none'; base-uri 'self'; form-action 'self'; upgrade-insecure-requests">
<link rel="canonical" href="{BASE}/blog/"><link rel="alternate" type="application/rss+xml" title="ClearGlass Intelligence RSS" href="{BASE}/blog/feed.xml"><link rel="alternate" type="application/atom+xml" title="ClearGlass Intelligence Atom" href="{BASE}/blog/atom.xml"><link rel="alternate" type="application/feed+json" title="ClearGlass Intelligence JSON Feed" href="{BASE}/blog/feed.json">
<meta property="og:type" content="website"><meta property="og:site_name" content="ClearGlass Inc."><meta property="og:title" content="ClearGlass Intelligence"><meta property="og:description" content="Cyber defense, governed AI, OSINT, and strategic intelligence briefings."><meta property="og:url" content="{BASE}/blog/"><meta property="og:image" content="{BASE}/assets/images/clearglass-logo.png">
<meta name="twitter:card" content="summary_large_image"><meta name="twitter:title" content="ClearGlass Intelligence"><meta name="twitter:description" content="Mission-ready cyber intelligence and governed AI briefings."><meta name="twitter:image" content="{BASE}/assets/images/clearglass-logo.png">
<link rel="icon" href="/favicon.ico"><link rel="stylesheet" href="mission.css"><script type="application/ld+json">{schema_json}</script><script defer src="mission.js"></script>
</head><body class="cg-blog-mission" data-mission-page="hub" data-motion="balanced" data-view="briefing">
<a class="mission-skip" href="#mission-archive">Skip to intelligence archive</a><div class="mission-boot" data-mission-boot role="status"><span>ARTEMIS FAWL // KNOWLEDGE LINK ESTABLISHED</span></div><div class="mission-progress" data-reading-progress aria-hidden="true"></div><div class="mission-particles" aria-hidden="true"></div>
<header class="mission-header"><nav aria-label="Primary"><a class="mission-brand" href="/" aria-label="ClearGlass Inc. home"><img src="/assets/images/clearglass-logo.png" width="44" height="44" alt=""><span>ClearGlass <b>Intelligence</b></span></a><div><a href="#featured">Featured</a><a href="#mission-archive">Archive</a><a href="feed.xml">RSS</a><button type="button" data-open-palette aria-keyshortcuts="Control+K Meta+K">Command <kbd>⌘K</kbd></button></div></nav></header>
<main><section class="mission-hero" aria-labelledby="mission-title"><p class="mission-eyebrow">CLEARGLASS INC. // OPEN-SOURCE INTELLIGENCE DESK</p><h1 id="mission-title">Signals become <em>decision advantage.</em></h1><p>Production-grade reporting on cyber defense, governed autonomy, OSINT, and high-trust systems—published with provenance, accessible controls, and no fabricated metrics.</p><a class="mission-action" href="#mission-archive">Enter intelligence archive <span aria-hidden="true">↓</span></a></section>
<section class="mission-featured" id="featured" aria-labelledby="featured-title"><div><span class="mission-status">LATEST INTELLIGENCE</span><p class="mission-eyebrow">FEATURED INTELLIGENCE BRIEFING</p><h2 id="featured-title">{esc(featured['title'])}</h2><p>{esc(featured.get('description', ''))}</p><div class="mission-featured__meta"><span>{esc(featured.get('category', 'Intelligence'))}</span><span>{int(featured.get('readMinutes') or 1)} min read</span><time datetime="{esc(featured.get('date', ''))}">{esc(featured.get('date', 'Date unavailable'))}</time></div><a class="mission-action" href="{esc(featured['url'])}">Read featured briefing <span aria-hidden="true">→</span></a></div><div class="mission-radar" aria-hidden="true"><i></i><span>INTEL//VERIFIED_SOURCE</span></div></section>
<section class="mission-controls" aria-labelledby="archive-controls"><div><p class="mission-eyebrow">ARTEMIS KNOWLEDGE OPERATIONS</p><h2 id="archive-controls">Search and refine the archive.</h2></div><div class="mission-modebar" role="group" aria-label="Intelligence view"><button type="button" data-view="briefing" aria-pressed="true">Briefing</button><button type="button" data-view="signals">Signals</button><button type="button" data-view="archive">Archive</button><button type="button" data-view="focus">Focus</button><button type="button" data-view="graph">Graph</button></div><label class="mission-search"><span>Search titles, summaries, categories, tags, dates, and authors</span><input type="search" data-search autocomplete="off" placeholder="Search intelligence…"></label><div class="mission-selects"><label>Category<select data-category><option value="">All categories</option>{''.join(f'<option>{esc(category)}</option>' for category in categories)}</select></label><label>Tag<select data-tag><option value="">All tags</option>{''.join(f'<option>{esc(tag)}</option>' for tag in tags)}</select></label><label>Sort<select data-sort><option value="newest">Newest</option><option value="oldest">Oldest</option><option value="reading-time">Reading time</option><option value="relevance">Relevance</option></select></label><label>Animation<select data-motion><option value="full">Full</option><option value="balanced" selected>Balanced</option><option value="minimal">Minimal</option></select></label></div><div class="mission-utility"><button type="button" data-saved-toggle>Saved articles</button><button type="button" data-save-view>Save view</button><button type="button" data-share-view>Share view</button><button type="button" data-reset>Clear controls</button></div><div class="mission-chips" data-active-chips aria-label="Active filters"></div><div class="mission-state" data-state role="status">Loading published intelligence…</div></section>
<section class="mission-archive" id="mission-archive" aria-labelledby="archive-title"><div class="mission-section-head"><div><p class="mission-eyebrow">PUBLISHED ARCHIVE</p><h2 id="archive-title">All intelligence briefings</h2></div><button type="button" data-history-toggle>Reading history</button></div><div class="mission-grid" data-grid>{''.join(card(post, i) for i, post in enumerate(posts))}</div><div class="mission-graph" data-graph hidden><h3>Category and tag relationship index</h3><p>Relationships below are derived only from published article metadata.</p><table><thead><tr><th>Category</th><th>Tag</th><th>Briefings</th></tr></thead><tbody data-graph-rows></tbody></table></div><div class="mission-empty" data-empty hidden><h3>No intelligence matched.</h3><p>Clear the search or filters to restore the complete, indexable archive.</p><button type="button" data-reset>Reset query</button></div><nav class="mission-pagination" aria-label="Article pagination"><button type="button" data-previous>Previous</button><span data-page-status></span><button type="button" data-next>Next</button></nav><noscript><p>JavaScript is optional: every article remains present and linked in this document. Search, sorting, and pagination require JavaScript.</p></noscript></section>
<section class="mission-newsletter" aria-labelledby="newsletter-title"><div><p class="mission-eyebrow">TRANSMISSION CONFIGURATION</p><h2 id="newsletter-title">Intelligence briefing delivery</h2><p>No verified newsletter provider is configured. Subscription collection is inactive; no address will be captured or transmitted.</p></div><button type="button" disabled>INACTIVE — PROVIDER REQUIRED</button></section></main>
<footer><a href="/">ClearGlass Inc.</a><span>Clarity Is Power.</span><a href="feed.xml">RSS</a><a href="feed.json">JSON Feed</a></footer>
<dialog class="mission-palette" data-palette aria-labelledby="palette-title"><form method="dialog"><div><h2 id="palette-title">Command palette</h2><button aria-label="Close command palette">×</button></div><input type="search" data-palette-search placeholder="Navigate or find intelligence…" autocomplete="off"><ul data-palette-results></ul><p><kbd>↑</kbd><kbd>↓</kbd> navigate · <kbd>Enter</kbd> open · <kbd>Esc</kbd> close</p></form></dialog><div class="mission-toast" data-toast role="status" aria-live="polite"></div>
{related}</body></html>'''


def build_rss(posts: list[dict]) -> str:
    rss = ET.Element("rss", version="2.0")
    channel = ET.SubElement(rss, "channel")
    for key, value in (("title", "ClearGlass Intelligence"), ("link", f"{BASE}/blog/"), ("description", "Cyber defense, governed AI, OSINT, and strategic intelligence briefings."), ("language", "en-ca")):
        ET.SubElement(channel, key).text = value
    for post in posts:
        item = ET.SubElement(channel, "item")
        for key, value in (("title", post["title"]), ("link", BASE + post["url"]), ("guid", BASE + post["url"]), ("description", post.get("description", ""))):
            ET.SubElement(item, key).text = value
        if post.get("date"):
            ET.SubElement(item, "pubDate").text = datetime.fromisoformat(post["date"]).replace(tzinfo=timezone.utc).strftime("%a, %d %b %Y %H:%M:%S %z")
        for tag in post.get("tags", []):
            ET.SubElement(item, "category").text = tag
    ET.indent(rss)
    return '<?xml version="1.0" encoding="utf-8"?>\n' + ET.tostring(rss, encoding="unicode") + "\n"


def build_json_feed(posts: list[dict]) -> str:
    feed = {"version": "https://jsonfeed.org/version/1.1", "title": "ClearGlass Intelligence", "home_page_url": f"{BASE}/blog/", "feed_url": f"{BASE}/blog/feed.json", "items": [{"id": BASE + p["url"], "url": BASE + p["url"], "title": p["title"], "summary": p.get("description", ""), **({"date_published": p["date"] + "T00:00:00Z"} if p.get("date") else {}), "authors": [{"name": p.get("author", "ClearGlass Inc.")}], "tags": p.get("tags", [])} for p in posts]}
    return json.dumps(feed, ensure_ascii=False, indent=2) + "\n"


def build_atom(posts: list[dict]) -> str:
    atom = ET.Element("feed", xmlns="http://www.w3.org/2005/Atom")
    ET.SubElement(atom, "title").text = "ClearGlass Intelligence"
    ET.SubElement(atom, "id").text = f"{BASE}/blog/"
    ET.SubElement(atom, "link", href=f"{BASE}/blog/atom.xml", rel="self")
    ET.SubElement(atom, "link", href=f"{BASE}/blog/")
    latest = max((post["date"] for post in posts), default="1970-01-01")
    ET.SubElement(atom, "updated").text = latest + "T00:00:00Z"
    for post in posts:
        entry = ET.SubElement(atom, "entry")
        ET.SubElement(entry, "id").text = BASE + post["url"]
        ET.SubElement(entry, "title").text = post["title"]
        ET.SubElement(entry, "link", href=BASE + post["url"])
        ET.SubElement(entry, "updated").text = post["date"] + "T00:00:00Z"
        ET.SubElement(entry, "summary").text = post["description"]
        author = ET.SubElement(entry, "author")
        ET.SubElement(author, "name").text = post["author"]
    ET.indent(atom)
    return '<?xml version="1.0" encoding="utf-8"?>\n' + ET.tostring(atom, encoding="unicode") + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    posts = load_posts()
    outputs = {BLOG / "index.html": build_index(posts), BLOG / "feed.xml": build_rss(posts), BLOG / "atom.xml": build_atom(posts), BLOG / "feed.json": build_json_feed(posts)}
    stale = [path for path, content in outputs.items() if not path.exists() or path.read_text(encoding="utf-8") != content]
    if args.check:
        if stale:
            print("Stale blog artifacts: " + ", ".join(str(path.relative_to(ROOT)) for path in stale))
            return 1
        print(f"Blog artifacts current ({len(posts)} published articles)")
        return 0
    for path, content in outputs.items():
        path.write_text(content, encoding="utf-8")
    print(f"Built blog hub and feeds from {len(posts)} published articles")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

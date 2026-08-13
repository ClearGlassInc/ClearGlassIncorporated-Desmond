#!/usr/bin/env python3
"""ClearGlass Interface System — site-wide adoption gate.

The static site is ~96 hand-authored pages that accumulated over time, so the
shared visual language only holds if something checks that every page actually
*loads* it. This tool is that check. It enforces four contracts:

  1. **Design system**  every public page links ``assets/css/cg-design-system.css``
     (the homepage-derived token + component layer).
  2. **Global chrome**  every public page loads ``nav.js``, which injects the one
     navigation, the focus-managed mobile drawer, and the command palette.
  3. **Keyboard contract**  every public page loads ``cg-a11y.js``, which
     guarantees a bypass link and ``aria-current`` regardless of
     which of the site's two navigation systems the page runs — pages loading
     ``control-surface.js`` suppress ``nav.js`` on purpose, and would otherwise
     ship with no bypass link at all.
  4. **Social metadata**  every indexable page carries a Twitter/X card, so a
     shared link renders as a card instead of a bare URL.

Nothing here invents content: the Twitter card is derived from metadata the page
already declares (``og:*`` first, then ``<title>``/``<meta name=description>``).
A page with no description to borrow is reported, never given filler text.

    python3 tools/design_system.py            # apply fixes in place
    python3 tools/design_system.py --check    # exit 1 if any page is stale (CI)
    python3 tools/design_system.py --report   # write the route inventory

stdlib only, idempotent, and safe to re-run.
"""
from __future__ import annotations

import argparse
import html
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REPORT_PATH = ROOT / "DESIGN_SYSTEM_AUDIT.md"

DESIGN_SYSTEM_CSS = "/assets/css/cg-design-system.css"
GLOBAL_NAV_JS = "/nav.js"
A11Y_JS = "/cg-a11y.js"

CSS_LINK = f'<link rel="stylesheet" href="{DESIGN_SYSTEM_CSS}"/>'
NAV_TAG = f'<script defer src="{GLOBAL_NAV_JS}"></script>'
A11Y_TAG = f'<script defer src="{A11Y_JS}"></script>'

# Surfaces deliberately outside the unified public shell. Each entry pairs the
# path with the reason, so an exemption has to be argued for rather than
# accumulated silently.
EXEMPT: dict[str, str] = {
    "index.html": "homepage is the design source of truth and ships its own nav",
    "loader.html": "boot shim; injecting chrome would flash a nav mid-redirect",
    "cg-loader.html": "branded loading surface, noindex",
    "404.html": "route-recovery page, noindex",
    "offline.html": "service-worker fallback; must not depend on network assets",
    "header-mockup-2040.html": "noindex design prototype studied in isolation",
    "seo-dashboard.html": "noindex internal reporting surface",
    "threads.html": "noindex internal surface",
    "platform-command-center.html": "noindex private operations console",
    "mission-control.html": "noindex private operations console",
    "sentinel/ARTEMIS_FAWL_COMMAND_SURFACE.html": "noindex private governance console",
    "sentinel/PHOENIX_DASHBOARD.html": "noindex private recovery console",
    "google23RWyXWkoxqgArev8achU8IfVxYC5EIUAYBsuTYKLFM.html": "Google ownership verification artifact",
}

# Pages that carry a bespoke full-viewport visual study. They keep the design
# system (tokens) but opt out of the injected top bar, which would overlap a
# fixed HUD. Listed separately so the CSS contract still applies to them.
NAV_EXEMPT: dict[str, str] = {
    "web-design.html": "full-bleed design study with its own fixed chrome",
}

TITLE_RE = re.compile(r"<title[^>]*>(.*?)</title>", re.I | re.S)
META_RE = re.compile(
    r'<meta[^>]+(?:name|property)=["\']{key}["\'][^>]*content=["\'](.*?)["\']',
    re.I | re.S,
)
NOINDEX_RE = re.compile(r'content=["\'][^"\']*noindex', re.I)


def pages() -> list[Path]:
    """Every static page in the site, in a stable order."""
    found: list[Path] = sorted(ROOT.glob("*.html"))
    for sub in ("offers", "sentinel", "blog", "products"):
        found += sorted((ROOT / sub).rglob("*.html"))
    return [p for p in found if p.is_file()]


def meta(text: str, key: str) -> str:
    match = re.search(META_RE.pattern.format(key=re.escape(key)), text, re.I | re.S)
    return match.group(1).strip() if match else ""


def title_of(text: str) -> str:
    match = TITLE_RE.search(text)
    return html.unescape(match.group(1)).strip() if match else ""


def is_noindex(text: str) -> bool:
    for tag in re.findall(r"<meta[^>]+robots[^>]*>", text, re.I):
        if NOINDEX_RE.search(tag):
            return True
    return False


def rel_path(page: Path) -> str:
    return page.relative_to(ROOT).as_posix()


def needs_css(text: str) -> bool:
    return "cg-design-system.css" not in text


def needs_nav(text: str) -> bool:
    return not re.search(r'src=["\'][^"\']*\bnav\.js', text)


def needs_a11y(text: str) -> bool:
    return "cg-a11y.js" not in text


def needs_twitter(text: str) -> bool:
    return not re.search(r'name=["\']twitter:card', text, re.I)


def insert_before_head_close(text: str, snippet: str) -> str:
    """Append into <head>, keeping the design system last so it wins cascade."""
    idx = text.lower().rfind("</head>")
    if idx == -1:
        return text
    return text[:idx] + snippet + "\n" + text[idx:]


def insert_before_body_close(text: str, snippet: str) -> str:
    idx = text.lower().rfind("</body>")
    if idx == -1:
        return text
    return text[:idx] + snippet + "\n" + text[idx:]


def twitter_block(text: str) -> str:
    """Build a Twitter card from metadata the page already declares.

    Returns "" when the page has nothing to borrow — a missing card is a
    reportable gap, not a licence to invent a description.
    """
    card_title = meta(text, "og:title") or title_of(text)
    card_desc = meta(text, "og:description") or meta(text, "description")
    if not card_title or not card_desc:
        return ""
    image = meta(text, "og:image")
    lines = [
        '<meta name="twitter:card" content="summary_large_image"/>',
        f'<meta name="twitter:title" content="{html.escape(card_title, quote=True)}"/>',
        f'<meta name="twitter:description" content="{html.escape(card_desc, quote=True)}"/>',
    ]
    if image:
        lines.append(f'<meta name="twitter:image" content="{html.escape(image, quote=True)}"/>')
    return "\n".join(lines)


def audit_page(page: Path) -> dict:
    text = page.read_text(encoding="utf-8", errors="replace")
    path = rel_path(page)
    exempt = path in EXEMPT
    nav_exempt = exempt or path in NAV_EXEMPT
    noindex = is_noindex(text)
    return {
        "path": path,
        "title": title_of(text),
        "noindex": noindex,
        "exempt": exempt,
        "nav_exempt": nav_exempt,
        "missing_css": (not exempt) and needs_css(text),
        "missing_nav": (not nav_exempt) and needs_nav(text),
        # The keyboard contract applies even where the top bar does not: a page
        # with a bespoke HUD still owes the user a bypass link.
        "missing_a11y": (not exempt) and needs_a11y(text),
        # Exempt surfaces (loaders, verification artifacts, private consoles)
        # are never shared as links, so a social card would be noise.
        "missing_twitter": (not noindex) and (not exempt) and needs_twitter(text),
        "can_build_twitter": bool(twitter_block(text)),
        "has_canonical": bool(re.search(r'rel=["\']canonical', text, re.I)),
        "has_og": bool(meta(text, "og:title")),
        "bytes": len(text),
    }


def fix_page(page: Path) -> list[str]:
    """Apply the three contracts to one page. Returns the list of changes."""
    text = page.read_text(encoding="utf-8", errors="replace")
    original = text
    path = rel_path(page)
    changes: list[str] = []

    if path not in EXEMPT and needs_css(text):
        text = insert_before_head_close(text, CSS_LINK)
        changes.append("design-system css")

    if path not in EXEMPT and path not in NAV_EXEMPT and needs_nav(text):
        text = insert_before_body_close(text, NAV_TAG)
        changes.append("global nav")

    if path not in EXEMPT and needs_a11y(text):
        text = insert_before_body_close(text, A11Y_TAG)
        changes.append("a11y contract")

    if path not in EXEMPT and not is_noindex(text) and needs_twitter(text):
        block = twitter_block(text)
        if block:
            text = insert_before_head_close(text, block)
            changes.append("twitter card")

    if text != original:
        page.write_text(text, encoding="utf-8")
    return changes


def write_report(rows: list[dict]) -> None:
    total = len(rows)
    public = [r for r in rows if not r["noindex"] and not r["exempt"]]
    lines = [
        "# ClearGlass Interface System — route inventory",
        "",
        "Generated by `python3 tools/design_system.py --report`. Do not hand-edit.",
        "",
        f"- **Total pages:** {total}",
        f"- **Public indexable pages:** {len(public)}",
        f"- **Exempt surfaces:** {len(EXEMPT) + len(NAV_EXEMPT)}",
        "",
        "## Contract coverage",
        "",
        "| Route | Design system | Global nav | A11y contract | Twitter card | Canonical | Indexable |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]

    def mark(missing: bool, exempt: bool) -> str:
        if exempt:
            return "exempt"
        return "no" if missing else "yes"

    for r in sorted(rows, key=lambda x: x["path"]):
        lines.append(
            "| `{path}` | {css} | {nav} | {a11y} | {tw} | {canon} | {idx} |".format(
                path=r["path"],
                css=mark(r["missing_css"], r["exempt"]),
                nav=mark(r["missing_nav"], r["nav_exempt"]),
                a11y=mark(r["missing_a11y"], r["exempt"]),
                tw="n/a" if r["noindex"] else mark(r["missing_twitter"], False),
                canon="yes" if r["has_canonical"] else "no",
                idx="no" if r["noindex"] else "yes",
            )
        )

    lines += ["", "## Exempt surfaces and why", ""]
    for path, reason in sorted({**EXEMPT, **NAV_EXEMPT}.items()):
        scope = "full" if path in EXEMPT else "nav only"
        lines.append(f"- `{path}` — _{scope}_ — {reason}")
    lines.append("")

    REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="exit 1 if any page is stale")
    parser.add_argument("--report", action="store_true", help="write the route inventory")
    args = parser.parse_args(argv)

    all_pages = pages()

    if args.check:
        rows = [audit_page(p) for p in all_pages]
        stale = [
            r
            for r in rows
            if r["missing_css"]
            or r["missing_nav"]
            or r["missing_a11y"]
            or (r["missing_twitter"] and r["can_build_twitter"])
        ]
        if stale:
            print("Design system out of date on the following routes:")
            for r in stale:
                gaps = []
                if r["missing_css"]:
                    gaps.append("design-system css")
                if r["missing_nav"]:
                    gaps.append("global nav")
                if r["missing_a11y"]:
                    gaps.append("a11y contract")
                if r["missing_twitter"] and r["can_build_twitter"]:
                    gaps.append("twitter card")
                print(f"  {r['path']}: missing {', '.join(gaps)}")
            print("\nRun: python3 tools/design_system.py")
            return 1
        print(f"Design system current across {len(rows)} routes.")
        return 0

    touched = 0
    for page in all_pages:
        changes = fix_page(page)
        if changes:
            touched += 1
            print(f"  {rel_path(page)}: +{', +'.join(changes)}")

    rows = [audit_page(p) for p in all_pages]
    write_report(rows)
    print(f"\nUpdated {touched} of {len(all_pages)} routes. Report: {REPORT_PATH.name}")

    unfixable = [r for r in rows if r["missing_twitter"] and not r["can_build_twitter"]]
    if unfixable:
        print("\nNeeds a human-written description before a card can be generated:")
        for r in unfixable:
            print(f"  {r['path']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

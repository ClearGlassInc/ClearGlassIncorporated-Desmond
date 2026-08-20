"""Structural-completeness invariants for every indexable page.

A botched automated edit once truncated `index.html` from 1,257 lines to 95,
deleting the entire document body. Nine unrelated content assertions went red,
but none of them named the actual fault, so the regression read as nine
separate content bugs rather than one destroyed file.

These checks fail with the root cause instead: the page is not a whole HTML
document, or its skip link points at a landmark that no longer exists.
"""

from __future__ import annotations

import importlib.util
from html.parser import HTMLParser
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("internal_links", ROOT / "tools/internal_links.py")
assert SPEC and SPEC.loader
internal_links = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(internal_links)


class LandmarkParser(HTMLParser):
    """Collects element ids and the targets of in-page skip links."""

    def __init__(self) -> None:
        super().__init__()
        self.ids: set[str] = set()
        self.skip_targets: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attributes = dict(attrs)
        if element_id := attributes.get("id"):
            self.ids.add(element_id)
        if tag != "a":
            return
        href = attributes.get("href") or ""
        if not href.startswith("#") or len(href) == 1:
            return
        # Skip links are the first tab stop and must reach a real landmark.
        marker = f"{attributes.get('class') or ''} {attributes.get('id') or ''}"
        if "skip" in marker:
            self.skip_targets.append(href[1:])


def read_page(page: str) -> str:
    return (ROOT / page).read_text(encoding="utf-8", errors="surrogateescape")


def test_every_indexable_page_is_a_complete_document() -> None:
    """Guards against truncated writes that leave a page without its body."""
    incomplete: list[str] = []
    for page in internal_links.PAGES:
        path = ROOT / page
        if not path.exists():
            incomplete.append(f"{page}: file is missing")
            continue
        document = read_page(page).lower()
        missing = [tag for tag in ("<body", "</body>", "</html>") if tag not in document]
        if missing:
            incomplete.append(f"{page}: missing {', '.join(missing)}")
    assert not incomplete, "Structurally incomplete pages: " + "; ".join(incomplete)


def test_skip_link_targets_resolve() -> None:
    """A skip link pointing at a removed landmark breaks keyboard navigation."""
    broken: list[str] = []
    for page in internal_links.PAGES:
        parser = LandmarkParser()
        parser.feed(read_page(page))
        broken.extend(
            f"{page} -> #{target}"
            for target in parser.skip_targets
            if target not in parser.ids
        )
    assert not broken, "Skip links with no matching element: " + "; ".join(broken)

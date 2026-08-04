# Copyright (c) 2024-2026 ClearGlass Inc. All Rights Reserved.
# Proprietary and confidential. See LICENSE for terms.
"""The tab-icon block must reach every page without ever rewriting one."""
from __future__ import annotations

import pathlib

from tools.tab_icons import (
    SEAL,
    TAGS,
    apply,
    head_span,
    iter_pages,
    missing_tags,
    plan,
)

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent

BARE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"/>
<title>t</title>
</head>
<body></body>
</html>
"""


def full_head(body: str = "") -> str:
    tags = "\n".join(markup for _, markup in TAGS)
    return (
        '<!DOCTYPE html>\n<html lang="en">\n<head>\n<meta charset="UTF-8"/>\n'
        f"{tags}\n</head>\n<body>{body}</body>\n</html>\n"
    )


# ── detection ─────────────────────────────────────────────────────────────────

def test_a_complete_head_is_left_alone():
    assert missing_tags(full_head()) == []
    assert plan(full_head()) is None


def test_a_bare_head_is_missing_every_tag():
    assert len(missing_tags(BARE)) == len(TAGS)


def test_probes_ignore_attribute_order():
    head = '<link href="/x.png" sizes="any" rel="icon">'
    assert TAGS[0][0].search(head)


def test_single_quotes_count_as_declared():
    assert TAGS[3][0].search("<link rel='apple-touch-icon' href='/x.png'>")


def test_body_copy_does_not_suppress_a_real_tag():
    """Detection reads the <head> only, so prose never fakes a declaration."""
    page = BARE.replace("<body>", '<body>we set rel="mask-icon" on every page')
    _, added = apply(page)
    assert any("mask-icon" in tag for tag in added)


# ── additive guarantee ────────────────────────────────────────────────────────

def test_nothing_is_ever_removed():
    updated, added = apply(BARE)
    assert added
    for line in BARE.splitlines():
        assert line in updated


def test_a_page_specific_theme_color_survives():
    page = BARE.replace(
        "<title>t</title>", '<meta name="theme-color" content="#05070d"/>\n<title>t</title>'
    )
    updated, added = apply(page)
    assert '<meta name="theme-color" content="#05070d"/>' in updated
    assert 'content="#07111f">' not in "".join(
        t for t in added if "theme-color" in t
    )


def test_an_existing_icon_href_is_not_rewritten():
    page = BARE.replace(
        "<title>", '<link rel="icon" type="image/png" href="/legacy.png">\n<title>'
    )
    updated, _ = apply(page)
    assert '<link rel="icon" type="image/png" href="/legacy.png">' in updated


def test_running_twice_changes_nothing():
    once, added = apply(BARE)
    assert added
    twice, again = apply(once)
    assert again == []
    assert twice == once


# ── placement ─────────────────────────────────────────────────────────────────

def test_charset_stays_ahead_of_the_block():
    updated, _ = apply(BARE)
    assert updated.index("charset") < updated.index(SEAL)


def test_charset_remains_inside_the_first_1024_bytes():
    updated, _ = apply(BARE)
    assert updated.encode("utf-8").index(b"charset") < 1024


def test_tags_are_appended_to_an_existing_block():
    page = BARE.replace(
        "<title>", '<link rel="apple-touch-icon" href="/x.png">\n<title>'
    )
    updated, _ = apply(page)
    anchor = updated.index('rel="apple-touch-icon"')
    assert updated.index('rel="mask-icon"') > anchor
    # …and stays above the rest of the head rather than drifting into <body>.
    assert updated.index('rel="mask-icon"') < updated.index("<title>")


def test_insertions_land_inside_the_head():
    updated, _ = apply(BARE)
    start, end = head_span(updated)
    assert start < updated.index(SEAL) < end


# ── files that are not pages ──────────────────────────────────────────────────

def test_a_headless_file_is_skipped():
    """Google's verification token is .html but must stay byte-exact."""
    token = "google-site-verification: 23RWyXWkoxqgArev8achU8IfVxYC5EIUAYBsuTYKLFM\n"
    assert head_span(token) is None
    updated, added = apply(token)
    assert (updated, added) == (token, [])


# ── the live site ─────────────────────────────────────────────────────────────

def test_every_page_in_the_repo_is_complete():
    incomplete = [
        str(p.relative_to(REPO_ROOT))
        for p in iter_pages(REPO_ROOT)
        if apply(p.read_text(encoding="utf-8"))[1]
    ]
    assert incomplete == [], f"run python3 tools/tab_icons.py: {incomplete}"


def test_the_seal_asset_the_tags_point_at_exists():
    assert (REPO_ROOT / SEAL.lstrip("/")).is_file()


def test_referenced_icon_assets_exist():
    for rel in ("safari-pinned-tab.svg", "site.webmanifest",
                "icon-192.png", "browserconfig.xml"):
        assert (REPO_ROOT / rel).is_file(), rel

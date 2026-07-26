# Copyright (c) 2024-2026 ClearGlass Inc. All Rights Reserved.
# Proprietary and confidential. See LICENSE for terms.
"""Regression tests for scripts/site_reliability_audit.py."""
from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

from scripts import site_reliability_audit as audit


def test_iter_repo_html_files_ignores_dependency_and_build_dirs(tmp_path: Path) -> None:
    """Generated dependency/build HTML must not create false audit failures."""

    (tmp_path / "index.html").write_text("<html></html>")
    ignored_html = tmp_path / "app" / "node_modules" / "pkg" / "broken.html"
    ignored_html.parent.mkdir(parents=True)
    ignored_html.write_text('<script src="/_next/static/chunks/missing.js"></script>')
    next_html = tmp_path / ".next" / "server" / "app.html"
    next_html.parent.mkdir(parents=True)
    next_html.write_text('<link href="/_next/static/chunks/missing.css" rel="stylesheet">')

    with patch.object(audit, "REPO_ROOT", tmp_path):
        assert audit.iter_repo_html_files() == [tmp_path / "index.html"]


def test_check_links_validates_fragments_and_directory_routes(tmp_path: Path) -> None:
    (tmp_path / "index.html").write_text(
        '<a href="/docs/#overview">valid</a><a href="#missing">broken</a>'
    )
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "index.html").write_text('<section id="overview"></section>')

    with patch.object(audit, "REPO_ROOT", tmp_path):
        issues = audit.check_links()

    assert [issue.message for issue in issues] == [
        "Missing fragment target index.html:1 -> #missing"
    ]


def test_check_sitemap_requires_a_canonical_existing_page(tmp_path: Path) -> None:
    (tmp_path / "sitemap.xml").write_text(
        '<?xml version="1.0"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
        '<url><loc>https://www.clearglassinc.com/missing.html</loc></url></urlset>'
    )

    with patch.object(audit, "REPO_ROOT", tmp_path):
        issues = audit.check_sitemap()

    assert "has no published file" in issues[0].message


def test_check_robots_rejects_malformed_and_missing_sitemap(tmp_path: Path) -> None:
    (tmp_path / "robots.txt").write_text(
        "User-agent: *\nAllow: /\n</content>\n"
        "Sitemap: https://www.clearglassinc.com/missing.xml\n"
    )

    with patch.object(audit, "REPO_ROOT", tmp_path):
        issues = audit.check_robots()

    assert [issue.message for issue in issues] == [
        "Malformed robots.txt directive at line 3: </content>",
        "robots.txt declares a missing sitemap: https://www.clearglassinc.com/missing.xml",
    ]

from pathlib import Path

import pytest

from scripts import live_sitemap_crawl as crawler


def test_sitemap_urls_combines_and_deduplicates_files(tmp_path: Path) -> None:
    body = """<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
<url><loc>https://www.clearglassinc.com/</loc></url></urlset>"""
    (tmp_path / "sitemap.xml").write_text(body, encoding="utf-8")
    (tmp_path / "sitemap-extra.xml").write_text(body, encoding="utf-8")
    assert crawler.sitemap_urls(tmp_path) == ["https://www.clearglassinc.com/"]


def test_sitemap_urls_rejects_noncanonical_origin(tmp_path: Path) -> None:
    (tmp_path / "sitemap.xml").write_text(
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"><url>'
        '<loc>http://example.com/</loc></url></urlset>',
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="non-canonical"):
        crawler.sitemap_urls(tmp_path)


def test_result_requires_2xx_html_on_canonical_host() -> None:
    assert crawler.Result(
        "https://www.clearglassinc.com/", 200, "https://www.clearglassinc.com/", "text/html; charset=utf-8", None
    ).healthy
    assert not crawler.Result(
        "https://www.clearglassinc.com/", 200, "https://example.com/", "text/html", None
    ).healthy
    assert not crawler.Result(
        "https://www.clearglassinc.com/", 404, "https://www.clearglassinc.com/", "text/html", "not found"
    ).healthy

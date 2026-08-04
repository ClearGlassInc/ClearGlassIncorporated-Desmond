from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SEAL = "assets/images/clearglass-holographic-seal.png"


def test_home_and_blog_feature_the_holographic_seal() -> None:
    homepage = (ROOT / "index.html").read_text(encoding="utf-8")
    blog = (ROOT / "blog" / "index.html").read_text(encoding="utf-8")

    assert homepage.count(SEAL) >= 4
    assert 'class="hero-seal"' in homepage
    assert blog.count(f"../{SEAL}") >= 2
    assert 'class="radar-seal"' in blog
    assert "prefers-reduced-motion:reduce" in homepage


def test_every_public_html_page_declares_a_tab_icon() -> None:
    excluded = {"google23RWyXWkoxqgArev8achU8IfVxYC5EIUAYBsuTYKLFM.html"}
    public_pages = [
        page
        for page in ROOT.rglob("*.html")
        if "node_modules" not in page.parts and page.name not in excluded
    ]

    missing = [
        str(page.relative_to(ROOT))
        for page in public_pages
        if 'href="/assets/images/clearglass-holographic-seal.png"' not in page.read_text(encoding="utf-8", errors="ignore")
    ]
    assert not missing, f"Public pages without the canonical holographic desktop tab logo: {missing}"


def test_tab_icon_assets_and_manifest_exist() -> None:
    for asset in (
        "logo.png",
        "favicon-16.png",
        "favicon-32.png",
        "apple-touch-icon.png",
        "safari-pinned-tab.svg",
        "site.webmanifest",
    ):
        assert (ROOT / asset).is_file(), asset



def test_desktop_tab_logo_uses_the_existing_holographic_asset() -> None:
    seal = ROOT / SEAL
    assert seal.is_file()

    manifest = (ROOT / "site.webmanifest").read_text(encoding="utf-8")
    assert '"src": "/assets/images/clearglass-holographic-seal.png"' in manifest
    assert '"sizes": "512x512"' in manifest

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_platform_static_assets_exist():
    for path in (
        "minerals-platform.html",
        "minerals-platform.css",
        "minerals-platform.js",
        "docs/minerals-platform-architecture.md",
        "data/minerals/platform/config.json",
        "data/minerals/platform/demo.json",
    ):
        assert (ROOT / path).is_file(), path


def test_demo_dataset_is_unambiguously_synthetic():
    demo = json.loads(read("data/minerals/platform/demo.json"))
    assert demo["demo"] is True
    assert "SYNTHETIC" in demo["warning"]
    assert all(row.get("demo") is True or row.get("confidence") == "DEMO" for row in demo["entities"])
    assert all(row.get("demo") is True for row in demo["flows"])
    assert all(row.get("demo") is True for row in demo["events"])


def test_platform_defaults_to_verified_mode():
    config = json.loads(read("data/minerals/platform/config.json"))
    assert config["default_mode"] == "verified"
    assert config["product"]["route"] == "/minerals-platform.html"


def test_platform_runtime_preserves_demo_live_separation():
    js = read("minerals-platform.js")
    assert 'state = { mode:"verified"' in js
    assert "SYNTHETIC DEMO" in js
    assert "No source-grounded geospatial entities" in js
    assert "No licensed price benchmark" in js


def test_product_catalog_and_nav_expose_platform():
    catalog = json.loads(read("data/products.json"))
    matches = [p for p in catalog["products"] if p.get("slug") == "minerals-intelligence-platform"]
    assert len(matches) == 1
    assert matches[0]["productUrl"] == "/minerals-platform.html"
    nav = read("nav.js")
    assert "Minerals Intelligence Platform" in nav
    assert "minerals-platform.html" in nav


def test_sitemap_contains_platform_route():
    sitemap = read("sitemap.xml")
    assert "https://www.clearglassinc.com/minerals-platform.html" in sitemap

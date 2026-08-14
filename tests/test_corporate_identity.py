"""Regression gates for the public ClearGlass corporate identity."""
from __future__ import annotations

import importlib.util
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "corporate_identity", ROOT / "tools" / "corporate_identity.py"
)
assert SPEC and SPEC.loader
corporate_identity = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(corporate_identity)


def test_identity_source_is_complete() -> None:
    identity = json.loads(
        (ROOT / "data" / "corporate-identity.json").read_text(encoding="utf-8")
    )
    assert identity["organization"]["email"] == "desmond@clearglassinc.com"
    assert identity["organization"]["telephone"] == "+1-289-707-0269"
    assert identity["organization"]["location"] == {
        "locality": "Burlington",
        "region": "Ontario",
        "country": "Canada",
    }
    assert identity["founder"]["jobTitle"] == "Founder & Software Architect"
    assert identity["organization"]["sameAs"] == [
        "https://github.com/ClearGlassInc",
        "https://www.linkedin.com/company/cleaglassinc",
    ]


def test_public_identity_is_synchronized() -> None:
    assert corporate_identity.stale_files() == [], (
        "Run `python3 tools/corporate_identity.py` and commit the resulting public-site changes"
    )


def test_homepage_schema_uses_canonical_identity() -> None:
    homepage = (ROOT / "index.html").read_text(encoding="utf-8")
    identity = json.loads(
        (ROOT / "data" / "corporate-identity.json").read_text(encoding="utf-8")
    )
    for expected in (
        '"legalName":"ClearGlass Inc."',
        '"telephone":"+1-289-707-0269"',
        '"email":"desmond@clearglassinc.com"',
        '"jobTitle":"Founder & Software Architect"',
        '"addressLocality":"Burlington"',
        'https://www.linkedin.com/company/cleaglassinc',
    ):
        assert expected in homepage
    block = re.search(
        r'<script type="application/ld\+json">(.*?)</script>', homepage, re.DOTALL
    )
    assert block
    graph = json.loads(block.group(1))["@graph"]
    organization = next(node for node in graph if node.get("@type") == "Organization")
    assert organization["sameAs"] == identity["organization"]["sameAs"]


def test_standalone_schema_uses_only_canonical_profiles() -> None:
    identity = json.loads(
        (ROOT / "data" / "corporate-identity.json").read_text(encoding="utf-8")
    )
    graph = json.loads((ROOT / "schema.json").read_text(encoding="utf-8"))["@graph"]
    organization = next(node for node in graph if node.get("@type") == "Organization")
    assert organization["sameAs"] == identity["organization"]["sameAs"]


def test_machine_facing_identity_files_use_the_canonical_record() -> None:
    for path in (ROOT / "humans.txt", ROOT / "llms.txt"):
        text = path.read_text(encoding="utf-8")
        assert "desmond@clearglassinc.com" in text
        assert "Burlington, Ontario, Canada" in text
        assert "https://github.com/ClearGlassInc" in text
        assert "https://www.linkedin.com/company/cleaglassinc" in text

# Copyright (c) 2024-2026 ClearGlass Inc. All Rights Reserved.
# Proprietary and confidential. See LICENSE for terms.
"""Regression checks for the homepage loader contract."""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_homepage_keeps_inline_loader_without_redirect_gate() -> None:
    html = (ROOT / "index.html").read_text(encoding="utf-8")
    assert "/loader.html?next=" not in html, "homepage must not bounce first visits to loader.html"
    assert 'id="cg-loader"' in html, "homepage must retain the inline premium loader"
    assert "CLEARGLASS PREMIUM LOADER" in html, "homepage loader markup/styles must remain present"

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

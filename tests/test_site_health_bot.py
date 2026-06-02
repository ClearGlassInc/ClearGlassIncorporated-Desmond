# Copyright (c) 2024-2026 ClearGlass Inc. All Rights Reserved.
# Proprietary and confidential. See LICENSE for terms.
"""Tests for bots/site_health_bot.py."""
from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from bots.site_health_bot import (  # noqa: E402
    PAGES_TO_CHECK,
    REQUIRED_ROOT_FILES,
    PageHealth,
    _check_local_files,
    _check_page,
)


class TestPageHealth:
    def test_dataclass_construction(self) -> None:
        ph = PageHealth(
            path="/", url="https://example.com/",
            status_code=200, reachable=True,
            response_ms=42, has_title=True, missing_meta=[],
        )
        assert ph.reachable is True
        assert ph.status_code == 200
        assert ph.error is None

    def test_unreachable_defaults(self) -> None:
        ph = PageHealth(
            path="/404", url="https://example.com/404",
            status_code=None, reachable=False,
            response_ms=0, has_title=False, missing_meta=["description"],
            error="Connection refused",
        )
        assert ph.reachable is False
        assert ph.error is not None


class TestCheckLocalFiles:
    def test_returns_list(self) -> None:
        issues = _check_local_files()
        assert isinstance(issues, list)

    def test_all_strings(self) -> None:
        issues = _check_local_files()
        for issue in issues:
            assert isinstance(issue, str)


class TestCheckPage:
    def test_url_error_returns_unreachable(self) -> None:
        from urllib.error import URLError
        with patch("bots.site_health_bot.urlopen", side_effect=URLError("timeout")):
            result = _check_page("/test-path")
        assert result.reachable is False
        assert result.error is not None
        assert result.path == "/test-path"

    def test_http_200_marks_reachable(self) -> None:
        mock_resp = MagicMock()
        mock_resp.__enter__ = lambda s: s
        mock_resp.__exit__ = MagicMock(return_value=False)
        mock_resp.status = 200
        mock_resp.read.return_value = b"<html><title>Test</title></html>"

        with patch("bots.site_health_bot.urlopen", return_value=mock_resp):
            result = _check_page("/")
        assert result.reachable is True
        assert result.status_code == 200

    def test_http_404_marks_unreachable(self) -> None:
        from urllib.error import HTTPError
        err = HTTPError(url="", code=404, msg="Not Found", hdrs=None, fp=None)
        with patch("bots.site_health_bot.urlopen", side_effect=err):
            result = _check_page("/missing")
        assert result.reachable is False


class TestConstants:
    def test_pages_to_check_not_empty(self) -> None:
        assert len(PAGES_TO_CHECK) > 0

    def test_required_root_files_not_empty(self) -> None:
        assert len(REQUIRED_ROOT_FILES) > 0

    def test_all_pages_start_with_slash(self) -> None:
        for p in PAGES_TO_CHECK:
            assert p.startswith("/"), f"Page path must start with /: {p}"

from pathlib import Path
from urllib.error import HTTPError

import pytest

from scripts import check_pypi_quota


def test_distribution_sizes_requires_artifacts(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="no distributions"):
        check_pypi_quota.distribution_sizes(tmp_path)


def test_check_quota_reports_file_and_project_overages() -> None:
    errors = check_pypi_quota.check_quota(
        [("large.whl", 101), ("package.tar.gz", 10)],
        retained_bytes=900,
        file_limit=100,
        project_limit=1_000,
    )

    assert errors == [
        "large.whl is 101 bytes; file quota is 100 bytes",
        "project would use 1011 bytes; project quota is 1000 bytes",
    ]


def test_missing_pypi_project_is_zero_usage(monkeypatch: pytest.MonkeyPatch) -> None:
    def missing(*args: object, **kwargs: object) -> None:
        raise HTTPError("https://pypi.org", 404, "Not Found", {}, None)

    monkeypatch.setattr(check_pypi_quota.urllib.request, "urlopen", missing)

    assert check_pypi_quota.published_bytes("not-yet-published", attempts=1) == 0


def test_registry_errors_fail_closed(monkeypatch: pytest.MonkeyPatch) -> None:
    def unavailable(*args: object, **kwargs: object) -> None:
        raise OSError("offline")

    monkeypatch.setattr(check_pypi_quota.urllib.request, "urlopen", unavailable)

    with pytest.raises(RuntimeError, match="after 1 attempts"):
        check_pypi_quota.published_bytes("package", attempts=1)

#!/usr/bin/env python3
"""Fail closed when a distribution would exceed configured PyPI quotas."""

from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

MIB = 1024 * 1024
GIB = 1024 * MIB


def published_bytes(package: str, *, timeout: float = 10, attempts: int = 3) -> int:
    """Return the bytes retained by PyPI for all releases of ``package``.

    A package that has never been published is a valid zero-byte baseline. Other
    HTTP and transport errors fail the check rather than producing a false pass.
    """

    encoded_name = urllib.parse.quote(package, safe="")
    request = urllib.request.Request(
        f"https://pypi.org/pypi/{encoded_name}/json",
        headers={"Accept": "application/json", "User-Agent": "pypi-quota-check/1"},
    )
    for attempt in range(attempts):
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                payload: Any = json.load(response)
            releases = payload.get("releases")
            if not isinstance(releases, dict):
                raise ValueError("PyPI response does not contain a releases mapping")
            return sum(
                file["size"]
                for files in releases.values()
                if isinstance(files, list)
                for file in files
                if isinstance(file, dict) and isinstance(file.get("size"), int)
            )
        except urllib.error.HTTPError as error:
            if error.code == 404:
                return 0
            last_error: Exception = error
        except (OSError, ValueError, json.JSONDecodeError) as error:
            last_error = error
        if attempt + 1 < attempts:
            time.sleep(2**attempt)
    raise RuntimeError(f"unable to read PyPI metadata after {attempts} attempts: {last_error}")


def distribution_sizes(directory: Path) -> list[tuple[str, int]]:
    files = sorted(path for path in directory.iterdir() if path.is_file())
    if not files:
        raise ValueError(f"no distributions found in {directory}")
    return [(path.name, path.stat().st_size) for path in files]


def check_quota(
    distributions: list[tuple[str, int]],
    retained_bytes: int,
    *,
    file_limit: int,
    project_limit: int,
) -> list[str]:
    errors = [
        f"{name} is {size} bytes; file quota is {file_limit} bytes"
        for name, size in distributions
        if size > file_limit
    ]
    upload_bytes = sum(size for _, size in distributions)
    if retained_bytes + upload_bytes > project_limit:
        errors.append(
            f"project would use {retained_bytes + upload_bytes} bytes; "
            f"project quota is {project_limit} bytes"
        )
    return errors


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--package", required=True)
    parser.add_argument("--dist-dir", type=Path, required=True)
    parser.add_argument("--file-limit-mib", type=int, default=100)
    parser.add_argument("--project-limit-gib", type=int, default=10)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        distributions = distribution_sizes(args.dist_dir)
        retained = published_bytes(args.package)
        errors = check_quota(
            distributions,
            retained,
            file_limit=args.file_limit_mib * MIB,
            project_limit=args.project_limit_gib * GIB,
        )
    except (OSError, RuntimeError, ValueError) as error:
        print(f"PyPI quota check failed: {error}", file=sys.stderr)
        return 2

    uploaded = sum(size for _, size in distributions)
    print(f"Published: {retained} bytes; candidate: {uploaded} bytes")
    for error in errors:
        print(f"::error::{error}", file=sys.stderr)
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Bounded production verification for the ClearGlass GitHub Pages site."""
from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
from dataclasses import asdict, dataclass
from pathlib import Path
from urllib.parse import urljoin, urlsplit

USER_AGENT = "ClearGlass-Production-Probe/1.0"
RETRY_DELAYS = (0, 2, 5)


@dataclass(frozen=True)
class ProbeResult:
    url: str
    ok: bool
    status: int | None
    final_url: str | None
    content_type: str | None
    error: str | None


def fetch(url: str, timeout: float) -> tuple[int, str, str, bytes]:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        status = int(response.status)
        final_url = response.geturl()
        content_type = response.headers.get("Content-Type", "")
        body = response.read(2_000_000)
    return status, final_url, content_type, body


def probe(url: str, timeout: float) -> ProbeResult:
    last_error: str | None = None
    for delay in RETRY_DELAYS:
        if delay:
            time.sleep(delay)
        try:
            status, final_url, content_type, _ = fetch(url, timeout)
            ok = 200 <= status < 400
            return ProbeResult(url, ok, status, final_url, content_type, None)
        except (urllib.error.URLError, TimeoutError, ValueError) as exc:
            last_error = f"{type(exc).__name__}: {exc}"
    return ProbeResult(url, False, None, None, None, last_error)


def sitemap_urls(base_url: str, timeout: float, limit: int) -> list[str]:
    sitemap_url = urljoin(base_url.rstrip("/") + "/", "sitemap.xml")
    try:
        status, _, _, body = fetch(sitemap_url, timeout)
    except (urllib.error.URLError, TimeoutError, ValueError, ET.ParseError):
        return []
    if not 200 <= status < 400:
        return []
    try:
        root = ET.fromstring(body)
    except ET.ParseError:
        return []

    base_host = urlsplit(base_url).netloc.lower()
    discovered: set[str] = set()
    for element in root.iter():
        if not element.tag.endswith("loc") or not element.text:
            continue
        candidate = element.text.strip()
        parsed = urlsplit(candidate)
        if parsed.scheme not in {"http", "https"}:
            continue
        if parsed.netloc.lower() != base_host:
            continue
        discovered.add(candidate)
    return sorted(discovered)[:limit]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("base_url")
    parser.add_argument("--timeout", type=float, default=12.0)
    parser.add_argument("--sitemap-limit", type=int, default=30)
    parser.add_argument("--report", default="operations/reports/production-probe.json")
    args = parser.parse_args()

    base_url = args.base_url.rstrip("/") + "/"
    urls = {
        base_url,
        urljoin(base_url, "robots.txt"),
        urljoin(base_url, "sitemap.xml"),
    }
    urls.update(sitemap_urls(base_url, args.timeout, max(args.sitemap_limit, 0)))

    results = [probe(url, args.timeout) for url in sorted(urls)]
    failures = [result for result in results if not result.ok]
    report = {
        "baseUrl": base_url,
        "checked": len(results),
        "passed": not failures,
        "results": [asdict(result) for result in results],
    }

    report_path = Path(args.report)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))

    if failures:
        for result in failures:
            print(f"PROBE FAIL: {result.url}: {result.error or result.status}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())

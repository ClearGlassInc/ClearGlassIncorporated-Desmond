# Copyright (c) 2024-2026 ClearGlass Inc. All Rights Reserved.
# Proprietary and confidential. See LICENSE for terms.
"""Site health bot — checks live page availability and SEO structure."""
from __future__ import annotations

import json
import re
import sys
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = ROOT / "operations" / "output"

SITE_URL = "https://clearglassinc.github.io"
REQUEST_TIMEOUT = 15
USER_AGENT = "ClearGlass-HealthBot/1.0"

PAGES_TO_CHECK = [
    "/",
    "/artemis.html",
    "/artemis-iv.html",
    "/guardian.html",
    "/clearglass-nexus.html",
    "/government.html",
]

REQUIRED_META_TAGS = ["description", "og:title", "og:description"]
REQUIRED_ROOT_FILES = ["sitemap.xml", "robots.txt", "schema.json", ".nojekyll"]


@dataclass
class PageHealth:
    path: str
    url: str
    status_code: int | None
    reachable: bool
    response_ms: int
    has_title: bool
    missing_meta: list[str]
    error: str | None = None


@dataclass
class HealthReport:
    run_utc: str
    site_url: str
    overall_healthy: bool
    pages_checked: int
    pages_healthy: int
    pages_unreachable: int
    pages: list[dict[str, Any]]
    local_issues: list[str]


def _check_page(path: str) -> PageHealth:
    url = f"{SITE_URL}{path}"
    start = time.monotonic()
    try:
        req = Request(url, headers={"User-Agent": USER_AGENT})
        with urlopen(req, timeout=REQUEST_TIMEOUT) as resp:
            status = resp.status
            html = resp.read().decode("utf-8", errors="replace")
        elapsed = int((time.monotonic() - start) * 1000)

        has_title = bool(re.search(r"<title[^>]*>.+?</title>", html, re.IGNORECASE | re.DOTALL))
        missing_meta = [
            tag for tag in REQUIRED_META_TAGS
            if not re.search(
                rf'(?:name|property)=["\'](?:og:)?{re.escape(tag.replace("og:", ""))}["\']',
                html,
                re.IGNORECASE,
            )
        ]

        return PageHealth(
            path=path, url=url, status_code=status,
            reachable=status < 400, response_ms=elapsed,
            has_title=has_title, missing_meta=missing_meta,
        )
    except (HTTPError, URLError, Exception) as exc:  # noqa: BLE001
        elapsed = int((time.monotonic() - start) * 1000)
        return PageHealth(
            path=path, url=url, status_code=None, reachable=False,
            response_ms=elapsed, has_title=False,
            missing_meta=list(REQUIRED_META_TAGS), error=str(exc),
        )


def _check_local_files() -> list[str]:
    issues: list[str] = []

    for fname in REQUIRED_ROOT_FILES:
        if not (ROOT / fname).exists():
            issues.append(f"Missing required file: {fname}")

    sitemap_path = ROOT / "sitemap.xml"
    if sitemap_path.exists():
        sitemap = sitemap_path.read_text()
        for html_file in sorted(ROOT.glob("*.html")):
            if html_file.name not in sitemap:
                issues.append(f"HTML page not referenced in sitemap.xml: {html_file.name}")

    return issues


def run() -> HealthReport:
    pages = [_check_page(p) for p in PAGES_TO_CHECK]
    local_issues = _check_local_files()

    healthy_count = sum(1 for p in pages if p.reachable and not p.missing_meta)
    unreachable_count = sum(1 for p in pages if not p.reachable)

    report = HealthReport(
        run_utc=datetime.now(timezone.utc).isoformat(),
        site_url=SITE_URL,
        overall_healthy=(unreachable_count == 0 and not local_issues),
        pages_checked=len(pages),
        pages_healthy=healthy_count,
        pages_unreachable=unreachable_count,
        pages=[asdict(p) for p in pages],
        local_issues=local_issues,
    )

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUTPUT_DIR / "site_health_report.json").write_text(json.dumps(asdict(report), indent=2))

    md: list[str] = [
        "# Site Health Report",
        "",
        f"**Run:** {report.run_utc}",
        f"**Status:** {'✅ Healthy' if report.overall_healthy else '⚠️ Issues Detected'}",
        f"**Pages:** {report.pages_healthy}/{report.pages_checked} healthy",
        "",
        "## Pages",
        "",
    ]
    for p in pages:
        icon = "✅" if p.reachable else "❌"
        timing = f"{p.response_ms}ms" if p.reachable else "—"
        md.append(f"- {icon} `{p.path}` ({timing})")
        if p.missing_meta:
            md.append(f"  - Missing meta: {', '.join(p.missing_meta)}")
        if p.error:
            md.append(f"  - Error: {p.error}")

    if local_issues:
        md += ["", "## Local Issues", ""]
        for issue in local_issues:
            md.append(f"- ⚠️ {issue}")

    (OUTPUT_DIR / "site_health_report.md").write_text("\n".join(md))
    return report


def main() -> None:
    report = run()
    status = "HEALTHY" if report.overall_healthy else "ISSUES DETECTED"
    print(f"Site Health: {status} — {report.pages_healthy}/{report.pages_checked} pages OK")
    if not report.overall_healthy:
        sys.exit(1)


if __name__ == "__main__":
    main()

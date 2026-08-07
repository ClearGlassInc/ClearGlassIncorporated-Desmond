#!/usr/bin/env python3
"""Build a fail-closed GitHub Pages artifact from explicitly public file types."""

from __future__ import annotations

import argparse
import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PUBLIC_EXTENSIONS = {
    ".css", ".geojson", ".gif", ".html", ".ico", ".jpeg", ".jpg", ".js",
    ".json", ".mp4", ".pdf", ".png", ".svg", ".txt", ".webm", ".webmanifest",
    ".webp", ".xml",
}
PUBLIC_EXTENSIONLESS = {"CNAME", "LICENSE", "NOTICE", "_headers", "_redirects"}
PUBLIC_MARKDOWN = {"SECURITY.md", "legal/WEBSITE_POLICY_TEMPLATES.md"}
DENIED_TOP_LEVEL = {
    ".git", ".github", "agent_army", "agent_os", "agents", "apps", "artemis",
    "artemis_platform", "automation", "boq", "bots", "clearglass-agentops",
    "clearglass-air-control", "clearglass-commerce", "config", "data", "deployment",
    "docs", "growth-engine", "infra", "jarvis-os", "marketing", "operations",
    "percival_v9", "platform", "products", "prompts", "runner", "scripts", "sentinel",
    "services", "strategy", "tests", "threads-growth", "tools", "workflows", "xenolith",
    "youtube_launch",
}
PUBLIC_DENIED_TREE_EXCEPTIONS = {Path("apps/command-center")}

# `data/` stays denied as a tree — it also holds internal working state (marketing
# shared memory, campaign packages, SEO targeting config). These specific feeds are
# the ones live pages fetch to render, so denying them left every dashboard on the
# site showing its "unavailable" fallback against a 404. Allowlisted file by file:
# adding a feed here is a deliberate decision to publish it.
PUBLIC_DATA_FEEDS = {
    # Control Surface contract feeds, refreshed hourly by control-surface-feeds.yml
    # and consumed by web-design.html, control-surface.{html,js}, systems.html.
    "data/control-surface/activity.json",
    "data/control-surface/alerts.json",
    "data/control-surface/health.json",
    "data/control-surface/metrics.json",
    "data/control-surface/pipeline.json",
    "data/control-surface/runs.json",
    # Page-specific feeds, each fetched by the page named beside it.
    "data/Ontario-osint/intel.json",      # Ontario-osint.html, web-design.html
    "data/platform/registry.json",        # intelligence-platform.html
    "data/store/catalog.json",            # web-design.html
    "data/xenolith/lattice.json",         # xenolith.html
    # Linked as downloads from the (noindex) SEO dashboard.
    "data/seo/alerts.json",
    "data/seo/audit.json",
    "data/seo/performance.json",
}

DENIED_PARTS = {"node_modules", "__pycache__", ".pytest_cache", ".mypy_cache"}
DENIED_NAMES = {"package.json", "package-lock.json", "pyproject.toml", "requirements.txt"}

# GitHub Pages does not process Netlify/Cloudflare-style `_headers` files. Keep the
# header policy for hosts that support it, but also inject a CSP meta policy into
# every deployable HTML document so the browser receives a baseline policy on
# GitHub Pages itself. `frame-ancestors`, HSTS, X-Frame-Options, Permissions-Policy,
# and other response-header-only controls remain in `_headers` for capable edges.
CSP_POLICY = (
    "default-src 'self'; "
    "base-uri 'self'; "
    "object-src 'none'; "
    "form-action 'self' https://formspree.io; "
    "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://cdnjs.cloudflare.com; "
    "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com https://cdnjs.cloudflare.com; "
    "font-src 'self' https://fonts.gstatic.com https://cdnjs.cloudflare.com data:; "
    "img-src 'self' data: blob: https:; "
    "media-src 'self' https:; "
    "connect-src 'self' https://formspree.io https://api.github.com; "
    "frame-src 'self' https://www.youtube-nocookie.com; "
    "manifest-src 'self'; "
    "worker-src 'self' blob:; "
    "upgrade-insecure-requests"
)


def _harden_html(path: Path) -> None:
    """Inject browser-enforced security metadata into a published HTML file."""
    text = path.read_text(encoding="utf-8")
    head = re.search(r"<head(?:\s[^>]*)?>", text, flags=re.IGNORECASE)
    if not head:
        return

    tags: list[str] = []
    if not re.search(
        r"<meta\b[^>]*http-equiv\s*=\s*['\"]Content-Security-Policy['\"]",
        text,
        flags=re.IGNORECASE,
    ):
        tags.append(
            f'<meta http-equiv="Content-Security-Policy" content="{CSP_POLICY}">'
        )
    if not re.search(
        r"<meta\b[^>]*name\s*=\s*['\"]referrer['\"]",
        text,
        flags=re.IGNORECASE,
    ):
        tags.append('<meta name="referrer" content="strict-origin-when-cross-origin">')

    if not tags:
        return

    injection = "\n" + "\n".join(tags)
    text = text[: head.end()] + injection + text[head.end() :]
    path.write_text(text, encoding="utf-8")


def public_relative_paths() -> list[Path]:
    paths: list[Path] = []
    for source in ROOT.rglob("*"):
        if not source.is_file():
            continue
        relative = source.relative_to(ROOT)
        relative_text = relative.as_posix()
        inside_public_exception = (
            any(relative.is_relative_to(path) for path in PUBLIC_DENIED_TREE_EXCEPTIONS)
            or relative_text in PUBLIC_DATA_FEEDS
        )
        if (
            relative.parts[0] in DENIED_TOP_LEVEL
            and not inside_public_exception
        ) or any(p in DENIED_PARTS for p in relative.parts):
            continue
        if source.name in DENIED_NAMES:
            continue
        if (
            source.suffix.lower() in PUBLIC_EXTENSIONS
            or source.name in PUBLIC_EXTENSIONLESS
            or relative_text in PUBLIC_MARKDOWN
            or relative_text == ".nojekyll"
        ):
            paths.append(relative)
    return sorted(paths)


def build(destination: Path) -> int:
    if destination.resolve() == ROOT:
        raise ValueError("destination cannot be repository root")
    shutil.rmtree(destination, ignore_errors=True)
    for relative in public_relative_paths():
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / relative, target)
        if target.suffix.lower() == ".html":
            _harden_html(target)
    (destination / ".nojekyll").touch()
    if not (destination / "index.html").is_file():
        raise FileNotFoundError("Pages artifact is missing index.html")
    return len([path for path in destination.rglob("*") if path.is_file()])


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("destination", nargs="?", type=Path, default=ROOT / "dist")
    args = parser.parse_args()
    count = build(args.destination)
    print(f"built {count} public files in {args.destination}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Build a fail-closed GitHub Pages artifact from explicitly public file types."""

from __future__ import annotations

import argparse
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

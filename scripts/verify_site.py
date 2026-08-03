#!/usr/bin/env python3
"""Non-destructive static-site integrity checks for ClearGlassInc."""
from __future__ import annotations

import argparse
import json
import re
import sys
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit

EXCLUDED_DIRS = {".git", "node_modules", "vendor", ".venv", "venv"}
SECRET_PATTERNS = {
    "private key": re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    "GitHub token": re.compile(r"gh[pousr]_[A-Za-z0-9_]{20,}"),
    "generic bearer token": re.compile(r"(?i)authorization\s*[:=]\s*bearer\s+[A-Za-z0-9._~+/=-]{20,}"),
}


class LinkParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.links: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = dict(attrs)
        for key in ("href", "src", "poster"):
            value = values.get(key)
            if value:
                self.links.append(value.strip())
        srcset = values.get("srcset")
        if srcset:
            self.links.extend(part.strip().split()[0] for part in srcset.split(",") if part.strip())


def ignored(path: Path) -> bool:
    return any(part in EXCLUDED_DIRS for part in path.parts)


def resolve_local(source: Path, raw: str, root: Path) -> Path | None:
    if not raw or raw.startswith(("#", "mailto:", "tel:", "javascript:", "data:")):
        return None
    parsed = urlsplit(raw)
    if parsed.scheme or parsed.netloc or raw.startswith("//"):
        return None
    target_text = unquote(parsed.path)
    if not target_text:
        return None
    target = root / target_text.lstrip("/") if target_text.startswith("/") else source.parent / target_text
    target = target.resolve()
    try:
        target.relative_to(root.resolve())
    except ValueError:
        return target
    if target.is_dir():
        target = target / "index.html"
    return target


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--report", default="operations/reports/site-integrity.json")
    args = parser.parse_args()
    root = Path(args.root).resolve()
    html_files = sorted(p for p in root.rglob("*.html") if not ignored(p.relative_to(root)))
    broken: list[dict[str, str]] = []
    secrets: list[dict[str, str]] = []

    for html_file in html_files:
        text = html_file.read_text(encoding="utf-8", errors="replace")
        link_parser = LinkParser()
        try:
            link_parser.feed(text)
        except Exception as exc:
            broken.append({"source": str(html_file.relative_to(root)), "target": "<parse-error>", "reason": str(exc)})
            continue
        for raw in link_parser.links:
            target = resolve_local(html_file, raw, root)
            if target is not None and not target.exists():
                broken.append({"source": str(html_file.relative_to(root)), "target": raw, "reason": "missing local target"})

    scan_extensions = {".html", ".js", ".json", ".yml", ".yaml", ".md", ".py", ".css"}
    for path in sorted(p for p in root.rglob("*") if p.is_file() and p.suffix.lower() in scan_extensions and not ignored(p.relative_to(root))):
        text = path.read_text(encoding="utf-8", errors="replace")
        for name, pattern in SECRET_PATTERNS.items():
            if pattern.search(text):
                secrets.append({"file": str(path.relative_to(root)), "pattern": name})

    report = {
        "htmlFilesChecked": len(html_files),
        "brokenLocalReferences": broken,
        "possibleSecrets": secrets,
        "passed": not broken and not secrets,
    }
    report_path = root / args.report
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())

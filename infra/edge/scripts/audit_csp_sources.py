#!/usr/bin/env python3
"""Inventory external runtime origins in an already-built public site artifact."""

from __future__ import annotations

import argparse
import json
import re
import sys
import urllib.parse
from collections import defaultdict
from html.parser import HTMLParser
from pathlib import Path
from typing import Iterable

EDGE_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INVENTORY = EDGE_ROOT / "csp-inventory.json"
TEXT_SUFFIXES = {".css", ".html", ".js", ".mjs"}


def origin(value: str | None) -> str | None:
    if not value or value.startswith(("#", "blob:", "data:", "javascript:", "mailto:", "tel:")):
        return None
    if value.startswith("//"):
        value = "https:" + value
    try:
        parsed = urllib.parse.urlsplit(value)
    except ValueError:
        return None
    if parsed.scheme not in {"http", "https", "ws", "wss"} or not parsed.hostname:
        return None
    port = f":{parsed.port}" if parsed.port else ""
    return f"{parsed.scheme.lower()}://{parsed.hostname.lower()}{port}"


class ArtifactHTMLParser(HTMLParser):
    def __init__(self, path: Path, found: dict[str, dict[str, set[str]]]) -> None:
        super().__init__()
        self.path = path
        self.found = found

    def add(self, directive: str, value: str | None) -> None:
        external = origin(value)
        if external:
            self.found[directive][external].add(str(self.path))

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = dict(attrs)
        tag = tag.lower()
        if tag == "script":
            self.add("script-src", values.get("src"))
        elif tag == "link" and "stylesheet" in (values.get("rel") or "").lower():
            self.add("style-src", values.get("href"))
        elif tag == "img":
            self.add("img-src", values.get("src"))
        elif tag in {"audio", "source", "video"}:
            self.add("media-src", values.get("src"))
        elif tag in {"frame", "iframe"}:
            self.add("frame-src", values.get("src"))
        elif tag == "form":
            self.add("form-action", values.get("action"))


def text_files(root: Path) -> Iterable[Path]:
    for path in root.rglob("*"):
        if path.is_file() and path.suffix.lower() in TEXT_SUFFIXES:
            yield path


def discover(root: Path) -> dict[str, dict[str, set[str]]]:
    found: dict[str, dict[str, set[str]]] = defaultdict(lambda: defaultdict(set))
    network_patterns = [
        re.compile(r"\b(?:fetch|fetchWithRetry|fetchWithProxy|jget|_fetchT|EventSource)\s*\(\s*[`\"']((?:https?|wss?)://[^`\"']+)", re.I),
        re.compile(r"\bnew\s+WebSocket\s*\(\s*[`\"']((?:https?|wss?)://[^`\"']+)", re.I),
        re.compile(r"\b(?:axios\.(?:get|post)|open)\s*\(\s*[`\"']((?:https?|wss?)://[^`\"']+)", re.I),
    ]
    script_loader = re.compile(r"\binjectScript\s*\(\s*[`\"'](https?://[^`\"']+)", re.I)
    css_url = re.compile(r"\burl\(\s*[\"']?(https?://[^)\"']+)", re.I)
    dynamic_frame = re.compile(r"<iframe\b[^>]*\bsrc\s*=\s*[`\"'](https?://[^`\"'\s>]+)", re.I)
    proxy_collection = re.compile(r"\b[A-Za-z0-9_]*PROX(?:Y|IES)[A-Za-z0-9_]*\s*=\s*\[([^\]]+)]", re.I)
    absolute_url = re.compile(r"(?:https?|wss?)://[^`\"'\s,\]]+", re.I)

    for path in text_files(root):
        text = path.read_text(encoding="utf-8", errors="ignore")
        relative = path.relative_to(root)
        if path.suffix.lower() == ".html":
            parser = ArtifactHTMLParser(relative, found)
            parser.feed(text)
        for pattern in network_patterns:
            for match in pattern.finditer(text):
                external = origin(match.group(1))
                if external:
                    found["connect-src"][external].add(str(relative))
        for match in script_loader.finditer(text):
            external = origin(match.group(1))
            if external:
                found["script-src"][external].add(str(relative))
        for match in dynamic_frame.finditer(text):
            external = origin(match.group(1))
            if external:
                found["frame-src"][external].add(str(relative))
        for collection in proxy_collection.finditer(text):
            for match in absolute_url.finditer(collection.group(1)):
                external = origin(match.group(0))
                if external:
                    found["connect-src"][external].add(str(relative))
        for match in css_url.finditer(text):
            external = origin(match.group(1))
            if external:
                found["style-src"][external].add(str(relative))
    return found


def source_allows(source: str, external: str) -> bool:
    if source == external or source == "https:" and external.startswith("https://"):
        return True
    if "*." in source:
        parsed_source = urllib.parse.urlsplit(source.replace("*.", "wildcard."))
        parsed_external = urllib.parse.urlsplit(external)
        suffix = parsed_source.hostname.removeprefix("wildcard.") if parsed_source.hostname else ""
        return parsed_source.scheme == parsed_external.scheme and bool(
            parsed_external.hostname and parsed_external.hostname.endswith("." + suffix)
        )
    return False


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True, help="Built public artifact root.")
    parser.add_argument("--inventory", type=Path, default=DEFAULT_INVENTORY)
    parser.add_argument("--check", action="store_true", help="Fail when a discovered origin is not inventoried.")
    args = parser.parse_args()

    if not args.root.is_dir():
        print(f"ERROR: artifact root is not a directory: {args.root}", file=sys.stderr)
        return 2
    try:
        inventory = json.loads(args.inventory.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"ERROR: cannot load CSP inventory: {exc}", file=sys.stderr)
        return 2
    configured = inventory.get("csp_sources")
    if not isinstance(configured, dict):
        print("ERROR: csp-inventory.json must contain a csp_sources object", file=sys.stderr)
        return 2

    found = discover(args.root)
    missing: list[str] = []
    serializable: dict[str, dict[str, list[str]]] = {}
    for directive in sorted(found):
        serializable[directive] = {}
        allowed = configured.get(directive, [])
        if not isinstance(allowed, list):
            print(f"ERROR: {directive} inventory entry must be an array", file=sys.stderr)
            return 2
        for external, paths in sorted(found[directive].items()):
            serializable[directive][external] = sorted(paths)
            if not any(source_allows(str(source), external) for source in allowed):
                missing.append(f"{directive}: {external} ({', '.join(sorted(paths)[:3])})")

    print(json.dumps(serializable, indent=2, sort_keys=True))
    if missing:
        for item in missing:
            print(f"ERROR: unreviewed CSP origin: {item}", file=sys.stderr)
        if args.check:
            return 1
    print(f"CSP artifact audit OK: {sum(len(origins) for origins in found.values())} directive/origin pairs")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

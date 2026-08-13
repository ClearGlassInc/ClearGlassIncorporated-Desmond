#!/usr/bin/env python3
"""Deterministic, network-free repository and Pages prerequisite diagnostics."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
CRITICAL_FILES = (
    "index.html",
    "CNAME",
    ".nojekyll",
    "package.json",
    "package-lock.json",
    "pyproject.toml",
    "tools/build_pages.py",
    "scripts/verify_site.py",
    "scripts/production_probe.py",
    ".github/workflows/ci.yml",
    ".github/workflows/pages.yml",
)


def diagnose() -> tuple[list[str], list[str], dict[str, int]]:
    failures = [path for path in CRITICAL_FILES if not (ROOT / path).is_file()]
    warnings: list[str] = []
    workflow_count = 0
    for workflow in sorted((ROOT / ".github/workflows").glob("*.y*ml")):
        workflow_count += 1
        try:
            document = yaml.safe_load(workflow.read_text(encoding="utf-8"))
        except yaml.YAMLError as exc:
            failures.append(f"{workflow.relative_to(ROOT)}: invalid YAML ({exc})")
            continue
        if not isinstance(document, dict) or not isinstance(document.get("jobs"), dict):
            failures.append(f"{workflow.relative_to(ROOT)}: missing jobs mapping")
        if not isinstance(document.get("permissions"), dict):
            warnings.append(f"{workflow.relative_to(ROOT)}: no top-level permissions mapping")

    package = json.loads((ROOT / "package.json").read_text(encoding="utf-8"))
    lock = json.loads((ROOT / "package-lock.json").read_text(encoding="utf-8"))
    if package.get("name") != lock.get("name"):
        failures.append("package.json and package-lock.json package names differ")
    metrics = {
        "workflows": workflow_count,
        "root_html_files": len(list(ROOT.glob("*.html"))),
        "critical_files": len(CRITICAL_FILES),
    }
    return failures, warnings, metrics


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--summary", type=Path)
    args = parser.parse_args()
    failures, warnings, metrics = diagnose()
    lines = [
        "## Repository Health",
        "",
        f"- Critical files: {metrics['critical_files'] - len([x for x in failures if x in CRITICAL_FILES])}/{metrics['critical_files']}",
        f"- Workflow files parsed: {metrics['workflows']}",
        f"- Root static HTML files: {metrics['root_html_files']}",
        f"- Blocking problems: {len(failures)}",
        f"- Advisory warnings: {len(warnings)}",
    ]
    if warnings:
        lines.extend(("", "### Warnings", *(f"- {warning}" for warning in warnings)))
    if failures:
        lines.extend(("", "### Blocking problems", *(f"- {failure}" for failure in failures)))
    report = "\n".join(lines) + "\n"
    print(report, end="")
    if args.summary:
        args.summary.write_text(report, encoding="utf-8")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())

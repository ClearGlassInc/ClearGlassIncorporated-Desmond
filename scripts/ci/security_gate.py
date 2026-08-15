#!/usr/bin/env python3
"""Fail closed on unapproved dependency vulnerabilities.

The version-controlled allowlist accepts exact identifiers only:
- npm:<numeric advisory source>
- npm-package:<package> (fallback only when npm provides no advisory source)
- pypa:<PYSEC/CVE/GHSA identifier>

Keep the file empty by default. Every exception should be reviewed, justified in
the commit that adds it, and removed as soon as the dependency is fixed.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path


BLOCKING_NPM_SEVERITIES = {"high", "critical"}


def load_allowlist(path: Path) -> set[str]:
    entries: set[str] = set()
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if not (
            line.startswith("npm:")
            or line.startswith("npm-package:")
            or line.startswith("pypa:")
        ):
            raise SystemExit(f"Invalid security allowlist entry: {line}")
        entries.add(line)
    return entries


def npm_findings(report: dict[str, object], allowlist: set[str]) -> list[str]:
    failures: list[str] = []
    vulnerabilities = report.get("vulnerabilities", {})
    if not isinstance(vulnerabilities, dict):
        return failures

    for package, raw_details in vulnerabilities.items():
        if not isinstance(raw_details, dict):
            continue
        severity = str(raw_details.get("severity", "")).lower()
        if severity not in BLOCKING_NPM_SEVERITIES:
            continue

        advisory_ids: set[str] = set()
        via = raw_details.get("via", [])
        if isinstance(via, list):
            for item in via:
                if isinstance(item, dict):
                    source = item.get("source")
                    if isinstance(source, (str, int)):
                        advisory_ids.add(f"npm:{source}")

        package_fallback = f"npm-package:{package}"
        if advisory_ids:
            unapproved = sorted(item for item in advisory_ids if item not in allowlist)
            if unapproved:
                failures.append(
                    f"npm {package} severity={severity} unapproved={','.join(unapproved)}"
                )
        elif package_fallback not in allowlist:
            failures.append(
                f"npm {package} severity={severity} has no advisory source; "
                f"explicit fallback allowlist entry required: {package_fallback}"
            )
    return failures


def pip_findings(report: object, allowlist: set[str]) -> list[str]:
    failures: list[str] = []

    dependencies: object = report
    if isinstance(report, dict):
        dependencies = report.get("dependencies", [])

    if not isinstance(dependencies, list):
        return ["pip-audit report has an unexpected JSON structure"]

    for dependency in dependencies:
        if not isinstance(dependency, dict):
            continue
        name = str(dependency.get("name", "unknown"))
        version = str(dependency.get("version", "unknown"))
        vulns = dependency.get("vulns", [])
        if not isinstance(vulns, list):
            continue
        for vuln in vulns:
            if not isinstance(vuln, dict):
                continue
            vuln_id = str(vuln.get("id", "")).strip()
            if not vuln_id:
                failures.append(f"pip {name}=={version} reported a vulnerability without an id")
                continue
            key = f"pypa:{vuln_id}"
            if key not in allowlist:
                # pip-audit does not consistently expose normalized severity for
                # every advisory source. Fail on every unapproved Python finding,
                # which is stricter than the requested high/critical floor.
                failures.append(f"pip {name}=={version} unapproved={key}")
    return failures


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--allowlist", type=Path, required=True)
    parser.add_argument("--npm", type=Path, required=True)
    parser.add_argument("--pip", type=Path, required=True)
    args = parser.parse_args()

    allowlist = load_allowlist(args.allowlist)
    npm_report = json.loads(args.npm.read_text(encoding="utf-8"))
    pip_report = json.loads(args.pip.read_text(encoding="utf-8"))

    failures = npm_findings(npm_report, allowlist)
    failures.extend(pip_findings(pip_report, allowlist))

    if failures:
        raise SystemExit(
            "Dependency security gate failed. Add only reviewed, version-controlled "
            "exceptions to scripts/ci/security-allowlist.txt.\n- "
            + "\n- ".join(failures)
        )

    print("Dependency security gate: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

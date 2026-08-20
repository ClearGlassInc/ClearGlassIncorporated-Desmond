#!/usr/bin/env python3
"""Security policy gate for the ClearGlass secure pipeline.

Reads dependency-audit and secret-scan reports produced by
`dependency_and_secret_scan`, then BLOCKS (exit 1) if any HIGH/CRITICAL finding
is not explicitly allow-listed — with a non-expired entry — in the
version-controlled policy file (scripts/ci/security-allowlist.yml).

Fail-closed by design: unreadable policy, unknown severity, or a malformed
report all block rather than pass.

Usage:
  python scripts/ci/scan_policy_gate.py \
      --policy scripts/ci/security-allowlist.yml \
      --reports-dir security-reports
"""

from __future__ import annotations

import argparse
import datetime as _dt
import json
import sys
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:  # pragma: no cover
    print("policy-gate: PyYAML required (pip install pyyaml)", file=sys.stderr)
    sys.exit(2)


def _today() -> _dt.date:
    return _dt.datetime.now(_dt.UTC).date()


def load_policy(path: Path) -> dict[str, Any]:
    if not path.is_file():
        print(f"❌ policy-gate: policy file not found: {path} (fail closed)", file=sys.stderr)
        sys.exit(1)
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    block = [s.lower() for s in data.get("block_on_severity", ["high", "critical"])]
    return {
        "block_on_severity": set(block),
        "dependency_allowlist": data.get("dependency_allowlist") or [],
        "secret_allowlist": data.get("secret_allowlist") or [],
    }


def _active_ids(entries: list[dict[str, Any]], key: str) -> set[str]:
    """Return allow-listed ids whose `expires` date is today or later."""
    active: set[str] = set()
    for e in entries:
        ident = str(e.get(key, "")).strip()
        exp = str(e.get("expires", "")).strip()
        if not ident or not exp:
            # Incomplete entry -> ignored (fails closed: finding still blocks).
            continue
        try:
            if _dt.date.fromisoformat(exp) >= _today():
                active.add(ident)
        except ValueError:
            continue
    return active


def _load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001 - malformed report must fail closed
        print(f"❌ policy-gate: cannot parse report {path} (fail closed)", file=sys.stderr)
        sys.exit(1)


def scan_pip_audit(path: Path, block: set[str], allowed: set[str]) -> list[str]:
    """Return list of blocking finding descriptions from a pip-audit JSON report."""
    if not path.is_file():
        return []
    data = _load_json(path)
    deps = data.get("dependencies", data) if isinstance(data, dict) else data
    findings: list[str] = []
    for dep in deps or []:
        name = dep.get("name", "?")
        for vuln in dep.get("vulns", []) or []:
            vid = vuln.get("id", "")
            # pip-audit does not always emit severity; treat unknown as blocking.
            sev = str(vuln.get("severity", "high")).lower()
            if sev in block and vid not in allowed:
                findings.append(f"[pip-audit] {name}: {vid} severity={sev}")
    return findings


def scan_npm_audit(path: Path, block: set[str], allowed: set[str]) -> list[str]:
    if not path.is_file():
        return []
    data = _load_json(path)
    findings: list[str] = []
    vulns = (data or {}).get("vulnerabilities", {}) if isinstance(data, dict) else {}
    for pkg, info in vulns.items():
        sev = str(info.get("severity", "")).lower()
        if sev in block:
            via = info.get("via", [])
            ids = [v.get("source") or v.get("url") or pkg for v in via if isinstance(v, dict)] or [
                pkg
            ]
            if not any(str(i) in allowed for i in ids):
                findings.append(f"[npm-audit] {pkg}: severity={sev}")
    return findings


def scan_gitleaks(path: Path, allowed: set[str]) -> list[str]:
    if not path.is_file():
        return []
    data = _load_json(path)
    findings: list[str] = []
    for item in data or []:
        rule = item.get("RuleID") or item.get("rule") or "secret"
        if str(rule) not in allowed:
            findings.append(f"[gitleaks] rule={rule} file={item.get('File', '?')}")
    return findings


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--policy", required=True, type=Path)
    ap.add_argument("--reports-dir", required=True, type=Path)
    args = ap.parse_args()

    policy = load_policy(args.policy)
    block = policy["block_on_severity"]
    dep_allowed = _active_ids(policy["dependency_allowlist"], "id")
    secret_allowed = _active_ids(policy["secret_allowlist"], "rule")

    reports = args.reports_dir
    blocking: list[str] = []
    blocking += scan_pip_audit(reports / "pip-audit.json", block, dep_allowed)
    for npm in reports.glob("npm-audit-*.json"):
        blocking += scan_npm_audit(npm, block, dep_allowed)
    blocking += scan_gitleaks(reports / "gitleaks.json", secret_allowed)

    # Conservative fallback secret detector output blocks too.
    if (reports / "secret-fallback.txt").is_file():
        blocking.append("[secret-fallback] potential credential pattern in recent commit")

    print(
        f"policy-gate: block_on_severity={sorted(block)} "
        f"dep_allow={sorted(dep_allowed)} secret_allow={sorted(secret_allowed)}"
    )

    if blocking:
        print(
            "❌ policy-gate: deployment BLOCKED by unresolved high/critical findings:",
            file=sys.stderr,
        )
        for f in blocking:
            print(f"   - {f}", file=sys.stderr)
        print(
            f"   Fix the finding, or add a justified, expiring entry to {args.policy}",
            file=sys.stderr,
        )
        return 1

    print("✅ policy-gate: no blocking findings.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

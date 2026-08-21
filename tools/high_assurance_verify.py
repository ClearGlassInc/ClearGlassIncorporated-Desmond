#!/usr/bin/env python3
"""ClearGlass high-assurance repository verifier.

Evidence-driven repository contract checks. This tool intentionally distinguishes
VERIFIED_FACT, OBSERVATION, UNKNOWN, and FAILURE instead of manufacturing
confidence from missing data.

The verifier is dependency-free and is safe to run in CI.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterable

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "operations" / "security" / "high_assurance_report.json"

WORKFLOW_DIR = ROOT / ".github" / "workflows"
PROVENANCE_CANDIDATES = (
    ROOT / "provenance" / "release-manifest.json",
    ROOT / "operations" / "artemis" / "provenance_manifest.json",
)
BASELINE_CANDIDATES = (
    ROOT / "baseline_metrics.json",
    ROOT / "data" / "baseline_metrics.json",
    ROOT / "operations" / "baseline_metrics.json",
)

SECRET_PATTERNS = (
    re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----"),
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    re.compile(r"\b(?:ghp|gho|ghs|ghr)_[A-Za-z0-9_]{30,}\b"),
    re.compile(r"\bgithub_pat_[A-Za-z0-9_]{40,}\b"),
    re.compile(r"\bsk-(?:proj|live|test)-[A-Za-z0-9_-]{20,}\b"),
    re.compile(r"\bxox[baprs]-[0-9A-Za-z-]{20,}\b"),
)

HIGH_ASSURANCE_SUPPRESSIONS = (
    re.compile(r"continue-on-error:\s*true", re.I),
    re.compile(r"\|\|\s*(?:true|echo\s+['\"]::warning::)", re.I),
)

CRITICAL_COMMANDS = (
    re.compile(r"npm\s+(?:test|run\s+(?:lint|typecheck|build))"),
    re.compile(r"(?:python\s+-m\s+pytest|pytest\b)"),
    re.compile(r"audit-ci\b|npm\s+audit\b"),
)


@dataclass
class Finding:
    control: str
    severity: str
    classification: str
    path: str | None
    detail: str
    evidence: str | None = None


def _git(*args: str) -> str | None:
    try:
        p = subprocess.run(
            ["git", *args],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=True,
            timeout=30,
        )
        return p.stdout.strip() or None
    except (OSError, subprocess.SubprocessError):
        return None


def _git_changed_files() -> list[Path]:
    base = os.environ.get("GITHUB_BASE_SHA")
    head = os.environ.get("GITHUB_SHA") or "HEAD"
    if base:
        out = _git("diff", "--name-only", base, head)
        if out:
            return [ROOT / line for line in out.splitlines() if line.strip()]
    out = _git("diff", "--name-only", "HEAD~1", "HEAD")
    if out:
        return [ROOT / line for line in out.splitlines() if line.strip()]
    return []


def _iter_text_files(paths: Iterable[Path] | None = None) -> Iterable[Path]:
    if paths is None:
        files = subprocess.run(
            ["git", "ls-files", "-z"], cwd=ROOT, capture_output=True, check=True
        ).stdout.split(b"\0")
        for raw in files:
            if raw:
                path = ROOT / raw.decode("utf-8", "replace")
                if path.is_file():
                    yield path
        return
    for path in paths:
        try:
            if path.is_file() and path.is_relative_to(ROOT):
                yield path
        except (OSError, ValueError):
            continue


def _read_text(path: Path) -> str | None:
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return None


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def check_secrets(findings: list[Finding]) -> None:
    scope = _git_changed_files() if os.environ.get("GITHUB_EVENT_NAME") == "pull_request" else None
    for path in _iter_text_files(scope):
        text = _read_text(path)
        if text is None:
            continue
        for pattern in SECRET_PATTERNS:
            if pattern.search(text):
                findings.append(
                    Finding(
                        "secret-detection",
                        "BLOCKING",
                        "VERIFIED_FACT",
                        str(path.relative_to(ROOT)),
                        "High-confidence credential/private-key pattern detected in tracked content.",
                        pattern.pattern,
                    )
                )


def check_workflow_gates(findings: list[Finding]) -> None:
    if not WORKFLOW_DIR.is_dir():
        findings.append(Finding("workflow-hygiene", "UNKNOWN", "UNKNOWN", None, "No .github/workflows directory found."))
        return
    for path in sorted(WORKFLOW_DIR.glob("*.y*ml")):
        text = _read_text(path) or ""
        lines = text.splitlines()
        for idx, line in enumerate(lines, start=1):
            for suppression in HIGH_ASSURANCE_SUPPRESSIONS:
                if not suppression.search(line):
                    continue
                context = "\n".join(lines[max(0, idx - 2): min(len(lines), idx + 2)])
                critical = any(rx.search(context) for rx in CRITICAL_COMMANDS)
                severity = "BLOCKING" if critical else "OBSERVATION"
                findings.append(
                    Finding(
                        "workflow-fail-open",
                        severity,
                        "VERIFIED_FACT",
                        str(path.relative_to(ROOT)),
                        f"Potential failure suppression at line {idx}; critical={critical}.",
                        line.strip(),
                    )
                )


def check_baseline_semantics(findings: list[Finding]) -> None:
    baseline = next((p for p in BASELINE_CANDIDATES if p.is_file()), None)
    if baseline is None:
        findings.append(Finding("measurement-provenance", "UNKNOWN", "UNKNOWN", None, "No baseline_metrics.json found in the repository."))
        return
    try:
        data = json.loads(baseline.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        findings.append(Finding("measurement-provenance", "BLOCKING", "VERIFIED_FACT", str(baseline.relative_to(ROOT)), f"Baseline JSON is invalid: {exc}"))
        return
    state = data.get("data_state")
    notes = data.get("collection_notes", [])
    if state == "not_collected" and not any("must not be interpreted as zero" in str(note).lower() for note in notes):
        findings.append(Finding("measurement-semantics", "BLOCKING", "VERIFIED_FACT", str(baseline.relative_to(ROOT)), "Not-collected baseline is missing the explicit null-vs-zero constraint."))
    if state == "not_collected":
        numeric_leaves: list[tuple[str, Any]] = []
        def walk(value: Any, key: str = "") -> None:
            if isinstance(value, dict):
                for k, v in value.items():
                    walk(v, f"{key}.{k}".strip("."))
            elif isinstance(value, (int, float)) and not isinstance(value, bool):
                numeric_leaves.append((key, value))
        walk(data.get("gbp", {}), "gbp")
        walk(data.get("web", {}), "web")
        walk(data.get("social", {}), "social")
        zeros = [key for key, value in numeric_leaves if value == 0]
        if zeros:
            findings.append(Finding("measurement-semantics", "BLOCKING", "VERIFIED_FACT", str(baseline.relative_to(ROOT)), "Not-collected dataset contains numeric zero where null is required.", ", ".join(zeros[:20])))


def check_provenance(findings: list[Finding]) -> None:
    manifest = next((p for p in PROVENANCE_CANDIDATES if p.is_file()), None)
    if manifest is None:
        findings.append(Finding("provenance", "UNKNOWN", "UNKNOWN", None, "No known provenance manifest is present."))
        return
    try:
        data = json.loads(manifest.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        findings.append(Finding("provenance", "BLOCKING", "VERIFIED_FACT", str(manifest.relative_to(ROOT)), f"Provenance manifest is invalid JSON: {exc}"))
        return
    artifacts = data.get("artifacts")
    if not isinstance(artifacts, list):
        findings.append(Finding("provenance", "BLOCKING", "VERIFIED_FACT", str(manifest.relative_to(ROOT)), "Manifest does not contain an artifacts list."))
        return
    for entry in artifacts:
        if not isinstance(entry, dict):
            findings.append(Finding("provenance", "BLOCKING", "VERIFIED_FACT", str(manifest.relative_to(ROOT)), "Manifest contains a malformed artifact entry."))
            continue
        # Both committed manifests name the file, under different keys:
        # the ARTEMIS bot writes "artifact", tools/security_release_manifest.py writes "path".
        artifact = entry.get("artifact") or entry.get("path")
        if not isinstance(artifact, str):
            findings.append(Finding("provenance", "BLOCKING", "VERIFIED_FACT", str(manifest.relative_to(ROOT)), "Artifact entry is missing a string artifact path."))
            continue
        path = ROOT / artifact
        if not path.is_file():
            findings.append(Finding("provenance", "BLOCKING", "VERIFIED_FACT", artifact, "Manifest references a missing artifact."))
            continue
        actual_hash = _sha256(path)
        expected_hash = entry.get("sha256")
        if expected_hash and expected_hash != actual_hash:
            findings.append(Finding("provenance-integrity", "BLOCKING", "VERIFIED_FACT", artifact, "SHA-256 does not match manifest.", f"expected={expected_hash} actual={actual_hash}"))
        expected_size = entry.get("size_bytes")
        if isinstance(expected_size, int) and expected_size != path.stat().st_size:
            findings.append(Finding("provenance-integrity", "BLOCKING", "VERIFIED_FACT", artifact, "Byte size does not match manifest.", f"expected={expected_size} actual={path.stat().st_size}"))


def check_security_documentation(findings: list[Finding]) -> None:
    required = (ROOT / "SECURITY.md", ROOT / "docs" / "PROVENANCE.md")
    for path in required:
        if not path.is_file():
            findings.append(Finding("governance-baseline", "BLOCKING", "VERIFIED_FACT", str(path.relative_to(ROOT)), "Required governance document is missing."))


def main() -> int:
    findings: list[Finding] = []
    check_secrets(findings)
    check_workflow_gates(findings)
    check_baseline_semantics(findings)
    check_provenance(findings)
    check_security_documentation(findings)

    blocking = [f for f in findings if f.severity == "BLOCKING"]
    report = {
        "schema_version": "1.0.0",
        "system": "ClearGlass High-Assurance Engineering Verifier",
        "classification": "OBSERVATION",
        "repository_head": _git("rev-parse", "HEAD"),
        "repository_branch": _git("rev-parse", "--abbrev-ref", "HEAD"),
        "generated_utc": __import__("datetime").datetime.now(__import__("datetime").timezone.utc).replace(microsecond=0).isoformat(),
        "decision": "BLOCK_RELEASE" if blocking else "PASS_WITH_FINDINGS",
        "blocking_count": len(blocking),
        "findings": [asdict(f) for f in findings],
    }
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"decision": report["decision"], "blocking_count": report["blocking_count"], "finding_count": len(findings)}))
    for finding in findings:
        print(f"[{finding.severity}] {finding.control}: {finding.path or '-'} — {finding.detail}")
    return 1 if blocking else 0


if __name__ == "__main__":
    raise SystemExit(main())

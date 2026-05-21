#!/usr/bin/env python3
"""ClearGlass GitHub Workflow Repair Agent.

Inspects GitHub Actions workflow automation, applies conservative repairs,
and writes a machine-readable + Markdown report for pull-request review.
"""

from __future__ import annotations

import json
import re
import subprocess
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError as exc:  # pragma: no cover
    raise SystemExit("PyYAML is required: python -m pip install pyyaml") from exc

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW_DIR = ROOT / ".github" / "workflows"
COMPOSITE_DIRS = [ROOT / ".github" / "actions", ROOT / "actions"]
REPORT_MD = ROOT / "workflow-repair-report.md"
REPORT_JSON = ROOT / "workflow-repair-report.json"

MUTABLE_ACTION_RE = re.compile(r"uses:\s*([^\s#]+@(master|main|latest))\b")
DANGEROUS_TRIGGER_KEYS = {"pull_request_target"}
ELEVATED_PERMISSIONS = {"write", "admin"}

SAFE_ACTION_PIN_UPGRADES = {
    "actions/checkout@master": "actions/checkout@v4.2.2",
    "actions/checkout@main": "actions/checkout@v4.2.2",
    "actions/setup-python@master": "actions/setup-python@v5.6.0",
    "actions/setup-python@main": "actions/setup-python@v5.6.0",
    "actions/setup-node@master": "actions/setup-node@v4.1.0",
    "actions/setup-node@main": "actions/setup-node@v4.1.0",
    "actions/upload-pages-artifact@master": "actions/upload-pages-artifact@v3.0.1",
    "actions/upload-pages-artifact@main": "actions/upload-pages-artifact@v3.0.1",
    "actions/deploy-pages@master": "actions/deploy-pages@v4.0.5",
    "actions/deploy-pages@main": "actions/deploy-pages@v4.0.5",
    "peter-evans/create-pull-request@master": "peter-evans/create-pull-request@v7.0.8",
    "peter-evans/create-pull-request@main": "peter-evans/create-pull-request@v7.0.8",
}


@dataclass
class Finding:
    file: str
    severity: str
    category: str
    message: str
    fix: str = ""


@dataclass
class Report:
    files_inspected: list[str]
    problems_found: list[Finding]
    fixes_applied: list[Finding]
    validation: list[str]
    remaining_risks: list[str]


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT))


def workflow_files() -> list[Path]:
    if not WORKFLOW_DIR.exists():
        return []
    return sorted(
        p for p in WORKFLOW_DIR.glob("*") if p.suffix.lower() in {".yml", ".yaml"}
    )


def action_yml_files() -> list[Path]:
    files: list[Path] = []
    for base in COMPOSITE_DIRS:
        if base.exists():
            files.extend(base.rglob("action.yml"))
            files.extend(base.rglob("action.yaml"))
    return sorted(files)


def load_yaml(path: Path) -> tuple[dict[str, Any] | None, str | None]:
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001
        return None, str(exc)
    if data is None:
        return {}, None
    if not isinstance(data, dict):
        return None, "top-level YAML document must be a mapping"
    return data, None


def normalize_on(data: dict[str, Any]) -> Any:
    # PyYAML YAML 1.1 may parse the key `on` as boolean True.
    return data.get("on", data.get(True))


def ensure_default_permissions(path: Path, data: dict[str, Any], text: str) -> tuple[str, Finding | None]:
    if "permissions" in data:
        return text, None
    insert_after = None
    for key in ("name:", "on:"):
        match = re.search(rf"^{re.escape(key)}.*(?:\n(?:\s+.*\n)*)?", text, flags=re.MULTILINE)
        if match:
            insert_after = match.end()
            break
    if insert_after is None:
        return text, None
    addition = "\npermissions:\n  contents: read\n"
    fixed = text[:insert_after].rstrip() + addition + text[insert_after:]
    return fixed, Finding(rel(path), "medium", "permissions", "Added default read-only workflow permissions.", "permissions: contents: read")


def safe_pin_mutable_actions(path: Path, text: str) -> tuple[str, list[Finding]]:
    fixes: list[Finding] = []
    fixed = text
    for source, target in SAFE_ACTION_PIN_UPGRADES.items():
        if source in fixed:
            fixed = fixed.replace(source, target)
            fixes.append(
                Finding(rel(path), "medium", "action-reference", f"Replaced mutable action reference {source}.", f"Pinned to {target}")
            )
    return fixed, fixes


def inspect_workflow(path: Path, report: Report) -> None:
    text = path.read_text(encoding="utf-8")
    data, err = load_yaml(path)
    if err:
        report.problems_found.append(Finding(rel(path), "critical", "yaml", f"YAML parse error: {err}"))
        return
    assert data is not None

    changed = text
    fixed, pin_fixes = safe_pin_mutable_actions(path, changed)
    if pin_fixes:
        report.problems_found.extend(
            Finding(f.file, f.severity, f.category, f.message) for f in pin_fixes
        )
        report.fixes_applied.extend(pin_fixes)
        changed = fixed

    mutable_refs = MUTABLE_ACTION_RE.findall(changed)
    for full, _ in mutable_refs:
        report.problems_found.append(
            Finding(rel(path), "medium", "action-reference", f"Mutable action reference remains: {full}", "Manual pin required; no safe replacement table entry.")
        )

    on_value = normalize_on(data)
    if isinstance(on_value, dict):
        for trigger in DANGEROUS_TRIGGER_KEYS.intersection(on_value.keys()):
            report.problems_found.append(
                Finding(rel(path), "high", "trigger", f"Risky trigger present: {trigger}", "Review isolation before allowing write tokens or secrets.")
            )

    permissions = data.get("permissions")
    if permissions is None:
        fixed, fix = ensure_default_permissions(path, data, changed)
        if fix:
            changed = fixed
            report.problems_found.append(Finding(fix.file, fix.severity, fix.category, "Workflow had no explicit default permissions."))
            report.fixes_applied.append(fix)
    elif isinstance(permissions, dict):
        for name, value in permissions.items():
            if value in ELEVATED_PERMISSIONS:
                report.problems_found.append(
                    Finding(rel(path), "medium", "permissions", f"Workflow-level elevated permission: {name}: {value}", "Prefer job-level elevation only where needed.")
                )
    elif permissions == "write-all":
        report.problems_found.append(
            Finding(rel(path), "high", "permissions", "Workflow uses permissions: write-all", "Replace with scoped job-level permissions.")
        )

    jobs = data.get("jobs", {})
    if isinstance(jobs, dict):
        for job_id, job in jobs.items():
            if not isinstance(job, dict):
                report.problems_found.append(Finding(rel(path), "critical", "jobs", f"Job {job_id} is not a mapping."))
                continue
            uses = job.get("uses")
            if isinstance(uses, str) and uses.startswith("./"):
                target = ROOT / uses[2:]
                if not target.exists():
                    report.problems_found.append(
                        Finding(rel(path), "critical", "workflow-reference", f"Reusable workflow reference missing: {uses}")
                    )
            job_permissions = job.get("permissions")
            if job_permissions == "write-all":
                report.problems_found.append(
                    Finding(rel(path), "high", "permissions", f"Job {job_id} uses write-all permissions.", "Scope to exact permissions.")
                )

    if changed != text:
        path.write_text(changed, encoding="utf-8")


def validate_yaml(paths: list[Path], report: Report) -> bool:
    ok = True
    for path in paths:
        _, err = load_yaml(path)
        if err:
            ok = False
            report.validation.append(f"FAIL yaml parse: {rel(path)} — {err}")
        else:
            report.validation.append(f"OK yaml parse: {rel(path)}")
    return ok


def git_diff_exists() -> bool:
    result = subprocess.run(["git", "status", "--porcelain"], cwd=ROOT, text=True, capture_output=True, check=False)
    return bool(result.stdout.strip())


def write_reports(report: Report) -> None:
    payload = asdict(report)
    REPORT_JSON.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")

    lines = [
        "# GitHub Workflow Repair Agent Report",
        "",
        "## Files inspected",
    ]
    lines.extend(f"- `{item}`" for item in report.files_inspected)
    lines.extend(["", "## Problems found"])
    if report.problems_found:
        for f in report.problems_found:
            lines.append(f"- **{f.severity.upper()}** `{f.file}` — {f.category}: {f.message}" + (f" Fix/Note: {f.fix}" if f.fix else ""))
    else:
        lines.append("- None detected.")
    lines.extend(["", "## Fixes applied"])
    if report.fixes_applied:
        for f in report.fixes_applied:
            lines.append(f"- `{f.file}` — {f.message} {f.fix}".rstrip())
    else:
        lines.append("- No safe automatic fixes were required.")
    lines.extend(["", "## Validation performed"])
    lines.extend(f"- {item}" for item in report.validation)
    lines.extend(["", "## Remaining risks"])
    if report.remaining_risks:
        lines.extend(f"- {item}" for item in report.remaining_risks)
    else:
        lines.append("- No unresolved critical risk identified by the local scanner.")
    lines.extend([
        "",
        "## Rollback notes",
        "Revert the generated pull request or restore the touched workflow files from the previous commit.",
    ])
    REPORT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    paths = workflow_files() + action_yml_files()
    report = Report(files_inspected=[rel(p) for p in paths], problems_found=[], fixes_applied=[], validation=[], remaining_risks=[])

    if not paths:
        report.remaining_risks.append("No workflow or action files found to inspect.")
        write_reports(report)
        return 0

    for path in paths:
        inspect_workflow(path, report)

    validate_yaml(paths, report)

    if any(f.severity == "critical" for f in report.problems_found if not f.fix):
        report.remaining_risks.append("One or more critical issues require manual repair before workflows are trustworthy.")
    if any("Mutable action reference remains" in f.message for f in report.problems_found):
        report.remaining_risks.append("Some third-party action references still need manual immutable pinning.")

    write_reports(report)
    print(REPORT_MD.read_text(encoding="utf-8"))
    print(f"workflow_agent_changed={str(git_diff_exists()).lower()}")
    return 1 if any(f.severity == "critical" and not f.fix for f in report.problems_found) else 0


if __name__ == "__main__":
    raise SystemExit(main())

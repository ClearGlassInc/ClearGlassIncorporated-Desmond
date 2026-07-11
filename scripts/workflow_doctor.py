#!/usr/bin/env python3
"""GitHub Actions workflow doctor.

Audits and repairs common workflow bootstrap failures:
- malformed YAML parsing
- deprecated / invalid action majors
- reusable workflow jobs with invalid per-job keys
- missing workflow_call support for locally-called workflows
- self-hosted runner labels without fallback
- Pages deploy permission inheritance
- missing explicit timeout-minutes (prevents hung jobs)

Run locally:
  python scripts/workflow_doctor.py --fix

CI dry run:
  python scripts/workflow_doctor.py
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:  # pragma: no cover
    print("Missing dependency: pyyaml. Install with: python -m pip install pyyaml", file=sys.stderr)
    sys.exit(2)

ROOT = Path(__file__).resolve().parents[1]
WORKFLOWS = ROOT / ".github" / "workflows"

STABLE_ACTIONS = {
    "actions/checkout": "v6",
    "actions/setup-python": "v6",
    "actions/setup-node": "v4",
    "actions/upload-artifact": "v7",
    "actions/download-artifact": "v4",
    "actions/configure-pages": "v6",
    "actions/upload-pages-artifact": "v5",
    "actions/deploy-pages": "v5",
    "actions/github-script": "v9",
    "actions/dependency-review-action": "v5",
}

INVALID_REUSABLE_JOB_KEYS = {"runs-on", "steps", "permissions"}
ALLOWED_REUSABLE_JOB_KEYS = {"name", "needs", "if", "uses", "with", "secrets", "strategy", "concurrency"}


def load_yaml(path: Path) -> tuple[dict[str, Any] | None, str | None]:
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        if not isinstance(data, dict):
            return None, "root document is not a mapping"
        return data, None
    except Exception as exc:
        return None, str(exc)


def dump_yaml(data: dict[str, Any]) -> str:
    # PyYAML 1.1 parses bare `on:` as the boolean True; restore the literal
    # key here so we never emit a `true:` block in place of the trigger map.
    if True in data:
        rebuilt: dict[Any, Any] = {}
        for key, value in data.items():
            rebuilt["on" if key is True else key] = value
        data = rebuilt
    return yaml.safe_dump(data, sort_keys=False, width=120)


def normalize_on(data: dict[str, Any]) -> Any:
    return data.get(True, data.get("on"))


def set_on(data: dict[str, Any], value: Any) -> None:
    if True in data:
        data["on"] = data.pop(True)
    data["on"] = value


def patch_action_versions(text: str) -> tuple[str, list[str]]:
    changes: list[str] = []
    for action, version in STABLE_ACTIONS.items():
        pattern = re.compile(rf"uses:\s*{re.escape(action)}@v\d+", re.IGNORECASE)
        new_text, count = pattern.subn(f"uses: {action}@{version}", text)
        if count and new_text != text:
            changes.append(f"pinned {action} to {version}")
            text = new_text
    return text, changes


def local_called_workflows(data: dict[str, Any]) -> set[str]:
    called: set[str] = set()
    jobs = data.get("jobs") or {}
    if not isinstance(jobs, dict):
        return called
    for job in jobs.values():
        if isinstance(job, dict):
            uses = job.get("uses")
            if isinstance(uses, str) and uses.startswith("./.github/workflows/"):
                called.add(uses.removeprefix("./"))
    return called


def ensure_workflow_call(path: Path, data: dict[str, Any]) -> list[str]:
    changes: list[str] = []
    on_block = normalize_on(data)
    if on_block is None:
        set_on(data, {"workflow_dispatch": None, "workflow_call": None})
        return ["created on.workflow_dispatch and on.workflow_call"]
    if isinstance(on_block, dict):
        if "workflow_call" not in on_block:
            on_block["workflow_call"] = None
            changes.append("added workflow_call trigger for local reusable call")
        set_on(data, on_block)
    return changes


def fix_reusable_jobs(data: dict[str, Any]) -> list[str]:
    changes: list[str] = []
    jobs = data.get("jobs") or {}
    if not isinstance(jobs, dict):
        return changes
    for job_name, job in jobs.items():
        if not isinstance(job, dict) or "uses" not in job:
            continue
        for key in list(job.keys()):
            if key not in ALLOWED_REUSABLE_JOB_KEYS:
                job.pop(key, None)
                changes.append(f"removed invalid reusable-job key {job_name}.{key}")
    return changes


def fix_self_hosted(data: dict[str, Any]) -> list[str]:
    changes: list[str] = []
    jobs = data.get("jobs") or {}
    if not isinstance(jobs, dict):
        return changes
    for job_name, job in jobs.items():
        if not isinstance(job, dict):
            continue
        runs_on = job.get("runs-on")
        if runs_on == "self-hosted" or (isinstance(runs_on, list) and "self-hosted" in runs_on):
            job["runs-on"] = "ubuntu-latest"
            changes.append(f"replaced self-hosted runner in {job_name} with ubuntu-latest fallback")
    return changes


def ensure_timeouts(data: dict[str, Any]) -> list[str]:
    """Add explicit timeout-minutes to prevent hung/stuck jobs (production hardening)."""
    changes: list[str] = []
    jobs = data.get("jobs") or {}
    if not isinstance(jobs, dict):
        return changes
    for job_name, job in jobs.items():
        if not isinstance(job, dict):
            continue
        # A job that calls a reusable workflow (`uses:`) cannot carry
        # timeout-minutes — the timeout lives in the called workflow's own jobs.
        # Adding it here would produce a schema-invalid workflow, so skip it.
        if "uses" in job:
            continue
        if "timeout-minutes" not in job:
            default_timeout = 60 if any(k in str(job).lower() for k in ["deploy", "scan", "audit", "build"]) else 30
            job["timeout-minutes"] = default_timeout
            changes.append(f"added timeout-minutes: {default_timeout} to {job_name}")
    return changes


def _needs_contents_write(data: dict[str, Any]) -> bool:
    """True when the workflow legitimately needs write access to repo contents.

    Some workflows must push commits or open branches (e.g. a bot that patches a
    file and commits it, or one that uses create-pull-request). Forcing those to
    ``contents: read`` would break their push step, so the doctor must not
    downgrade them. Detection is intentionally conservative: an explicit
    ``git push``/``git commit`` in a run step, the create-pull-request action, or
    a job that already declares job-level ``contents: write``.
    """
    blob = str(data)
    if "git push" in blob or "git commit" in blob or "create-pull-request" in blob:
        return True
    jobs = data.get("jobs") or {}
    if isinstance(jobs, dict):
        for job in jobs.values():
            if isinstance(job, dict):
                perms = job.get("permissions")
                if isinstance(perms, dict) and perms.get("contents") == "write":
                    return True
    return False


def ensure_permissions(data: dict[str, Any]) -> list[str]:
    changes: list[str] = []
    text_needs_pages = "deploy-pages" in str(data) or "upload-pages-artifact" in str(data)
    needs_write = _needs_contents_write(data)
    permissions = data.get("permissions")
    if permissions is None or permissions == "read-all":
        permissions = {"contents": "write" if needs_write else "read"}
    if isinstance(permissions, dict):
        # Least privilege: downgrade to read — but never for workflows that must
        # push/commit, or their write step would fail at runtime.
        if permissions.get("contents") != "read" and not needs_write:
            permissions["contents"] = "read"
            changes.append("normalized contents permission to read")
        if text_needs_pages and not _pages_perms_at_job_level(data):
            for key, value in {"pages": "write", "id-token": "write"}.items():
                if permissions.get(key) != value:
                    permissions[key] = value
                    changes.append(f"added {key}: {value} for Pages deploy")
        data["permissions"] = permissions
    return changes


def _pages_perms_at_job_level(data: dict[str, Any]) -> bool:
    """Job-level pages/id-token write satisfies least privilege — don't widen to workflow level."""
    jobs = data.get("jobs") or {}
    if not isinstance(jobs, dict):
        return False
    for job in jobs.values():
        if not isinstance(job, dict):
            continue
        perms = job.get("permissions")
        if isinstance(perms, dict) and perms.get("pages") == "write" and perms.get("id-token") == "write":
            return True
    return False


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--fix", action="store_true", help="write repairs to disk")
    args = parser.parse_args()

    if not WORKFLOWS.exists():
        print("No .github/workflows directory found")
        return 0

    findings: list[str] = []
    all_called: set[str] = set()
    parsed: dict[Path, dict[str, Any]] = {}

    for path in sorted(WORKFLOWS.glob("*.y*ml")):
        original = path.read_text(encoding="utf-8")
        patched_text, action_changes = patch_action_versions(original)
        if patched_text != original and args.fix:
            path.write_text(patched_text, encoding="utf-8")
        data, error = load_yaml(path)
        if error:
            findings.append(f"ERROR {path}: YAML parse failed: {error}")
            continue
        assert data is not None
        parsed[path] = data
        all_called |= local_called_workflows(data)
        if action_changes and args.fix:
            findings.extend(f"FIX {path}: {c}" for c in action_changes)
        elif action_changes:
            findings.extend(f"NEEDS_FIX {path}: {c}" for c in action_changes)

    for path, data in parsed.items():
        changes: list[str] = []
        changes += fix_reusable_jobs(data)
        changes += fix_self_hosted(data)
        if args.fix:
            changes += ensure_timeouts(data)
        changes += ensure_permissions(data)
        rel = str(path.relative_to(ROOT))
        if rel in all_called:
            changes += ensure_workflow_call(path, data)
        if changes:
            prefix = "FIX" if args.fix else "NEEDS_FIX"
            findings.extend(f"{prefix} {path}: {c}" for c in changes)
            if args.fix:
                path.write_text(dump_yaml(data), encoding="utf-8")

    for item in findings:
        print(item)

    errors = [f for f in findings if f.startswith("ERROR")]
    needs_fix = [f for f in findings if f.startswith("NEEDS_FIX")]
    if errors:
        return 1
    # Advisory only — repair job applies fixes on schedule/dispatch
    if needs_fix:
        print("Workflow doctor found repairable issues. Run with --fix to apply.")
    print("Workflow doctor clean." if not findings else "Workflow doctor repairs complete.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
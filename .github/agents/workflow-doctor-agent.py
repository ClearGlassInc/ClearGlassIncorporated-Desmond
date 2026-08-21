#!/usr/bin/env python3
"""Read-only workflow doctor.

The agent classifies evidence and records proposals. It never silently changes
production workflows or bypasses GitHub security controls.
"""
from __future__ import annotations

import json
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PATTERNS = ROOT / "workflow-patterns.json"


def gh(*args: str) -> str:
    result = subprocess.run(["gh", *args], text=True, capture_output=True, check=False)
    if result.returncode:
        raise RuntimeError(result.stderr.strip() or f"gh exited {result.returncode}")
    return result.stdout


def main() -> int:
    repo = os.environ.get("GITHUB_REPOSITORY", "")
    if not repo:
        raise SystemExit("GITHUB_REPOSITORY is required")

    raw = gh("run", "list", "--repo", repo, "--limit", "100", "--json", "databaseId,name,status,conclusion,workflowName,url,createdAt")
    runs = json.loads(raw)
    patterns = json.loads(PATTERNS.read_text(encoding="utf-8"))
    existing = patterns.setdefault("patterns", [])

    for run in runs:
        if run.get("conclusion") in {"failure", "cancelled", "timed_out", "startup_failure"}:
            existing.append({
                "id": f"run-{run['databaseId']}",
                "workflow": run.get("workflowName"),
                "root_cause": "requires-evidence",
                "status": run.get("status"),
                "conclusion": run.get("conclusion"),
                "run_url": run.get("url"),
                "observed_at": datetime.now(timezone.utc).isoformat(),
            })

    # Deduplicate by immutable run ID while preserving chronology.
    unique = {item.get("id"): item for item in existing if item.get("id")}
    patterns["patterns"] = list(unique.values())
    PATTERNS.write_text(json.dumps(patterns, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

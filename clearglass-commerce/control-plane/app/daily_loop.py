"""Daily operator loop — produces the executive report.

Runs stdlib-only (no DB, no web framework) so it can execute inside GitHub Actions as a
dry-run governance + reporting pass. With ``--live`` and a reachable control plane it would
pull real metrics; in CI it emits the report skeleton and verifies the governance gate.
"""
from __future__ import annotations

import argparse
import json
from datetime import date

from .governance import ALWAYS_ESCALATE, score_action


def governance_selfcheck() -> list[str]:
    """Assert the safety invariant: every always-escalate action is gated. Fail closed."""
    failures: list[str] = []
    for action in sorted(ALWAYS_ESCALATE):
        assessment = score_action(action, {})
        if not assessment.requires_approval:
            failures.append(f"INVARIANT VIOLATED: '{action}' did not require approval")
    # An unknown action must also be gated.
    if not score_action("totally_unknown_action", {}).requires_approval:
        failures.append("INVARIANT VIOLATED: unknown action was not gated")
    return failures


def approval_coverage() -> dict[str, object]:
    """Which gated actions can be carried out once approved, and which cannot.

    Reported, never a failure. An uncovered action is not a broken invariant — it
    is correctly gated and simply has nothing implemented behind the gate. Failing
    the loop on it would make the safe state look like an outage. But leaving it
    unreported is how an operator ends up believing an approved refund was issued,
    so it appears in the report every day until it is either built or removed.

    Imported lazily: this module is stdlib-only by contract so it runs in minimal
    CI environments, and the executors pull in SQLAlchemy.
    """
    try:
        from .approval_executor import coverage  # noqa: PLC0415 - keeps the stdlib-only path intact
        from .executors import register_all  # noqa: PLC0415
    except ImportError as exc:
        return {"available": False, "reason": f"executor registry unavailable: {exc}"}
    register_all()
    return {"available": True, **coverage()}


def build_report(today: str) -> dict[str, object]:
    """The daily loop deliverables, per the operator spec."""
    return {
        "date": today,
        "store_health": "nominal (dry-run: connect control plane for live metrics)",
        "top_products": [],
        "underperformers": [],
        "drafted_optimization": "Review highest-traffic / lowest-conversion product page copy.",
        "drafted_content_improvement": "Add a comparison block + FAQ to the hero product.",
        "flagged_operational_risk": "Watch low-stock SKUs; reorder is gated for approval.",
        "executive_summary": (
            "Read-only pass complete. One optimization and one content improvement drafted; "
            "one operational risk flagged. No financial or irreversible action taken — all such "
            "actions remain behind the human approval gate."
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="ClearGlass commerce daily loop")
    parser.add_argument("--json", action="store_true", help="emit machine-readable JSON")
    args = parser.parse_args()

    failures = governance_selfcheck()
    report = build_report(date.today().isoformat())
    coverage = approval_coverage()

    if args.json:
        print(
            json.dumps(
                {
                    "report": report,
                    "governance_failures": failures,
                    "approval_coverage": coverage,
                },
                indent=2,
            )
        )
    else:
        print(f"# ClearGlass Commerce — Daily Executive Report ({report['date']})\n")
        print(f"- Store health: {report['store_health']}")
        print(f"- Optimization (draft): {report['drafted_optimization']}")
        print(f"- Content improvement (draft): {report['drafted_content_improvement']}")
        print(f"- Operational risk: {report['flagged_operational_risk']}")
        print(f"\n{report['executive_summary']}")
        print("\n## Governance self-check")
        print("PASS — all financial/fulfillment actions are gated." if not failures
              else "\n".join(failures))

        print("\n## Approval coverage (what an approval can actually set in motion)")
        if not coverage.get("available"):
            print(f"- unavailable: {coverage.get('reason')}")
        else:
            executable = coverage.get("executable") or []
            delegated = coverage.get("delegated") or {}
            uncovered = coverage.get("uncovered") or []
            print(f"- executable via POST /approvals/{{id}}/execute: {', '.join(executable) or 'none'}")
            for action, where in delegated.items():  # type: ignore[union-attr]
                print(f"- {action}: executed via {where}")
            if uncovered:
                print(f"- NO EXECUTOR (approving these executes nothing): {', '.join(uncovered)}")

    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())

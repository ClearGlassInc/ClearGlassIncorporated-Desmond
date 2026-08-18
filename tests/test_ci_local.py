"""The local gate runner must mirror ci.yml, not drift away from it.

`scripts/ci_local.py` exists so the repository can be validated while GitHub
Actions is unavailable. Its whole value is that a green summary means the same
thing CI would have meant. A gate that quietly disappears from the runner turns
that summary into a false assurance, which is worse than having no runner — so
the mapping between ci.yml's jobs and the runner's gates is asserted here.
"""

from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("ci_local", ROOT / "scripts/ci_local.py")
assert SPEC and SPEC.loader
ci_local = importlib.util.module_from_spec(SPEC)
# dataclasses resolves a field's default_factory through sys.modules[__module__],
# so the module has to be registered before it is executed.
sys.modules[SPEC.name] = ci_local
SPEC.loader.exec_module(ci_local)


def workflow_jobs() -> set[str]:
    workflow = yaml.safe_load((ROOT / ".github/workflows/ci.yml").read_text(encoding="utf-8"))
    return set(workflow["jobs"])


def test_every_ci_job_has_a_local_gate() -> None:
    covered = {gate.job for gate in ci_local.GATES}
    missing = sorted(workflow_jobs() - covered)
    assert not missing, (
        "ci.yml jobs with no gate in scripts/ci_local.py: "
        + ", ".join(missing)
        + " — add them, or the local run reports green while skipping a check"
    )


def test_no_gate_points_at_a_job_that_no_longer_exists() -> None:
    jobs = workflow_jobs()
    orphans = sorted(gate.key for gate in ci_local.GATES if gate.job not in jobs)
    assert not orphans, f"gates referencing removed ci.yml jobs: {', '.join(orphans)}"


def test_gate_keys_are_unique() -> None:
    keys = [gate.key for gate in ci_local.GATES]
    assert len(keys) == len(set(keys))


def test_selectors_reject_unknown_gate_names() -> None:
    args = ci_local.parse_args(["--only", "definitely-not-a-gate"])
    try:
        ci_local.select(args)
    except SystemExit as exc:
        assert "unknown gate" in str(exc)
    else:  # pragma: no cover - guards against a silent no-op selector
        raise AssertionError("an unknown --only value must not be accepted silently")


def test_fast_mode_skips_only_network_bound_gates() -> None:
    for gate in ci_local.GATES:
        skipped = ci_local.missing_requirements(gate, fast=True)
        wants_network = ci_local.NEEDS_NETWORK in gate.requires
        assert bool(skipped) == wants_network or not wants_network


def test_runner_lists_its_gates_without_running_them() -> None:
    """--list must stay a dry description, so it is safe on any machine."""
    completed = subprocess.run(
        [sys.executable, "scripts/ci_local.py", "--list"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert completed.returncode == 0
    for gate in ci_local.GATES:
        assert gate.key in completed.stdout

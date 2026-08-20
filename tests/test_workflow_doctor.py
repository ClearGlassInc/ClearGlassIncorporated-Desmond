"""Regression tests for scripts.workflow_doctor."""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

# The doctor calls sys.exit(2) at import if pyyaml is missing; skip cleanly
# so the suite reports a clear "skip" instead of a fixture crash.
pytest.importorskip("yaml")

ROOT = Path(__file__).resolve().parents[1]
DOCTOR_PATH = ROOT / "scripts" / "workflow_doctor.py"


@pytest.fixture(scope="module")
def doctor():
    spec = importlib.util.spec_from_file_location("workflow_doctor", DOCTOR_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules["workflow_doctor"] = module
    spec.loader.exec_module(module)
    return module


def test_dump_yaml_preserves_on_key(doctor):
    # PyYAML 1.1 parses bare `on:` into the Python boolean True; if dump_yaml
    # doesn't normalize it back, the rewritten workflow loses its triggers
    # and becomes a no-op.
    parsed = doctor.yaml.safe_load("on:\n  push:\n    branches: [main]\njobs:\n  a:\n    runs-on: ubuntu-latest\n    steps: []\n")
    assert True in parsed, "fixture precondition: PyYAML must parse on: as True"

    rendered = doctor.dump_yaml(parsed)
    assert "true:" not in rendered.splitlines()[0:3]
    reparsed = doctor.yaml.safe_load(rendered)
    assert "on" in reparsed or True in reparsed
    trigger = reparsed.get("on") or reparsed.get(True)
    assert "push" in trigger


def test_patch_action_versions_bumps_stable(doctor):
    text = "      - uses: actions/checkout@v4\n      - uses: actions/upload-artifact@v4\n"
    new_text, changes = doctor.patch_action_versions(text)
    assert "actions/checkout@v6" in new_text
    assert "actions/upload-artifact@v7" in new_text
    assert any("checkout" in c for c in changes)
    assert any("upload-artifact" in c for c in changes)


def test_patch_action_versions_leaves_sha_pins_alone(doctor):
    text = "      - uses: actions/checkout@692973e3d937129bcbf40652eb9f2f61becf3332\n"
    new_text, changes = doctor.patch_action_versions(text)
    assert new_text == text
    assert changes == []


def test_unpinned_external_actions_checks_composite_steps(doctor, tmp_path):
    action_file = tmp_path / "action.yml"
    mutable = "runs:\n  using: composite\n  steps:\n    - uses: actions/setup-python@v6\n"
    assert doctor.unpinned_external_actions(action_file, mutable) == [
        f"ERROR {action_file}: external action is not pinned to a full commit SHA: actions/setup-python@v6"
    ]

    pinned = mutable.replace("@v6", "@a309ff8b426b58ec0e2a45f0f869d46889d02405")
    assert doctor.unpinned_external_actions(action_file, pinned) == []


def test_self_hosted_runners_are_rewritten_to_hosted(doctor):
    """A public, forkable repository must not run jobs on machines we own.

    A pull request from a fork runs that fork's code. On a self-hosted runner
    that is arbitrary code execution on the host, which also holds a runner
    registration token. This repository is public with forking enabled, so the
    doctor rewrites the label rather than trusting reviewers to catch it.
    """
    data = {
        "jobs": {
            "scalar": {"runs-on": "self-hosted"},
            "labelled": {"runs-on": ["self-hosted", "linux", "x64"]},
            "hosted": {"runs-on": "ubuntu-latest"},
        }
    }
    changes = doctor.fix_self_hosted(data)

    assert data["jobs"]["scalar"]["runs-on"] == "ubuntu-latest"
    assert data["jobs"]["labelled"]["runs-on"] == "ubuntu-latest"
    assert data["jobs"]["hosted"]["runs-on"] == "ubuntu-latest", "must not disturb hosted jobs"
    assert len(changes) == 2


def test_shipped_workflows_declare_no_self_hosted_runner(doctor):
    """The policy above is only worth anything if the tree actually obeys it."""
    import yaml

    offenders: list[str] = []
    for path in sorted((ROOT / ".github" / "workflows").glob("*.yml")):
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        for name, job in ((data or {}).get("jobs") or {}).items():
            if not isinstance(job, dict):
                continue
            runs_on = job.get("runs-on")
            labels = runs_on if isinstance(runs_on, list) else [runs_on]
            if "self-hosted" in labels:
                offenders.append(f"{path.name}:{name}")
    assert not offenders, "self-hosted runners on a public repository: " + ", ".join(offenders)

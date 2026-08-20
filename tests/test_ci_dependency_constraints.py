"""Regression checks for deterministic Python test environments.

A dependency that is declared but never installed does not fail the build — it
turns the tests that need it into skips, and a suite reporting "1318 passed"
with a handful of quiet skips looks indistinguishable from one that verified
everything. That is how the two control-surface feed *contract* validations
went unrun on every CI run for as long as they have existed, and it is the same
failure mode `clearglass-commerce/control-plane/requirements.txt` already
documents in its httpx comment.
"""

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REQUIREMENTS = ROOT / "requirements.txt"


def declared_distributions() -> set[str]:
    """Distribution names requirements.txt asks for."""
    names = set()
    for line in REQUIREMENTS.read_text(encoding="utf-8").splitlines():
        line = line.split("#", 1)[0].strip()
        if not line or line.startswith("-"):
            continue
        match = re.match(r"^([A-Za-z0-9._-]+)", line)
        if match:
            names.add(match.group(1).lower())
    return names


def test_python_ci_installs_requirements_rather_than_only_constraining_them() -> None:
    """`-c requirements.txt` pins versions; it installs nothing.

    pip applies a constraints file only to packages some other argument already
    pulls in. `jsonschema` is declared in requirements.txt and in no extra of
    pyproject.toml, so under `-c` it was never installed on a CI runner and
    `tests/test_control_surface_feeds.py` skipped its two schema checks in
    silence. Reproduced in a clean venv by running this job's exact install
    lines. `-r` keeps the same pins — they live in the file — and installs.
    """
    workflow = (ROOT / ".github/workflows/ci.yml").read_text(encoding="utf-8")

    assert 'pip install -r requirements.txt -e ".[test]"' in workflow, (
        "ci.yml must install requirements.txt, not merely constrain with it — "
        "anything declared there but absent from an extra is silently skipped"
    )
    assert 'pip install -c requirements.txt -e ".[test]"' not in workflow


def test_every_declared_dependency_is_reachable_from_the_test_job() -> None:
    """Nothing in requirements.txt may be orphaned from the install command."""
    workflow = (ROOT / ".github/workflows/ci.yml").read_text(encoding="utf-8")
    install = next(
        line for line in workflow.splitlines()
        if "pip install" in line and "requirements.txt" in line and '".[test]"' in line
    )
    assert " -r requirements.txt" in install, install

    # Guard the declarations themselves: a name with no version bound drifts.
    unpinned = [
        name for name in declared_distributions()
        if not re.search(
            rf"^{re.escape(name)}\s*[<>=~!]", REQUIREMENTS.read_text(encoding="utf-8"),
            re.I | re.M,
        )
    ]
    assert not unpinned, f"requirements.txt entries with no version bound: {unpinned}"


def test_test_only_dependencies_are_declared_not_assumed() -> None:
    """Packages the suite imports must be declared, or their tests just skip.

    Both of these were found skipping: `jsonschema` was declared but orphaned by
    `-c`, and `Pillow` was declared nowhere at all, so the 15 tests in
    `tests/test_generate_favicons.py` had never run in CI.
    """
    declared = declared_distributions()
    for name in ("jsonschema", "pillow", "pytest"):
        assert name in declared, f"{name} must be declared in requirements.txt"


def test_function_agent_ci_uses_reviewed_test_tool_constraints() -> None:
    workflow = (ROOT / ".github/workflows/function-agent-ci.yml").read_text(encoding="utf-8")

    assert 'pip install -c requirements.txt -e ".[dev]"' in workflow

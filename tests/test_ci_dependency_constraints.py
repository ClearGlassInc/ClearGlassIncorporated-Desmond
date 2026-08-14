"""Regression checks for deterministic Python test environments."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_python_ci_uses_reviewed_test_tool_constraints() -> None:
    workflow = (ROOT / ".github/workflows/ci.yml").read_text(encoding="utf-8")

    assert 'pip install -c requirements.txt -e ".[test]"' in workflow


def test_function_agent_ci_uses_reviewed_test_tool_constraints() -> None:
    workflow = (ROOT / ".github/workflows/function-agent-ci.yml").read_text(encoding="utf-8")

    assert 'pip install -c requirements.txt -e ".[dev]"' in workflow

from pathlib import Path

from scripts.audit_github_actions import GitHubLoader, Result, audit
import yaml


def workflow(tmp_path: Path, text: str) -> Result:
    path = tmp_path / "workflow.yml"
    path.write_text(text)
    data = yaml.load(text, Loader=GitHubLoader)
    result = Result(path=path, data=data)
    audit(result)
    return result


def test_loader_preserves_on_trigger(tmp_path: Path) -> None:
    result = workflow(
        tmp_path,
        """on: {workflow_dispatch: null}
permissions: {contents: read}
jobs:
  check:
    runs-on: ubuntu-latest
    timeout-minutes: 5
    steps: [{run: 'echo safe'}]
""",
    )
    assert "workflow_dispatch" in result.data["on"]
    assert result.status == "valid and ready"


def test_unpinned_action_fails_closed(tmp_path: Path) -> None:
    result = workflow(
        tmp_path,
        """on: {push: null}
permissions: {contents: read}
jobs:
  check:
    runs-on: ubuntu-latest
    timeout-minutes: 5
    steps: [{uses: actions/checkout@v4}]
""",
    )
    assert any("full commit SHA" in error for error in result.errors)
    assert result.status == "broken and requiring immediate patching"


def test_deploy_without_environment_requires_governance(tmp_path: Path) -> None:
    result = workflow(
        tmp_path,
        """on: {workflow_dispatch: null}
permissions: {contents: read}
jobs:
  test:
    runs-on: ubuntu-latest
    timeout-minutes: 5
    steps: [{run: 'echo test'}]
  deploy:
    needs: test
    runs-on: ubuntu-latest
    timeout-minutes: 5
    steps: [{run: 'curl -fsS "$HOOK"'}]
""",
    )
    assert result.status == "unsafe and requiring governance changes before execution"

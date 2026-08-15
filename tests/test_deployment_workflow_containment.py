import re

import yaml

from scripts.audit_github_actions import ROOT, GitHubLoader


def test_pages_deployment_is_manual_and_cannot_mutate_source_mode() -> None:
    path = ROOT / ".github/workflows/pages.yml"
    text = path.read_text(encoding="utf-8")
    data = yaml.load(text, Loader=GitHubLoader)

    triggers = data["on"]
    assert isinstance(triggers, dict)
    assert set(triggers) == {"workflow_dispatch"}

    build = data["jobs"]["build"]
    assert build.get("permissions") == {"contents": "read"}

    for step in build.get("steps", []):
        run = step.get("run")
        if not isinstance(run, str) or "/pages" not in run:
            continue
        assert not re.search(r"\b(?:PUT|PATCH|DELETE)\b", run, flags=re.IGNORECASE)

    deploy_permissions = data["jobs"]["deploy"]["permissions"]
    assert deploy_permissions["pages"] == "write"
    assert deploy_permissions["id-token"] == "write"

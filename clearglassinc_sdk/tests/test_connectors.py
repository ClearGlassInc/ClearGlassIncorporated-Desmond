import sys

import pytest

CONNECTORS = [
    ("clearglassinc_sdk.connectors.github", "GitHubConnector"),
    ("clearglassinc_sdk.connectors.slack", "SlackConnector"),
    ("clearglassinc_sdk.connectors.outlook", "OutlookConnector"),
]


@pytest.mark.parametrize("module_name,class_name", CONNECTORS)
def test_connector_raises_clean_import_error_without_httpx(module_name, class_name):
    if "httpx" in sys.modules:
        pytest.skip("httpx is installed in this environment; import-error path not exercised")

    import importlib

    connector_cls = getattr(importlib.import_module(module_name), class_name)
    with pytest.raises(ImportError, match="httpx"):
        connector_cls("fake-token")


# --- Behavior tests, exercised whenever httpx is available -------------------

httpx = pytest.importorskip("httpx")


def _connector_with_transport(connector_cls, handler, **kwargs):
    """Build a connector, then swap its httpx client for a mock transport so
    the request-shaping logic is tested without any network access."""
    connector = connector_cls("fake-token", **kwargs)
    connector._client = httpx.Client(
        base_url=str(connector._client.base_url),
        headers=connector._client.headers,
        transport=httpx.MockTransport(handler),
    )
    return connector


@pytest.mark.parametrize("module_name,class_name", CONNECTORS)
def test_connector_exposes_tools_with_schemas(module_name, class_name):
    import importlib

    connector_cls = getattr(importlib.import_module(module_name), class_name)
    tools = connector_cls("fake-token").as_tools()

    assert tools
    for tool in tools:
        schema = tool.to_schema()
        assert schema["name"]
        assert schema["description"]
        assert schema["parameters"]["type"] == "object"


def test_github_list_issues_calls_the_right_endpoint():
    from clearglassinc_sdk.connectors.github import GitHubConnector

    seen = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["url"] = str(request.url)
        seen["auth"] = request.headers.get("authorization")
        return httpx.Response(200, json=[{"number": 1, "title": "a bug"}])

    connector = _connector_with_transport(GitHubConnector, handler)
    issues = connector.list_issues("owner/repo", state="open")

    assert issues[0]["title"] == "a bug"
    assert "/repos/owner/repo/issues" in seen["url"]
    assert "state=open" in seen["url"]
    assert seen["auth"] == "Bearer fake-token"


def test_github_create_issue_posts_title_and_body():
    from clearglassinc_sdk.connectors.github import GitHubConnector

    seen = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["method"] = request.method
        seen["body"] = request.content.decode()
        return httpx.Response(201, json={"number": 7})

    connector = _connector_with_transport(GitHubConnector, handler)
    result = connector.create_issue("owner/repo", title="Bug", body="Details")

    assert result["number"] == 7
    assert seen["method"] == "POST"
    assert "Bug" in seen["body"]


def test_github_raises_on_http_error():
    from clearglassinc_sdk.connectors.github import GitHubConnector

    connector = _connector_with_transport(
        GitHubConnector, lambda request: httpx.Response(404, json={"message": "Not Found"})
    )
    with pytest.raises(httpx.HTTPStatusError):
        connector.list_issues("owner/missing")


def test_slack_send_message_posts_to_chat_postmessage():
    from clearglassinc_sdk.connectors.slack import SlackConnector

    seen = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["url"] = str(request.url)
        return httpx.Response(200, json={"ok": True})

    connector = _connector_with_transport(SlackConnector, handler)
    assert connector.send_message("#general", "hello")["ok"] is True
    assert seen["url"].endswith("/chat.postMessage")


def test_slack_list_channels_unwraps_the_channels_key():
    from clearglassinc_sdk.connectors.slack import SlackConnector

    connector = _connector_with_transport(
        SlackConnector,
        lambda request: httpx.Response(200, json={"ok": True, "channels": [{"name": "general"}]}),
    )
    assert connector.list_channels() == [{"name": "general"}]


def test_outlook_send_mail_builds_a_graph_payload():
    from clearglassinc_sdk.connectors.outlook import OutlookConnector

    seen = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["url"] = str(request.url)
        seen["body"] = request.content.decode()
        return httpx.Response(202)

    connector = _connector_with_transport(OutlookConnector, handler)
    result = connector.send_mail("someone@example.com", "Subject", "Body")

    assert result["status"] == "sent"
    assert seen["url"].endswith("/me/sendMail")
    assert "someone@example.com" in seen["body"]
    assert "toRecipients" in seen["body"]


def test_outlook_list_events_unwraps_the_value_key():
    from clearglassinc_sdk.connectors.outlook import OutlookConnector

    connector = _connector_with_transport(
        OutlookConnector,
        lambda request: httpx.Response(200, json={"value": [{"subject": "Standup"}]}),
    )
    assert connector.list_events() == [{"subject": "Standup"}]

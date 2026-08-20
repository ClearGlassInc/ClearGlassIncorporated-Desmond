"""Tests for the real provider adapters (OpenAI, Anthropic).

The rest of the suite runs against `FakeLLMClient`, so nothing else exercises
the translation layer between our provider-agnostic `Message`/tool schemas and
each vendor's wire format — the code most likely to break on an SDK upgrade.

These construct the adapters against the actually-installed SDKs (with dummy
keys — no network is touched) and assert the translation helpers directly.
Each class skips cleanly when its SDK isn't installed; the `all` extra
installs both, and CI installs that extra so these always run there.
"""

import pytest

from clearglassinc_sdk.memory import Message

TOOL_SCHEMA = {
    "name": "ping",
    "description": "Returns pong",
    "parameters": {"type": "object", "properties": {"loud": {"type": "boolean"}}, "required": []},
}


class _Usage:
    """Stands in for a provider usage object (duck-typed via getattr)."""

    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)


class TestOpenAIAdapter:
    @pytest.fixture
    def client(self):
        pytest.importorskip("openai")
        from clearglassinc_sdk.clients.openai_client import OpenAIClient

        return OpenAIClient(api_key="sk-test-not-a-real-key", model="gpt-4o-mini", timeout=30.0)

    def test_system_prompt_is_prepended_as_a_system_message(self, client):
        payload = client._to_openai_messages([Message(role="user", content="hi")], "BE HELPFUL")
        assert payload[0] == {"role": "system", "content": "BE HELPFUL"}
        assert payload[1]["role"] == "user"

    def test_no_system_message_when_none_given(self, client):
        payload = client._to_openai_messages([Message(role="user", content="hi")], None)
        assert [m["role"] for m in payload] == ["user"]

    def test_tool_messages_carry_their_call_id(self, client):
        messages = [Message(role="tool", content="pong", name="ping", tool_call_id="c1")]
        payload = client._to_openai_messages(messages, None)
        assert payload[0]["tool_call_id"] == "c1"
        assert payload[0]["name"] == "ping"

    def test_tools_are_wrapped_in_the_function_envelope(self, client):
        tools = client._to_openai_tools([TOOL_SCHEMA])
        assert tools[0]["type"] == "function"
        assert tools[0]["function"]["name"] == "ping"
        assert tools[0]["function"]["parameters"]["properties"]["loud"]["type"] == "boolean"

    def test_empty_tool_list_becomes_none(self, client):
        # OpenAI rejects an empty `tools` array, so it must be omitted entirely.
        assert client._to_openai_tools(None) is None
        assert client._to_openai_tools([]) is None

    def test_usage_is_mapped_from_prompt_and_completion_tokens(self, client):
        usage = client._parse_usage(_Usage(prompt_tokens=11, completion_tokens=5))
        assert (usage.input_tokens, usage.output_tokens, usage.total_tokens) == (11, 5, 16)

    def test_missing_usage_is_none(self, client):
        assert client._parse_usage(None) is None

    def test_streamed_tool_call_deltas_are_reassembled(self, client):
        buffer = {0: {"id": "c1", "name": "ping", "arguments": '{"loud": true}'}}
        calls = client._accumulate_tool_calls(buffer)
        assert calls[0].id == "c1"
        assert calls[0].name == "ping"
        assert calls[0].arguments == {"loud": True}

    def test_multiple_streamed_tool_calls_keep_index_order(self, client):
        buffer = {
            1: {"id": "b", "name": "second", "arguments": "{}"},
            0: {"id": "a", "name": "first", "arguments": "{}"},
        }
        assert [c.name for c in client._accumulate_tool_calls(buffer)] == ["first", "second"]

    def test_truncated_tool_call_json_degrades_to_empty_arguments(self, client):
        # A stream cut mid-flight must not raise while parsing partial JSON.
        buffer = {0: {"id": "c1", "name": "ping", "arguments": '{"loud":'}}
        assert client._accumulate_tool_calls(buffer)[0].arguments == {}

    def test_tool_call_without_a_name_is_dropped(self, client):
        assert client._accumulate_tool_calls({0: {"id": "c1", "arguments": "{}"}}) == []


class TestAnthropicAdapter:
    @pytest.fixture
    def client(self):
        pytest.importorskip("anthropic")
        from clearglassinc_sdk.clients.anthropic_client import AnthropicClient

        return AnthropicClient(
            api_key="sk-ant-test-not-a-real-key", model="claude-sonnet-5", timeout=30.0
        )

    def test_system_messages_are_stripped_from_the_message_list(self, client):
        # Anthropic takes the system prompt as a top-level arg, not a message.
        messages = [Message(role="system", content="ignored"), Message(role="user", content="hi")]
        payload = client._to_anthropic_messages(messages)
        assert [m["role"] for m in payload] == ["user"]

    def test_tool_results_become_user_turn_tool_result_blocks(self, client):
        messages = [Message(role="tool", content="pong", name="ping", tool_call_id="tu_1")]
        payload = client._to_anthropic_messages(messages)
        block = payload[0]["content"][0]
        assert payload[0]["role"] == "user"
        assert block["type"] == "tool_result"
        assert block["tool_use_id"] == "tu_1"
        assert block["content"] == "pong"

    def test_tools_use_input_schema_not_parameters(self, client):
        tools = client._to_anthropic_tools([TOOL_SCHEMA])
        assert tools[0]["name"] == "ping"
        assert "input_schema" in tools[0]
        assert "parameters" not in tools[0]
        assert tools[0]["input_schema"]["properties"]["loud"]["type"] == "boolean"

    def test_empty_tool_list_becomes_none(self, client):
        assert client._to_anthropic_tools(None) is None
        assert client._to_anthropic_tools([]) is None

    def test_usage_is_mapped_from_input_and_output_tokens(self, client):
        usage = client._parse_usage(_Usage(input_tokens=7, output_tokens=3))
        assert (usage.input_tokens, usage.output_tokens, usage.total_tokens) == (7, 3, 10)

    def test_missing_usage_is_none(self, client):
        assert client._parse_usage(None) is None

    def test_response_parsing_splits_text_and_tool_use_blocks(self, client):
        class Block:
            def __init__(self, **kwargs):
                self.__dict__.update(kwargs)

        response = _Usage(
            content=[
                Block(type="text", text="Let me check. "),
                Block(type="tool_use", id="tu_1", name="ping", input={"loud": True}),
                Block(type="text", text="Done."),
            ],
            usage=_Usage(input_tokens=4, output_tokens=2),
        )
        result = client._parse_response(response)

        assert result.content == "Let me check. Done."
        assert result.has_tool_calls
        assert result.tool_calls[0].name == "ping"
        assert result.tool_calls[0].arguments == {"loud": True}
        assert result.usage.total_tokens == 6

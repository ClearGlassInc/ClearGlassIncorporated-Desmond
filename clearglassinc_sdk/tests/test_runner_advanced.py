"""Tests for the Runner's advanced wiring: tracing, retry, structured output,
sessions, and usage accounting."""

import pytest

from clearglassinc_sdk.agent import Agent
from clearglassinc_sdk.exceptions import ToolExecutionError
from clearglassinc_sdk.retry import RetryPolicy
from clearglassinc_sdk.runner import Runner
from clearglassinc_sdk.sessions import InMemorySessionStore
from clearglassinc_sdk.structured import OutputSchema, OutputValidationError
from clearglassinc_sdk.testing import (
    ChunkedFakeLLMClient,
    FakeLLMClient,
    FlakyLLMClient,
    text_response,
    tool_call_response,
)
from clearglassinc_sdk.tools import tool
from clearglassinc_sdk.tracing import InMemoryExporter, Tracer, Usage

TRIAGE_SCHEMA = OutputSchema(
    name="triage",
    schema={
        "type": "object",
        "properties": {"severity": {"type": "string", "enum": ["low", "high"]}},
        "required": ["severity"],
    },
)


def test_run_emits_run_step_and_llm_spans():
    agent = Agent(name="A", instructions="Be helpful.")
    exporter = InMemoryExporter()
    client = FakeLLMClient(responses=[text_response("done")])

    Runner(agent, client, tracer=Tracer(exporters=[exporter])).run("hi")

    kinds = {span.kind for span in exporter.spans}
    assert {"run", "step", "llm", "guardrail"} <= kinds


def test_tool_calls_produce_tool_spans():
    agent = Agent(name="A", instructions="Be helpful.")

    @tool()
    def ping() -> str:
        return "pong"

    agent.add_tool(ping)
    exporter = InMemoryExporter()
    client = FakeLLMClient(
        responses=[tool_call_response("c1", "ping", {}), text_response("done")]
    )

    Runner(agent, client, tracer=Tracer(exporters=[exporter])).run("call ping")

    tool_spans = exporter.by_kind("tool")
    assert [span.name for span in tool_spans] == ["ping"]


def test_failing_tool_span_records_the_error():
    agent = Agent(name="A", instructions="Be helpful.")

    @tool()
    def boom() -> str:
        raise RuntimeError("kaboom")

    agent.add_tool(boom)
    exporter = InMemoryExporter()
    client = FakeLLMClient(responses=[tool_call_response("c1", "boom", {})])

    with pytest.raises(ToolExecutionError):
        Runner(agent, client, tracer=Tracer(exporters=[exporter])).run("go")

    assert exporter.by_kind("tool")[0].error is not None


def test_run_result_reports_token_usage():
    agent = Agent(name="A", instructions="Be helpful.")
    client = FakeLLMClient(
        responses=[text_response("done", usage=Usage(input_tokens=100, output_tokens=25))]
    )

    result = Runner(agent, client, tracer=Tracer(exporters=[InMemoryExporter()])).run("hi")

    assert result.usage.input_tokens == 100
    assert result.usage.total_tokens == 125
    assert result.trace_id


def test_runner_retries_transient_provider_failures():
    agent = Agent(
        name="A",
        instructions="Be helpful.",
        retry_policy=RetryPolicy(max_attempts=4, base_delay=0.001, jitter=False),
    )
    client = FlakyLLMClient(result=text_response("recovered"), fail_times=2)

    result = Runner(agent, client).run("hi")

    assert result.output == "recovered"
    assert client.attempts == 3


def test_runner_surfaces_error_when_retries_are_exhausted():
    agent = Agent(
        name="A",
        instructions="Be helpful.",
        retry_policy=RetryPolicy(max_attempts=2, base_delay=0.001, jitter=False),
    )
    client = FlakyLLMClient(fail_times=5)

    with pytest.raises(RuntimeError):
        Runner(agent, client).run("hi")


def test_structured_output_is_parsed_onto_the_result():
    agent = Agent(name="A", instructions="Triage.", output_schema=TRIAGE_SCHEMA)
    client = FakeLLMClient(responses=[text_response('{"severity": "high"}')])

    result = Runner(agent, client).run("something broke")

    assert result.structured_output == {"severity": "high"}
    assert result.repair_attempts == 0


def test_structured_output_repairs_a_malformed_reply():
    agent = Agent(name="A", instructions="Triage.", output_schema=TRIAGE_SCHEMA)
    client = FakeLLMClient(
        responses=[text_response("it is pretty bad"), text_response('{"severity": "high"}')]
    )

    result = Runner(agent, client).run("something broke")

    assert result.structured_output == {"severity": "high"}
    assert result.repair_attempts == 1


def test_structured_output_gives_up_after_repair_budget():
    schema = OutputSchema(name="triage", schema=TRIAGE_SCHEMA.schema, max_repair_attempts=1)
    agent = Agent(name="A", instructions="Triage.", output_schema=schema)
    client = FakeLLMClient(default_response=text_response("still not json"))

    with pytest.raises(OutputValidationError):
        Runner(agent, client).run("something broke")


def test_system_prompt_includes_schema_instructions():
    agent = Agent(name="A", instructions="Triage.", output_schema=TRIAGE_SCHEMA)
    assert "Triage." in agent.system_prompt()
    assert "severity" in agent.system_prompt()


def test_agent_without_schema_has_plain_system_prompt():
    agent = Agent(name="A", instructions="Just be helpful.")
    assert agent.system_prompt() == "Just be helpful."


def test_session_is_saved_after_a_run():
    store = InMemorySessionStore()
    agent = Agent(name="A", instructions="Be helpful.")
    client = FakeLLMClient(responses=[text_response("noted")])

    Runner(agent, client, session_store=store, session_id="s1").run("remember this")

    assert [m.content for m in store.load("s1")] == ["remember this", "noted"]


def test_session_is_restored_into_a_fresh_agent():
    store = InMemorySessionStore()
    first = Agent(name="A", instructions="Be helpful.")
    Runner(first, FakeLLMClient(responses=[text_response("noted")]),
           session_store=store, session_id="s1").run("my name is Desmond")

    second = Agent(name="A", instructions="Be helpful.")
    result = Runner(second, FakeLLMClient(responses=[text_response("Desmond")]),
                    session_store=store, session_id="s1").run("what is my name?")

    contents = [m.content for m in result.messages]
    assert "my name is Desmond" in contents
    assert result.output == "Desmond"


def test_runs_without_a_session_id_are_not_persisted():
    store = InMemorySessionStore()
    agent = Agent(name="A", instructions="Be helpful.")
    Runner(agent, FakeLLMClient(responses=[text_response("ok")]), session_store=store).run("hi")
    assert store.list_sessions() == []


def test_run_stream_emits_multiple_incremental_chunks():
    agent = Agent(name="A", instructions="Be helpful.")
    client = ChunkedFakeLLMClient(responses=[text_response("streaming output here")], chunk_size=5)

    chunks = list(Runner(agent, client).run_stream("hi"))
    deltas = [c.delta for c in chunks if c.delta]

    assert len(deltas) > 1
    assert "".join(deltas) == "streaming output here"
    assert chunks[-1].done is True


def test_run_stream_persists_session():
    store = InMemorySessionStore()
    agent = Agent(name="A", instructions="Be helpful.")
    client = ChunkedFakeLLMClient(responses=[text_response("streamed")])

    list(Runner(agent, client, session_store=store, session_id="s1").run_stream("hi"))

    assert [m.content for m in store.load("s1")] == ["hi", "streamed"]

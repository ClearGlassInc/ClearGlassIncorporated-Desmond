"""Advanced example: tracing, structured output, retries, sessions, and
multi-agent delegation — all against offline fakes, so it runs with no API key.

    python examples/advanced_agent.py
"""

import tempfile

from clearglassinc_sdk import (
    Agent,
    ConsoleExporter,
    Handoff,
    InMemoryExporter,
    OutputSchema,
    RetryPolicy,
    Runner,
    Tracer,
    build_supervisor,
    tool,
)
from clearglassinc_sdk.sessions import FileSessionStore
from clearglassinc_sdk.testing import (
    FakeLLMClient,
    FlakyLLMClient,
    text_response,
    tool_call_response,
)
from clearglassinc_sdk.tracing import Usage


def demo_tracing_and_usage() -> None:
    print("\n=== 1. Tracing + token accounting ===")

    @tool(description="Looks up an order's status by id.")
    def order_status(order_id: str) -> str:
        return f"order {order_id}: shipped"

    agent = Agent(name="Support Agent", instructions="Help with orders.")
    agent.add_tool(order_status)

    collector = InMemoryExporter()
    tracer = Tracer(exporters=[collector, ConsoleExporter()])

    client = FakeLLMClient(
        responses=[
            tool_call_response("c1", "order_status", {"order_id": "A-42"}),
            text_response("Order A-42 has shipped.", usage=Usage(input_tokens=120, output_tokens=18)),
        ]
    )
    result = Runner(agent, client, tracer=tracer).run("Where is order A-42?")

    print(f"answer: {result.output}")
    print(f"tokens: {result.usage.to_dict()}")
    print(f"spans recorded: {len(collector.spans)} (tool spans: {len(collector.by_kind('tool'))})")


def demo_structured_output() -> None:
    print("\n=== 2. Structured output with schema repair ===")

    schema = OutputSchema(
        name="triage",
        description="Classify the incoming support ticket.",
        schema={
            "type": "object",
            "properties": {
                "severity": {"type": "string", "enum": ["low", "medium", "high"]},
                "summary": {"type": "string"},
            },
            "required": ["severity", "summary"],
        },
    )
    agent = Agent(name="Triage Agent", instructions="Trige tickets.", output_schema=schema)

    # First reply is malformed; the runner feeds the error back and the model
    # corrects itself on the next turn.
    client = FakeLLMClient(
        responses=[
            text_response("severity is high, honestly"),
            text_response('```json\n{"severity": "high", "summary": "Checkout is down"}\n```'),
        ]
    )
    result = Runner(agent, client).run("Checkout returns 500 for all users.")

    print(f"parsed: {result.structured_output}")
    print(f"repair attempts: {result.repair_attempts}")


def demo_retry() -> None:
    print("\n=== 3. Retry on transient provider errors ===")

    agent = Agent(
        name="Resilient Agent",
        instructions="Be resilient.",
        retry_policy=RetryPolicy(max_attempts=4, base_delay=0.01, jitter=False),
    )
    client = FlakyLLMClient(result=text_response("survived the outage"), fail_times=2)
    result = Runner(agent, client).run("ping")

    print(f"answer: {result.output} (after {client.attempts} provider attempts)")


def demo_sessions() -> None:
    print("\n=== 4. Session persistence across runs ===")

    with tempfile.TemporaryDirectory() as directory:
        store = FileSessionStore(directory=directory)

        first = Agent(name="Session Agent", instructions="Remember context.")
        Runner(first, FakeLLMClient(responses=[text_response("Noted: your name is Desmond.")]),
               session_store=store, session_id="demo").run("My name is Desmond.")

        # A brand new Agent object — history comes back from disk, not memory.
        second = Agent(name="Session Agent", instructions="Remember context.")
        result = Runner(second, FakeLLMClient(responses=[text_response("Your name is Desmond.")]),
                        session_store=store, session_id="demo").run("What is my name?")

        print(f"answer: {result.output}")
        print(f"restored history turns: {len(result.messages)}")
        print(f"stored sessions: {store.list_sessions()}")


def demo_multi_agent() -> None:
    print("\n=== 5. Multi-agent delegation ===")

    researcher = Agent(name="Researcher", instructions="You research topics deeply.")
    researcher_client = FakeLLMClient(responses=[text_response("Findings: the market grew 12% YoY.")])

    supervisor = build_supervisor(
        name="Supervisor",
        instructions="You coordinate specialists.",
        handoffs=[Handoff(agent=researcher, llm_client=researcher_client)],
    )
    supervisor_client = FakeLLMClient(
        responses=[
            tool_call_response("c1", "delegate_to_researcher", {"task": "Research market growth."}),
            text_response("The researcher reports 12% YoY market growth."),
        ]
    )
    result = Runner(supervisor, supervisor_client).run("How fast is the market growing?")

    print(f"supervisor tools: {supervisor.list_tools()}")
    print(f"answer: {result.output}")


def main() -> None:
    demo_tracing_and_usage()
    demo_structured_output()
    demo_retry()
    demo_sessions()
    demo_multi_agent()
    print("\nAll advanced demos completed.")


if __name__ == "__main__":
    main()

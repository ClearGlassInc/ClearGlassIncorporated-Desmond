from clearglassinc_sdk.agent import Agent
from clearglassinc_sdk.handoff import Handoff, build_supervisor
from clearglassinc_sdk.runner import Runner
from clearglassinc_sdk.testing import FakeLLMClient, text_response, tool_call_response


def make_specialist(name: str = "Researcher") -> tuple[Agent, FakeLLMClient]:
    agent = Agent(name=name, instructions="You research topics deeply.")
    client = FakeLLMClient(responses=[text_response("specialist findings")])
    return agent, client


def test_handoff_derives_tool_name_from_agent_name():
    agent, client = make_specialist("Market Research Bot")
    handoff = Handoff(agent=agent, llm_client=client)
    assert handoff.tool_name == "delegate_to_market_research_bot"


def test_handoff_honors_explicit_tool_name():
    agent, client = make_specialist()
    handoff = Handoff(agent=agent, llm_client=client, tool_name="ask_research")
    assert handoff.as_tool().name == "ask_research"


def test_handoff_tool_schema_requires_a_task_string():
    agent, client = make_specialist()
    schema = Handoff(agent=agent, llm_client=client).as_tool().to_schema()
    assert schema["parameters"]["required"] == ["task"]
    assert schema["parameters"]["properties"]["task"]["type"] == "string"


def test_handoff_tool_runs_the_specialist():
    agent, client = make_specialist()
    tool = Handoff(agent=agent, llm_client=client).as_tool()
    assert tool.run(task="What is the market size?") == "specialist findings"


def test_build_supervisor_registers_one_tool_per_handoff():
    researcher, researcher_client = make_specialist("Researcher")
    writer, writer_client = make_specialist("Writer")

    supervisor = build_supervisor(
        name="Supervisor",
        instructions="Coordinate specialists.",
        handoffs=[
            Handoff(agent=researcher, llm_client=researcher_client),
            Handoff(agent=writer, llm_client=writer_client),
        ],
    )

    assert supervisor.list_tools() == ["delegate_to_researcher", "delegate_to_writer"]
    assert "delegate_to_researcher" in supervisor.instructions


def test_supervisor_delegates_end_to_end():
    researcher, researcher_client = make_specialist()
    supervisor = build_supervisor(
        name="Supervisor",
        instructions="Coordinate specialists.",
        handoffs=[Handoff(agent=researcher, llm_client=researcher_client)],
    )
    supervisor_client = FakeLLMClient(
        responses=[
            tool_call_response("c1", "delegate_to_researcher", {"task": "research it"}),
            text_response("Summarized: specialist findings"),
        ]
    )

    result = Runner(supervisor, supervisor_client).run("Do the research.")

    assert result.output == "Summarized: specialist findings"
    tool_messages = [m for m in supervisor.memory.history() if m.role == "tool"]
    assert tool_messages[0].content == "specialist findings"


def test_fresh_memory_isolates_repeated_delegations():
    agent = Agent(name="Specialist", instructions="Answer.")
    client = FakeLLMClient(default_response=text_response("answer"))
    tool = Handoff(agent=agent, llm_client=client, fresh_memory=True).as_tool()

    tool.run(task="first task")
    first_len = len(agent.memory.history())
    tool.run(task="second task")

    # Memory is cleared before each delegation, so history doesn't accumulate.
    assert len(agent.memory.history()) == first_len

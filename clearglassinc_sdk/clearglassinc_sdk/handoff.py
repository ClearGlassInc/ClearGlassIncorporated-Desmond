"""Multi-agent orchestration: expose a specialist `Agent` as a `Tool` so a
supervisor agent can delegate to it.

This is the "agent as tool" pattern — the supervisor's LLM sees the specialist
in its tool list, calls it with a task string, and gets the specialist's final
answer back as the tool result. Specialists keep their own instructions,
tools, guardrails, and memory, so delegation stays isolated.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from clearglassinc_sdk.agent import Agent
from clearglassinc_sdk.clients.base import LLMClient
from clearglassinc_sdk.tools import Tool


def _normalize_tool_name(name: str) -> str:
    cleaned = "".join(char if char.isalnum() else "_" for char in name.strip().lower())
    while "__" in cleaned:
        cleaned = cleaned.replace("__", "_")
    return cleaned.strip("_") or "agent"


@dataclass
class Handoff:
    """A delegation target: a specialist agent plus how it's advertised."""

    agent: Agent
    llm_client: LLMClient
    tool_name: str = ""
    description: str = ""
    fresh_memory: bool = True

    def __post_init__(self) -> None:
        if not self.tool_name:
            self.tool_name = f"delegate_to_{_normalize_tool_name(self.agent.name)}"
        if not self.description:
            self.description = (
                f"Delegate a task to the '{self.agent.name}' specialist agent. "
                f"Its role: {self.agent.instructions.strip()[:200]}"
            )

    def _run_task(self, task: str) -> str:
        # Imported here to avoid a circular import at module load time.
        from clearglassinc_sdk.runner import Runner

        if self.fresh_memory:
            self.agent.memory.clear()
        result = Runner(self.agent, self.llm_client).run(task)
        return result.output

    def as_tool(self) -> Tool:
        """Wrap the specialist as a callable tool for a supervisor agent."""

        def delegate(task: str) -> str:
            return self._run_task(task)

        delegate.__name__ = self.tool_name
        return Tool(
            name=self.tool_name,
            description=self.description,
            func=delegate,
            parameters={
                "type": "object",
                "properties": {
                    "task": {
                        "type": "string",
                        "description": "The complete, self-contained task for the specialist.",
                    }
                },
                "required": ["task"],
            },
        )


def build_supervisor(
    name: str,
    instructions: str,
    handoffs: list[Handoff],
    **agent_kwargs: Any,
) -> Agent:
    """Create a supervisor `Agent` with one delegation tool per handoff.

    The supervisor's instructions are augmented with a roster of its
    specialists so the model knows who it can route work to.
    """
    roster = "\n".join(f"- {h.tool_name}: {h.agent.name}" for h in handoffs)
    augmented = (
        f"{instructions}\n\nYou can delegate to these specialist agents:\n{roster}\n"
        "Delegate when a task matches a specialist's role; answer directly otherwise."
    )
    supervisor = Agent(name=name, instructions=augmented, **agent_kwargs)
    supervisor.add_tools([handoff.as_tool() for handoff in handoffs])
    return supervisor

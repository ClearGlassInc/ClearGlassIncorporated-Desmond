"""The `Runner`: drives an `Agent` through an LLM client, dispatching tool
calls and enforcing guardrails until a final answer is produced.

Beyond the basic loop it wires in the SDK's production concerns: retry with
backoff on transient provider errors, hierarchical tracing with token
accounting, schema-validated structured output with a bounded repair loop,
and optional session persistence so conversations survive restarts.
"""

from __future__ import annotations

import json
from collections.abc import AsyncIterator, Iterator
from dataclasses import dataclass, field
from typing import Any

from clearglassinc_sdk.agent import Agent
from clearglassinc_sdk.clients.base import CompletionResult, LLMClient, StreamChunk, ToolCall
from clearglassinc_sdk.exceptions import GuardrailViolation, MaxStepsExceeded, ToolExecutionError
from clearglassinc_sdk.guardrails import run_guardrails
from clearglassinc_sdk.memory import Message
from clearglassinc_sdk.sessions import SessionStore, load_into_memory, save_from_memory
from clearglassinc_sdk.structured import OutputValidationError
from clearglassinc_sdk.tracing import NoOpTracer, Tracer, Usage


@dataclass
class RunResult:
    output: str
    messages: list[Message] = field(default_factory=list)
    steps: int = 0
    structured_output: Any = None
    usage: Usage = field(default_factory=Usage)
    trace_id: str = ""
    repair_attempts: int = 0


def _tool_calls_to_dicts(tool_calls: list[ToolCall]) -> list[dict[str, Any]]:
    return [
        {
            "id": call.id,
            "type": "function",
            "function": {"name": call.name, "arguments": json.dumps(call.arguments)},
        }
        for call in tool_calls
    ]


class Runner:
    """Executes an `Agent`'s tool-calling loop against an `LLMClient`."""

    def __init__(
        self,
        agent: Agent,
        llm_client: LLMClient,
        tracer: Tracer | None = None,
        session_store: SessionStore | None = None,
        session_id: str | None = None,
    ):
        self.agent = agent
        self.llm_client = llm_client
        self.tracer = tracer or NoOpTracer()
        self.session_store = session_store
        self.session_id = session_id

    # -- lifecycle -----------------------------------------------------

    def _begin(self, prompt: str) -> None:
        """Load any persisted session, validate input, and record the prompt."""
        if self.session_store is not None and self.session_id:
            load_into_memory(self.session_store, self.session_id, self.agent.memory)
        self._check_input(prompt)
        self.agent.memory.add_user(prompt)

    def _finish(self) -> None:
        if self.session_store is not None and self.session_id:
            save_from_memory(self.session_store, self.session_id, self.agent.memory)

    # -- guardrails ----------------------------------------------------

    def _check_input(self, prompt: str) -> None:
        with self.tracer.span("input_guardrails", "guardrail"):
            result = run_guardrails(self.agent.input_guardrails, prompt)
            if not result.passed:
                raise GuardrailViolation("input", result.reason)

    def _check_output(self, content: str) -> None:
        with self.tracer.span("output_guardrails", "guardrail"):
            result = run_guardrails(self.agent.output_guardrails, content)
            if not result.passed:
                raise GuardrailViolation("output", result.reason)

    # -- tool dispatch -------------------------------------------------

    def _execute_tool_calls(self, tool_calls: list[ToolCall]) -> None:
        for call in tool_calls:
            with self.tracer.span(call.name, "tool", arguments=call.arguments):
                tool = self.agent.get_tool(call.name)
                if tool is None:
                    self.agent.memory.add_tool_result(
                        call.id, call.name, f"error: no such tool '{call.name}'"
                    )
                    continue
                try:
                    output = tool.run(**call.arguments)
                except Exception as exc:
                    raise ToolExecutionError(call.name, exc) from exc
                self.agent.memory.add_tool_result(call.id, call.name, str(output))

    async def _aexecute_tool_calls(self, tool_calls: list[ToolCall]) -> None:
        for call in tool_calls:
            with self.tracer.span(call.name, "tool", arguments=call.arguments):
                tool = self.agent.get_tool(call.name)
                if tool is None:
                    self.agent.memory.add_tool_result(
                        call.id, call.name, f"error: no such tool '{call.name}'"
                    )
                    continue
                try:
                    output = await tool.arun(**call.arguments)
                except Exception as exc:
                    raise ToolExecutionError(call.name, exc) from exc
                self.agent.memory.add_tool_result(call.id, call.name, str(output))

    # -- model calls ---------------------------------------------------

    def _complete(self) -> CompletionResult:
        """One traced, retried model call."""
        with self.tracer.span("llm.complete", "llm", model=self.agent.model) as span:
            result = self.agent.retry_policy.call(
                self.llm_client.complete,
                self.agent.memory.history(),
                system=self.agent.system_prompt(),
                tools=self.agent.tool_schemas() or None,
                model=self.agent.model,
                temperature=self.agent.temperature,
            )
            span.usage = result.usage
            return result

    async def _acomplete(self) -> CompletionResult:
        with self.tracer.span("llm.acomplete", "llm", model=self.agent.model) as span:
            result = await self.agent.retry_policy.acall(
                self.llm_client.acomplete,
                self.agent.memory.history(),
                system=self.agent.system_prompt(),
                tools=self.agent.tool_schemas() or None,
                model=self.agent.model,
                temperature=self.agent.temperature,
            )
            span.usage = result.usage
            return result

    # -- structured output ---------------------------------------------

    def _try_structured(self, content: str, repair_attempts: int) -> tuple[Any, bool]:
        """Parse `content` against the agent's schema.

        Returns `(value, ok)`. When parsing fails and repair budget remains, a
        corrective user turn is appended to memory and `ok` is False so the
        caller loops again. Once the budget is exhausted the error propagates.
        """
        schema = self.agent.output_schema
        if schema is None:
            return None, True

        try:
            return schema.parse(content), True
        except OutputValidationError as exc:
            if repair_attempts >= schema.max_repair_attempts:
                raise
            self.agent.memory.add_assistant(content)
            self.agent.memory.add_user(schema.repair_prompt(str(exc)))
            return None, False

    # -- run -----------------------------------------------------------

    def run(self, prompt: str) -> RunResult:
        """Run the agent to completion (synchronous, non-streaming)."""
        with self.tracer.span(f"run:{self.agent.name}", "run", prompt_chars=len(prompt)):
            self._begin(prompt)
            repair_attempts = 0

            for step in range(1, self.agent.max_steps + 1):
                with self.tracer.span(f"step:{step}", "step"):
                    result = self._complete()

                    if result.has_tool_calls:
                        self.agent.memory.add_assistant(
                            result.content, tool_calls=_tool_calls_to_dicts(result.tool_calls)
                        )
                        self._execute_tool_calls(result.tool_calls)
                        continue

                    self._check_output(result.content)
                    structured, ok = self._try_structured(result.content, repair_attempts)
                    if not ok:
                        repair_attempts += 1
                        continue

                    self.agent.memory.add_assistant(result.content)
                    self._finish()
                    return RunResult(
                        output=result.content,
                        messages=self.agent.memory.history(),
                        steps=step,
                        structured_output=structured,
                        usage=self.tracer.total_usage,
                        trace_id=self.tracer.trace_id,
                        repair_attempts=repair_attempts,
                    )

            raise MaxStepsExceeded(self.agent.max_steps)

    async def arun(self, prompt: str) -> RunResult:
        """Run the agent to completion (async, non-streaming)."""
        with self.tracer.span(f"run:{self.agent.name}", "run", prompt_chars=len(prompt)):
            self._begin(prompt)
            repair_attempts = 0

            for step in range(1, self.agent.max_steps + 1):
                with self.tracer.span(f"step:{step}", "step"):
                    result = await self._acomplete()

                    if result.has_tool_calls:
                        self.agent.memory.add_assistant(
                            result.content, tool_calls=_tool_calls_to_dicts(result.tool_calls)
                        )
                        await self._aexecute_tool_calls(result.tool_calls)
                        continue

                    self._check_output(result.content)
                    structured, ok = self._try_structured(result.content, repair_attempts)
                    if not ok:
                        repair_attempts += 1
                        continue

                    self.agent.memory.add_assistant(result.content)
                    self._finish()
                    return RunResult(
                        output=result.content,
                        messages=self.agent.memory.history(),
                        steps=step,
                        structured_output=structured,
                        usage=self.tracer.total_usage,
                        trace_id=self.tracer.trace_id,
                        repair_attempts=repair_attempts,
                    )

            raise MaxStepsExceeded(self.agent.max_steps)

    # -- streaming -----------------------------------------------------

    def run_stream(self, prompt: str) -> Iterator[StreamChunk]:
        """Run the agent, yielding `StreamChunk`s as each step produces them.
        Tool-call steps are yielded (empty-delta, tool_calls populated) then
        executed before continuing; the final text-only step streams its
        content incrementally if the underlying client supports it."""
        self._begin(prompt)

        for _step in range(1, self.agent.max_steps + 1):
            content = ""
            tool_calls: list[ToolCall] = []
            # Streams are consumed incrementally and deliberately not retried:
            # a mid-flight failure has already emitted partial output to the
            # caller, so replaying it would duplicate tokens.
            for chunk in self.llm_client.stream(
                self.agent.memory.history(),
                system=self.agent.system_prompt(),
                tools=self.agent.tool_schemas() or None,
                model=self.agent.model,
                temperature=self.agent.temperature,
            ):
                content += chunk.delta
                if chunk.tool_calls:
                    tool_calls = chunk.tool_calls
                yield chunk

            if tool_calls:
                self.agent.memory.add_assistant(content, tool_calls=_tool_calls_to_dicts(tool_calls))
                self._execute_tool_calls(tool_calls)
                continue

            self._check_output(content)
            self.agent.memory.add_assistant(content)
            self._finish()
            return

        raise MaxStepsExceeded(self.agent.max_steps)

    async def arun_stream(self, prompt: str) -> AsyncIterator[StreamChunk]:
        """Async variant of `run_stream`."""
        self._begin(prompt)

        for _step in range(1, self.agent.max_steps + 1):
            content = ""
            tool_calls: list[ToolCall] = []
            async for chunk in self.llm_client.astream(
                self.agent.memory.history(),
                system=self.agent.system_prompt(),
                tools=self.agent.tool_schemas() or None,
                model=self.agent.model,
                temperature=self.agent.temperature,
            ):
                content += chunk.delta
                if chunk.tool_calls:
                    tool_calls = chunk.tool_calls
                yield chunk

            if tool_calls:
                self.agent.memory.add_assistant(content, tool_calls=_tool_calls_to_dicts(tool_calls))
                await self._aexecute_tool_calls(tool_calls)
                continue

            self._check_output(content)
            self.agent.memory.add_assistant(content)
            self._finish()
            return

        raise MaxStepsExceeded(self.agent.max_steps)

"""OpenAI (and OpenAI-compatible) chat completions adapter.

Requires the `openai` package (`pip install clearglassinc-sdk[openai]`). The
import is deferred to instantiation time so the base SDK has zero hard
dependency on any single provider's SDK.
"""

from __future__ import annotations

import json
from collections.abc import AsyncIterator, Iterator
from typing import Any

from clearglassinc_sdk.clients.base import CompletionResult, LLMClient, StreamChunk, ToolCall
from clearglassinc_sdk.memory import Message
from clearglassinc_sdk.tracing import Usage


class OpenAIClient(LLMClient):
    """Adapter for OpenAI's Chat Completions API (and Azure/OpenAI-compatible
    endpoints via `base_url`)."""

    def __init__(
        self,
        api_key: str | None = None,
        model: str = "gpt-4o-mini",
        base_url: str | None = None,
        timeout: float = 60.0,
    ) -> None:
        try:
            import openai
        except ImportError as exc:  # pragma: no cover
            raise ImportError(
                "OpenAIClient requires the 'openai' package: pip install clearglassinc-sdk[openai]"
            ) from exc

        self._client = openai.OpenAI(api_key=api_key, base_url=base_url, timeout=timeout)
        self._async_client = openai.AsyncOpenAI(
            api_key=api_key, base_url=base_url, timeout=timeout
        )
        self.default_model = model

    def _to_openai_messages(
        self, messages: list[Message], system: str | None
    ) -> list[dict[str, Any]]:
        payload: list[dict[str, Any]] = []
        if system:
            payload.append({"role": "system", "content": system})
        payload.extend(message.to_dict() for message in messages)
        return payload

    def _to_openai_tools(self, tools: list[dict[str, Any]] | None) -> list[dict[str, Any]] | None:
        if not tools:
            return None
        return [{"type": "function", "function": schema} for schema in tools]

    def _parse_response(self, response: Any) -> CompletionResult:
        choice = response.choices[0]
        content = choice.message.content or ""
        tool_calls: list[ToolCall] = []
        for raw_call in choice.message.tool_calls or []:
            tool_calls.append(
                ToolCall(
                    id=raw_call.id,
                    name=raw_call.function.name,
                    arguments=json.loads(raw_call.function.arguments or "{}"),
                )
            )
        return CompletionResult(
            content=content,
            tool_calls=tool_calls,
            raw=response,
            usage=self._parse_usage(getattr(response, "usage", None)),
        )

    def _parse_usage(self, usage: Any) -> Usage | None:
        if usage is None:
            return None
        return Usage(
            input_tokens=getattr(usage, "prompt_tokens", 0) or 0,
            output_tokens=getattr(usage, "completion_tokens", 0) or 0,
        )

    def _accumulate_tool_calls(self, buffer: dict[int, dict[str, Any]]) -> list[ToolCall]:
        """Turn the per-index deltas collected during a stream into ToolCalls."""
        calls: list[ToolCall] = []
        for index in sorted(buffer):
            entry = buffer[index]
            if not entry.get("name"):
                continue
            try:
                arguments = json.loads(entry.get("arguments") or "{}")
            except json.JSONDecodeError:
                arguments = {}
            calls.append(ToolCall(id=entry.get("id") or f"call_{index}", name=entry["name"], arguments=arguments))
        return calls

    def complete(
        self,
        messages: list[Message],
        *,
        system: str | None = None,
        tools: list[dict[str, Any]] | None = None,
        model: str | None = None,
        temperature: float = 0.7,
    ) -> CompletionResult:
        response = self._client.chat.completions.create(
            model=model or self.default_model,
            messages=self._to_openai_messages(messages, system),
            tools=self._to_openai_tools(tools),
            temperature=temperature,
        )
        return self._parse_response(response)

    async def acomplete(
        self,
        messages: list[Message],
        *,
        system: str | None = None,
        tools: list[dict[str, Any]] | None = None,
        model: str | None = None,
        temperature: float = 0.7,
    ) -> CompletionResult:
        response = await self._async_client.chat.completions.create(
            model=model or self.default_model,
            messages=self._to_openai_messages(messages, system),
            tools=self._to_openai_tools(tools),
            temperature=temperature,
        )
        return self._parse_response(response)

    def stream(
        self,
        messages: list[Message],
        *,
        system: str | None = None,
        tools: list[dict[str, Any]] | None = None,
        model: str | None = None,
        temperature: float = 0.7,
    ) -> Iterator[StreamChunk]:
        """True token-by-token streaming, accumulating any tool-call deltas."""
        stream = self._client.chat.completions.create(
            model=model or self.default_model,
            messages=self._to_openai_messages(messages, system),
            tools=self._to_openai_tools(tools),
            temperature=temperature,
            stream=True,
            stream_options={"include_usage": True},
        )

        tool_buffer: dict[int, dict[str, Any]] = {}
        usage: Usage | None = None

        for event in stream:
            usage = self._parse_usage(getattr(event, "usage", None)) or usage
            if not event.choices:
                continue
            delta = event.choices[0].delta
            for raw_call in getattr(delta, "tool_calls", None) or []:
                entry = tool_buffer.setdefault(raw_call.index, {"arguments": ""})
                if raw_call.id:
                    entry["id"] = raw_call.id
                if raw_call.function and raw_call.function.name:
                    entry["name"] = raw_call.function.name
                if raw_call.function and raw_call.function.arguments:
                    entry["arguments"] += raw_call.function.arguments
            if delta.content:
                yield StreamChunk(delta=delta.content)

        yield StreamChunk(
            delta="", done=True, tool_calls=self._accumulate_tool_calls(tool_buffer), usage=usage
        )

    async def astream(
        self,
        messages: list[Message],
        *,
        system: str | None = None,
        tools: list[dict[str, Any]] | None = None,
        model: str | None = None,
        temperature: float = 0.7,
    ) -> AsyncIterator[StreamChunk]:
        """Async variant of `stream`."""
        stream = await self._async_client.chat.completions.create(
            model=model or self.default_model,
            messages=self._to_openai_messages(messages, system),
            tools=self._to_openai_tools(tools),
            temperature=temperature,
            stream=True,
            stream_options={"include_usage": True},
        )

        tool_buffer: dict[int, dict[str, Any]] = {}
        usage: Usage | None = None

        async for event in stream:
            usage = self._parse_usage(getattr(event, "usage", None)) or usage
            if not event.choices:
                continue
            delta = event.choices[0].delta
            for raw_call in getattr(delta, "tool_calls", None) or []:
                entry = tool_buffer.setdefault(raw_call.index, {"arguments": ""})
                if raw_call.id:
                    entry["id"] = raw_call.id
                if raw_call.function and raw_call.function.name:
                    entry["name"] = raw_call.function.name
                if raw_call.function and raw_call.function.arguments:
                    entry["arguments"] += raw_call.function.arguments
            if delta.content:
                yield StreamChunk(delta=delta.content)

        yield StreamChunk(
            delta="", done=True, tool_calls=self._accumulate_tool_calls(tool_buffer), usage=usage
        )

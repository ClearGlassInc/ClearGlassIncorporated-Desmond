"""Observability: hierarchical spans, token accounting, and pluggable exporters.

Every agent run emits a tree of `Span`s (run → step → llm/tool) carrying
timings, token usage, and errors. Attach an exporter to ship them to a log,
a file, or your own telemetry backend — stdlib only, no vendor SDK required.
"""

from __future__ import annotations

import json
import time
import uuid
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Any, Protocol


@dataclass
class Usage:
    """Token accounting for one call, or summed across a run."""

    input_tokens: int = 0
    output_tokens: int = 0

    @property
    def total_tokens(self) -> int:
        return self.input_tokens + self.output_tokens

    def __add__(self, other: Usage) -> Usage:
        return Usage(
            input_tokens=self.input_tokens + other.input_tokens,
            output_tokens=self.output_tokens + other.output_tokens,
        )

    def to_dict(self) -> dict[str, int]:
        return {
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "total_tokens": self.total_tokens,
        }


@dataclass
class Span:
    """One timed unit of work inside a run."""

    name: str
    kind: str  # "run" | "step" | "llm" | "tool" | "guardrail"
    span_id: str = field(default_factory=lambda: uuid.uuid4().hex[:16])
    parent_id: str | None = None
    trace_id: str = ""
    started_at: float = field(default_factory=time.time)
    ended_at: float | None = None
    attributes: dict[str, Any] = field(default_factory=dict)
    usage: Usage | None = None
    error: str | None = None

    @property
    def duration_ms(self) -> float | None:
        if self.ended_at is None:
            return None
        return (self.ended_at - self.started_at) * 1000

    def to_dict(self) -> dict[str, Any]:
        return {
            "trace_id": self.trace_id,
            "span_id": self.span_id,
            "parent_id": self.parent_id,
            "name": self.name,
            "kind": self.kind,
            "started_at": self.started_at,
            "ended_at": self.ended_at,
            "duration_ms": self.duration_ms,
            "attributes": self.attributes,
            "usage": self.usage.to_dict() if self.usage else None,
            "error": self.error,
        }


class SpanExporter(Protocol):
    """Receives each span as it completes."""

    def export(self, span: Span) -> None: ...


@dataclass
class ConsoleExporter:
    """Prints a one-line summary per span. Handy in development."""

    stream: Any = None

    def export(self, span: Span) -> None:
        duration = f"{span.duration_ms:.1f}ms" if span.duration_ms is not None else "-"
        status = f" ERROR={span.error}" if span.error else ""
        usage = f" tokens={span.usage.total_tokens}" if span.usage else ""
        line = f"[{span.kind}] {span.name} {duration}{usage}{status}"
        print(line, file=self.stream)


@dataclass
class JSONLExporter:
    """Appends one JSON object per span to a file — cheap, greppable traces."""

    path: str

    def export(self, span: Span) -> None:
        with open(self.path, "a", encoding="utf-8") as handle:
            handle.write(json.dumps(span.to_dict()) + "\n")


@dataclass
class InMemoryExporter:
    """Collects spans in a list. Used by tests and the `/traces` debug endpoint."""

    spans: list[Span] = field(default_factory=list)

    def export(self, span: Span) -> None:
        self.spans.append(span)

    def by_kind(self, kind: str) -> list[Span]:
        return [span for span in self.spans if span.kind == kind]

    def clear(self) -> None:
        self.spans.clear()


class Tracer:
    """Creates spans and forwards completed ones to every registered exporter.

    Spans nest via a simple stack, so `with tracer.span(...)` blocks inside
    another span automatically record the right `parent_id`.
    """

    def __init__(self, exporters: list[SpanExporter] | None = None, trace_id: str | None = None):
        self.exporters: list[SpanExporter] = list(exporters or [])
        self.trace_id = trace_id or uuid.uuid4().hex
        self._stack: list[Span] = []
        self.total_usage = Usage()

    def add_exporter(self, exporter: SpanExporter) -> None:
        self.exporters.append(exporter)

    @contextmanager
    def span(self, name: str, kind: str, **attributes: Any) -> Iterator[Span]:
        span = Span(
            name=name,
            kind=kind,
            trace_id=self.trace_id,
            parent_id=self._stack[-1].span_id if self._stack else None,
            attributes=dict(attributes),
        )
        self._stack.append(span)
        try:
            yield span
        except Exception as exc:
            span.error = f"{type(exc).__name__}: {exc}"
            raise
        finally:
            span.ended_at = time.time()
            self._stack.pop()
            if span.usage is not None:
                self.total_usage = self.total_usage + span.usage
            for exporter in self.exporters:
                exporter.export(span)


class NoOpTracer(Tracer):
    """A tracer with no exporters — the zero-overhead default."""

    def __init__(self) -> None:
        super().__init__(exporters=[])

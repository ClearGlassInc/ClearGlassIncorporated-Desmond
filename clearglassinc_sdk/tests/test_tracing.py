import json

import pytest

from clearglassinc_sdk.tracing import InMemoryExporter, JSONLExporter, Tracer, Usage


def test_usage_addition_and_totals():
    total = Usage(input_tokens=10, output_tokens=5) + Usage(input_tokens=3, output_tokens=2)
    assert total.input_tokens == 13
    assert total.output_tokens == 7
    assert total.total_tokens == 20


def test_span_records_duration_and_exports_once():
    exporter = InMemoryExporter()
    tracer = Tracer(exporters=[exporter])

    with tracer.span("work", "run"):
        pass

    assert len(exporter.spans) == 1
    span = exporter.spans[0]
    assert span.name == "work"
    assert span.duration_ms is not None
    assert span.error is None


def test_nested_spans_record_parent_ids():
    exporter = InMemoryExporter()
    tracer = Tracer(exporters=[exporter])

    with tracer.span("outer", "run") as outer:
        with tracer.span("inner", "step") as inner:
            inner_id = inner.span_id
        outer_id = outer.span_id

    by_name = {span.name: span for span in exporter.spans}
    assert by_name["inner"].parent_id == outer_id
    assert by_name["outer"].parent_id is None
    assert by_name["inner"].span_id == inner_id
    # Both spans belong to the same trace.
    assert by_name["inner"].trace_id == by_name["outer"].trace_id


def test_span_captures_exception_then_reraises():
    exporter = InMemoryExporter()
    tracer = Tracer(exporters=[exporter])

    with pytest.raises(ValueError), tracer.span("boom", "tool"):
        raise ValueError("kaboom")

    assert exporter.spans[0].error is not None
    assert "kaboom" in exporter.spans[0].error


def test_tracer_accumulates_usage_across_spans():
    tracer = Tracer(exporters=[InMemoryExporter()])

    with tracer.span("call1", "llm") as span:
        span.usage = Usage(input_tokens=10, output_tokens=4)
    with tracer.span("call2", "llm") as span:
        span.usage = Usage(input_tokens=6, output_tokens=2)

    assert tracer.total_usage.total_tokens == 22


def test_jsonl_exporter_writes_one_object_per_span(tmp_path):
    path = tmp_path / "trace.jsonl"
    tracer = Tracer(exporters=[JSONLExporter(path=str(path))])

    with tracer.span("a", "run"):
        pass
    with tracer.span("b", "run"):
        pass

    lines = path.read_text().strip().splitlines()
    assert len(lines) == 2
    assert json.loads(lines[0])["name"] == "a"


def test_in_memory_exporter_filters_by_kind():
    exporter = InMemoryExporter()
    tracer = Tracer(exporters=[exporter])
    with tracer.span("t", "tool"):
        pass
    with tracer.span("r", "run"):
        pass

    assert [s.name for s in exporter.by_kind("tool")] == ["t"]

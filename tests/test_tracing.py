from recipe_agents import tracing
from recipe_agents.tracing import TraceRecorder


def test_trace_has_session_turn_and_bytes_are_json_safe(tmp_path) -> None:
    recorder = TraceRecorder(tmp_path)
    with recorder.context("session_123", "turn_456"):
        recorder.emit("example", raw_event={"reasoning": b"private-ish"})

    events = recorder.read("session_123")
    assert events[0]["session_id"] == "session_123"
    assert events[0]["turn_id"] == "turn_456"
    assert events[0]["data"]["raw_event"]["reasoning"]["length"] == 11


def test_model_timer_reports_first_stream_only_once(monkeypatch, tmp_path) -> None:
    readings = iter([10.0, 10.125, 11.0])
    monkeypatch.setattr(tracing.time, "perf_counter", lambda: next(readings))
    recorder = TraceRecorder(tmp_path)

    with recorder.context("session_123", "turn_456"):
        recorder.begin_model_call("expert")
        assert recorder.note_first_model_stream("expert") == 125.0
        assert recorder.note_first_model_stream("expert") is None
        assert recorder.finish_model_call("expert") == (1000.0, 125.0)

from recipe_agents.tracing import TraceRecorder


def test_trace_has_session_turn_and_bytes_are_json_safe(tmp_path) -> None:
    recorder = TraceRecorder(tmp_path)
    with recorder.context("session_123", "turn_456"):
        recorder.emit("example", raw_event={"reasoning": b"private-ish"})

    events = recorder.read("session_123")
    assert events[0]["session_id"] == "session_123"
    assert events[0]["turn_id"] == "turn_456"
    assert events[0]["data"]["raw_event"]["reasoning"]["length"] == 11

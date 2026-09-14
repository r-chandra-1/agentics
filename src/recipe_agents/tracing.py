"""A transparent JSONL tracer built on Strands lifecycle hooks.

Strands already emits OpenTelemetry spans. This module adds a teaching-oriented
event log whose values are intentionally easy to inspect in a browser. It uses
framework hooks for stable lifecycle events and the Python streaming callback
for raw provider chunks.
"""

from __future__ import annotations

import contextvars
import dataclasses
import json
import threading
import time
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator

from pydantic import BaseModel
from strands.telemetry.metrics import EventLoopMetrics
from strands.hooks import (
    AfterInvocationEvent,
    AfterModelCallEvent,
    AfterToolCallEvent,
    BeforeInvocationEvent,
    BeforeModelCallEvent,
    BeforeToolCallEvent,
    HookProvider,
    HookRegistry,
    MessageAddedEvent,
)


_session_id: contextvars.ContextVar[str] = contextvars.ContextVar("trace_session_id", default="unscoped")
_turn_id: contextvars.ContextVar[str] = contextvars.ContextVar("trace_turn_id", default="unscoped")


def _json_safe(value: Any) -> Any:
    """Convert SDK objects, dataclasses, bytes, and models into JSON values."""

    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, bytes):
        return {"type": "bytes", "length": len(value), "hex": value.hex()}
    if isinstance(value, BaseModel):
        return _json_safe(value.model_dump(mode="json"))
    if dataclasses.is_dataclass(value) and not isinstance(value, type):
        return _json_safe(dataclasses.asdict(value))
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_json_safe(item) for item in value]
    if isinstance(value, EventLoopMetrics):
        return _json_safe(value.get_summary())
    # Do not recursively inspect arbitrary SDK objects. Some tool proxies use
    # dynamic attribute lookup, and some objects contain cycles. Their repr is
    # safer and the stable hook fields above already carry the useful payload.
    return repr(value)


class TraceRecorder:
    """Append-only, process-local trace store.

    One file per session makes it easy to copy, diff, or delete a learning run.
    A lock prevents interleaved JSON when nested agents finish close together.
    """

    _SENSITIVE_KEYS = {
        "system_prompt",
        "messages",
        "message",
        "prompt",
        "input",
        "result",
        "raw_event",
        "structured_output",
    }

    def __init__(self, directory: Path, capture_content: bool = True) -> None:
        self.directory = directory.resolve()
        self.directory.mkdir(parents=True, exist_ok=True)
        self.capture_content = capture_content
        self._lock = threading.Lock()

    @contextmanager
    def context(self, session_id: str, turn_id: str) -> Iterator[None]:
        session_token = _session_id.set(session_id)
        turn_token = _turn_id.set(turn_id)
        try:
            yield
        finally:
            _turn_id.reset(turn_token)
            _session_id.reset(session_token)

    def emit(self, event_type: str, *, agent: str = "application", **data: Any) -> dict[str, Any]:
        """Write and return a single trace event."""

        session_id = _session_id.get()
        payload = _json_safe(data)
        if not self.capture_content:
            payload = {
                key: "[content capture disabled]" if key in self._SENSITIVE_KEYS else value
                for key, value in payload.items()
            }

        event = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "monotonic_ns": time.monotonic_ns(),
            "session_id": session_id,
            "turn_id": _turn_id.get(),
            "agent": agent,
            "event": event_type,
            "data": payload,
        }
        line = json.dumps(event, ensure_ascii=False, separators=(",", ":"))
        path = self.directory / f"{session_id}.jsonl"
        with self._lock, path.open("a", encoding="utf-8") as handle:
            handle.write(line + "\n")
        return event

    def sessions(self) -> list[dict[str, Any]]:
        """List newest trace files without trusting arbitrary path input."""

        found: list[dict[str, Any]] = []
        for path in self.directory.glob("*.jsonl"):
            stat = path.stat()
            found.append(
                {
                    "session_id": path.stem,
                    "bytes": stat.st_size,
                    "updated_at": datetime.fromtimestamp(stat.st_mtime, timezone.utc).isoformat(),
                }
            )
        return sorted(found, key=lambda item: item["updated_at"], reverse=True)

    def read(self, session_id: str, after: int = 0) -> list[dict[str, Any]]:
        """Read events after a zero-based offset. The API validates session_id."""

        path = self.directory / f"{session_id}.jsonl"
        if not path.exists():
            return []
        events: list[dict[str, Any]] = []
        with self._lock, path.open("r", encoding="utf-8") as handle:
            for index, line in enumerate(handle):
                if index >= after:
                    events.append(json.loads(line))
        return events


class LearningTraceHooks(HookProvider):
    """Subscribe a recorder to the stable Strands agent lifecycle."""

    def __init__(self, recorder: TraceRecorder) -> None:
        self.recorder = recorder
        self._model_started: dict[tuple[str, str, str], float] = {}

    def register_hooks(self, registry: HookRegistry, **_: Any) -> None:
        registry.add_callback(BeforeInvocationEvent, self.before_invocation)
        registry.add_callback(BeforeModelCallEvent, self.before_model)
        registry.add_callback(AfterModelCallEvent, self.after_model)
        registry.add_callback(BeforeToolCallEvent, self.before_tool)
        registry.add_callback(AfterToolCallEvent, self.after_tool)
        registry.add_callback(MessageAddedEvent, self.message_added)
        registry.add_callback(AfterInvocationEvent, self.after_invocation)

    @staticmethod
    def _agent_name(event: Any) -> str:
        return getattr(event.agent, "name", None) or event.agent.__class__.__name__

    def before_invocation(self, event: BeforeInvocationEvent) -> None:
        agent = event.agent
        self.recorder.emit(
            "agent_invocation_start",
            agent=self._agent_name(event),
            system_prompt=agent.system_prompt,
            input_messages=event.messages,
            existing_history=agent.messages,
            model_config=getattr(agent.model, "config", {}),
            tool_definitions=agent.tool_registry.get_all_tool_specs(),
            invocation_state=event.invocation_state,
        )

    def before_model(self, event: BeforeModelCallEvent) -> None:
        name = self._agent_name(event)
        key = (_session_id.get(), _turn_id.get(), name)
        self._model_started[key] = time.perf_counter()
        self.recorder.emit(
            "model_call_start",
            agent=name,
            system_prompt=event.agent.system_prompt,
            messages=event.agent.messages,
            tool_definitions=event.agent.tool_registry.get_all_tool_specs(),
            projected_input_tokens=event.projected_input_tokens,
        )

    def after_model(self, event: AfterModelCallEvent) -> None:
        name = self._agent_name(event)
        key = (_session_id.get(), _turn_id.get(), name)
        started = self._model_started.pop(key, None)
        response = event.stop_response
        metadata = response.message.get("metadata", {}) if response else {}
        usage = metadata.get("usage", {})
        provider_metrics = metadata.get("metrics", {})
        self.recorder.emit(
            "model_call_end",
            agent=name,
            duration_ms=round((time.perf_counter() - started) * 1000, 3) if started else None,
            stop_reason=response.stop_reason if response else None,
            message=response.message if response else None,
            token_usage={
                "inputTokens": usage.get("inputTokens"),
                "outputTokens": usage.get("outputTokens"),
                "totalTokens": usage.get("totalTokens"),
                "cacheReadInputTokens": usage.get("cacheReadInputTokens"),
                "cacheWriteInputTokens": usage.get("cacheWriteInputTokens"),
                "cache_note": "null means this model provider did not report a cache count",
            },
            provider_metrics=provider_metrics,
            error=repr(event.exception) if event.exception else None,
        )

    def before_tool(self, event: BeforeToolCallEvent) -> None:
        selected = event.selected_tool
        self.recorder.emit(
            "tool_call_start",
            agent=self._agent_name(event),
            tool_name=event.tool_use.get("name"),
            tool_use_id=event.tool_use.get("toolUseId"),
            input=event.tool_use.get("input", {}),
            selected_tool_schema=getattr(selected, "tool_spec", None),
        )

    def after_tool(self, event: AfterToolCallEvent) -> None:
        self.recorder.emit(
            "tool_call_end",
            agent=self._agent_name(event),
            tool_name=event.tool_use.get("name"),
            tool_use_id=event.tool_use.get("toolUseId"),
            duration_ms=round(event.duration * 1000, 3) if event.duration is not None else None,
            result=event.result,
            error=repr(event.exception) if event.exception else None,
        )

    def message_added(self, event: MessageAddedEvent) -> None:
        self.recorder.emit("history_message_added", agent=self._agent_name(event), message=event.message)

    def after_invocation(self, event: AfterInvocationEvent) -> None:
        result = event.result
        self.recorder.emit(
            "agent_invocation_end",
            agent=self._agent_name(event),
            stop_reason=result.stop_reason if result else None,
            message=result.message if result else None,
            structured_output=result.structured_output if result else None,
            metrics=result.metrics.get_summary() if result else None,
        )


def make_stream_callback(recorder: TraceRecorder, agent_name: str):
    """Capture raw streaming chunks, including provider-exposed reasoning.

    The callback receives transient Strands events that are intentionally not
    part of the stable hook API. Keeping this adapter small isolates that detail.
    """

    def callback(**event: Any) -> None:
        if "event" in event:
            recorder.emit("raw_model_stream", agent=agent_name, raw_event=event["event"])
        elif event.get("reasoning"):
            recorder.emit(
                "provider_reasoning_delta",
                agent=agent_name,
                rationale=event.get("reasoningText"),
                delta=event.get("delta"),
            )
        elif event.get("data"):
            recorder.emit("model_text_delta", agent=agent_name, text=event["data"], delta=event.get("delta"))
        elif event.get("type") == "tool_use_stream":
            recorder.emit("tool_argument_delta", agent=agent_name, stream_event=event)
        elif event.get("init_event_loop") or event.get("start_event_loop") or event.get("force_stop"):
            recorder.emit("agent_loop_event", agent=agent_name, stream_event=event)

    return callback


def configure_otel(endpoint: str | None) -> None:
    """Enable Strands' standard OTLP/HTTP exporter only when configured."""

    if not endpoint:
        return
    from strands.telemetry import StrandsTelemetry

    StrandsTelemetry().setup_otlp_exporter(endpoint=endpoint)

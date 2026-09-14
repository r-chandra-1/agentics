"""Application service: session ownership and one complete recipe turn."""

from __future__ import annotations

import asyncio
import time
import uuid
from collections import OrderedDict
from dataclasses import dataclass, field

from recipe_agents.agents import AgentBundle, build_agent_bundle
from recipe_agents.config import Settings
from recipe_agents.schemas import RecipeResponse
from recipe_agents.tracing import TraceRecorder


class RecipeServiceError(RuntimeError):
    """Raised when the model loop cannot produce the promised response schema."""


@dataclass
class Session:
    """An orchestrator and lock belonging to one conversational session."""

    session_id: str
    agents: AgentBundle
    lock: asyncio.Lock = field(default_factory=asyncio.Lock)


@dataclass(frozen=True)
class TurnResult:
    response: RecipeResponse
    session_id: str
    turn_id: str


class RecipeService:
    """Keep a bounded in-memory map of independent conversation histories."""

    def __init__(self, settings: Settings, recorder: TraceRecorder, max_sessions: int = 100) -> None:
        self.settings = settings
        self.recorder = recorder
        self.max_sessions = max_sessions
        self._sessions: OrderedDict[str, Session] = OrderedDict()
        self._store_lock = asyncio.Lock()

    async def _get_session(self, requested_id: str | None) -> Session:
        async with self._store_lock:
            if requested_id and requested_id in self._sessions:
                session = self._sessions.pop(requested_id)
                self._sessions[requested_id] = session
                return session

            session_id = requested_id or uuid.uuid4().hex
            session = Session(
                session_id=session_id,
                agents=build_agent_bundle(self.settings, self.recorder),
            )
            self._sessions[session_id] = session

            # This demo stores histories only in RAM. Bounding the map avoids an
            # accidental memory leak during repeated experiments.
            while len(self._sessions) > self.max_sessions:
                self._sessions.popitem(last=False)
            return session

    async def create_recipe(self, prompt: str, requested_session_id: str | None = None) -> TurnResult:
        session = await self._get_session(requested_session_id)
        turn_id = uuid.uuid4().hex[:12]

        # A single orchestrator owns mutable message history. Serialize turns in
        # one session while still allowing different sessions to run concurrently.
        async with session.lock:
            with self.recorder.context(session.session_id, turn_id):
                turn_started = time.perf_counter()
                self.recorder.emit(
                    "api_request",
                    prompt=prompt,
                    requested_session_id=requested_session_id,
                    history_messages_before=len(session.agents.orchestrator.messages),
                )
                try:
                    result = await session.agents.orchestrator.invoke_async(
                        prompt,
                        invocation_state={
                            "session_id": session.session_id,
                            "turn_id": turn_id,
                        },
                        limits={"turns": self.settings.max_agent_turns},
                    )
                except Exception as exc:
                    self.recorder.emit("api_error", error=repr(exc))
                    raise RecipeServiceError(f"Agent execution failed: {exc}") from exc

                output = result.structured_output
                if output is None:
                    self.recorder.emit(
                        "api_error",
                        error="Orchestrator returned no structured output.",
                        message=result.message,
                    )
                    raise RecipeServiceError("Orchestrator returned no Pydantic structured output.")

                try:
                    response = RecipeResponse.model_validate(output)
                except Exception as exc:
                    self.recorder.emit("api_error", error=repr(exc), structured_output=output)
                    raise RecipeServiceError(f"Invalid RecipeResponse: {exc}") from exc

                self.recorder.emit(
                    "api_response",
                    structured_output=response,
                    stop_reason=result.stop_reason,
                    metrics=result.metrics.get_summary(),
                    history_messages_after=len(session.agents.orchestrator.messages),
                    turn_duration_ms=round((time.perf_counter() - turn_started) * 1000, 3),
                )
                return TurnResult(response=response, session_id=session.session_id, turn_id=turn_id)

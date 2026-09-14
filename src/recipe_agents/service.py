"""Application service: session ownership and one complete recipe turn."""

from __future__ import annotations

import asyncio
import time
import uuid
from collections import OrderedDict
from dataclasses import dataclass, field
from typing import Any, Callable

from recipe_agents.agents import (
    AgentBundle,
    build_agent_bundle,
    check_recipe_availability,
    estimate_ingredient_cost,
)
from recipe_agents.config import Settings
from recipe_agents.pricing import calculate_cost, lookup_availability
from recipe_agents.routing import RequestedItem, extract_requested_items
from recipe_agents.schemas import CostEstimate, RecipeBatchResponse, RecipeDraft, RecipeResponse
from recipe_agents.tracing import TraceRecorder


class RecipeServiceError(RuntimeError):
    """Raised when an expert cannot produce the promised response schema."""


@dataclass
class Session:
    """Expert instances and a lock belonging to one trace session."""

    session_id: str
    agents: AgentBundle
    lock: asyncio.Lock = field(default_factory=asyncio.Lock)


@dataclass(frozen=True)
class TurnResult:
    response: RecipeBatchResponse
    session_id: str
    turn_id: str


class RecipeService:
    """Deterministically route work while Strands experts generate recipes."""

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

    def _run_tool(
        self,
        name: str,
        tool_input: dict[str, Any],
        schema: dict[str, Any],
        operation: Callable[[], Any],
    ) -> Any:
        """Execute a Python lookup while preserving full tool-call trace events."""

        started = time.perf_counter()
        self.recorder.emit(
            "tool_call_start",
            agent="recipe_orchestrator",
            tool_name=name,
            input=tool_input,
            selected_tool_schema=schema,
            execution="deterministic_python",
        )
        try:
            result = operation()
        except Exception as exc:
            self.recorder.emit(
                "tool_call_end",
                agent="recipe_orchestrator",
                tool_name=name,
                duration_ms=round((time.perf_counter() - started) * 1000, 3),
                error=repr(exc),
            )
            raise
        self.recorder.emit(
            "tool_call_end",
            agent="recipe_orchestrator",
            tool_name=name,
            duration_ms=round((time.perf_counter() - started) * 1000, 3),
            result=result,
            execution="deterministic_python",
        )
        return result

    async def _invoke_expert(self, session: Session, requested: RequestedItem, prompt: str) -> RecipeDraft:
        """Invoke exactly one fresh-context specialist for a supported item."""

        agent = session.agents.coffee_expert if requested.item == "coffee" else session.agents.soup_expert
        agent.messages.clear()
        expert_prompt = (
            f"Create only the {requested.request_fragment!r} item from this request: {prompt!r}. "
            "Return the schema-conforming JSON object immediately without analysis."
        )
        result = await agent.invoke_async(
            expert_prompt,
            invocation_state={"session_id": session.session_id, "requested_item": requested.item},
            limits={"turns": self.settings.max_agent_turns},
        )
        text = "".join(
            block.get("text", "")
            for block in result.message.get("content", [])
            if isinstance(block, dict)
        )
        if not text.strip():
            raise RecipeServiceError(f"{requested.item} expert returned no JSON recipe draft.")
        return RecipeDraft.model_validate_json(text)

    @staticmethod
    def _format_recipe(draft: RecipeDraft) -> str:
        ingredients = "\n".join(
            f"- {ingredient.amount} {ingredient.unit} {ingredient.name}" for ingredient in draft.ingredients
        )
        steps = "\n".join(f"{index}. {step}" for index, step in enumerate(draft.steps, start=1))
        return f"Ingredients:\n{ingredients}\n\nSteps:\n{steps}"

    async def create_recipe(self, prompt: str, requested_session_id: str | None = None) -> TurnResult:
        session = await self._get_session(requested_session_id)
        turn_id = uuid.uuid4().hex[:12]

        # Expert objects own mutable message lists. Serialize one session while
        # allowing different sessions to run concurrently.
        async with session.lock:
            with self.recorder.context(session.session_id, turn_id):
                turn_started = time.perf_counter()
                self.recorder.emit(
                    "api_request",
                    prompt=prompt,
                    requested_session_id=requested_session_id,
                    history_messages_before=0,
                )
                requested_items = extract_requested_items(prompt)
                self.recorder.emit(
                    "agent_invocation_start",
                    agent="recipe_orchestrator",
                    execution="deterministic_python",
                    input_messages=[{"role": "user", "content": [{"text": prompt}]}],
                    routing_rules={
                        "coffee": sorted(["coffee", "latte", "espresso", "cappuccino", "mocha"]),
                        "soup": sorted(["soup", "chowder", "bisque"]),
                        "other": "unsupported",
                    },
                )
                try:
                    availability = {
                        requested.item: self._run_tool(
                            "check_recipe_availability",
                            {"item": requested.item},
                            check_recipe_availability.tool_spec,
                            lambda item=requested.item: lookup_availability(item),
                        )
                        for requested in requested_items
                    }
                    supported = [requested for requested in requested_items if availability[requested.item].available]
                    self.recorder.emit(
                        "routing_decision",
                        agent="recipe_orchestrator",
                        requested_items=requested_items,
                        supported_items=[requested.item for requested in supported],
                        dispatch="sequential_single_ollama",
                        reason="Concurrent generations on one local model contend for the same GPU.",
                    )
                    drafts = [
                        await self._invoke_expert(session, requested, prompt) for requested in supported
                    ]
                    drafts_by_item = {requested.item: draft for requested, draft in zip(supported, drafts)}

                    estimates: dict[str, CostEstimate] = {}
                    for requested, draft in zip(supported, drafts):
                        raw_ingredients = [ingredient.model_dump(mode="json") for ingredient in draft.ingredients]
                        estimates[requested.item] = self._run_tool(
                            "estimate_ingredient_cost",
                            {"ingredients": raw_ingredients},
                            estimate_ingredient_cost.tool_spec,
                            lambda ingredients=raw_ingredients: calculate_cost(ingredients),
                        )

                    responses: list[RecipeResponse] = []
                    for requested in requested_items:
                        if not availability[requested.item].available:
                            responses.append(
                                RecipeResponse(
                                    item=requested.item,
                                    description=f"No recipe expert is available for {requested.item}.",
                                    recipe="",
                                    cost="unavailable",
                                )
                            )
                            continue
                        draft = drafts_by_item[requested.item]
                        responses.append(
                            RecipeResponse(
                                item=draft.item,
                                description=draft.description,
                                recipe=self._format_recipe(draft),
                                cost=estimates[requested.item].display,
                            )
                        )
                    response = RecipeBatchResponse(recipes=responses)
                except Exception as exc:
                    self.recorder.emit("api_error", error=repr(exc))
                    raise RecipeServiceError(f"Agent execution failed: {exc}") from exc

                self.recorder.emit(
                    "agent_invocation_end",
                    agent="recipe_orchestrator",
                    execution="deterministic_python",
                    stop_reason="completed",
                    structured_output=response,
                )
                self.recorder.emit(
                    "api_response",
                    structured_output=response,
                    stop_reason="completed",
                    metrics={"model_calls": len(supported), "expert_execution": "sequential_single_ollama"},
                    history_messages_after=0,
                    turn_duration_ms=round((time.perf_counter() - turn_started) * 1000, 3),
                )
                return TurnResult(response=response, session_id=session.session_id, turn_id=turn_id)

from types import SimpleNamespace

import pytest

from recipe_agents.config import Settings
from recipe_agents.service import RecipeService, Session
from recipe_agents.tracing import TraceRecorder


class FakeExpert:
    def __init__(self, item: str) -> None:
        self.item = item
        self.messages: list = []

    async def invoke_async(self, _prompt: str, **_kwargs):
        ingredients = (
            [{"name": "ground_coffee", "amount": 10, "unit": "gram"}]
            if self.item == "coffee"
            else [{"name": "egg", "amount": 2, "unit": "each"}]
        )
        import json

        payload = {
                "item": self.item,
                "description": f"A simple {self.item} recipe.",
                "ingredients": ingredients,
                "steps": ["Make it.", "Serve it."],
            }
        return SimpleNamespace(message={"content": [{"text": json.dumps(payload)}]})


@pytest.mark.asyncio
async def test_python_orchestrator_routes_prices_and_assembles_in_order(monkeypatch, tmp_path) -> None:
    recorder = TraceRecorder(tmp_path)
    service = RecipeService(Settings(trace_directory=tmp_path), recorder)
    session = Session(
        session_id="session_123",
        agents=SimpleNamespace(coffee_expert=FakeExpert("coffee"), soup_expert=FakeExpert("soup")),
    )

    async def get_session(_requested_id):
        return session

    monkeypatch.setattr(service, "_get_session", get_session)
    result = await service.create_recipe("Give me tomato soup and a mocha")

    assert [recipe.item for recipe in result.response.recipes] == ["soup", "coffee"]
    assert [recipe.cost for recipe in result.response.recipes] == ["$0.60 USD", "$0.40 USD"]
    events = recorder.read("session_123")
    assert sum(event["event"] == "routing_decision" for event in events) == 1
    routing = next(event for event in events if event["event"] == "routing_decision")
    assert routing["data"]["dispatch"] == "sequential_single_ollama"
    assert sum(event["event"] == "tool_call_start" for event in events) == 4
    assert not any(event["event"] == "model_call_start" and event["agent"] == "recipe_orchestrator" for event in events)

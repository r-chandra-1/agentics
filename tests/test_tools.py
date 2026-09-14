from unittest.mock import Mock

from strands.hooks import BeforeToolCallEvent

from recipe_agents.agents import OrchestrationOrderGuard, check_recipe_availability, estimate_ingredient_cost


def test_tool_schemas_teach_the_model_expected_arguments() -> None:
    availability = check_recipe_availability.tool_spec
    cost = estimate_ingredient_cost.tool_spec

    assert availability["name"] == "check_recipe_availability"
    assert availability["inputSchema"]["json"]["required"] == ["item"]
    json_schema = cost["inputSchema"]["json"]
    ingredient_schema = json_schema["$defs"]["IngredientAmount"]
    assert ingredient_schema["properties"]["name"]["type"] == "string"
    assert set(ingredient_schema["required"]) == {"name", "amount", "unit"}


def _tool_event(name: str, state: dict) -> BeforeToolCallEvent:
    return BeforeToolCallEvent(
        agent=Mock(name="orchestrator"),
        selected_tool=None,
        tool_use={"name": name, "toolUseId": "test", "input": {}},
        invocation_state=state,
    )


def test_order_guard_requires_current_turn_availability_and_single_pricing() -> None:
    guard = OrchestrationOrderGuard()
    state: dict = {}

    too_early = _tool_event("soup_expert", state)
    guard.before_tool(too_early)
    assert "Availability must be checked" in too_early.cancel_tool

    guard.before_tool(_tool_event("check_recipe_availability", state))
    first_price = _tool_event("estimate_ingredient_cost", state)
    guard.before_tool(first_price)
    assert first_price.cancel_tool is False

    duplicate_price = _tool_event("estimate_ingredient_cost", state)
    guard.before_tool(duplicate_price)
    assert "already ran" in duplicate_price.cancel_tool

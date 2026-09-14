from recipe_agents.agents import build_agent_bundle, check_recipe_availability, estimate_ingredient_cost
from recipe_agents.config import Settings
from recipe_agents.schemas import RecipeDraft
from recipe_agents.tracing import TraceRecorder


def test_tool_schemas_teach_the_model_expected_arguments() -> None:
    availability = check_recipe_availability.tool_spec
    cost = estimate_ingredient_cost.tool_spec

    assert availability["name"] == "check_recipe_availability"
    assert availability["inputSchema"]["json"]["required"] == ["item"]
    json_schema = cost["inputSchema"]["json"]
    ingredient_schema = json_schema["$defs"]["IngredientAmount"]
    assert ingredient_schema["properties"]["name"]["type"] == "string"
    assert set(ingredient_schema["required"]) == {"name", "amount", "unit"}


def test_ollama_requests_explicitly_disable_thinking(tmp_path) -> None:
    settings = Settings(ollama_model="qwen3:30b-a3b", trace_directory=tmp_path)
    bundle = build_agent_bundle(settings, TraceRecorder(tmp_path))

    request = bundle.coffee_expert.model.format_request(messages=[], tool_specs=[])

    assert request["model"] == "qwen3:30b-a3b"
    assert request["think"] is False
    assert request["format"] == RecipeDraft.model_json_schema()

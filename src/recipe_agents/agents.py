"""Build the expert agents and publish deterministic tool schemas."""

from dataclasses import dataclass

from strands import Agent, tool
from strands.models.ollama import OllamaModel

from recipe_agents.config import Settings
from recipe_agents.pricing import calculate_cost, lookup_availability
from recipe_agents.prompts import COFFEE_EXPERT_PROMPT, SOUP_EXPERT_PROMPT
from recipe_agents.schemas import IngredientAmount, RecipeDraft
from recipe_agents.tracing import LearningTraceHooks, TraceRecorder, make_stream_callback


@tool
def check_recipe_availability(item: str) -> dict:
    """Check the fixed recipe catalog before choosing an expert.

    Args:
        item: One normalized lower-case singular item, such as coffee or soup.

    Returns:
        The normalized item, boolean availability, and exact `<item>:yes|no` answer.
    """

    return lookup_availability(item).model_dump(mode="json")


@tool
def estimate_ingredient_cost(ingredients: list[IngredientAmount]) -> dict:
    """Calculate a recipe cost from the fixed in-code ingredient price table.

    Args:
        ingredients: Exact normalized ingredient names, amounts, and units from an expert.

    Returns:
        A USD total, display string, line-item calculations, and unknown ingredients.
    """

    # Strands validates the outer tool object, but nested Pydantic values arrive
    # as ordinary dictionaries in the decorated function at runtime.
    raw = [IngredientAmount.model_validate(ingredient).model_dump(mode="json") for ingredient in ingredients]
    return calculate_cost(raw).model_dump(mode="json")


@dataclass
class AgentBundle:
    """The specialists invoked by the deterministic Python orchestrator."""

    coffee_expert: Agent
    soup_expert: Agent


def _model(settings: Settings) -> OllamaModel:
    """Configure one no-thinking, JSON-schema-constrained expert model."""

    return OllamaModel(
        host=settings.ollama_host,
        model_id=settings.ollama_model,
        temperature=0.0,
        max_tokens=800,
        keep_alive="10m",
        options={"num_ctx": 32_768},
        # Strands passes `additional_args` directly into ollama.AsyncClient.chat.
        # `think=False` is therefore a top-level Ollama request field, not a
        # prompt hint. The Qwen prompts also use /no_think as a model-specific
        # belt-and-suspenders instruction.
        additional_args={
            "think": False,
            "format": RecipeDraft.model_json_schema(),
        },
    )


def build_agent_bundle(settings: Settings, recorder: TraceRecorder) -> AgentBundle:
    """Construct the two Strands specialists used by the Python orchestrator."""

    coffee_expert = Agent(
        name="coffee_expert",
        description="Creates structured coffee recipes using priceable ingredients.",
        model=_model(settings),
        system_prompt=COFFEE_EXPERT_PROMPT,
        callback_handler=make_stream_callback(recorder, "coffee_expert"),
        hooks=[LearningTraceHooks(recorder)],
    )
    soup_expert = Agent(
        name="soup_expert",
        description="Creates structured soup recipes using priceable ingredients.",
        model=_model(settings),
        system_prompt=SOUP_EXPERT_PROMPT,
        callback_handler=make_stream_callback(recorder, "soup_expert"),
        hooks=[LearningTraceHooks(recorder)],
    )

    return AgentBundle(coffee_expert=coffee_expert, soup_expert=soup_expert)

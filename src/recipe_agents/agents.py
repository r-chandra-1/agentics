"""Build the expert agents, deterministic tools, and central orchestrator."""

from dataclasses import dataclass

from strands import Agent, tool
from strands.hooks import BeforeToolCallEvent, HookProvider, HookRegistry
from strands.models.ollama import OllamaModel

from recipe_agents.config import Settings
from recipe_agents.pricing import calculate_cost, lookup_availability
from recipe_agents.prompts import COFFEE_EXPERT_PROMPT, ORCHESTRATOR_PROMPT, SOUP_EXPERT_PROMPT
from recipe_agents.schemas import IngredientAmount, RecipeDraft, RecipeResponse
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
    """One isolated set of agents per user session."""

    orchestrator: Agent
    coffee_expert: Agent
    soup_expert: Agent


class OrchestrationOrderGuard(HookProvider):
    """Enforce two teaching-flow invariants that prompts cannot guarantee.

    The LLM still selects tools. If it chooses an invalid order, Strands returns
    this cancellation message as a tool error and gives the model another turn.
    That correction is visible in the trace rather than hidden in application
    control flow.
    """

    def register_hooks(self, registry: HookRegistry, **_: object) -> None:
        registry.add_callback(BeforeToolCallEvent, self.before_tool)

    def before_tool(self, event: BeforeToolCallEvent) -> None:
        state = event.invocation_state
        tool_name = event.tool_use.get("name")

        if tool_name == "check_recipe_availability":
            state["recipe_availability_checked_this_turn"] = True
            return

        if tool_name in {"coffee_expert", "soup_expert", "estimate_ingredient_cost", "RecipeResponse"}:
            if not state.get("recipe_availability_checked_this_turn"):
                event.cancel_tool = (
                    "Availability must be checked in this turn. Call "
                    "check_recipe_availability before any expert, pricing, or final response."
                )
                return

        if tool_name == "estimate_ingredient_cost":
            if state.get("recipe_pricing_called_this_turn"):
                event.cancel_tool = "Pricing already ran in this turn; submit RecipeResponse now."
            else:
                state["recipe_pricing_called_this_turn"] = True


def _model(settings: Settings) -> OllamaModel:
    """Give every agent the same local model configuration."""

    return OllamaModel(
        host=settings.ollama_host,
        model_id=settings.ollama_model,
        temperature=0.0,
        max_tokens=1_600,
        keep_alive="10m",
        options={"num_ctx": 32_768},
        # Qwen's native `thinking` field is not mapped by Strands 1.55.1's
        # Ollama adapter. Leaving it enabled produces many empty text chunks
        # and spends the output budget on data the app cannot observe.
        additional_args={"think": False},
    )


def build_agent_bundle(settings: Settings, recorder: TraceRecorder) -> AgentBundle:
    """Construct a hub-and-spoke "agents as tools" topology.

    Expert context is reset for each call (`preserve_context=False`). The central
    orchestrator remains alive for the whole API session, so its history is the
    memory window shown in later-turn traces.
    """

    coffee_expert = Agent(
        name="coffee_expert",
        description="Creates structured coffee recipes using priceable ingredients.",
        model=_model(settings),
        system_prompt=COFFEE_EXPERT_PROMPT,
        structured_output_model=RecipeDraft,
        callback_handler=make_stream_callback(recorder, "coffee_expert"),
        hooks=[LearningTraceHooks(recorder)],
    )
    soup_expert = Agent(
        name="soup_expert",
        description="Creates structured soup recipes using priceable ingredients.",
        model=_model(settings),
        system_prompt=SOUP_EXPERT_PROMPT,
        structured_output_model=RecipeDraft,
        callback_handler=make_stream_callback(recorder, "soup_expert"),
        hooks=[LearningTraceHooks(recorder)],
    )

    orchestrator = Agent(
        name="recipe_orchestrator",
        description="Checks availability, selects one specialist, prices ingredients, and compiles JSON.",
        model=_model(settings),
        system_prompt=ORCHESTRATOR_PROMPT,
        structured_output_model=RecipeResponse,
        tools=[
            check_recipe_availability,
            coffee_expert.as_tool(
                name="coffee_expert",
                description="Create a structured coffee recipe for the complete user request.",
                preserve_context=False,
            ),
            soup_expert.as_tool(
                name="soup_expert",
                description="Create a structured soup recipe for the complete user request.",
                preserve_context=False,
            ),
            estimate_ingredient_cost,
        ],
        callback_handler=make_stream_callback(recorder, "recipe_orchestrator"),
        hooks=[LearningTraceHooks(recorder), OrchestrationOrderGuard()],
    )
    return AgentBundle(orchestrator=orchestrator, coffee_expert=coffee_expert, soup_expert=soup_expert)

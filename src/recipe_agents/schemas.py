"""Pydantic contracts shared by the API, agents, and deterministic tools."""

from typing import Literal

from pydantic import BaseModel, Field


IngredientUnit = Literal["each", "gram", "ml", "tsp", "tbsp"]


class RecipeRequest(BaseModel):
    """The public request. Reusing a session preserves orchestrator history."""

    prompt: str = Field(min_length=2, max_length=2_000)
    session_id: str | None = Field(
        default=None,
        description="Optional prior X-Session-ID value for a multi-turn conversation.",
        pattern=r"^[A-Za-z0-9_-]{8,80}$",
    )


class IngredientAmount(BaseModel):
    """A normalized amount that the pricing function can calculate exactly."""

    name: str = Field(description="Canonical lower-case ingredient name from the price table.")
    amount: float = Field(gt=0, le=10_000)
    unit: IngredientUnit


class RecipeDraft(BaseModel):
    """Structured output created by either specialist agent."""

    item: Literal["coffee", "soup"]
    description: str = Field(min_length=5, max_length=240)
    ingredients: list[IngredientAmount] = Field(min_length=1, max_length=20)
    steps: list[str] = Field(min_length=1, max_length=20)


class AvailabilityResult(BaseModel):
    """Machine-friendly form plus the exact teaching-demo answer requested."""

    item: str
    available: bool
    answer: str


class CostLineItem(BaseModel):
    ingredient: str
    amount: float
    unit: IngredientUnit
    unit_price_usd: float | None
    subtotal_usd: float | None
    note: str | None = None


class CostEstimate(BaseModel):
    currency: Literal["USD"] = "USD"
    total_usd: float
    display: str
    line_items: list[CostLineItem]
    unknown_ingredients: list[str]


class RecipeResponse(BaseModel):
    """One requested item's exact four-key recipe result."""

    item: str = Field(description="Normalized item name.")
    description: str = Field(description="A brief description or availability explanation.")
    recipe: str = Field(description="Ingredients and numbered method, or an empty string.")
    cost: str = Field(description="Estimated ingredient cost, e.g. '$2.31 USD'.")


class RecipeBatchResponse(BaseModel):
    """All requested items, kept in the same order as the user's prompt."""

    recipes: list[RecipeResponse] = Field(
        min_length=1,
        max_length=8,
        description="One result per distinct requested item; never omit an unsupported item.",
    )


class HealthResponse(BaseModel):
    status: Literal["ok"] = "ok"
    model: str
    ollama_host: str

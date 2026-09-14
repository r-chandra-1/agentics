"""Deterministic availability and price lookups.

LLMs are good at interpreting a request and writing readable instructions. They
are a poor place to keep business facts. These tables and functions therefore
remain ordinary Python and are easy to unit test.
"""

from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
from typing import Any

from recipe_agents.schemas import (
    AvailabilityResult,
    CostEstimate,
    CostLineItem,
    IngredientAmount,
)


SUPPORTED_ITEMS = frozenset({"coffee", "soup"})


@dataclass(frozen=True)
class UnitPrice:
    unit: str
    usd: Decimal


# Prices are fictional teaching values, not current store prices. The first
# three preserve the examples from the project request: one egg is $0.30,
# 100 ml milk is $0.10, and one teaspoon sugar is $0.02.
PRICE_TABLE: dict[str, UnitPrice] = {
    "egg": UnitPrice("each", Decimal("0.30")),
    "milk": UnitPrice("ml", Decimal("0.001")),
    "sugar": UnitPrice("tsp", Decimal("0.02")),
    "ground_coffee": UnitPrice("gram", Decimal("0.04")),
    "water": UnitPrice("ml", Decimal("0.00")),
    "olive_oil": UnitPrice("tbsp", Decimal("0.15")),
    "onion": UnitPrice("each", Decimal("0.75")),
    "carrot": UnitPrice("each", Decimal("0.30")),
    "celery_stalk": UnitPrice("each", Decimal("0.25")),
    "garlic_clove": UnitPrice("each", Decimal("0.10")),
    "broth": UnitPrice("ml", Decimal("0.002")),
    "salt": UnitPrice("tsp", Decimal("0.01")),
    "pepper": UnitPrice("tsp", Decimal("0.03")),
}


def normalize_item(item: str) -> str:
    """Normalize only enough for a stable lookup; do not guess synonyms."""

    return "_".join(item.strip().lower().split()) or "unknown"


def lookup_availability(item: str) -> AvailabilityResult:
    """Return `coffee:yes`, `soup:yes`, or `<anything-else>:no`."""

    normalized = normalize_item(item)
    available = normalized in SUPPORTED_ITEMS
    return AvailabilityResult(
        item=normalized,
        available=available,
        answer=f"{normalized}:{'yes' if available else 'no'}",
    )


def calculate_cost(raw_ingredients: list[dict[str, Any]]) -> CostEstimate:
    """Validate ingredient data, apply fixed values, and sum with Decimal.

    A unit mismatch is deliberately reported as unknown instead of silently
    converting or guessing. That makes tool mistakes obvious in the trace.
    """

    line_items: list[CostLineItem] = []
    unknown: list[str] = []
    total = Decimal("0")

    for raw in raw_ingredients:
        ingredient = IngredientAmount.model_validate(raw)
        key = normalize_item(ingredient.name)
        price = PRICE_TABLE.get(key)

        if price is None or price.unit != ingredient.unit:
            expected = price.unit if price else "not in price table"
            note = f"Cannot price {key}: expected unit {expected}."
            unknown.append(key)
            line_items.append(
                CostLineItem(
                    ingredient=key,
                    amount=ingredient.amount,
                    unit=ingredient.unit,
                    unit_price_usd=None,
                    subtotal_usd=None,
                    note=note,
                )
            )
            continue

        amount = Decimal(str(ingredient.amount))
        subtotal = (amount * price.usd).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        total += subtotal
        line_items.append(
            CostLineItem(
                ingredient=key,
                amount=ingredient.amount,
                unit=ingredient.unit,
                unit_price_usd=float(price.usd),
                subtotal_usd=float(subtotal),
            )
        )

    total = total.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    suffix = " (known ingredients only)" if unknown else ""
    return CostEstimate(
        total_usd=float(total),
        display=f"${total:.2f} USD{suffix}",
        line_items=line_items,
        unknown_ingredients=unknown,
    )

from recipe_agents.pricing import calculate_cost, lookup_availability


def test_availability_has_exact_requested_answers() -> None:
    assert lookup_availability(" Coffee ").answer == "coffee:yes"
    assert lookup_availability("soup").answer == "soup:yes"
    assert lookup_availability("bread").answer == "bread:no"


def test_cost_uses_fixed_values() -> None:
    estimate = calculate_cost(
        [
            {"name": "egg", "amount": 2, "unit": "each"},
            {"name": "milk", "amount": 100, "unit": "ml"},
            {"name": "sugar", "amount": 1, "unit": "tsp"},
        ]
    )
    assert estimate.total_usd == 0.72
    assert estimate.display == "$0.72 USD"
    assert estimate.unknown_ingredients == []


def test_unknown_and_unit_mismatch_are_visible_not_guessed() -> None:
    estimate = calculate_cost(
        [
            {"name": "truffle", "amount": 1, "unit": "gram"},
            {"name": "milk", "amount": 1, "unit": "tbsp"},
        ]
    )
    assert estimate.display == "$0.00 USD (known ingredients only)"
    assert estimate.unknown_ingredients == ["truffle", "milk"]

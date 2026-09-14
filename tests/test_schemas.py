from recipe_agents.schemas import RecipeBatchResponse


def test_recipe_batch_keeps_multiple_results_in_order() -> None:
    response = RecipeBatchResponse.model_validate(
        {
            "recipes": [
                {"item": "coffee", "description": "A latte.", "recipe": "Make it.", "cost": "$1.00 USD"},
                {"item": "soup", "description": "Tomato soup.", "recipe": "Cook it.", "cost": "$2.00 USD"},
            ]
        }
    )

    assert [recipe.item for recipe in response.recipes] == ["coffee", "soup"]

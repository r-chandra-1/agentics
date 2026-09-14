from recipe_agents.routing import extract_requested_items


def test_supported_items_are_extracted_in_user_order() -> None:
    items = extract_requested_items("Give me tomato soup and a mocha")
    assert [item.item for item in items] == ["soup", "coffee"]


def test_unsupported_items_are_preserved_for_availability_lookup() -> None:
    items = extract_requested_items("Please make bread and cake")
    assert [item.item for item in items] == ["bread", "cake"]


def test_duplicate_normalized_items_are_not_dispatched_twice() -> None:
    items = extract_requested_items("coffee and a latte")
    assert [item.item for item in items] == ["coffee"]

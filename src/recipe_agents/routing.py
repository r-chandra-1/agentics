"""Small deterministic request parser for the deliberately tiny recipe catalog.

This is intentionally not a general natural-language parser. It recognizes the
two supported catalog families and extracts a reasonable noun for unsupported
items so the availability lookup can return `<item>:no`.
"""

from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class RequestedItem:
    """One distinct item plus the request fragment that named it."""

    item: str
    request_fragment: str


COFFEE_WORDS = frozenset({"coffee", "latte", "espresso", "cappuccino", "mocha"})
SOUP_WORDS = frozenset({"soup", "chowder", "bisque"})
FILLER_WORDS = frozenset(
    {
        "a",
        "an",
        "the",
        "please",
        "give",
        "get",
        "make",
        "me",
        "i",
        "want",
        "would",
        "like",
        "how",
        "do",
        "to",
        "for",
        "recipe",
        "recipes",
        "simple",
    }
)


def _normalize_fragment(fragment: str) -> str:
    words = re.findall(r"[a-z0-9]+", fragment.lower())
    if COFFEE_WORDS.intersection(words):
        return "coffee"
    if SOUP_WORDS.intersection(words):
        return "soup"
    meaningful = [word for word in words if word not in FILLER_WORDS]
    return meaningful[-1] if meaningful else "unknown"


def extract_requested_items(prompt: str) -> list[RequestedItem]:
    """Return distinct normalized items in the order the user mentioned them."""

    fragments = [part.strip(" .!?\t\n") for part in re.split(r"\s*(?:,|;|\band\b|&)\s*", prompt, flags=re.I)]
    items: list[RequestedItem] = []
    seen: set[str] = set()
    for fragment in fragments:
        if not fragment:
            continue
        item = _normalize_fragment(fragment)
        if item not in seen:
            items.append(RequestedItem(item=item, request_fragment=fragment))
            seen.add(item)
    return items or [RequestedItem(item="unknown", request_fragment=prompt)]

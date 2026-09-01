"""Deterministic query rephrase: slots → a short lexical search string."""
from __future__ import annotations

from typing import Iterable

NOISE = {
    "imported", "manufacturer", "discontinued", "inches", "ounces", "dimensions",
    "closure", "available", "date", "gift", "box", "package", "product",
    "approximately", "measures", "shaft", "arch", "first", "made", "usa",
    "please", "special", "celebrate", "holiday", "office", "party",
    "anniversary", "christmas", "valentine", "thanksgiving", "independence",
    "labor", "easter", "mother", "mothers", "year", "day", "new", "looking",
    "still", "exploring",
}
MATERIALS = {
    "cotton", "polyester", "nylon", "leather", "wool", "spandex", "silk",
    "rayon", "fabric", "mesh", "textile", "suede", "canvas", "denim", "rubber",
    "alloy", "stainless", "gold", "silver",
}
COLORS = {
    "black", "white", "blue", "red", "pink", "green", "brown", "gray", "grey",
    "purple", "yellow", "orange", "navy", "beige", "gold", "silver", "ivory",
    "khaki",
}


def rephrase_terms(category: str, constraints: Iterable[str], extra_terms: Iterable[str]) -> list[str]:
    """Build a short, distinctive token list (materials/colors first, catalog filler dropped)."""
    raw: list[str] = []
    if category:
        raw.extend(category.lower().split())
    for constraint in constraints:
        raw.extend(constraint.lower().replace(":", " ").split())
    raw.extend(str(t).lower() for t in extra_terms)
    cleaned = []
    for token in raw:
        token = "".join(ch for ch in token if ch.isalnum())
        if len(token) < 2 or token in NOISE:
            continue
        cleaned.append(token)
    head = [t for t in cleaned if t in MATERIALS or t in COLORS]
    tail = [t for t in cleaned if t not in MATERIALS and t not in COLORS]
    ordered: list[str] = []
    seen: set[str] = set()
    for token in head + tail:
        if token in seen:
            continue
        seen.add(token)
        ordered.append(token)
        if len(ordered) >= 28:
            break
    return ordered


def rephrase_brief(category: str, constraints: list[str], dont_care: set[str], tags: list[str]) -> str:
    """Human-readable shopper brief for optional LLM rerank (not used as FTS query)."""
    bits = []
    if category:
        bits.append(f"category: {category}")
    if constraints:
        bits.append("must-have: " + "; ".join(constraints[:6]))
    if dont_care:
        bits.append("ignore: " + ", ".join(sorted(dont_care)))
    if tags:
        bits.append("soft: " + ", ".join(tags))
    return " | ".join(bits) if bits else "clothing item"

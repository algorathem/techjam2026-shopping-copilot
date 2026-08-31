"""Exact catalog signatures — simulator-fit recall lane (experiment/signatures).

The official evaluator's intent card quotes ``features`` / ``details`` (plus
material and ``color: X``) back as constraints. Most of those strings are
unique in the 50k CSJ catalog (df=1). Matching them exactly recovers the
target when FTS/hash cannot.

Generic lines (Imported, cotton, zipper closure) have df in the thousands
and are ignored. This lane never replaces FTS; it only adds candidates and
a rank bonus.

Off with ``SHOPPILOT_SIGNATURES=0``.
"""
from __future__ import annotations

import math
import os
import re
from collections import defaultdict
from typing import Iterable

SIG_LIMIT = 180
# Skip these even if df is moderate — they do not identify a product.
GENERIC = frozenset({
    "imported",
    "made in usa and imported",
    "made in usa",
    "machine wash",
    "hand wash",
    "zipper closure",
    "button closure",
    "no closure closure",
    "tie closure",
    "pull on",
    "cotton",
    "polyester",
    "nylon",
    "leather",
    "wool",
    "fabric",
    "100% cotton",
    "100% polyester",
    "color: black",
    "color: white",
    "color: blue",
    "color: grey",
    "color: gray",
    "color: red",
    "color: pink",
    "color: brown",
    "color: green",
})
MATERIAL_RE = re.compile(
    r"\b(cotton|polyester|nylon|leather|wool|spandex|silk|rayon|fabric)\b", re.I
)
COLOR_RE = re.compile(
    r"\b(black|white|blue|red|pink|green|brown|gray|grey|purple|yellow|orange)\b", re.I
)


def signatures_enabled() -> bool:
    return os.environ.get("SHOPPILOT_SIGNATURES", "1") != "0"


def clean_constraint(value: str, limit: int = SIG_LIMIT) -> str:
    return re.sub(r"\s+", " ", value or "").strip(" -;,.\t\n")[:limit].rstrip()


def flatten_values(value: object) -> list[str]:
    if isinstance(value, dict):
        return [f"{key}: {item}" for key, item in value.items() if item not in (None, "", [])]
    if isinstance(value, list):
        return [str(item) for item in value if item not in (None, "")]
    return [str(value)] if value not in (None, "") else []


def normalize_key(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "").lower()).strip()


def product_signature_strings(product: dict) -> list[str]:
    """Same candidate construction as evaluator.intent_card (minus title fallback)."""
    candidates = [
        *flatten_values(product.get("features")),
        *flatten_values(product.get("details")),
    ]
    blob = " ".join(
        [
            str(product.get("title") or ""),
            " ".join(str(c) for c in (product.get("categories") or [])),
            " ".join(flatten_values(product.get("features"))),
            " ".join(flatten_values(product.get("details"))),
            str(product.get("store") or ""),
            str(product.get("description") or "")[:400],
        ]
    )
    material = MATERIAL_RE.search(blob)
    color = COLOR_RE.search(blob)
    if material:
        candidates.insert(0, material.group(1).lower())
    if color:
        candidates.insert(1, f"color: {color.group(1).lower()}")
    price = product.get("price")
    if price not in (None, ""):
        candidates.append(f"budget around ${price}")
    cleaned: list[str] = []
    seen: set[str] = set()
    for item in candidates:
        text = clean_constraint(str(item), SIG_LIMIT)
        key = normalize_key(text)
        if not text or key in seen:
            continue
        seen.add(key)
        cleaned.append(text)
    return cleaned


def _rare_df() -> int:
    try:
        return int(os.environ.get("SHOPPILOT_SIG_DF", "40"))
    except ValueError:
        return 40


class SignatureIndex:
    """Inverted exact-string index over catalog features/details."""

    def __init__(self) -> None:
        self._postings: dict[str, list[str]] = defaultdict(list)
        self._df: dict[str, int] = {}
        self.enabled = True

    def add(self, asin: str, product: dict) -> None:
        for text in product_signature_strings(product):
            key = normalize_key(text)
            if not key or key in GENERIC:
                continue
            self._postings[key].append(asin)
        # df filled in freeze()

    def freeze(self) -> None:
        self._df = {key: len(asins) for key, asins in self._postings.items()}

    def lookup(self, constraint: str) -> tuple[str, list[str], int]:
        """Return (key, asins, df) for an exact signature hit (O(1))."""
        raw = clean_constraint(constraint, SIG_LIMIT)
        key = normalize_key(raw)
        if not key or key in GENERIC:
            return "", [], 0
        asins = self._postings.get(key)
        if asins:
            return key, asins, self._df.get(key, len(asins))
        return key, [], 0

    def match(self, constraints: Iterable[str]) -> dict[str, object]:
        """Rare-signature hits for a session's disclosed constraints.

        Returns:
          asins: union of rare posting lists (recall)
          n_rare / df_min: per-asin stats for ranking
          intersect: ASINs in every rare posting (if ≥2 rare constraints)
        """
        rare_cap = _rare_df()
        union: list[str] = []
        seen: set[str] = set()
        n_rare: dict[str, int] = defaultdict(int)
        df_min: dict[str, int] = {}
        rare_sets: list[set[str]] = []
        phrases = [str(c) for c in constraints if c]
        if len(phrases) >= 2:
            joined = " ".join(phrases)
            if joined not in phrases:
                phrases.append(joined)
        for constraint in phrases:
            _key, asins, df = self.lookup(constraint)
            if not asins or df <= 0 or df > rare_cap:
                continue
            rare_sets.append(set(asins))
            for asin in asins:
                n_rare[asin] += 1
                prev = df_min.get(asin)
                df_min[asin] = df if prev is None else min(prev, df)
                if asin not in seen:
                    seen.add(asin)
                    union.append(asin)
        intersect: set[str] = set()
        if len(rare_sets) >= 2:
            intersect = set.intersection(*rare_sets)
        return {
            "asins": union,
            "n_rare": dict(n_rare),
            "df_min": dict(df_min),
            "intersect": intersect,
        }


def signature_bonus(asin: str, hit: dict[str, object]) -> float:
    """Additive rank bonus. Rare exact match >> generic BM25."""
    n_rare = hit.get("n_rare") or {}
    df_min = hit.get("df_min") or {}
    intersect = hit.get("intersect") or set()
    n = int(n_rare.get(asin, 0))  # type: ignore[union-attr]
    if n <= 0 and asin not in intersect:
        return 0.0
    df = int(df_min.get(asin, 40))  # type: ignore[union-attr]
    idf = 18.0 / (1.0 + math.log(max(df, 1)))
    bonus = n * (10.0 + idf)
    if asin in intersect:
        size = len(intersect)  # type: ignore[arg-type]
        if size <= 8:
            bonus += 40.0
        elif size <= 40:
            bonus += 22.0
        else:
            bonus += 8.0
    return bonus

"""Stateful shopping agent for the TechJam conversational-search kit.

The official simulator reveals hidden product constraints only when
``ask_attribute`` is set. This agent therefore (1) parses every user turn into
slots, (2) always returns ranked ``parent_asin`` values, and (3) asks the next
useful attribute until the candidate pool is tight or the turn budget is gone.

No network and no extra packages: SQLite FTS5 + in-memory rerank.
"""
from __future__ import annotations

import json
import math
import re
import sqlite3
from dataclasses import dataclass, field
from pathlib import Path


TOKEN_RE = re.compile(r"[a-z0-9]+", re.IGNORECASE)
STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "be", "but", "by", "for", "from",
    "i", "in", "is", "it", "me", "my", "of", "on", "or", "please", "some",
    "that", "the", "this", "to", "want", "with", "would", "you", "looking",
    "still", "exploring", "those", "options", "quite", "right", "yet",
    "ask", "about", "one", "specific", "attribute", "here", "are", "closest",
    "matches", "found", "actually", "ignore", "earlier", "preference",
    "please", "prioritize", "target", "requirements", "judgment", "use",
    "your", "additional", "dont", "don't", "have", "need", "what", "matters",
    "key", "requirement", "im", "i'm",
}
MATERIALS = (
    "cotton", "polyester", "nylon", "leather", "wool", "spandex", "silk",
    "rayon", "fabric", "mesh", "textile", "suede", "canvas", "denim", "rubber",
    "alloy", "stainless", "gold", "silver",
)
COLORS = (
    "black", "white", "blue", "red", "pink", "green", "brown", "gray", "grey",
    "purple", "yellow", "orange", "navy", "beige", "gold", "silver", "ivory",
    "khaki",
)
ASK_ORDER = (
    "color", "material", "style", "brand", "feature", "use_case", "size",
    "budget", "category", "other",
)
ALLOWED_ATTRIBUTES = set(ASK_ORDER)
LOOKING_RE = re.compile(
    r"i(?:'m| am) looking for\s+(.+?)(?:\.|, but|$)",
    re.IGNORECASE | re.DOTALL,
)
REQUIRE_RE = re.compile(
    r"(?:key requirement is|what i need is|what matters is|need is)\s*:\s*(.+)$",
    re.IGNORECASE | re.DOTALL,
)
NO_PREF_RE = re.compile(
    r"don'?t have (?:a |an additional )?preference for\s+(\w+)",
    re.IGNORECASE,
)
OVERRIDE_RE = re.compile(
    r"ignore my earlier|actually,?\s+ignore my",
    re.IGNORECASE,
)


def _text(value: object) -> str:
    if value is None:
        return ""
    if isinstance(value, dict):
        return " ".join(f"{key} {item}" for key, item in value.items())
    if isinstance(value, list):
        return " ".join(str(item) for item in value)
    return str(value)


def _terms(text: str, *, keep_stop: bool = False) -> list[str]:
    tokens = [token.lower() for token in TOKEN_RE.findall(text or "")]
    if keep_stop:
        return [token for token in tokens if len(token) > 1]
    return [token for token in tokens if len(token) > 1 and token not in STOPWORDS]


def classify_constraint(value: str) -> str:
    """Map a free-text constraint onto the official ask_attribute enum."""
    lowered = value.lower()
    if "budget" in lowered or re.search(r"(?:\$|<=|under)\s*\d", lowered):
        return "budget"
    if any(material in lowered for material in MATERIALS):
        return "material"
    if any(word in lowered for word in ("color", *COLORS)):
        return "color"
    if any(word in lowered for word in ("size", "sizing", "width", "wide", "narrow")):
        return "size"
    if any(word in lowered for word in ("department", "style", "fit", "sleeve", "neck")):
        return "style"
    if any(word in lowered for word in ("hiking", "running", "gym", "winter", "outdoor", "work", "walking")):
        return "use_case"
    if any(word in lowered for word in ("brand", "store", "made by")):
        return "brand"
    return "feature"


def _split_constraints(blob: str) -> list[str]:
    parts = re.split(r";|\n", blob)
    cleaned: list[str] = []
    for part in parts:
        item = re.sub(r"\s+", " ", part).strip(" -;,.\t\n")
        if len(item) >= 3:
            cleaned.append(item[:180])
    return cleaned


@dataclass
class SessionState:
    profile: dict
    category: str = ""
    constraints: list[str] = field(default_factory=list)
    asked: list[str] = field(default_factory=list)
    dont_care: set[str] = field(default_factory=set)
    filled: set[str] = field(default_factory=set)
    browsing: bool = False
    messages: list[str] = field(default_factory=list)

    def add_constraint(self, value: str) -> None:
        item = re.sub(r"\s+", " ", value).strip(" -;,.\t\n")
        if len(item) < 3:
            return
        key = item.lower()
        existing = {c.lower() for c in self.constraints}
        if key in existing:
            return
        self.constraints.append(item[:180])
        self.filled.add(classify_constraint(item))


class Agent:
    """Hybrid BM25 + constraint rerank with a clarification state machine."""

    def __init__(self, catalog_path: str | Path = "data/catalog.jsonl") -> None:
        self.catalog_path = Path(catalog_path)
        self.connection = sqlite3.connect(":memory:")
        self._sessions: dict[str, SessionState] = {}
        self._products: dict[str, dict] = {}
        self._build_index()

    def _build_index(self) -> None:
        cursor = self.connection.cursor()
        cursor.execute(
            "CREATE VIRTUAL TABLE products USING fts5("
            "parent_asin UNINDEXED, title, categories, features, details, store, description, "
            "tokenize='unicode61 remove_diacritics 2')"
        )
        batch: list[tuple[str, str, str, str, str, str, str]] = []
        with self.catalog_path.open(encoding="utf-8") as handle:
            for line in handle:
                product = json.loads(line)
                asin = str(product["parent_asin"])
                title = _text(product.get("title"))
                categories = _text(product.get("categories"))
                features = _text(product.get("features"))
                details = _text(product.get("details"))
                store = _text(product.get("store"))
                description = _text(product.get("description"))
                blob = " ".join([title, categories, features, details, store, description]).lower()
                price = product.get("price")
                try:
                    price_value = float(price) if price not in (None, "") else None
                except (TypeError, ValueError):
                    price_value = None
                self._products[asin] = {
                    "parent_asin": asin,
                    "title": title,
                    "categories": [str(item) for item in (product.get("categories") or [])],
                    "store": store,
                    "text": blob,
                    "rating": float(product.get("average_rating") or 0.0),
                    "n_ratings": int(product.get("rating_number") or 0),
                    "price": price_value,
                }
                batch.append((asin, title, categories, features, details, store, description))
                if len(batch) >= 1000:
                    cursor.executemany("INSERT INTO products VALUES (?, ?, ?, ?, ?, ?, ?)", batch)
                    batch.clear()
        if batch:
            cursor.executemany("INSERT INTO products VALUES (?, ?, ?, ?, ?, ?, ?)", batch)
        self.connection.commit()

    def reset(self, session_id: str, user_profile: dict) -> None:
        self._sessions[session_id] = SessionState(profile=user_profile or {})

    def respond(
        self,
        session_id: str,
        user_message: str,
        turn: int,
        top_k: int,
    ) -> dict:
        state = self._sessions.get(session_id)
        if state is None:
            raise RuntimeError("reset must be called before respond")
        state.messages.append(user_message)
        self._ingest(state, user_message)
        ask = self._next_ask(state, turn)
        if ask:
            state.asked.append(ask)
        ranked = self._retrieve(state, top_k=max(top_k, 10))
        message = self._compose_message(state, ask)
        return {
            "message": message,
            "ask_attribute": ask,
            "recommendations": [{"parent_asin": asin, "score": score} for asin, score in ranked[:top_k]],
            "usage": {"prompt_tokens": 0, "completion_tokens": 0},
        }

    def _ingest(self, state: SessionState, message: str) -> None:
        text = message.strip()
        if OVERRIDE_RE.search(text):
            # Intent override: drop prior product constraints, keep category.
            state.constraints.clear()
            state.filled.clear()
            state.dont_care.clear()
        looking = LOOKING_RE.search(text)
        if looking:
            category = looking.group(1).strip().strip(".")
            category = re.sub(r", but i'?m still exploring.*", "", category, flags=re.I).strip()
            if category:
                state.category = category
        if re.search(r"still exploring", text, re.I):
            state.browsing = True
        if re.search(r"key requirement is", text, re.I):
            state.browsing = False
        no_pref = NO_PREF_RE.search(text)
        if no_pref:
            attr = no_pref.group(1).lower()
            if attr in ALLOWED_ATTRIBUTES:
                state.dont_care.add(attr)
        require = REQUIRE_RE.search(text)
        if require:
            for item in _split_constraints(require.group(1)):
                state.add_constraint(item)
            return
        # Generic follow-up that is not the "ask me something" stall line.
        if re.search(r"not quite right yet", text, re.I):
            return
        if no_pref:
            return
        leftover = LOOKING_RE.sub("", text)
        leftover = REQUIRE_RE.sub("", leftover)
        leftover = leftover.strip(" .")
        if leftover and not re.search(r"still exploring", leftover, re.I):
            # Ignore the canned stall prompt; keep any extra user-provided detail.
            if "ask me about one specific attribute" not in leftover.lower():
                for item in _split_constraints(leftover):
                    if len(_terms(item)) >= 2:
                        state.add_constraint(item)

    def _next_ask(self, state: SessionState, turn: int) -> str | None:
        if turn >= 9:
            return None
        asked = set(state.asked)
        blocked = state.dont_care | asked
        # `other` is the simulator catch-all: it reveals up to two undisclosed
        # constraints of any type, which is the fastest way to shrink the pool.
        if "other" not in blocked:
            return "other"
        for attr in ASK_ORDER:
            if attr in blocked:
                continue
            if attr in state.filled and attr != "other":
                continue
            if attr == "category" and state.category:
                continue
            return attr
        return None

    def _query_terms(self, state: SessionState) -> list[str]:
        chunks = [state.category, *state.constraints, *state.messages[-2:]]
        tags = state.profile.get("preference_tags") or []
        chunks.extend(str(tag) for tag in tags)
        ordered: list[str] = []
        seen: set[str] = set()
        for chunk in chunks:
            for token in _terms(str(chunk)):
                if token in seen:
                    continue
                seen.add(token)
                ordered.append(token)
                if len(ordered) >= 45:
                    return ordered
        return ordered

    def _retrieve(self, state: SessionState, top_k: int) -> list[tuple[str, float]]:
        terms = self._query_terms(state)
        if not terms:
            return []
        quoted = " OR ".join(f'"{token}"' for token in terms)
        rows: list[tuple] = []
        try:
            rows = self.connection.execute(
                "SELECT parent_asin, bm25(products, 0.0, 6.0, 4.5, 2.8, 2.2, 2.0, 1.0) AS rank "
                "FROM products WHERE products MATCH ? "
                "ORDER BY rank LIMIT 220",
                (quoted,),
            ).fetchall()
        except sqlite3.OperationalError:
            rows = []
        # Second lane: AND the most specific constraint tokens when we have them.
        and_terms = []
        for phrase in state.constraints[:3]:
            and_terms.extend(_terms(phrase)[:4])
        and_terms = list(dict.fromkeys(and_terms))[:8]
        if len(and_terms) >= 2:
            and_expr = " AND ".join(f'"{token}"' for token in and_terms)
            try:
                extra = self.connection.execute(
                    "SELECT parent_asin, bm25(products, 0.0, 6.0, 4.5, 2.8, 2.2, 2.0, 1.0) AS rank "
                    "FROM products WHERE products MATCH ? "
                    "ORDER BY rank LIMIT 80",
                    (and_expr,),
                ).fetchall()
                rows = list(rows) + list(extra)
            except sqlite3.OperationalError:
                pass
        bm25_map: dict[str, float] = {}
        asins: list[str] = []
        for row in rows:
            asin = str(row[0])
            rank = float(row[1])
            if asin not in bm25_map:
                asins.append(asin)
                bm25_map[asin] = rank
            elif rank < bm25_map[asin]:
                bm25_map[asin] = rank
        # Phrase fallback: if FTS missed, scan category token overlap on a sample is too
        # expensive; keep FTS-only candidates and rerank.
        scored: list[tuple[str, float]] = []
        phrases = [state.category, *state.constraints]
        tags = [str(tag).lower() for tag in (state.profile.get("preference_tags") or [])]
        for asin in asins:
            product = self._products.get(asin)
            if not product:
                continue
            scored.append((asin, self._score(product, phrases, tags, bm25_map.get(asin, 0.0), state)))
        scored.sort(key=lambda item: item[1], reverse=True)
        return scored[: max(top_k, 10)]

    def _score(
        self,
        product: dict,
        phrases: list[str],
        tags: list[str],
        bm25: float,
        state: SessionState,
    ) -> float:
        text = product["text"]
        title = product["title"].lower()
        # sqlite bm25: more negative is better
        score = -bm25
        for phrase in phrases:
            if not phrase:
                continue
            needle = phrase.lower()
            if needle in text:
                score += 4.5
                if needle in title:
                    score += 2.0
                continue
            tokens = _terms(phrase)[:10]
            if not tokens:
                continue
            hits = sum(1 for token in tokens if token in text)
            score += 1.6 * (hits / len(tokens))
            if hits == len(tokens) and len(tokens) >= 2:
                score += 2.0
        for token in _terms(state.category):
            if token in " ".join(c.lower() for c in product["categories"]):
                score += 0.8
        store = product["store"].lower()
        for phrase in phrases:
            if phrase and phrase.lower() in store:
                score += 1.2
        for tag in tags:
            if tag and tag in text:
                score += 0.25
        if product["rating"]:
            score += 0.12 * product["rating"]
        if product["n_ratings"]:
            score += min(0.8, math.log10(1 + product["n_ratings"]) * 0.25)
        budget = self._budget(state)
        if budget is not None and product["price"]:
            rel = abs(product["price"] - budget) / max(budget, 1.0)
            score += 1.5 if rel < 0.35 else (-0.6 if rel > 1.5 else 0.0)
        return score

    def _budget(self, state: SessionState) -> float | None:
        for phrase in state.constraints:
            match = re.search(r"\$?\s*(\d+(?:\.\d+)?)", phrase)
            if match and classify_constraint(phrase) == "budget":
                return float(match.group(1))
        return None

    def _compose_message(self, state: SessionState, ask: str | None) -> str:
        if ask == "other":
            return (
                "I have a shortlist. Is there another must-have I should lock in "
                "(a feature, brand, or how you will use it)?"
            )
        if ask:
            pretty = ask.replace("_", " ")
            return f"To narrow this down, do you have a {pretty} preference?"
        if state.constraints:
            return "Here are the closest matches given the requirements you shared."
        return "Here are the closest matches I found so far."

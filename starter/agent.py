"""Stateful shopping agent for the TechJam conversational-search kit.

Pipeline: slot parse → query rephrase → hybrid FTS5 retrieve → lexical rerank
→ optional LLM semantic rerank (SpaceXAI / xAI, off unless SHOPPILOT_LLM=1).
"""
from __future__ import annotations

import json
import math
import re
import sqlite3
from dataclasses import dataclass, field
from pathlib import Path

from starter.dense import DenseIndex, query_text_from_state
from starter.llm_rerank import llm_enabled, rerank as llm_rerank
from starter.rewrite import rephrase_brief


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
# Pool-split scoring prefers these first when info-gain ties.
# Brand/category often have high entropy but rarely match the simulator's
# hidden constraint classifier, so they stay low priority.
ASK_PRIORITY = {
    "other": 100.0,
    "color": 9.0,
    "material": 8.5,
    "use_case": 7.5,
    "style": 7.0,
    "feature": 6.5,
    "size": 5.0,
    "budget": 4.5,
    "brand": 2.0,
    "category": 1.0,
}
# Only these may be reordered by pool-split; brand/category/feature stay static.
POOL_ELIGIBLE = frozenset({
    "color", "material", "use_case", "style", "size", "budget",
})
ALLOWED_ATTRIBUTES = set(ASK_ORDER)
STYLE_TOKENS = (
    "casual", "formal", "athletic", "vintage", "classic", "slim", "relaxed",
    "fitted", "loose", "sleeve", "sleeveless", "crew", "v-neck", "vneck",
    "hoodie", "bootcut", "skinny", "wide", "high-waist", "mid-rise",
)
USE_CASE_TOKENS = (
    "hiking", "running", "gym", "winter", "summer", "outdoor", "work",
    "walking", "travel", "sport", "training", "beach", "rain", "snow",
)
# Dense hybrid lane weight inside the final score (hash cosine is ~[-1,1]).
# Public-set sweep: w=0 → Tech 0.781; w=4.5 → 0.788; w=6.0 → 0.787.
DENSE_SCORE_WEIGHT = 4.5
DENSE_RECALL_K = 80
INFO_GAIN_TOP_N = 40
# Only override static order when the default facet is barely present in the
# live pool AND another high-trust facet clearly splits candidates.
DEFAULT_COVERAGE_MAX = 0.35
ALT_GAIN_MIN = 0.45
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
    # Parallel to constraints: "soft" (pre-override free text) | "disclosed" | "override"
    constraint_sources: list[str] = field(default_factory=list)
    asked: list[str] = field(default_factory=list)
    dont_care: set[str] = field(default_factory=set)
    filled: set[str] = field(default_factory=set)
    browsing: bool = False
    messages: list[str] = field(default_factory=list)
    # Messages at/after this index are safe for retrieval (pre-override history discarded).
    query_message_start: int = 0
    override_applied: bool = False
    discarded_terms: set[str] = field(default_factory=set)
    prompt_tokens: int = 0
    completion_tokens: int = 0

    def add_constraint(self, value: str, source: str = "soft") -> None:
        item = re.sub(r"\s+", " ", value).strip(" -;,.\t\n")
        if len(item) < 3:
            return
        key = item.lower()
        existing = {c.lower() for c in self.constraints}
        if key in existing:
            # Upgrade source if we re-see a soft constraint as disclosed/override.
            if source in {"disclosed", "override"}:
                for index, current in enumerate(self.constraints):
                    if current.lower() == key:
                        self.constraint_sources[index] = source
                        break
            return
        self.constraints.append(item[:180])
        self.constraint_sources.append(source)
        self.filled.add(classify_constraint(item))

    def apply_override(self) -> None:
        """Erase discarded soft prefs; keep simulator-disclosed hard facts."""
        if self.override_applied:
            return
        dropped = [
            phrase
            for phrase, source in zip(self.constraints, self.constraint_sources)
            if source == "soft"
        ]
        for phrase in dropped:
            self.discarded_terms.update(_terms(phrase))
        kept = [
            (phrase, source)
            for phrase, source in zip(self.constraints, self.constraint_sources)
            if source != "soft"
        ]
        self.constraints = [phrase for phrase, _ in kept]
        self.constraint_sources = [source for _, source in kept]
        self.filled = {classify_constraint(phrase) for phrase in self.constraints}
        # Pre-override dont_care and asks may no longer match the new goal.
        self.dont_care.clear()
        self.asked.clear()
        # respond() appends the current message before _ingest, so the override
        # utterance is already in messages — keep it and everything after.
        self.query_message_start = max(0, len(self.messages) - 1)
        self.override_applied = True
        self.browsing = False


class Agent:
    """Hybrid BM25 + constraint rerank with a clarification state machine."""

    def __init__(self, catalog_path: str | Path = "data/catalog.jsonl") -> None:
        self.catalog_path = Path(catalog_path)
        self.connection = sqlite3.connect(":memory:")
        self._sessions: dict[str, SessionState] = {}
        self._products: dict[str, dict] = {}
        self._build_index()
        # Optional second lane. Stdlib-only judges get DenseIndex(backend=none).
        self._dense = DenseIndex.build(
            self._products,
            cache_dir=self.catalog_path.parent,
        )

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
                facets = self._extract_facets(blob, store, price_value, title)
                self._products[asin] = {
                    "parent_asin": asin,
                    "title": title,
                    "categories": [str(item) for item in (product.get("categories") or [])],
                    "store": store,
                    "text": blob,
                    "rating": float(product.get("average_rating") or 0.0),
                    "n_ratings": int(product.get("rating_number") or 0),
                    "price": price_value,
                    "facets": facets,
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
        # Retrieve first so clarification can maximize expected split on the live pool.
        ranked = self._retrieve(state, top_k=max(top_k, INFO_GAIN_TOP_N))
        ask = self._next_ask(state, turn, ranked)
        if ask:
            state.asked.append(ask)
        message = self._compose_message(state, ask, ranked)
        return {
            "message": message,
            "ask_attribute": ask,
            "recommendations": [{"parent_asin": asin, "score": score} for asin, score in ranked[:top_k]],
            "usage": {
                "prompt_tokens": state.prompt_tokens,
                "completion_tokens": state.completion_tokens,
            },
        }

    @staticmethod
    def _extract_facets(blob: str, store: str, price: float | None, title: str) -> dict[str, str | None]:
        """Corpus-grounded facet tags used by the info-gain ask policy."""
        text = blob.lower()
        facets: dict[str, str | None] = {
            "color": None,
            "material": None,
            "style": None,
            "brand": None,
            "use_case": None,
            "size": None,
            "budget": None,
            "category": None,
            "feature": None,
        }
        for color in COLORS:
            if re.search(rf"\b{re.escape(color)}\b", text):
                facets["color"] = color
                break
        for material in MATERIALS:
            if re.search(rf"\b{re.escape(material)}\b", text):
                facets["material"] = material
                break
        for token in STYLE_TOKENS:
            if token in text:
                facets["style"] = token
                break
        for token in USE_CASE_TOKENS:
            if token in text:
                facets["use_case"] = token
                break
        if store and store.strip():
            facets["brand"] = store.strip().lower()[:40]
        if re.search(r"\b(size|sizing|wide|narrow|x-?small|x-?large|medium|plus)\b", text):
            facets["size"] = "sized"
        if price is not None:
            # Coarse buckets so entropy reflects price spread, not every cent.
            bucket = int(price // 25) * 25
            facets["budget"] = f"{bucket}-{bucket + 24}"
        # Category proxy: last non-trivial title token path is too noisy; use a
        # stable hash of the first two content words as a weak category signal.
        title_terms = _terms(title)[:2]
        if title_terms:
            facets["category"] = " ".join(title_terms)
        # Feature presence: any distinctive multi-digit / model-like token.
        if re.search(r"\b\w{5,}\b", text):
            facets["feature"] = "present"
        return facets

    def _ingest(self, state: SessionState, message: str) -> None:
        text = message.strip()
        if OVERRIDE_RE.search(text):
            # Soft wipe only: keep disclosed hard facts; reset asks so `other` re-fires.
            state.apply_override()
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
            # Simulator disclosures + override "What I need is:" land here.
            source = "override" if OVERRIDE_RE.search(text) else "disclosed"
            for item in _split_constraints(require.group(1)):
                state.add_constraint(item, source=source)
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
                        state.add_constraint(item, source="soft")

    def _next_ask(
        self,
        state: SessionState,
        turn: int,
        ranked: list[tuple[str, float]] | None = None,
    ) -> str | None:
        if turn >= 9:
            return None
        asked = set(state.asked)
        blocked = state.dont_care | asked
        # `other` is the simulator catch-all: reveals up to two undisclosed
        # constraints of any type — highest protocol-level information gain.
        if "other" not in blocked:
            return "other"
        candidates: list[str] = []
        for attr in ASK_ORDER:
            if attr in blocked or attr == "other":
                continue
            if attr in state.filled:
                continue
            if attr == "category" and state.category:
                continue
            candidates.append(attr)
        if not candidates:
            return None
        default = candidates[0]
        if not ranked:
            return default
        # Public-set A/B (deterministic seed): pure static ASK_ORDER scores
        # Tech≈0.753; aggressive pool max-IG drops to ~0.72 (brand entropy trap);
        # coverage-gated swaps sit at ~0.752. Keep static selection for score,
        # and use the live pool only to ground the natural-language message
        # (see _facet_options). Facet stats remain available for future policy.
        return default

    def _attribute_stats(self, attr: str, ranked: list[tuple[str, float]]) -> tuple[float, float]:
        """Return (info_gain, coverage) for attr over the top-N candidate pool.

        Retained for message grounding / future policy experiments. Not used to
        override ASK_ORDER on the official public set (see _next_ask).
        """
        pool = ranked[:INFO_GAIN_TOP_N]
        if not pool:
            return 0.0, 0.0
        counts: dict[str, int] = {}
        known = 0
        for asin, _ in pool:
            product = self._products.get(asin)
            if not product:
                continue
            value = (product.get("facets") or {}).get(attr)
            if not value:
                continue
            known += 1
            key = str(value)
            counts[key] = counts.get(key, 0) + 1
        n = len(pool)
        coverage = known / n
        if known < 2 or len(counts) < 2:
            return 0.15 * coverage, coverage
        entropy = 0.0
        for count in counts.values():
            p = count / known
            entropy -= p * math.log(p + 1e-12, 2)
        max_entropy = math.log(len(counts), 2) if len(counts) > 1 else 1.0
        norm = entropy / max_entropy if max_entropy else 0.0
        return coverage * norm, coverage

    def _pool_swap_ask(self, default: str, candidates: list[str], ranked: list[tuple[str, float]]) -> str:
        """Optional coverage-gated swap (off by default; used in unit tests)."""
        if default not in POOL_ELIGIBLE:
            return default
        eligible = [attr for attr in candidates if attr in POOL_ELIGIBLE]
        if len(eligible) < 2:
            return default
        default_gain, default_cov = self._attribute_stats(default, ranked)
        if default_cov > DEFAULT_COVERAGE_MAX:
            return default
        best_attr = default
        best_gain = default_gain
        for attr in eligible:
            if attr == default:
                continue
            gain, _ = self._attribute_stats(attr, ranked)
            if gain > best_gain:
                best_gain = gain
                best_attr = attr
        if best_attr != default and best_gain >= ALT_GAIN_MIN:
            return best_attr
        return default

    def _query_terms(self, state: SessionState) -> list[str]:
        # High-recall FTS query: keep raw constraint tokens. Aggressive
        # "Imported"/filler stripping lost ~3.5 Hit@10 points on the public set.
        # After intent override, ignore pre-override messages and discarded soft tokens.
        safe_messages = state.messages[state.query_message_start :]
        recent = safe_messages[-2:] if safe_messages else []
        chunks = [state.category, *state.constraints, *recent]
        tags = state.profile.get("preference_tags") or []
        chunks.extend(str(tag) for tag in tags)
        blocked = state.discarded_terms
        # Category tokens must never be blocked even if they appeared in a soft pref.
        category_keep = set(_terms(state.category))
        ordered: list[str] = []
        seen: set[str] = set()
        for chunk in chunks:
            for token in _terms(str(chunk)):
                if token in seen:
                    continue
                if token in blocked and token not in category_keep:
                    continue
                seen.add(token)
                ordered.append(token)
                if len(ordered) >= 45:
                    return ordered
        return ordered

    def _retrieve(self, state: SessionState, top_k: int) -> list[tuple[str, float]]:
        terms = self._query_terms(state)
        if not terms and not (state.category or state.constraints):
            return []
        rows: list[tuple] = []
        if terms:
            quoted = " OR ".join(f'"{token}"' for token in terms)
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

        # Dense recall lane: bring in paraphrase / near-duplicate candidates FTS missed.
        tags = [str(tag) for tag in (state.profile.get("preference_tags") or [])]
        dense_query = query_text_from_state(state.category, state.constraints, tags)
        dense_hits = self._dense.search(dense_query, top_k=DENSE_RECALL_K) if dense_query else []
        dense_map = {asin: score for asin, score in dense_hits}
        for asin, _ in dense_hits:
            if asin not in bm25_map:
                asins.append(asin)
                # Neutral BM25 placeholder so dense-only candidates still enter rerank.
                bm25_map[asin] = 0.0
        # Also score FTS candidates under the dense metric for rerank boost.
        if dense_query and asins:
            extra_dense = self._dense.score_asins(dense_query, asins)
            for asin, score in extra_dense.items():
                # keep the better of global-search score vs candidate-set score
                if asin not in dense_map or score > dense_map[asin]:
                    dense_map[asin] = score

        scored: list[tuple[str, float]] = []
        phrases = [state.category, *state.constraints]
        tag_l = [str(tag).lower() for tag in tags]
        for asin in asins:
            product = self._products.get(asin)
            if not product:
                continue
            base = self._score(product, phrases, tag_l, bm25_map.get(asin, 0.0), state)
            dense = dense_map.get(asin)
            if dense is not None:
                base += DENSE_SCORE_WEIGHT * dense
            scored.append((asin, base))
        scored.sort(key=lambda item: item[1], reverse=True)
        scored = scored[: max(top_k, 20)]
        if llm_enabled() and scored:
            brief = rephrase_brief(
                state.category,
                state.constraints,
                state.dont_care,
                tags,
            )
            payload = [
                {
                    "parent_asin": asin,
                    "title": self._products[asin]["title"],
                    "store": self._products[asin]["store"],
                }
                for asin, _ in scored[:20]
                if asin in self._products
            ]
            order, prompt_tokens, completion_tokens = llm_rerank(brief, payload, top_k)
            state.prompt_tokens += prompt_tokens
            state.completion_tokens += completion_tokens
            if order:
                score_map = {asin: value for asin, value in scored}
                merged = [(asin, score_map.get(asin, 0.0)) for asin in order]
                seen = set(order)
                merged.extend((asin, value) for asin, value in scored if asin not in seen)
                scored = merged
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

    def _compose_message(
        self,
        state: SessionState,
        ask: str | None,
        ranked: list[tuple[str, float]] | None = None,
    ) -> str:
        if ask == "other":
            return (
                "I have a shortlist. Is there another must-have I should lock in "
                "(a feature, brand, or how you will use it)?"
            )
        if ask:
            pretty = ask.replace("_", " ")
            options = self._facet_options(ask, ranked or [])
            if options:
                joined = ", ".join(options[:4])
                return (
                    f"To narrow this down, any {pretty} preference "
                    f"(for example: {joined})?"
                )
            return f"To narrow this down, do you have a {pretty} preference?"
        if state.constraints:
            return "Here are the closest matches given the requirements you shared."
        return "Here are the closest matches I found so far."

    def _facet_options(self, attr: str, ranked: list[tuple[str, float]]) -> list[str]:
        """Top distinct corpus values for attr in the current pool (message grounding)."""
        if attr in {"other", "feature", "category"}:
            return []
        counts: dict[str, int] = {}
        for asin, _ in ranked[:INFO_GAIN_TOP_N]:
            product = self._products.get(asin)
            if not product:
                continue
            value = (product.get("facets") or {}).get(attr)
            if not value or value in {"present", "sized"}:
                continue
            key = str(value)
            counts[key] = counts.get(key, 0) + 1
        ordered = sorted(counts.items(), key=lambda item: item[1], reverse=True)
        return [name for name, _ in ordered if name]

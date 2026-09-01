"""Dense retrieval backends for ShopPilot (optional second recall lane).

Architecture
------------
Default dense lane is hashed char n-grams when NumPy is available (no extra ML
deps). Sentence-Transformer backends are opt-in via ``SHOPPILOT_DENSE``:

* ``minilm`` → ``sentence-transformers/all-MiniLM-L6-v2``
* ``bge``    → ``BAAI/bge-small-en-v1.5`` (stronger small retrieval model)

Vectors cache under ``data/dense_*.npz``. Dense scores fuse additively into
the lexical evidence ranker in ``starter.agent.Agent._retrieve``.
"""
from __future__ import annotations

import hashlib
import math
import os
import re
import struct
from pathlib import Path
from typing import Iterable, Sequence

TOKEN_RE = re.compile(r"[a-z0-9]+", re.IGNORECASE)

# Hashed bag-of-char-ngrams. 512 dims × 50k × float32 ≈ 100 MB.
HASH_DIM = 512
NGRAM_N = 3
DENSE_TOP_K = 80

# name → (HF model id, cache file stem, backend key used on DenseIndex)
ST_BACKENDS: dict[str, tuple[str, str]] = {
    "minilm": (
        "sentence-transformers/all-MiniLM-L6-v2",
        "dense_minilm_all-MiniLM-L6-v2.npz",
    ),
    "bge": (
        "BAAI/bge-small-en-v1.5",
        "dense_bge_small_en_v1.5.npz",
    ),
}

_ST_MODELS: dict[str, object] = {}


def _st_model(backend: str):
    """Load a sentence-transformers model once per process."""
    if backend not in ST_BACKENDS:
        raise ValueError(f"unknown ST backend {backend}")
    if backend not in _ST_MODELS:
        from sentence_transformers import SentenceTransformer

        model_id, _ = ST_BACKENDS[backend]
        _ST_MODELS[backend] = SentenceTransformer(model_id)
    return _ST_MODELS[backend]


def dense_mode() -> str:
    """none | hash | minilm | bge — SHOPPILOT_DENSE (default hash/auto)."""
    raw = (os.environ.get("SHOPPILOT_DENSE") or "auto").strip().lower()
    if raw in {"0", "none", "off", "false"}:
        return "none"
    if raw in {"minilm", "mini", "st"}:
        try:
            import sentence_transformers  # noqa: F401
            return "minilm"
        except Exception:
            pass
        try:
            import numpy  # noqa: F401
            return "hash"
        except Exception:
            return "none"
    if raw in {"bge", "bge-small", "bge_small"}:
        try:
            import sentence_transformers  # noqa: F401
            return "bge"
        except Exception:
            try:
                import numpy  # noqa: F401
                return "hash"
            except Exception:
                return "none"
    if raw in {"hash", "ngram", "1", "true", "on"}:
        return "hash"
    try:
        import numpy  # noqa: F401
        return "hash"
    except Exception:
        return "none"


def _tokens(text: str) -> list[str]:
    return [t.lower() for t in TOKEN_RE.findall(text or "") if len(t) > 1]


def _char_ngrams(text: str, n: int = NGRAM_N) -> list[str]:
    cleaned = re.sub(r"[^a-z0-9]+", " ", (text or "").lower())
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    if not cleaned:
        return []
    grams: list[str] = []
    for word in cleaned.split():
        if len(word) < n:
            grams.append(f"w:{word}")
            continue
        padded = f"#{word}#"
        grams.extend(padded[i : i + n] for i in range(len(padded) - n + 1))
    return grams


def _stable_bucket(gram: str, dim: int) -> tuple[int, float]:
    digest = hashlib.blake2b(gram.encode("utf-8"), digest_size=8).digest()
    value = struct.unpack(">Q", digest)[0]
    index = value % dim
    sign = 1.0 if (value >> 63) == 0 else -1.0
    return index, sign


def encode_hash(text: str, dim: int = HASH_DIM) -> list[float]:
    vec = [0.0] * dim
    grams = _char_ngrams(text)
    if not grams:
        return vec
    for gram in grams:
        index, sign = _stable_bucket(gram, dim)
        vec[index] += sign
    norm = math.sqrt(sum(v * v for v in vec)) or 1.0
    return [v / norm for v in vec]


def product_text(product: dict) -> str:
    parts = [
        str(product.get("title") or ""),
        " ".join(str(c) for c in (product.get("categories") or [])),
        str(product.get("store") or ""),
        str(product.get("text") or "")[:400],
    ]
    return " ".join(parts)


class DenseIndex:
    """Cosine dense index over parent_asin keys."""

    def __init__(self, backend: str = "none") -> None:
        self.backend = backend
        self.asins: list[str] = []
        self._matrix = None  # numpy ndarray or list[list[float]]
        self._model = None
        self._q_text: str | None = None
        self._q_vec = None
        self.enabled = backend != "none"

    @classmethod
    def build(
        cls,
        products: dict[str, dict],
        *,
        cache_dir: str | Path = "data",
        backend: str | None = None,
    ) -> "DenseIndex":
        mode = backend or dense_mode()
        if mode == "none":
            return cls("none")
        if mode in ST_BACKENDS:
            try:
                return cls._build_st(products, Path(cache_dir), mode)
            except Exception:
                mode = "hash"
        if mode == "hash":
            try:
                return cls._build_hash(products)
            except Exception:
                return cls("none")
        return cls("none")

    @classmethod
    def _build_hash(cls, products: dict[str, dict]) -> "DenseIndex":
        import numpy as np

        index = cls("hash")
        asins = list(products.keys())
        matrix = np.zeros((len(asins), HASH_DIM), dtype=np.float32)
        for row, asin in enumerate(asins):
            vec = encode_hash(product_text(products[asin]), HASH_DIM)
            matrix[row] = np.asarray(vec, dtype=np.float32)
        index.asins = asins
        index._matrix = matrix
        return index

    @classmethod
    def _build_st(cls, products: dict[str, dict], cache_dir: Path, backend: str) -> "DenseIndex":
        import numpy as np

        _, cache_name = ST_BACKENDS[backend]
        cache_dir.mkdir(parents=True, exist_ok=True)
        cache_path = cache_dir / cache_name
        asins = list(products.keys())
        if cache_path.exists():
            payload = np.load(cache_path, allow_pickle=False)
            cached_asins = [str(x) for x in payload["asins"].tolist()]
            if cached_asins == asins:
                index = cls(backend)
                index.asins = asins
                index._matrix = payload["matrix"].astype(np.float32)
                return index

        model = _st_model(backend)
        texts = [product_text(products[asin])[:800] for asin in asins]
        matrix = model.encode(
            texts,
            batch_size=64,
            show_progress_bar=True,
            convert_to_numpy=True,
            normalize_embeddings=True,
        ).astype(np.float32)
        np.savez_compressed(cache_path, asins=np.asarray(asins), matrix=matrix)
        index = cls(backend)
        index.asins = asins
        index._matrix = matrix
        index._model = model
        return index

    # Back-compat alias
    @classmethod
    def _build_minilm(cls, products: dict[str, dict], cache_dir: Path) -> "DenseIndex":
        return cls._build_st(products, cache_dir, "minilm")

    def encode_query(self, text: str):
        if not self.enabled or self._matrix is None:
            return None
        if self._q_text == text and self._q_vec is not None:
            return self._q_vec
        if self.backend == "hash":
            import numpy as np
            vec = np.asarray(encode_hash(text, HASH_DIM), dtype=np.float32)
        elif self.backend in ST_BACKENDS:
            import numpy as np
            if self._model is None:
                self._model = _st_model(self.backend)
            vec = self._model.encode(
                [text], convert_to_numpy=True, normalize_embeddings=True
            )[0].astype(np.float32)
        else:
            return None
        self._q_text = text
        self._q_vec = vec
        return vec

    def search(self, query_text: str, top_k: int = DENSE_TOP_K) -> list[tuple[str, float]]:
        if not self.enabled or self._matrix is None:
            return []
        import numpy as np

        q = self.encode_query(query_text)
        if q is None:
            return []
        scores = self._matrix @ q
        k = min(top_k, scores.shape[0])
        if k <= 0:
            return []
        if k < scores.shape[0]:
            idx = np.argpartition(-scores, k)[:k]
            idx = idx[np.argsort(-scores[idx])]
        else:
            idx = np.argsort(-scores)[:k]
        return [(self.asins[int(i)], float(scores[int(i)])) for i in idx]

    def score_asins(self, query_text: str, asins: Sequence[str]) -> dict[str, float]:
        """Cosine scores for a specific candidate set (rerank assist)."""
        if not self.enabled or self._matrix is None or not asins:
            return {}
        q = self.encode_query(query_text)
        if q is None:
            return {}
        asin_to_row = {asin: i for i, asin in enumerate(self.asins)}
        out: dict[str, float] = {}
        for asin in asins:
            row = asin_to_row.get(asin)
            if row is None:
                continue
            out[asin] = float(self._matrix[row] @ q)
        return out


def query_text_from_state(
    category: str,
    constraints: Iterable[str],
    tags: Iterable[str],
    *,
    family: str | None = None,
    audience: str | None = None,
    canonical: bool = True,
) -> str:
    """Build dense-query text. Canonical mode mimics catalog title structure."""
    if not canonical or os.environ.get("SHOPPILOT_CANONICAL_QUERY", "0") != "1":
        parts = [category, *list(constraints)[:8], *list(tags)[:6]]
        return " ".join(str(p) for p in parts if p)

    bits: list[str] = []
    if audience:
        bits.append(str(audience).replace("_", " "))
    if family and family not in {"lounge"}:
        bits.append(family if family != "bottom" else "jeans pants")
    elif family == "lounge":
        bits.append("robe bathrobe")
    if category:
        bits.append(str(category))
    cons = [str(c).strip() for c in constraints if c]
    short = [c for c in cons if len(c) <= 24]
    long = [c for c in cons if len(c) > 24]
    bits.extend(short[-6:])
    bits.extend(long[-2:])
    bits.extend(str(t) for t in list(tags)[:4] if t)
    out: list[str] = []
    seen: set[str] = set()
    for b in bits:
        key = b.lower()
        if key in seen or not b:
            continue
        seen.add(key)
        out.append(b)
    return " ".join(out)

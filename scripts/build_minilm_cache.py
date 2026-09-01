"""Build data/dense_minilm_all-MiniLM-L6-v2.npz from catalog.jsonl."""
from __future__ import annotations

import json
import os
from pathlib import Path

os.environ["SHOPPILOT_DENSE"] = "minilm"

from starter.dense import DenseIndex, product_text


def main() -> None:
    catalog = Path("data/catalog.jsonl")
    products: dict[str, dict] = {}
    with catalog.open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            asin = str(row["parent_asin"])
            title = str(row.get("title") or "")
            cats = [str(c) for c in (row.get("categories") or [])]
            store = str(row.get("store") or "")
            products[asin] = {
                "title": title,
                "categories": cats,
                "store": store,
                "text": " ".join([title, " ".join(cats), store]),
            }
    print(f"products {len(products)}", flush=True)
    index = DenseIndex.build(products, cache_dir=catalog.parent, backend="minilm")
    print(f"backend={index.backend} enabled={index.enabled} rows={len(index.asins)}", flush=True)
    hits = index.search("men boot cut cotton jean ariat", top_k=5)
    print("sample hits", hits, flush=True)


if __name__ == "__main__":
    main()

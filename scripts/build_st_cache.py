#!/usr/bin/env python3
"""Build dense ST cache for minilm or bge from catalog.jsonl."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--backend",
        default="minilm",
        choices=["minilm", "bge"],
        help="sentence-transformers backend",
    )
    parser.add_argument("--catalog", default="data/catalog.jsonl")
    args = parser.parse_args()
    os.environ["SHOPPILOT_DENSE"] = args.backend

    from starter.dense import DenseIndex, ST_BACKENDS

    catalog = Path(args.catalog)
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
    print(f"backend={args.backend} products={len(products)}", flush=True)
    print(f"model={ST_BACKENDS[args.backend][0]} cache={ST_BACKENDS[args.backend][1]}", flush=True)
    index = DenseIndex.build(products, cache_dir=catalog.parent, backend=args.backend)
    print(
        f"built backend={index.backend} enabled={index.enabled} rows={len(index.asins)}",
        flush=True,
    )
    hits = index.search("men boot cut cotton jean ariat", top_k=5)
    print("sample hits", hits, flush=True)


if __name__ == "__main__":
    main()

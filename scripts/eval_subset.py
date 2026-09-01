"""Run the official evaluator on a public_set slice (local A/B, not the 200-score)."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from evaluator.local_evaluator import Agent, catalog_index, evaluate, load_jsonl
from starter.dense import dense_mode


def main() -> None:
    parser = argparse.ArgumentParser(description="Subset local eval for dense A/B")
    parser.add_argument("--catalog", default="data/catalog.jsonl")
    parser.add_argument("--dataset", default="data/public_set.jsonl")
    parser.add_argument("--limit", type=int, default=24)
    parser.add_argument(
        "--ids",
        default="",
        help="Comma-separated sample_id list; overrides --limit when set",
    )
    parser.add_argument("--output", default="")
    args = parser.parse_args()

    samples = load_jsonl(args.dataset)
    if args.ids.strip():
        want = {item.strip() for item in args.ids.split(",") if item.strip()}
        samples = [row for row in samples if row["sample_id"] in want]
    else:
        samples = samples[: max(0, args.limit)]
    print(
        f"dense_mode={dense_mode()} n={len(samples)} "
        f"SHOPPILOT_DENSE={os.environ.get('SHOPPILOT_DENSE', '')!r}",
        flush=True,
    )
    catalog_ids, categories, products = catalog_index(args.catalog)
    result = evaluate(Agent(args.catalog), samples, catalog_ids, categories, products)
    summary = {key: value for key, value in result.items() if key != "sessions"}
    print(json.dumps(summary, indent=2))
    if args.output:
        Path(args.output).write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()

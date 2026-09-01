"""Inspect the 5 public-set misses: indexer miss vs ranker miss."""
from __future__ import annotations

import os

from evaluator.local_evaluator import (
    TOP_K,
    catalog_index,
    coarse_category,
    customer_reply,
    initial_message,
    load_jsonl,
    materialize_hidden_fields,
    normalize_recommendations,
)
from starter.agent import Agent

os.environ.setdefault("SHOPPILOT_DENSE", "hash")
WANT = {"public_0020", "public_0076", "public_0144", "public_0174", "public_0175"}


def main() -> None:
    samples = [s for s in load_jsonl("data/public_set.jsonl") if s["sample_id"] in WANT]
    ids, cats, products = catalog_index("data/catalog.jsonl")
    print("loading agent", flush=True)
    agent = Agent("data/catalog.jsonl")
    print(
        f"backend={getattr(agent._dense, 'backend', None)} "
        f"enabled={getattr(agent._dense, 'enabled', None)}",
        flush=True,
    )
    for sample in samples:
        sid = "m" + sample["sample_id"]
        agent.reset(sid, sample["user_profile"])
        target = str(sample["ground_truth"]["parent_asin"])
        product = products[target]
        print("=" * 60)
        print(sample["sample_id"], sample["scenario_type"], target)
        print("title:", str(product.get("title") or "")[:160])
        print("cats:", product.get("categories"))
        print("store:", product.get("store"))
        card, behavior = materialize_hidden_fields(sample, products)
        print("hard:", card.get("hard_constraints"))
        print("soft:", card.get("soft_preferences"))
        eff = {**sample, "intent_card": card, "behavior": behavior}
        disclosed: set[str] = set()
        boundary_used = False
        override_applied = sample["scenario_type"] != "intent_override"
        msg = initial_message(eff, coarse_category(cats.get(target, [])), disclosed)
        in_pool = False
        in_emit = False
        best = None
        for turn in range(1, 11):
            resp = agent.respond(sid, msg, turn, TOP_K)
            state = agent._sessions[sid]
            ranked = agent._retrieve(state, top_k=220)
            pool_asins = [asin for asin, _ in ranked]
            emit = normalize_recommendations(resp.get("recommendations"), ids)
            pos_pool = pool_asins.index(target) + 1 if target in pool_asins else None
            pos_emit = emit.index(target) + 1 if target in emit else None
            if pos_pool:
                in_pool = True
            if pos_emit:
                in_emit = True
                best = pos_emit
            ask = resp.get("ask_attribute")
            print(
                f"  t{turn} ncons={len(state.constraints)} pool={pos_pool} "
                f"emit={pos_emit} nrec={len(emit)} ask={ask}",
                flush=True,
            )
            if override_applied and target in emit:
                break
            override = (eff.get("behavior") or {}).get("override") or {}
            if not override_applied and turn + 1 == int(override.get("turn", 3)):
                override_applied = True
                msg = str(override.get("message", "x"))
            else:
                msg, boundary_used = customer_reply(
                    eff, resp.get("ask_attribute"), disclosed, boundary_used
                )
        print("  RESULT in_pool_ever", in_pool, "in_emit_ever", in_emit, "best_emit", best)


if __name__ == "__main__":
    main()

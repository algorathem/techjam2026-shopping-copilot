#!/usr/bin/env python3
"""Interactive CLI shopping assistant over ShopPilot Agent.

Usage (from repo root):
  python3 cli_chat.py
  python3 cli_chat.py --dense hash
  python3 cli_chat.py --catalog data/catalog.jsonl

Commands mid-chat:
  /new     start a fresh session
  /state   show slots / constraints
  /quit    exit  (also: empty line, Ctrl-D, exit, quit)
"""
from __future__ import annotations

import argparse
import os
import sys
import uuid
from pathlib import Path


def _profile() -> dict:
    return {
        "purchase_frequency": "3-4 prior purchases",
        "average_prior_rating": 5.0,
        "rating_style": "usually positive",
        "preference_tags": ["fit", "comfort", "durability"],
        "summary": "CLI demo shopper; prefers fit, comfort, durability.",
    }


def _print_recs(agent, recs: list, limit: int = 5) -> None:
    if not recs:
        print("  (no recommendations yet)")
        return
    for i, item in enumerate(recs[:limit], 1):
        asin = item.get("parent_asin", item) if isinstance(item, dict) else str(item)
        score = item.get("score") if isinstance(item, dict) else None
        product = agent._products.get(str(asin), {})
        title = (product.get("title") or asin)[:72]
        store = product.get("store") or ""
        price = product.get("price")
        bits = [f"{i}. {title}"]
        if store:
            bits.append(f"[{store}]")
        if price is not None:
            bits.append(f"${price:.2f}" if isinstance(price, (int, float)) else str(price))
        if score is not None:
            bits.append(f"score={score:.2f}")
        bits.append(f"ASIN={asin}")
        print("  " + "  ".join(bits))


def _print_state(agent, session_id: str) -> None:
    state = agent._sessions.get(session_id)
    if state is None:
        print("  (no session)")
        return
    print(f"  category:    {state.category or '(none)'}")
    print(f"  browsing:    {state.browsing}")
    print(f"  override:    {state.override_applied}")
    print(f"  constraints: {state.constraints or '(none)'}")
    print(f"  sources:     {state.constraint_sources or '(none)'}")
    print(f"  filled:      {sorted(state.filled) or '(none)'}")
    print(f"  dont_care:   {sorted(state.dont_care) or '(none)'}")
    print(f"  asked:       {state.asked or '(none)'}")
    tags = state.profile.get("preference_tags") or []
    print(f"  profile tags:{list(tags) or '(none)'}")


def main() -> int:
    parser = argparse.ArgumentParser(description="ShopPilot interactive CLI")
    parser.add_argument("--catalog", default="data/catalog.jsonl")
    parser.add_argument(
        "--dense",
        default=None,
        choices=["none", "hash", "minilm", "auto"],
        help="Sets SHOPPILOT_DENSE for this run",
    )
    parser.add_argument("--top-k", type=int, default=5, help="How many products to print each turn")
    parser.add_argument("--max-turns", type=int, default=10)
    args = parser.parse_args()

    catalog = Path(args.catalog)
    if not catalog.is_file():
        print(f"Catalog not found: {catalog}", file=sys.stderr)
        print("Download the kit catalog first (see README).", file=sys.stderr)
        return 1

    if args.dense is not None:
        os.environ["SHOPPILOT_DENSE"] = args.dense

    # Import after env so dense backend sees SHOPPILOT_DENSE.
    from starter.agent import Agent

    print("Loading catalog (FTS" + (" + dense" if os.environ.get("SHOPPILOT_DENSE", "auto") != "none" else "") + ")…")
    agent = Agent(catalog)
    print(f"Ready. dense_backend={agent._dense.backend} enabled={agent._dense.enabled}")
    print("Chat like a shopper. Commands: /new  /state  /quit")
    print("-" * 60)

    def new_session() -> str:
        sid = f"cli-{uuid.uuid4().hex[:8]}"
        agent.reset(sid, _profile())
        print(f"\n(new session {sid})")
        print("Agent: What are you shopping for? (category, must-haves, budget…)")
        return sid

    session_id = new_session()
    turn = 0

    while True:
        try:
            raw = input("\nYou: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nBye.")
            return 0

        if not raw or raw.lower() in {"quit", "exit", "/quit", "/exit", "/q"}:
            print("Bye.")
            return 0
        if raw.lower() in {"/new", "/reset"}:
            session_id = new_session()
            turn = 0
            continue
        if raw.lower() in {"/state", "/slots"}:
            _print_state(agent, session_id)
            continue
        if raw.startswith("/"):
            print("Unknown command. Try /new, /state, /quit")
            continue

        turn += 1
        if turn > args.max_turns:
            print(f"(hit max turns={args.max_turns}; starting a new session)")
            session_id = new_session()
            turn = 1

        try:
            response = agent.respond(session_id, raw, turn, top_k=max(args.top_k, 10))
        except Exception as exc:
            print(f"Error: {exc}", file=sys.stderr)
            continue

        ask = response.get("ask_attribute")
        msg = response.get("message") or ""
        recs = response.get("recommendations") or []

        print(f"\nAgent: {msg}")
        if ask:
            print(f"       (asking attribute: {ask})")
        else:
            print("       (no further question this turn)")
        print("Suggestions:")
        _print_recs(agent, recs, limit=args.top_k)
        print(f"       turn {turn}/{args.max_turns}")


if __name__ == "__main__":
    raise SystemExit(main())

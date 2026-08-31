#!/usr/bin/env python3
"""Astrid — interactive colored CLI for the shopping agent (demo UI).

Single brand / single theme. Project repo may still be named ShopPilot for
TechJam; this terminal experience is always Astrid.

Usage:
  python3 cli_chat.py
  python3 cli_chat.py --dense hash --top-k 6
  python3 cli_chat.py --no-color

Commands: /new  /state  /quit
"""
from __future__ import annotations

import argparse
import os
import sys
import uuid
from pathlib import Path

# --- Astrid palette (ANSI, no third-party deps) ---
_RESET = "\033[0m"
_BOLD = "\033[1m"

# Soft rose / cyan editorial
THEME = {
    "accent": "\033[95m",   # magenta
    "accent2": "\033[35m",
    "user": "\033[97m",
    "agent": "\033[96m",    # cyan replies
    "ask": "\033[93m",      # gold ask chip
    "meta": "\033[90m",
    "title": "\033[1;95m",
    "score": "\033[96m",
    "line": "\033[90m",
}

NAME = "Astrid"
TAGLINE = "quiet clarity for every aisle"

# Figlet-ish wordmark (fixed width, demo-friendly)
_ASCII = r"""
     _        _        _     _
    / \   ___| |_ _ __(_) __| |
   / _ \ / __| __| '__| |/ _` |
  / ___ \\__ \ |_| |  | | (_| |
 /_/   \_\___/\__|_|  |_|\__,_|
""".rstrip(
    "\n"
)


def _c(code: str, text: str, enabled: bool) -> str:
    if not enabled:
        return text
    return f"{code}{text}{_RESET}"


def _supports_color() -> bool:
    if os.environ.get("NO_COLOR"):
        return False
    if os.environ.get("FORCE_COLOR"):
        return True
    return sys.stdout.isatty()


def _profile() -> dict:
    return {
        "purchase_frequency": "3-4 prior purchases",
        "average_prior_rating": 5.0,
        "rating_style": "usually positive",
        "preference_tags": ["fit", "comfort", "durability"],
        "summary": "CLI demo shopper; prefers fit, comfort, durability.",
    }


def _banner(color: bool, dense: str) -> None:
    w = 58
    line = "─" * w
    print()
    for row in _ASCII.splitlines():
        print(_c(THEME["title"], row, color))
    print(_c(THEME["line"], line, color))
    print(
        _c(THEME["title"], f"  {NAME}", color)
        + _c(THEME["meta"], f"  ·  {TAGLINE}", color)
    )
    print(
        _c(
            THEME["meta"],
            f"  offline hybrid shopping agent  ·  dense={dense}",
            color,
        )
    )
    print(_c(THEME["meta"], "  commands: /new   /state   /quit", color))
    print(_c(THEME["line"], line, color))
    print()


def _print_recs(agent, recs: list, limit: int, color: bool) -> None:
    if not recs:
        print(_c(THEME["meta"], "  (no recommendations yet)", color))
        return
    for i, item in enumerate(recs[:limit], 1):
        asin = item.get("parent_asin", item) if isinstance(item, dict) else str(item)
        score = item.get("score") if isinstance(item, dict) else None
        product = getattr(agent, "_products", {}).get(str(asin), {})
        title = (product.get("title") or asin)[:64]
        store = product.get("store") or ""
        price = product.get("price")
        idx = _c(THEME["accent"], f"{i:>2}.", color)
        tit = _c(_BOLD, title, color) if color else title
        bits = [f"  {idx} {tit}"]
        if store:
            bits.append(_c(THEME["meta"], f"· {store}", color))
        if price is not None:
            p = f"${price:.2f}" if isinstance(price, (int, float)) else str(price)
            bits.append(_c(THEME["score"], p, color))
        if score is not None:
            bits.append(_c(THEME["meta"], f"({score:.2f})", color))
        bits.append(_c(THEME["meta"], f"[{asin}]", color))
        print(" ".join(bits))


def _print_state(agent, session_id: str, color: bool) -> None:
    state = agent._sessions.get(session_id)
    if state is None:
        print(_c(THEME["meta"], "  (no session)", color))
        return

    def row(label: str, value: object) -> None:
        empty = value in (None, "", [], set())
        shown = "—" if empty else str(value)
        print(
            _c(THEME["meta"], f"  {label:<12}", color)
            + _c(THEME["accent2"], shown, color)
        )

    row("category", getattr(state, "category", None))
    row("family", getattr(state, "product_family", None))
    row("audience", getattr(state, "audience", None))
    row("browsing", getattr(state, "browsing", False))
    row("override", getattr(state, "override_applied", False))
    row("constraints", getattr(state, "constraints", None))
    row("filled", sorted(getattr(state, "filled", set()) or []))
    row("dont_care", sorted(getattr(state, "dont_care", set()) or []))
    row("asked", getattr(state, "asked", None))
    tags = (getattr(state, "profile", None) or {}).get("preference_tags") or []
    row("profile", tags)


def main() -> int:
    parser = argparse.ArgumentParser(description="Astrid — shopping agent CLI")
    parser.add_argument("--catalog", default="data/catalog.jsonl")
    parser.add_argument(
        "--dense",
        default=None,
        choices=["none", "hash", "minilm", "auto"],
        help="Sets SHOPPILOT_DENSE for this run",
    )
    parser.add_argument("--top-k", type=int, default=5)
    parser.add_argument("--max-turns", type=int, default=10)
    parser.add_argument("--no-color", action="store_true")
    args = parser.parse_args()

    color = _supports_color() and not args.no_color

    catalog = Path(args.catalog)
    if not catalog.is_file():
        print(f"Catalog not found: {catalog}", file=sys.stderr)
        print("Download the kit catalog first (see README).", file=sys.stderr)
        return 1

    if args.dense is not None:
        os.environ["SHOPPILOT_DENSE"] = args.dense

    from starter.agent import Agent

    print(_c(THEME["meta"], "  loading catalog…", color))
    agent = Agent(catalog)
    dense_backend = getattr(getattr(agent, "_dense", None), "backend", "n/a")
    _banner(color, str(dense_backend))

    def new_session() -> str:
        sid = f"cli-{uuid.uuid4().hex[:8]}"
        agent.reset(sid, _profile())
        print(_c(THEME["meta"], f"  session {sid}", color))
        print(
            _c(THEME["agent"], f"  {NAME}: ", color)
            + "What are you shopping for?  "
            + _c(THEME["meta"], "(category, vibe, must-haves, budget…)", color)
        )
        return sid

    session_id = new_session()
    turn = 0

    while True:
        try:
            prompt = _c(THEME["accent"], "\n  You · ", color)
            raw = input(prompt).strip()
        except (EOFError, KeyboardInterrupt):
            print(_c(THEME["meta"], f"\n  {NAME}: goodbye.\n", color))
            return 0

        if not raw or raw.lower() in {"quit", "exit", "/quit", "/exit", "/q"}:
            print(_c(THEME["meta"], f"  {NAME}: goodbye.\n", color))
            return 0
        if raw.lower() in {"/new", "/reset"}:
            print()
            session_id = new_session()
            turn = 0
            continue
        if raw.lower() in {"/state", "/slots"}:
            print()
            _print_state(agent, session_id, color)
            continue
        if raw.startswith("/"):
            print(_c(THEME["meta"], "  commands: /new  /state  /quit", color))
            continue

        turn += 1
        if turn > args.max_turns:
            print(_c(THEME["score"], f"  (max {args.max_turns} turns — new session)", color))
            session_id = new_session()
            turn = 1

        try:
            response = agent.respond(session_id, raw, turn, top_k=max(args.top_k, 10))
        except Exception as exc:
            print(_c("\033[91m", f"  error: {exc}", color), file=sys.stderr)
            continue

        ask = response.get("ask_attribute")
        msg = response.get("message") or ""
        recs = response.get("recommendations") or []

        print()
        print(_c(THEME["agent"], f"  {NAME}: ", color) + msg)
        if ask:
            print(
                _c(THEME["ask"], "  ↳ asking · ", color)
                + _c(_BOLD + THEME["ask"], str(ask), color)
            )
        else:
            print(_c(THEME["meta"], "  ↳ no clarifying question this turn", color))
        print(_c(THEME["meta"], "  suggestions", color))
        _print_recs(agent, recs, limit=args.top_k, color=color)
        print(_c(THEME["meta"], f"  turn {turn}/{args.max_turns}", color))


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Interactive colored CLI for the shopping agent (demo polish).

Usage:
  python3 cli_chat.py
  python3 cli_chat.py --name ShopPilot
  python3 cli_chat.py --name Astrid --theme astrid
  python3 cli_chat.py --name "Maison AI" --theme maison
  python3 cli_chat.py --dense hash --top-k 6
  python3 cli_chat.py --no-color

Commands: /new  /state  /theme  /quit
"""
from __future__ import annotations

import argparse
import os
import sys
import uuid
from pathlib import Path

# --- ANSI themes (no third-party deps) ---
_RESET = "\033[0m"
_BOLD = "\033[1m"
_DIM = "\033[2m"
_ITALIC = "\033[3m"


def _c(code: str, text: str, enabled: bool) -> str:
    if not enabled:
        return text
    return f"{code}{text}{_RESET}"


THEMES: dict[str, dict[str, str]] = {
    # Cool slate / cyan — product engineering
    "shoppilot": {
        "accent": "\033[96m",      # bright cyan
        "accent2": "\033[94m",     # blue
        "user": "\033[97m",        # white
        "agent": "\033[92m",       # green
        "ask": "\033[95m",         # magenta
        "meta": "\033[90m",        # gray
        "title": "\033[1;96m",
        "score": "\033[93m",       # yellow
        "line": "\033[90m",
        "banner_bg": "",
    },
    # Soft rose / ivory — "Astrid" editorial
    "astrid": {
        "accent": "\033[95m",      # magenta
        "accent2": "\033[35m",
        "user": "\033[97m",
        "agent": "\033[96m",
        "ask": "\033[93m",
        "meta": "\033[90m",
        "title": "\033[1;95m",
        "score": "\033[96m",
        "line": "\033[90m",
        "banner_bg": "",
    },
    # Warm gold / deep — "Maison AI" boutique
    "maison": {
        "accent": "\033[33m",      # gold/yellow
        "accent2": "\033[93m",
        "user": "\033[97m",
        "agent": "\033[37m",
        "ask": "\033[33m",
        "meta": "\033[90m",
        "title": "\033[1;33m",
        "score": "\033[93m",
        "line": "\033[90m",
        "banner_bg": "",
    },
}


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


def _banner(name: str, theme: dict[str, str], color: bool, dense: str) -> None:
    w = 58
    line = "─" * w
    tagline = {
        "ShopPilot": "catalog findability · multi-turn · offline-first",
        "Astrid": "quiet clarity for every aisle",
        "Maison AI": "concierge search for the modern rack",
    }.get(name, "conversational shopping agent")
    print()
    print(_c(theme["line"], line, color))
    print(_c(theme["title"], f"  {name}", color) + _c(theme["meta"], f"  ·  {tagline}", color))
    print(_c(theme["line"], line, color))
    print(
        _c(theme["meta"], f"  dense={dense}  ·  /new  /state  /theme  /quit", color)
    )
    print(_c(theme["line"], line, color))
    print()


def _print_recs(agent, recs: list, limit: int, theme: dict, color: bool) -> None:
    if not recs:
        print(_c(theme["meta"], "  (no recommendations yet)", color))
        return
    for i, item in enumerate(recs[:limit], 1):
        asin = item.get("parent_asin", item) if isinstance(item, dict) else str(item)
        score = item.get("score") if isinstance(item, dict) else None
        product = getattr(agent, "_products", {}).get(str(asin), {})
        title = (product.get("title") or asin)[:64]
        store = product.get("store") or ""
        price = product.get("price")
        idx = _c(theme["accent"], f"{i:>2}.", color)
        tit = _c(_BOLD, title, color) if color else title
        bits = [f"  {idx} {tit}"]
        if store:
            bits.append(_c(theme["meta"], f"· {store}", color))
        if price is not None:
            p = f"${price:.2f}" if isinstance(price, (int, float)) else str(price)
            bits.append(_c(theme["score"], p, color))
        if score is not None:
            bits.append(_c(theme["meta"], f"({score:.2f})", color))
        bits.append(_c(theme["meta"], f"[{asin}]", color))
        print(" ".join(bits))


def _print_state(agent, session_id: str, theme: dict, color: bool) -> None:
    state = agent._sessions.get(session_id)
    if state is None:
        print(_c(theme["meta"], "  (no session)", color))
        return

    def row(label: str, value: object) -> None:
        print(
            _c(theme["meta"], f"  {label:<12}", color)
            + _c(theme["accent2"], str(value if value not in (None, "", [], set()) else "—"), color)
        )

    family = getattr(state, "product_family", None)
    row("category", getattr(state, "category", None) or "—")
    row("family", family or "—")
    row("browsing", getattr(state, "browsing", False))
    row("override", getattr(state, "override_applied", False))
    row("constraints", getattr(state, "constraints", None) or "—")
    row("filled", sorted(getattr(state, "filled", set()) or []) or "—")
    row("dont_care", sorted(getattr(state, "dont_care", set()) or []) or "—")
    row("asked", getattr(state, "asked", None) or "—")
    tags = (getattr(state, "profile", None) or {}).get("preference_tags") or []
    row("profile", tags or "—")


def main() -> int:
    parser = argparse.ArgumentParser(description="Styled shopping-agent CLI")
    parser.add_argument("--catalog", default="data/catalog.jsonl")
    parser.add_argument("--name", default="ShopPilot", help="Agent display name")
    parser.add_argument(
        "--theme",
        default=None,
        choices=list(THEMES.keys()),
        help="Color theme (default: inferred from --name)",
    )
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
    name = args.name.strip() or "ShopPilot"
    theme_key = args.theme
    if theme_key is None:
        lowered = name.lower().replace(" ", "")
        if "astrid" in lowered:
            theme_key = "astrid"
        elif "maison" in lowered:
            theme_key = "maison"
        else:
            theme_key = "shoppilot"
    theme = THEMES[theme_key]

    catalog = Path(args.catalog)
    if not catalog.is_file():
        print(f"Catalog not found: {catalog}", file=sys.stderr)
        print("Download the kit catalog first (see README).", file=sys.stderr)
        return 1

    if args.dense is not None:
        os.environ["SHOPPILOT_DENSE"] = args.dense

    from starter.agent import Agent

    dense_env = os.environ.get("SHOPPILOT_DENSE", "auto")
    print(_c(theme["meta"], "  loading catalog…", color))
    agent = Agent(catalog)
    dense_backend = getattr(getattr(agent, "_dense", None), "backend", "n/a")
    _banner(name, theme, color, str(dense_backend))

    def new_session() -> str:
        sid = f"cli-{uuid.uuid4().hex[:8]}"
        agent.reset(sid, _profile())
        print(_c(theme["meta"], f"  session {sid}", color))
        print(
            _c(theme["agent"], f"  {name}: ", color)
            + "What are you shopping for?  "
            + _c(theme["meta"], "(category, vibe, must-haves, budget…)", color)
        )
        return sid

    session_id = new_session()
    turn = 0

    while True:
        try:
            prompt = _c(theme["accent"], "\n  You · ", color)
            raw = input(prompt).strip()
        except (EOFError, KeyboardInterrupt):
            print(_c(theme["meta"], f"\n  {name}: goodbye.\n", color))
            return 0

        if not raw or raw.lower() in {"quit", "exit", "/quit", "/exit", "/q"}:
            print(_c(theme["meta"], f"  {name}: goodbye.\n", color))
            return 0
        if raw.lower() in {"/new", "/reset"}:
            print()
            session_id = new_session()
            turn = 0
            continue
        if raw.lower() in {"/state", "/slots"}:
            print()
            _print_state(agent, session_id, theme, color)
            continue
        if raw.lower().startswith("/theme"):
            parts = raw.split()
            if len(parts) >= 2 and parts[1] in THEMES:
                theme_key = parts[1]
                theme = THEMES[theme_key]
                print(_c(theme["accent"], f"  theme → {theme_key}", color))
                _banner(name, theme, color, str(dense_backend))
            else:
                print(_c(theme["meta"], f"  themes: {', '.join(THEMES)}", color))
            continue
        if raw.startswith("/"):
            print(_c(theme["meta"], "  commands: /new  /state  /theme shoppilot|astrid|maison  /quit", color))
            continue

        turn += 1
        if turn > args.max_turns:
            print(_c(theme["score"], f"  (max {args.max_turns} turns — new session)", color))
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
        print(_c(theme["agent"], f"  {name}: ", color) + msg)
        if ask:
            print(
                _c(theme["ask"], "  ↳ asking · ", color)
                + _c(_BOLD + theme["ask"], str(ask), color)
            )
        else:
            print(_c(theme["meta"], "  ↳ no clarifying question this turn", color))
        print(_c(theme["meta"], "  suggestions", color))
        _print_recs(agent, recs, limit=args.top_k, theme=theme, color=color)
        print(_c(theme["meta"], f"  turn {turn}/{args.max_turns}", color))


if __name__ == "__main__":
    raise SystemExit(main())

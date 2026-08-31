#!/usr/bin/env python3
"""Non-interactive Astrid demo script for screen recording.

Runs a fixed multi-turn shopping dialog (buying → other dump → recommend,
then a short override beat) so you can record Terminal without typing live.

Usage:
  # dry-run in current terminal
  python3 scripts/demo_astrid_scripted.py

  # slower pacing (easier to read while recording)
  python3 scripts/demo_astrid_scripted.py --delay 1.2

  # then start screen record and run again, or record the dry-run window
"""
from __future__ import annotations

import argparse
import os
import sys
import time
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

os.environ.setdefault("SHOPPILOT_DENSE", "hash")

from starter.agent import Agent  # noqa: E402

# Import theme helpers from cli_chat without starting its loop
import cli_chat as cli  # noqa: E402


def _typewrite(prompt: str, text: str, delay: float, color: bool) -> None:
    """Print user line; optional char delay for recording flair."""
    print(cli._c(cli.THEME["accent"], prompt, color), end="", flush=True)
    if delay <= 0:
        print(text, flush=True)
        return
    for ch in text:
        print(ch, end="", flush=True)
        time.sleep(min(delay, 0.05))
    print(flush=True)


def _show_response(agent: Agent, response: dict, turn: int, max_turns: int, top_k: int, color: bool) -> None:
    ask = response.get("ask_attribute")
    msg = response.get("message") or ""
    recs = response.get("recommendations") or []
    print()
    print(cli._c(cli.THEME["agent"], f"  {cli.NAME}: ", color) + msg)
    if ask:
        print(
            cli._c(cli.THEME["ask"], "  ↳ asking · ", color)
            + cli._c(cli._BOLD + cli.THEME["ask"], str(ask), color)
        )
    else:
        print(cli._c(cli.THEME["meta"], "  ↳ no clarifying question this turn", color))
    print(cli._c(cli.THEME["meta"], "  suggestions", color))
    cli._print_recs(agent, recs, limit=top_k, color=color)
    print(cli._c(cli.THEME["meta"], f"  turn {turn}/{max_turns}", color))


def main() -> int:
    parser = argparse.ArgumentParser(description="Scripted Astrid demo for screen recording")
    parser.add_argument("--delay", type=float, default=0.9, help="pause between turns (seconds)")
    parser.add_argument("--type-delay", type=float, default=0.02, help="per-char user typing delay")
    parser.add_argument("--top-k", type=int, default=5)
    parser.add_argument("--catalog", default="data/catalog.jsonl")
    parser.add_argument("--no-color", action="store_true")
    args = parser.parse_args()

    color = not args.no_color and sys.stdout.isatty()
    catalog = Path(args.catalog)
    if not catalog.is_file():
        print(f"missing catalog: {catalog}", file=sys.stderr)
        return 1

    print(cli._c(cli.THEME["meta"], "  loading catalog…", color))
    agent = Agent(catalog)
    dense = getattr(getattr(agent, "_dense", None), "backend", "n/a")
    cli._banner(color, str(dense))

    sid = f"demo-{uuid.uuid4().hex[:8]}"
    agent.reset(
        sid,
        {
            "preference_tags": ["fit", "comfort", "quality"],
            "summary": "Prefers well-reviewed everyday pieces.",
            "average_prior_rating": 4.5,
            "rating_style": "usually positive",
            "purchase_frequency": "occasional",
        },
    )
    print(cli._c(cli.THEME["meta"], f"  session {sid}", color))
    print(
        cli._c(cli.THEME["agent"], f"  {cli.NAME}: ", color)
        + "What are you shopping for?  "
        + cli._c(cli.THEME["meta"], "(category, vibe, must-haves, budget…)", color)
    )

    # Beat 1 — buying path with key requirement (mirrors kit "buying" open)
    beats = [
        "I'm looking for Women Dresses. A key requirement is: black.",
        "For that, what matters is: cotton; midi length.",
        "I don't have an additional preference for style.",
    ]
    # Beat 2 — intent override (must match OVERRIDE_RE + clear new goal)
    beats += [
        "Actually, ignore my earlier preference. I'm looking for walking shoes. What I need is: breathable mesh under 80.",
    ]

    max_turns = 10
    for turn, user in enumerate(beats, start=1):
        time.sleep(args.delay)
        _typewrite("\n  You · ", user, args.type_delay, color)
        time.sleep(0.35)
        response = agent.respond(sid, user, turn, top_k=max(args.top_k, 10))
        _show_response(agent, response, turn, max_turns, args.top_k, color)

    time.sleep(args.delay)
    print()
    print(cli._c(cli.THEME["meta"], f"  {cli.NAME}: that's the multi-turn loop — state, ask, recommend.", color))
    print(cli._c(cli.THEME["meta"], "  offline default · ShopPilot agent · Astrid face", color))
    print(cli._c(cli.THEME["meta"], "  /quit when recording ends\n", color))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

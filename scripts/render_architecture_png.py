#!/usr/bin/env python3
"""Slide-ready ShopPilot architecture diagram — simple + comprehensive.

Glanceable spine: Entry → 5 steps → Response
Bottom: SessionState | Catalog | Optional (dim)
Few arrows, short labels, Astrid cyan/pink palette.
"""
from __future__ import annotations

import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
OUT_PNG = ROOT / "docs" / "architecture_diagram.png"
OUT_HTML = ROOT / "docs" / "architecture_diagram.html"
W, H = 1920, 1080

BG = (10, 18, 31)
CARD = (21, 32, 51)
CARD2 = (26, 38, 60)
CYAN = (0, 212, 255)
PINK = (255, 45, 143)
VIOLET = (168, 85, 247)
GOLD = (251, 191, 36)
GOOD = (52, 211, 153)
WHITE = (248, 250, 252)
MUTED = (160, 174, 192)
MUTED2 = (100, 116, 139)
LINE = (42, 58, 85)


def font(size: int, bold: bool = False):
    for p in (
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf" if bold else "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
    ):
        try:
            return ImageFont.truetype(p, size)
        except OSError:
            continue
    return ImageFont.load_default()


def t(d, xy, s, size=16, fill=WHITE, bold=False, anchor="lt"):
    d.text(xy, s, font=font(size, bold), fill=fill, anchor=anchor)


def rr(d, box, fill=CARD, outline=None, width=2, radius=16):
    d.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=width)


def arrow(d, a, b, col=MUTED2, w=5, dash=False, head=16):
    x1, y1 = a
    x2, y2 = b
    if dash:
        length = math.hypot(x2 - x1, y2 - y1) or 1
        n = max(int(length // 14), 1)
        for i in range(0, n, 2):
            t0, t1 = i / n, min((i + 1) / n, 1.0)
            d.line(
                [
                    (x1 + (x2 - x1) * t0, y1 + (y2 - y1) * t0),
                    (x1 + (x2 - x1) * t1, y1 + (y2 - y1) * t1),
                ],
                fill=col,
                width=w,
            )
    else:
        d.line([a, b], fill=col, width=w)
    ang = math.atan2(y2 - y1, x2 - x1)
    for off in (2.4, -2.4):
        d.line(
            [b, (x2 + head * math.cos(ang + off), y2 + head * math.sin(ang + off))],
            fill=col,
            width=w,
        )


def step(d, x, y, w, h, n, title, sub, col):
    rr(d, (x, y, x + w, y + h), fill=CARD, outline=col, width=3, radius=20)
    # number
    r = 22
    cx, cy = x + 32, y + h // 2
    d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=col)
    t(d, (cx, cy), str(n), 18, BG, True, "mm")
    t(d, (x + 70, y + h // 2 - 16), title, 22, WHITE, True, "lt")
    t(d, (x + 70, y + h // 2 + 14), sub, 15, MUTED, False, "lt")


def render_png() -> Path:
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)

    # soft atmosphere
    d.ellipse((1550, -200, 2150, 450), fill=(28, 12, 40))
    d.ellipse((-200, 750, 450, 1200), fill=(12, 40, 52))

    # header (compact — slides may crop; keep readable standalone)
    t(d, (56, 28), "SHOPPILOT  ·  ARCHITECTURE", 12, PINK, True, "lt")
    t(d, (56, 52), "State-first multi-turn agent", 30, WHITE, True, "lt")
    t(d, (56, 94), "offline · hybrid FTS+dense · one ask · ≤10 turns", 15, MUTED, False, "lt")
    for i, (lab, col) in enumerate([("0.907 Tech", CYAN), ("0.975 Hit", PINK), ("0 tok", GOOD)]):
        x0 = 1480 + i * 140
        rr(d, (x0, 48, x0 + 128, 92), fill=CARD, outline=col, width=2, radius=16)
        t(d, (x0 + 64, 70), lab, 14, WHITE, True, "mm")

    # ── ENTRY ────────────────────────────────────────────────────────────
    t(d, (56, 140), "ENTRY", 12, CYAN, True, "lt")
    rr(d, (56, 162, 250, 360), fill=CARD2, outline=CYAN, width=3, radius=18)
    rr(d, (76, 190, 230, 250), fill=CARD, outline=CYAN, width=2, radius=14)
    t(d, (153, 208), "CLI / Eval", 17, WHITE, True, "mm")
    t(d, (153, 232), "reset · respond", 13, MUTED, False, "mm")
    rr(d, (76, 270, 230, 330), fill=CARD, outline=CYAN, width=2, radius=14)
    t(d, (153, 288), "User turn t", 17, WHITE, True, "mm")
    t(d, (153, 312), "text + session", 13, MUTED, False, "mm")

    # ── HOT PATH ─────────────────────────────────────────────────────────
    t(d, (290, 140), "HOT PATH  ·  Agent.respond (sync)", 12, GOOD, True, "lt")
    steps = [
        (280, 1, "Ingest", "slots · family · override", CYAN),
        (560, 2, "Retrieve", "FTS5 + dense hash", VIOLET),
        (840, 3, "Rank", "coverage · priors", GOOD),
        (1120, 4, "Ask", "other-first ladder", GOLD),
        (1400, 5, "Respond", "msg + ask + Top-10", PINK),
    ]
    sy, sw, sh = 162, 250, 140
    for x, n, title, sub, col in steps:
        step(d, x, sy, sw, sh, n, title, sub, col)
    # chain
    mid_y = sy + sh // 2
    for x in (530, 810, 1090, 1370):
        arrow(d, (x, mid_y), (x + 28, mid_y), MUTED, 5)
    # entry → ingest
    arrow(d, (250, 300), (280, mid_y), CYAN, 5)

    # out chip
    rr(d, (1680, 200, 1864, 270), fill=CARD2, outline=PINK, width=2, radius=14)
    t(d, (1772, 235), "→ client", 16, WHITE, True, "mm")
    arrow(d, (1650, mid_y), (1680, 235), PINK, 4)

    # ── BOTTOM PANELS ────────────────────────────────────────────────────
    by = 380
    # SessionState
    rr(d, (56, by, 900, 820), fill=CARD, outline=GOOD, width=3, radius=20)
    d.rectangle((56, by, 72, 820), fill=GOOD)
    t(d, (100, by + 30), "SessionState", 26, GOOD, True, "lt")
    t(d, (100, by + 68), "mutable dialogue memory  ·  RAM only", 15, MUTED, False, "lt")
    state_lines = [
        ("Slots", "soft | disclosed | override   ·   filled / asked / dont_care"),
        ("Route", "product_family  ·  gift audience  ·  buy / browse"),
        ("Clean", "soft-only wipe on override  ·  never re-ask filled"),
        ("Loop", "next turn = past state + current text  (same session_id)"),
    ]
    yy = by + 115
    for k, v in state_lines:
        col = CYAN if k in ("Slots", "Route") else (PINK if k == "Clean" else GOOD)
        t(d, (100, yy), k, 17, col, True, "lt")
        t(d, (200, yy), v, 16, WHITE, False, "lt")
        yy += 44
    # invariant strip
    rr(d, (90, 740, 860, 800), fill=CARD2, outline=CYAN, width=2, radius=12)
    t(d, (475, 770), 't3 "black" ranks with dress + plus + black — not alone', 15, WHITE, True, "mm")

    # Catalog
    rr(d, (930, by, 1400, 820), fill=CARD, outline=VIOLET, width=3, radius=20)
    d.rectangle((930, by, 946, 820), fill=VIOLET)
    t(d, (970, by + 28), "Catalog index", 22, VIOLET, True, "lt")
    t(d, (970, by + 62), "immutable after load", 15, MUTED, False, "lt")
    for i, line in enumerate(
        [
            "FTS5 BM25  ·  in-memory",
            "Dense hash 512-d  (default)",
            "MiniLM  ·  opt-in only",
            "_products[asin]  ·  50k CSJ",
            "no writes at turn time",
        ]
    ):
        t(d, (970, by + 120 + i * 40), "·  " + line, 17, WHITE, False, "lt")

    # Optional + measure
    rr(d, (1430, by, 1864, 600), fill=(42, 18, 32), outline=PINK, width=3, radius=20)
    d.rectangle((1430, by, 1446, 600), fill=PINK)
    t(d, (1470, by + 28), "Optional LLM", 20, PINK, True, "lt")
    t(d, (1470, by + 60), "gated · fail-open · OFF by default", 14, MUTED, False, "lt")
    for i, line in enumerate(
        [
            "slots NLU (lowconf)",
            "rerank top-20",
            "timeout → rules",
            "not on score path",
        ]
    ):
        t(d, (1470, by + 110 + i * 34), "·  " + line, 16, WHITE, False, "lt")

    rr(d, (1430, 630, 1864, 820), fill=CARD2, outline=MUTED2, width=2, radius=18)
    t(d, (1470, 660), "Measure", 18, WHITE, True, "lt")
    t(d, (1470, 700), "local_evaluator", 16, MUTED, False, "lt")
    t(d, (1470, 740), "Hit · MRR · MTTC → Tech", 16, WHITE, False, "lt")
    t(d, (1470, 780), "public 200  ·  ship guardrail", 15, GOLD, False, "lt")

    # ── FEW CLEAN ARROWS ─────────────────────────────────────────────────
    # write: center of step1 bottom → state top
    arrow(d, (405, 302), (405, 380), GOOD, 5)
    t(d, (420, 335), "write", 14, GOOD, True, "lt")

    # read: state top → step2 bottom (short vertical-ish from right of state header)
    arrow(d, (700, 380), (685, 302), GOOD, 5)
    t(d, (720, 335), "read", 14, GOOD, True, "lt")

    # catalog up to retrieve — short, from catalog top-left
    arrow(d, (1100, 380), (720, 302), VIOLET, 4)
    t(d, (900, 330), "index", 13, VIOLET, True, "lt")

    # ask policy from state — gold dashed, short arc-ish from right of state
    arrow(d, (880, 420), (1245, 302), GOLD, 3, dash=True)
    t(d, (1020, 355), "filled?", 13, GOLD, True, "lt")

    # next-turn loop BELOW everything (no cross through middle)
    loop_y = 860
    d.line([(1772, 270), (1772, loop_y)], fill=CYAN, width=4)
    d.line([(1772, loop_y), (153, loop_y)], fill=CYAN, width=4)
    arrow(d, (153, loop_y), (153, 330), CYAN, 5)
    t(d, (960, 890), "next turn  ↺  same session_id", 18, CYAN, True, "mm")

    # optional stub (one short dashed) — from LLM left to rank area, high and short
    # keep VERY short so it doesn't spaghetti: just a label near LLM
    t(d, (1647, 365), "dashed pink = optional", 12, PINK, False, "mm")

    # ── FOOTER legend (thin) ─────────────────────────────────────────────
    rr(d, (56, 930, 1864, 1048), fill=CARD, outline=LINE, width=1, radius=14)
    items = [
        (CYAN, "cyan", "I/O + next turn"),
        (GOOD, "green", "state write/read"),
        (VIOLET, "violet", "catalog"),
        (GOLD, "gold dash", "ask from state"),
        (PINK, "pink", "optional LLM"),
    ]
    x = 80
    for col, name, desc in items:
        d.ellipse((x, 970, x + 14, 984), fill=col)
        t(d, (x + 24, 977), f"{name}  {desc}", 14, MUTED, False, "lm")
        x += 340
    t(
        d,
        (80, 1015),
        "Primitives:  SessionState · Agent · FTS5+Dense · _products  ·  {message, ask_attribute, Top-10}",
        14,
        MUTED2,
        False,
        "lt",
    )

    OUT_PNG.parent.mkdir(parents=True, exist_ok=True)
    img.save(OUT_PNG, "PNG", optimize=True)
    print(f"WROTE {OUT_PNG} ({OUT_PNG.stat().st_size} bytes)")
    return OUT_PNG


def render_html() -> Path:
    OUT_HTML.write_text(
        """<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8"/><title>ShopPilot Architecture</title>
<style>
body{margin:0;background:#0a121f;color:#f8fafc;font-family:system-ui,sans-serif;padding:20px}
h1{margin:0 0 6px;font-size:20px}.sub{color:#8b9bb4;margin:0 0 12px}
img{width:100%;border-radius:12px;border:1px solid #2a3a55}
</style></head>
<body>
<h1>ShopPilot · System Architecture</h1>
<p class="sub">Rebuild: python3 scripts/render_architecture_png.py</p>
<img src="architecture_diagram.png" alt="architecture"/>
</body></html>
""",
        encoding="utf-8",
    )
    print(f"WROTE {OUT_HTML}")
    return OUT_HTML


def main() -> None:
    render_png()
    render_html()


if __name__ == "__main__":
    main()

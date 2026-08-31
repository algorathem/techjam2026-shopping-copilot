#!/usr/bin/env python3
"""Slide-ready ShopPilot architecture diagram — clean arrows, no legend.

Layout:
  Header
  ENTRY | 1 Ingest → 2 Retrieve → 3 Rank → 4 Ask → 5 Respond → client
  SessionState (wide) | Catalog | Optional LLM + Measure
  next-turn loop under panels (orthogonal only)

No color legend / primitives footer (wordy). Labels sit on arrows.
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


def arrow_head(d, tip, direction, col, w=4, size=14):
    """direction: 'up'|'down'|'left'|'right'."""
    x, y = tip
    if direction == "right":
        pts = [(x, y), (x - size, y - size * 0.55), (x - size, y + size * 0.55)]
    elif direction == "left":
        pts = [(x, y), (x + size, y - size * 0.55), (x + size, y + size * 0.55)]
    elif direction == "down":
        pts = [(x, y), (x - size * 0.55, y - size), (x + size * 0.55, y - size)]
    else:  # up
        pts = [(x, y), (x - size * 0.55, y + size), (x + size * 0.55, y + size)]
    d.polygon(pts, fill=col)


def hline(d, x1, x2, y, col, w=4):
    d.line([(x1, y), (x2, y)], fill=col, width=w)


def vline(d, x, y1, y2, col, w=4):
    d.line([(x, y1), (x, y2)], fill=col, width=w)


def step(d, x, y, w, h, n, title, sub, col):
    rr(d, (x, y, x + w, y + h), fill=CARD, outline=col, width=3, radius=18)
    r = 20
    cx, cy = x + 30, y + h // 2
    d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=col)
    t(d, (cx, cy), str(n), 17, BG, True, "mm")
    t(d, (x + 62, y + h // 2 - 14), title, 20, WHITE, True, "lt")
    t(d, (x + 62, y + h // 2 + 12), sub, 14, MUTED, False, "lt")


def render_png() -> Path:
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)

    # atmosphere
    d.ellipse((1550, -180, 2150, 420), fill=(28, 12, 40))
    d.ellipse((-180, 820, 400, 1200), fill=(12, 40, 52))

    # ── HEADER ───────────────────────────────────────────────────────────
    t(d, (48, 24), "SHOPPILOT  ·  ARCHITECTURE", 12, PINK, True, "lt")
    t(d, (48, 48), "State-first multi-turn agent", 28, WHITE, True, "lt")
    t(d, (48, 86), "offline · hybrid FTS+dense · one ask · ≤10 turns", 14, MUTED, False, "lt")
    for i, (lab, col) in enumerate([("Tech 0.909", CYAN), ("Hit 0.975", PINK), ("0 tokens", GOOD)]):
        x0 = 1490 + i * 135
        rr(d, (x0, 40, x0 + 125, 84), fill=CARD, outline=col, width=2, radius=14)
        t(d, (x0 + 62, 62), lab, 13, WHITE, True, "mm")

    # ── GEOMETRY ─────────────────────────────────────────────────────────
    # Hot path row
    entry_x, entry_y, entry_w, entry_h = 48, 130, 200, 200
    sy, sw, sh = 145, 235, 120  # step y/w/h
    steps_x = [280, 545, 810, 1075, 1340]  # 1..5
    gap = 30  # between steps for arrows
    client_x, client_y = 1700, 175

    # Bottom panels (more height — no legend)
    by = 360
    bh = 620  # bottom of panels
    # SessionState | Catalog | Optional+Measure
    state_box = (48, by, 880, bh)
    cat_box = (910, by, 1360, bh)
    opt_box = (1390, by, 1872, 520)
    meas_box = (1390, 545, 1872, bh)

    # ── ENTRY ────────────────────────────────────────────────────────────
    t(d, (48, 112), "ENTRY", 11, CYAN, True, "lt")
    rr(d, (entry_x, entry_y, entry_x + entry_w, entry_y + entry_h), CARD2, CYAN, 3, 16)
    rr(d, (entry_x + 16, entry_y + 24, entry_x + entry_w - 16, entry_y + 90), CARD, CYAN, 2, 12)
    t(d, (entry_x + entry_w / 2, entry_y + 48), "CLI / Eval", 15, WHITE, True, "mm")
    t(d, (entry_x + entry_w / 2, entry_y + 72), "reset · respond", 12, MUTED, False, "mm")
    rr(d, (entry_x + 16, entry_y + 110, entry_x + entry_w - 16, entry_y + 176), CARD, CYAN, 2, 12)
    t(d, (entry_x + entry_w / 2, entry_y + 134), "User turn t", 15, WHITE, True, "mm")
    t(d, (entry_x + entry_w / 2, entry_y + 158), "text + session_id", 12, MUTED, False, "mm")

    # ── HOT PATH ─────────────────────────────────────────────────────────
    t(d, (280, 112), "HOT PATH  ·  Agent.respond (sync)", 11, GOOD, True, "lt")
    steps = [
        (1, "Ingest", "slots · family · override", CYAN),
        (2, "Retrieve", "FTS5 + dense hash", VIOLET),
        (3, "Rank", "coverage · priors", GOOD),
        (4, "Ask", "other-first ladder", GOLD),
        (5, "Respond", "msg + ask + Top-10", PINK),
    ]
    for x, (n, title, sub, col) in zip(steps_x, steps):
        step(d, x, sy, sw, sh, n, title, sub, col)

    # horizontal chain arrows between steps (short, centered)
    mid_y = sy + sh // 2
    for i in range(4):
        x1 = steps_x[i] + sw
        x2 = steps_x[i + 1]
        hline(d, x1 + 4, x2 - 4, mid_y, MUTED, 4)
        arrow_head(d, (x2 - 2, mid_y), "right", MUTED, size=12)

    # entry → ingest (horizontal from entry right mid to step1 left)
    ey = entry_y + entry_h // 2 + 20
    hline(d, entry_x + entry_w, steps_x[0] - 2, ey, CYAN, 4)
    # small vertical adjust into step mid if needed
    if abs(ey - mid_y) > 2:
        vline(d, steps_x[0] - 8, ey, mid_y, CYAN, 4)
        hline(d, steps_x[0] - 8, steps_x[0] - 2, mid_y, CYAN, 4)
    arrow_head(d, (steps_x[0] - 2, mid_y), "right", CYAN, size=12)

    # client chip
    rr(d, (client_x, client_y, 1872, client_y + 60), CARD2, PINK, 2, 12)
    t(d, ((client_x + 1872) / 2, client_y + 30), "→ client", 15, WHITE, True, "mm")
    hline(d, steps_x[4] + sw + 2, client_x - 2, mid_y, PINK, 4)
    vline(d, client_x - 8, mid_y, client_y + 30, PINK, 4)
    hline(d, client_x - 8, client_x - 2, client_y + 30, PINK, 4)
    arrow_head(d, (client_x - 2, client_y + 30), "right", PINK, size=12)

    # ── BOTTOM PANELS ────────────────────────────────────────────────────
    # SessionState
    rr(d, state_box, CARD, GOOD, 3, 18)
    d.rectangle((state_box[0], state_box[1], state_box[0] + 10, state_box[3]), fill=GOOD)
    t(d, (state_box[0] + 28, state_box[1] + 22), "SessionState", 24, GOOD, True, "lt")
    t(d, (state_box[0] + 28, state_box[1] + 54), "mutable dialogue memory · RAM", 14, MUTED, False, "lt")
    rows = [
        ("Slots", "soft | disclosed | override · filled / asked / dont_care", CYAN),
        ("Route", "product_family · gift audience · buy / browse", CYAN),
        ("Clean", "soft-only wipe on override · never re-ask filled", PINK),
        ("Loop", "next turn = past state + current text (same session_id)", GOOD),
    ]
    yy = state_box[1] + 100
    for k, v, col in rows:
        t(d, (state_box[0] + 28, yy), k, 16, col, True, "lt")
        t(d, (state_box[0] + 120, yy), v, 15, WHITE, False, "lt")
        yy += 42
    # invariant chip
    rr(d, (state_box[0] + 28, state_box[3] - 70, state_box[2] - 28, state_box[3] - 24), CARD2, CYAN, 2, 10)
    t(
        d,
        ((state_box[0] + state_box[2]) / 2, state_box[3] - 47),
        't3 "black" ranks with dress + plus + black — not alone',
        14,
        WHITE,
        True,
        "mm",
    )

    # Catalog
    rr(d, cat_box, CARD, VIOLET, 3, 18)
    d.rectangle((cat_box[0], cat_box[1], cat_box[0] + 10, cat_box[3]), fill=VIOLET)
    t(d, (cat_box[0] + 28, cat_box[1] + 22), "Catalog index", 22, VIOLET, True, "lt")
    t(d, (cat_box[0] + 28, cat_box[1] + 54), "immutable after load", 14, MUTED, False, "lt")
    for i, line in enumerate(
        [
            "FTS5 BM25 · in-memory",
            "Dense hash 512-d (default)",
            "MiniLM · opt-in only",
            "_products[asin] · 50k CSJ",
            "no writes at turn time",
        ]
    ):
        t(d, (cat_box[0] + 28, cat_box[1] + 110 + i * 40), "·  " + line, 16, WHITE, False, "lt")

    # Optional LLM
    rr(d, opt_box, (42, 18, 32), PINK, 3, 16)
    d.rectangle((opt_box[0], opt_box[1], opt_box[0] + 10, opt_box[3]), fill=PINK)
    t(d, (opt_box[0] + 28, opt_box[1] + 20), "Optional LLM", 18, PINK, True, "lt")
    t(d, (opt_box[0] + 28, opt_box[1] + 48), "OFF by default · not on score path", 13, MUTED, False, "lt")
    for i, line in enumerate(["slots NLU (lowconf)", "rerank top-20", "timeout → rules"]):
        t(d, (opt_box[0] + 28, opt_box[1] + 88 + i * 32), "·  " + line, 15, WHITE, False, "lt")

    # Measure
    rr(d, meas_box, CARD2, MUTED2, 2, 16)
    t(d, (meas_box[0] + 28, meas_box[1] + 22), "Measure", 18, WHITE, True, "lt")
    t(d, (meas_box[0] + 28, meas_box[1] + 55), "local_evaluator", 14, MUTED, False, "lt")
    t(d, (meas_box[0] + 28, meas_box[1] + 90), "Hit · MRR · MTTC → Tech", 15, WHITE, False, "lt")
    t(d, (meas_box[0] + 28, meas_box[1] + 125), "public 200 · ship guardrail", 14, GOLD, False, "lt")

    # ── ORTHOGONAL ARROWS ONLY (no diagonals) ────────────────────────────
    # Channel between hot path and panels: y = 320
    chan = 320

    # 1) write: Ingest bottom center → down to channel → down into SessionState top
    ix = steps_x[0] + sw // 2  # center of Ingest
    vline(d, ix, sy + sh, chan, GOOD, 4)
    # continue into state top (state top is by)
    vline(d, ix, chan, by, GOOD, 4)
    arrow_head(d, (ix, by - 1), "down", GOOD, size=12)
    t(d, (ix + 12, (sy + sh + chan) // 2), "write", 13, GOOD, True, "lt")

    # 2) read: from SessionState top (right of write) up to Retrieve
    rx = steps_x[1] + sw // 2  # Retrieve center
    # start just inside state top edge, go up to channel, then up to retrieve
    vline(d, rx, by, chan, GOOD, 4)
    vline(d, rx, chan, sy + sh, GOOD, 4)
    arrow_head(d, (rx, sy + sh + 1), "up", GOOD, size=12)
    t(d, (rx + 12, (chan + sy + sh) // 2), "read", 13, GOOD, True, "lt")

    # 3) catalog → Retrieve: vertical from catalog top center up to channel, then left/right to rx
    cx = (cat_box[0] + cat_box[2]) // 2
    vline(d, cx, by, chan, VIOLET, 4)
    # horizontal along channel from cx to rx
    if cx > rx:
        hline(d, rx, cx, chan, VIOLET, 4)
    else:
        hline(d, cx, rx, chan, VIOLET, 4)
    # already have vertical into retrieve at rx — share the read column:
    # small stub: channel already connects; arrow into retrieve is the read arrow.
    # Add label on channel
    t(d, ((rx + cx) // 2, chan - 16), "index", 12, VIOLET, True, "mm")

    # 4) ask policy from state → Ask: orthogonal
    # from right edge of SessionState at mid-panel height, right along a mid rail, up to Ask
    ask_x = steps_x[3] + sw // 2
    rail_y = by + 40  # just under panel top, inside? better outside between
    # Use channel-adjacent lower rail at y = chan is crowded; use y = by - 8 area already used.
    # Path: state right border mid → right to ask_x → up to step bottom
    state_right = state_box[2]
    state_mid_y = by + 30
    # exit right from state near top
    hline(d, state_right, ask_x, state_mid_y, GOLD, 3)
    vline(d, ask_x, state_mid_y, sy + sh, GOLD, 3)
    arrow_head(d, (ask_x, sy + sh + 1), "up", GOLD, size=11)
    t(d, (state_right + 40, state_mid_y - 16), "filled / asked", 12, GOLD, True, "lt")

    # 5) next-turn loop: orthogonal under everything
    loop_y = 1000
    # from client bottom center down
    clx = (client_x + 1872) // 2
    vline(d, clx, client_y + 60, loop_y, CYAN, 4)
    # left across bottom
    entry_cx = entry_x + entry_w // 2
    hline(d, entry_cx, clx, loop_y, CYAN, 4)
    # up into entry bottom
    vline(d, entry_cx, loop_y, entry_y + entry_h, CYAN, 4)
    arrow_head(d, (entry_cx, entry_y + entry_h + 1), "up", CYAN, size=12)
    t(d, (W // 2, loop_y - 22), "next turn  ·  same session_id", 16, CYAN, True, "mm")

    # Optional: no arrow into hot path (avoids spaghetti). Dim caption only.
    t(d, ((opt_box[0] + opt_box[2]) / 2, opt_box[3] - 18), "no arrow on score path", 12, MUTED2, False, "mm")

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
<p class="sub">Rebuild: python3 scripts/render_architecture_png.py · no legend · orthogonal arrows</p>
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

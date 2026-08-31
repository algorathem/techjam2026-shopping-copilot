#!/usr/bin/env python3
"""Render architecture diagram PNG with distinct shapes per system aspect."""
from __future__ import annotations

import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

OUT = Path(__file__).resolve().parents[1] / "docs" / "architecture_diagram.png"
W, H = 1600, 1000

BG = (2, 6, 23)
CARD = (15, 23, 42)
CYAN = (34, 211, 238)
EM = (52, 211, 153)
VIO = (167, 139, 250)
ROSE = (251, 113, 133)
AMB = (251, 191, 36)
WHITE = (226, 232, 240)
MUTED = (148, 163, 184)
SLATE = (100, 116, 139)
ZONE = (30, 41, 59)


def font(size: int, bold: bool = False):
    paths = [
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf"
        if bold
        else "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
    ]
    for p in paths:
        try:
            return ImageFont.truetype(p, size)
        except OSError:
            pass
    return ImageFont.load_default()


def t(d, xy, s, size=14, fill=WHITE, bold=False, anchor="lt"):
    d.text(xy, s, font=font(size, bold), fill=fill, anchor=anchor)


def arrow(d, a, b, col=SLATE, w=2, dash=False):
    x1, y1 = a
    x2, y2 = b
    if dash:
        length = math.hypot(x2 - x1, y2 - y1) or 1
        n = max(int(length // 9), 1)
        for i in range(0, n, 2):
            t0, t1 = i / n, min((i + 1) / n, 1)
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
    for off in (2.6, -2.6):
        d.line(
            [
                b,
                (x2 + 11 * math.cos(ang + off), y2 + 11 * math.sin(ang + off)),
            ],
            fill=col,
            width=w,
        )


def zone(d, box, col, label):
    d.rounded_rectangle(box, radius=14, outline=col, width=2)
    t(d, (box[0] + 12, box[1] + 8), label, 12, col, True)


def stadium(d, x, y, w, h, fill, stroke, title, sub, tw=14):
    d.rounded_rectangle([x, y, x + w, y + h], radius=h // 2, fill=fill, outline=stroke, width=2)
    t(d, (x + w / 2, y + h / 2 - 8), title, tw, WHITE, True, "mt")
    if sub:
        t(d, (x + w / 2, y + h / 2 + 10), sub, 11, MUTED, False, "mt")


def hexagon(d, cx, cy, rw, rh, fill, stroke, title, lines):
    pts = [
        (cx - rw * 0.7, cy - rh),
        (cx + rw * 0.7, cy - rh),
        (cx + rw, cy),
        (cx + rw * 0.7, cy + rh),
        (cx - rw * 0.7, cy + rh),
        (cx - rw, cy),
    ]
    d.polygon(pts, fill=fill, outline=stroke)
    # outline thicker
    d.line(pts + [pts[0]], fill=stroke, width=2)
    t(d, (cx, cy - 18), title, 15, WHITE, True, "mt")
    yy = cy + 2
    for line in lines:
        t(d, (cx, yy), line, 11, MUTED, False, "mt")
        yy += 14


def parallelogram(d, x, y, w, h, skew, fill, stroke, title, lines):
    pts = [
        (x + skew, y),
        (x + w, y),
        (x + w - skew, y + h),
        (x, y + h),
    ]
    d.polygon(pts, fill=fill, outline=stroke)
    d.line(pts + [pts[0]], fill=stroke, width=2)
    cx, cy = x + w / 2, y + h / 2
    t(d, (cx, cy - 16), title, 15, WHITE, True, "mt")
    yy = cy + 4
    for line in lines:
        t(d, (cx, yy), line, 11, MUTED, False, "mt")
        yy += 14


def round_rect(d, box, fill, stroke, title, lines, radius=10):
    d.rounded_rectangle(box, radius=radius, fill=fill, outline=stroke, width=2)
    x0, y0, x1, y1 = box
    cx = (x0 + x1) / 2
    t(d, (cx, y0 + 16), title, 15, WHITE, True, "mt")
    yy = y0 + 40
    for line in lines:
        t(d, (cx, yy), line, 11, MUTED, False, "mt")
        yy += 15


def diamond(d, cx, cy, rw, rh, fill, stroke, title, lines):
    pts = [(cx, cy - rh), (cx + rw, cy), (cx, cy + rh), (cx - rw, cy)]
    d.polygon(pts, fill=fill, outline=stroke)
    d.line(pts + [pts[0]], fill=stroke, width=2)
    t(d, (cx, cy - 10), title, 14, WHITE, True, "mt")
    yy = cy + 8
    for line in lines:
        t(d, (cx, yy), line, 10, MUTED, False, "mt")
        yy += 13


def cylinder(d, cx, cy, rw, rh, body_h, stroke, title, sub):
    # top ellipse
    d.ellipse([cx - rw, cy - rh, cx + rw, cy + rh], outline=stroke, width=2, fill=CARD)
    d.rectangle([cx - rw, cy, cx + rw, cy + body_h], fill=CARD, outline=stroke, width=2)
    d.ellipse(
        [cx - rw, cy + body_h - rh, cx + rw, cy + body_h + rh],
        outline=stroke,
        width=2,
        fill=CARD,
    )
    # redraw sides
    d.line([(cx - rw, cy), (cx - rw, cy + body_h)], fill=stroke, width=2)
    d.line([(cx + rw, cy), (cx + rw, cy + body_h)], fill=stroke, width=2)
    t(d, (cx, cy + body_h / 2 - 4), title, 13, WHITE, True, "mt")
    if sub:
        t(d, (cx, cy + body_h / 2 + 14), sub, 10, MUTED, False, "mt")


def doc_shape(d, x, y, w, h, stroke, title, lines):
    # folded doc: rectangle with wavy bottom
    d.rounded_rectangle([x, y, x + w, y + h], radius=8, fill=(8, 40, 30), outline=stroke, width=3)
    t(d, (x + w / 2, y + 18), title, 16, EM, True, "mt")
    yy = y + 48
    for line in lines:
        t(d, (x + w / 2, yy), line, 12, WHITE, False, "mt")
        yy += 18


def main():
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)

    # header
    t(d, (W / 2, 22), "ShopPilot · system architecture", 22, WHITE, True, "mt")
    t(
        d,
        (W / 2, 48),
        "state-first multi-turn · hybrid IR · one ask_attribute · offline default",
        13,
        MUTED,
        False,
        "mt",
    )

    # zones
    zone(d, (20, 70, 200, 620), CYAN, "ENTRY")
    zone(d, (220, 70, 1080, 360), EM, "HOT PATH  ·  Agent.respond  ·  sync / offline")
    zone(d, (220, 390, 720, 620), EM, "DIALOGUE MEMORY  (mutable · RAM)")
    zone(d, (740, 390, 1080, 620), VIO, "CATALOG INDEX  (immutable after load)")
    zone(d, (1100, 70, 1580, 360), ROSE, "OPTIONAL  ·  gated  ·  fail-open")
    zone(d, (1100, 390, 1580, 620), SLATE, "MEASURE")

    # --- ENTRY ---
    stadium(d, 40, 110, 140, 52, CARD, CYAN, "CLI / Eval", "reset · respond", 13)
    stadium(d, 40, 190, 140, 52, CARD, CYAN, "User turn t", "text + session", 13)
    cylinder(d, 110, 290, 55, 12, 55, SLATE, "profile", "long-term")

    # --- HOT PATH shapes ---
    hexagon(
        d,
        340,
        200,
        95,
        55,
        (8, 40, 30),
        EM,
        "Ingest / NLU",
        ["regex · expand", "family · audience", "soft override"],
    )
    parallelogram(
        d,
        470,
        145,
        200,
        110,
        28,
        (30, 20, 50),
        VIO,
        "Hybrid retrieve",
        ["FTS OR + AND", "∪ dense top-80", "query ← state"],
    )
    round_rect(
        d,
        (700, 145, 900, 255),
        (8, 40, 30),
        EM,
        "Linear rank",
        ["phrase · family · aud", "+ w·cosine · priors"],
    )
    diamond(
        d,
        1020,
        200,
        70,
        55,
        (40, 30, 10),
        AMB,
        "Ask",
        ["other→ladder", "skip filled"],
    )
    t(d, (1020, 270), "max-IG ✗ 0.72", 11, ROSE, False, "mt")

    stadium(d, 930, 295, 180, 50, CARD, CYAN, "Response t", "msg · ask · Top-10", 13)

    # --- SESSION STATE ---
    doc_shape(
        d,
        260,
        430,
        420,
        160,
        EM,
        "SessionState",
        [
            "constraints[source] · filled · asked",
            "family · audience · messages",
            "override · query_message_start",
            "latest-wins · size poles · soft wipe",
        ],
    )

    # --- CATALOG ---
    cylinder(d, 820, 450, 60, 14, 70, VIO, "FTS5", "BM25 in-mem")
    round_rect(
        d,
        (910, 440, 1050, 540),
        (30, 20, 50),
        VIO,
        "Dense",
        ["hash 512-d", "MiniLM opt"],
        radius=12,
    )
    round_rect(
        d,
        (780, 560, 1050, 600),
        CARD,
        VIO,
        "",
        [],
        radius=6,
    )
    t(d, (915, 580), "_products[asin] · 50k CSJ", 12, MUTED, False, "mm")

    # --- OPTIONAL LLM ---
    round_rect(
        d,
        (1130, 110, 1550, 200),
        (40, 15, 25),
        ROSE,
        "LLM slots NLU",
        ["lowconf | always → state"],
        radius=10,
    )
    round_rect(
        d,
        (1130, 220, 1550, 310),
        (40, 15, 25),
        ROSE,
        "LLM rerank top-20",
        ["+MRR · slow · off"],
        radius=10,
    )
    t(d, (1340, 340), "timeout → rules  ·  not required for 0.794", 12, ROSE, False, "mt")

    # --- MEASURE ---
    round_rect(
        d,
        (1130, 440, 1550, 590),
        (25, 30, 40),
        SLATE,
        "local_evaluator",
        ["Hit@10 · MRR · MTTC", "Tech ~0.794", "guardrail before ship"],
        radius=10,
    )

    # --- ARROWS ---
    arrow(d, (180, 216), (245, 200), CYAN, 3)  # user -> ingest
    arrow(d, (340, 255), (340, 430), EM, 3)  # ingest write state
    t(d, (355, 340), "write", 11, EM)
    arrow(d, (480, 500), (560, 255), EM, 2)  # state read retrieve
    t(d, (530, 400), "read", 11, EM)
    arrow(d, (435, 200), (490, 200), SLATE, 2)  # ingest -> retrieve
    arrow(d, (670, 200), (700, 200), SLATE, 2)  # retrieve -> rank
    arrow(d, (900, 200), (950, 200), SLATE, 2)  # rank -> ask
    arrow(d, (1020, 255), (1020, 295), CYAN, 2)  # ask -> response
    arrow(d, (820, 450), (600, 255), VIO, 2)  # catalog -> retrieve
    # state to ask (policy)
    arrow(d, (680, 520), (980, 250), AMB, 2, dash=True)
    t(d, (820, 420), "filled/asked", 11, AMB)
    # next turn loop
    arrow(d, (930, 320), (110, 242), CYAN, 2, dash=True)
    t(d, (400, 310), "next turn ↺", 12, CYAN)
    # optional llm
    arrow(d, (1130, 155), (430, 155), ROSE, 2, dash=True)
    arrow(d, (1130, 260), (880, 220), ROSE, 2, dash=True)
    # response to eval
    arrow(d, (1110, 320), (1200, 440), SLATE, 2, dash=True)

    # callout
    d.rounded_rectangle([40, 640, 700, 700], radius=8, outline=EM, width=2, fill=(8, 30, 25))
    t(d, (370, 658), "Multi-turn = past SessionState + current text", 14, EM, True, "mt")
    t(d, (370, 682), 't3 "black" ranks with dress+plus+black — not black alone', 12, WHITE, False, "mt")

    # bottom legend
    d.rounded_rectangle([20, 720, 1580, 980], radius=12, fill=CARD, outline=ZONE, width=1)
    t(d, (40, 740), "Shape key", 14, WHITE, True)
    # mini shapes
    stadium(d, 40, 770, 100, 36, BG, CYAN, "I/O", "", 11)
    hexagon(d, 220, 788, 40, 22, BG, EM, "NLU", [])
    parallelogram(d, 290, 770, 90, 36, 12, BG, VIO, "IR", [])
    round_rect(d, (410, 770, 510, 806), BG, EM, "rank", [], 6)
    diamond(d, 580, 788, 28, 22, BG, AMB, "ask", [])
    doc_shape(d, 640, 770, 90, 40, EM, "state", [])
    cylinder(d, 800, 775, 28, 6, 28, VIO, "idx", "")
    round_rect(d, (860, 770, 960, 806), BG, ROSE, "LLM", [], 6)

    t(d, (40, 840), "Lines", 13, WHITE, True)
    t(
        d,
        (40, 865),
        "solid slate/green = required hot path     dashed rose = optional LLM     dashed cyan = next-turn loop     gold dash = ask policy from state",
        12,
        MUTED,
    )
    t(d, (40, 900), "Invariants", 13, WHITE, True)
    t(
        d,
        (40, 925),
        "one ask_attribute  ·  state-first retrieve  ·  soft-only override  ·  offline default  ·  LLM fail-open  ·  ≤10 turns  ·  demote ≠ hard delete",
        12,
        MUTED,
    )
    t(d, (40, 955), "Primitives", 13, WHITE, True)
    t(
        d,
        (40, 978),
        "SessionState · Agent · FTS5 + DenseIndex · _products[asin] · turn response {message, ask, Top-10}",
        12,
        MUTED,
    )

    OUT.parent.mkdir(parents=True, exist_ok=True)
    img.save(OUT, "PNG")
    print(f"WROTE {OUT} ({OUT.stat().st_size} bytes)")


if __name__ == "__main__":
    main()

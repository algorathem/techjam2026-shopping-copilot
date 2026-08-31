#!/usr/bin/env python3
"""Build ShopPilot demo slide deck (16:9) for TechJam video / pitch."""
from __future__ import annotations

from pathlib import Path

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.util import Inches, Pt, Emu

# Palette — dark tech
BG = RGBColor(0x0B, 0x0F, 0x14)
BG2 = RGBColor(0x12, 0x18, 0x22)
CARD = RGBColor(0x16, 0x1E, 0x2A)
ACCENT = RGBColor(0x2E, 0xD3, 0xC6)  # teal
ACCENT2 = RGBColor(0xA7, 0x8B, 0xFA)  # soft violet
WHITE = RGBColor(0xF1, 0xF5, 0xF9)
MUTED = RGBColor(0x94, 0xA3, 0xB8)
GOOD = RGBColor(0x34, 0xD3, 0x99)
WARN = RGBColor(0xF8, 0xB4, 0x4C)

OUT = Path(__file__).resolve().parents[1] / "docs" / "ShopPilot_Demo_Slides.pptx"
W, H = Inches(13.333), Inches(7.5)


def _set_run(run, text, size=20, bold=False, color=WHITE, font="Calibri"):
    run.text = text
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.color.rgb = color
    run.font.name = font


def _bg(slide, color=BG):
    fill = slide.background.fill
    fill.solid()
    fill.fore_color.rgb = color


def _rect(slide, l, t, w, h, fill):
    shape = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, l, t, w, h)
    shape.fill.solid()
    shape.fill.fore_color.rgb = fill
    shape.line.fill.background()
    try:
        shape.adjustments[0] = 0.08
    except Exception:
        pass
    return shape


def _textbox(slide, l, t, w, h, lines, align=PP_ALIGN.LEFT):
    """lines: list of (text, size, bold, color)"""
    box = slide.shapes.add_textbox(l, t, w, h)
    tf = box.text_frame
    tf.word_wrap = True
    for i, (text, size, bold, color) in enumerate(lines):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = align
        p.space_after = Pt(6)
        run = p.add_run()
        _set_run(run, text, size=size, bold=bold, color=color)
    return box


def _bullets(slide, l, t, w, h, items, size=18):
    box = slide.shapes.add_textbox(l, t, w, h)
    tf = box.text_frame
    tf.word_wrap = True
    for i, item in enumerate(items):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.level = 0
        p.space_after = Pt(10)
        run = p.add_run()
        _set_run(run, "•  " + item, size=size, bold=False, color=WHITE)
    return box


def _footer(slide, text="ShopPilot · TechJam 2026 Track 4"):
    _textbox(
        slide,
        Inches(0.5),
        Inches(7.05),
        Inches(12),
        Inches(0.35),
        [(text, 12, False, MUTED)],
    )


def slide_title(prs):
    s = prs.slides.add_slide(prs.slide_layouts[6])
    _bg(s)
    # accent bar
    bar = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0), Inches(0), Inches(0.18), H)
    bar.fill.solid()
    bar.fill.fore_color.rgb = ACCENT
    bar.line.fill.background()

    _textbox(
        s,
        Inches(0.9),
        Inches(2.0),
        Inches(11),
        Inches(1.2),
        [("ShopPilot", 54, True, WHITE)],
    )
    _textbox(
        s,
        Inches(0.9),
        Inches(3.2),
        Inches(11),
        Inches(0.6),
        [("Offline-first multi-turn shopping copilot", 26, False, ACCENT)],
    )
    _textbox(
        s,
        Inches(0.9),
        Inches(4.1),
        Inches(11),
        Inches(0.8),
        [
            ("TechJam 2026  ·  Track 4 — Conversational Search & Recommendations", 16, False, MUTED),
            ("Demo UI: Astrid CLI  ·  GitHub: algorathem/techjam2026-shopping-copilot", 14, False, MUTED),
        ],
    )
    _footer(s, "Public kit · TechnicalScore ~0.794  ·  Hit@10 0.935  ·  MTTC ~3.0")


def slide_problem(prs):
    s = prs.slides.add_slide(prs.slide_layouts[6])
    _bg(s)
    _textbox(s, Inches(0.6), Inches(0.4), Inches(12), Inches(0.6), [("Problem", 32, True, ACCENT)])
    _textbox(
        s,
        Inches(0.6),
        Inches(1.1),
        Inches(12),
        Inches(0.8),
        [
            (
                "Keyword search fails when shoppers are vague, change their mind, or need multi-turn constraints.",
                18,
                False,
                WHITE,
            )
        ],
    )
    cards = [
        ("Vague queries", '"something nice for summer"'),
        ("Ambiguity", "dress vs dress shoes · for my son"),
        ("Mind-change", "intent override mid-session"),
        ("Turn budget", "≤10 turns or the session fails"),
    ]
    for i, (h, b) in enumerate(cards):
        x = Inches(0.6 + i * 3.15)
        _rect(s, x, Inches(2.3), Inches(3.0), Inches(2.8), CARD)
        _textbox(s, x + Inches(0.2), Inches(2.55), Inches(2.6), Inches(0.5), [(h, 16, True, ACCENT2)])
        _textbox(s, x + Inches(0.2), Inches(3.2), Inches(2.6), Inches(1.5), [(b, 15, False, WHITE)])
    _textbox(
        s,
        Inches(0.6),
        Inches(5.5),
        Inches(12),
        Inches(1.0),
        [
            (
                "Scored on: Hit@10 · MRR · MTTC → TechnicalScore   |   Frozen CSJ catalog (50k) · hidden parent_asin",
                15,
                False,
                MUTED,
            )
        ],
    )
    _footer(s)


def slide_solution(prs):
    s = prs.slides.add_slide(prs.slide_layouts[6])
    _bg(s)
    _textbox(s, Inches(0.6), Inches(0.35), Inches(12), Inches(0.5), [("Solution", 32, True, ACCENT)])
    _textbox(
        s,
        Inches(0.6),
        Inches(0.95),
        Inches(12),
        Inches(0.55),
        [
            (
                "Headless offline-first agent: each turn returns message + one ask_attribute + Top-10 ASINs",
                16,
                False,
                WHITE,
            )
        ],
    )
    steps = [
        ("1", "Intent", "Buy/browse · family · audience"),
        ("2", "State", "Slots · override hygiene · multi-fill"),
        ("3", "Retrieve", "FTS5 + dense hybrid (in-memory)"),
        ("4", "Clarify", "other-first · skip filled · ≤10 turns"),
        ("5", "Rank", "Constraints · family · light priors"),
    ]
    for i, (n, h, b) in enumerate(steps):
        y = Inches(1.7 + i * 0.9)
        circ = s.shapes.add_shape(MSO_SHAPE.OVAL, Inches(0.7), y, Inches(0.55), Inches(0.55))
        circ.fill.solid()
        circ.fill.fore_color.rgb = ACCENT
        circ.line.fill.background()
        tf = circ.text_frame
        tf.paragraphs[0].alignment = PP_ALIGN.CENTER
        run = tf.paragraphs[0].add_run()
        _set_run(run, n, size=16, bold=True, color=BG)
        _textbox(s, Inches(1.5), y - Inches(0.05), Inches(3), Inches(0.35), [(h, 18, True, WHITE)])
        _textbox(s, Inches(4.5), y - Inches(0.05), Inches(8), Inches(0.35), [(b, 16, False, MUTED)])
    _footer(s)


def slide_architecture(prs):
    s = prs.slides.add_slide(prs.slide_layouts[6])
    _bg(s)
    _textbox(s, Inches(0.5), Inches(0.3), Inches(12), Inches(0.5), [("Architecture", 32, True, ACCENT)])

    boxes = [
        (0.5, 1.3, "User turn", "free text"),
        (3.2, 1.3, "DST state", "slots · family · audience"),
        (5.9, 1.3, "Hybrid retrieve", "FTS + dense"),
        (8.6, 1.3, "Rank", "constraints · priors"),
        (5.9, 3.5, "Clarify policy", "other → open slots"),
        (8.6, 3.5, "Response", "msg + ask + Top-10"),
    ]
    for x, y, h, b in boxes:
        _rect(s, Inches(x), Inches(y), Inches(2.5), Inches(1.5), CARD)
        _textbox(s, Inches(x + 0.15), Inches(y + 0.3), Inches(2.2), Inches(0.4), [(h, 15, True, ACCENT)])
        _textbox(s, Inches(x + 0.15), Inches(y + 0.8), Inches(2.2), Inches(0.5), [(b, 13, False, MUTED)])

    _textbox(
        s,
        Inches(0.5),
        Inches(5.4),
        Inches(12),
        Inches(1.2),
        [
            ("Design choices (measured)", 16, True, ACCENT2),
            (
                "other-first + static ask ladder (max-IG ask policy → Tech ~0.72 — rejected)  ·  "
                "soft-only override wipe  ·  corpus-grounded facet wording  ·  offline default, optional LLM gated",
                14,
                False,
                WHITE,
            ),
        ],
    )
    _footer(s)


def slide_results(prs):
    s = prs.slides.add_slide(prs.slide_layouts[6])
    _bg(s)
    _textbox(s, Inches(0.6), Inches(0.35), Inches(12), Inches(0.5), [("Results — public 200", 32, True, ACCENT)])

    metrics = [
        ("TechnicalScore", "0.11 → 0.794", "7×+ vs weak BM25"),
        ("Hit@10", "0.125 → 0.935", "target in top 10"),
        ("MTTC", "9.8 → 3.0", "fewer turns to hit"),
        ("Tokens", "0", "offline default path"),
    ]
    for i, (h, v, note) in enumerate(metrics):
        x = Inches(0.6 + (i % 4) * 3.15)
        y = Inches(1.3)
        _rect(s, x, y, Inches(3.0), Inches(2.6), CARD)
        _textbox(s, x + Inches(0.2), y + Inches(0.35), Inches(2.6), Inches(0.4), [(h, 14, False, MUTED)])
        _textbox(s, x + Inches(0.2), y + Inches(0.9), Inches(2.6), Inches(0.7), [(v, 22, True, GOOD)])
        _textbox(s, x + Inches(0.2), y + Inches(1.8), Inches(2.6), Inches(0.5), [(note, 13, False, WHITE)])

    _textbox(
        s,
        Inches(0.6),
        Inches(4.3),
        Inches(12),
        Inches(2.0),
        [
            ("What moved the needle", 16, True, ACCENT2),
            (
                "Override hygiene · hybrid dense hash · family/audience routing · multi-slot freeform · "
                "profile/rating cold-start priors — each kept only if Tech stayed ≥ prior baseline.",
                15,
                False,
                WHITE,
            ),
            (
                "Optional Gemini NLU/rerank: gated flags only; not required for score.",
                14,
                False,
                MUTED,
            ),
        ],
    )
    _footer(s)


def slide_demo(prs):
    s = prs.slides.add_slide(prs.slide_layouts[6])
    _bg(s)
    _textbox(s, Inches(0.6), Inches(0.35), Inches(12), Inches(0.5), [("Live demo — Astrid CLI", 32, True, ACCENT)])
    _rect(s, Inches(0.6), Inches(1.1), Inches(12.1), Inches(5.2), CARD)
    mono = [
        ("$ python3 cli_chat.py --dense hash", 14, False, MUTED),
        ("", 10, False, MUTED),
        ("     _        _        _     _", 14, False, ACCENT2),
        ("    / \\   ___| |_ _ __(_) __| |", 14, False, ACCENT2),
        ("   / _ \\ / __| __| '__| |/ _` |", 14, False, ACCENT2),
        ("  / ___ \\__ \\ |_| |  | | (_| |", 14, False, ACCENT2),
        (" /_/   \\_\\___/\\__|_|  |_|\\__,_|", 14, False, ACCENT2),
        ("", 8, False, MUTED),
        ("  Astrid  ·  quiet clarity for every aisle", 15, True, WHITE),
        ("  offline hybrid shopping agent  ·  dense=hash", 13, False, MUTED),
        ("", 8, False, MUTED),
        ("  You · shoes for my son", 14, False, ACCENT),
        ("  Astrid: Got it (footwear; boys). Any color…?", 14, False, WHITE),
        ("  ↳ asking · other", 13, False, WARN),
        ("  1. Kids Boys Girls Soft Slippers …", 13, False, MUTED),
    ]
    _textbox(s, Inches(0.9), Inches(1.3), Inches(11.5), Inches(4.8), mono)
    _footer(s, "Record real terminal for YouTube · this slide is a storyboard fallback")


def slide_impact(prs):
    s = prs.slides.add_slide(prs.slide_layouts[6])
    _bg(s)
    _textbox(s, Inches(0.6), Inches(0.35), Inches(12), Inches(0.5), [("Impact & takeaways", 32, True, ACCENT)])
    _bullets(
        s,
        Inches(0.8),
        Inches(1.2),
        Inches(11.5),
        Inches(4.5),
        [
            "Findability KPI: Hit@10 0.935 on public kit (exact parent_asin).",
            "Cost-to-serve: MTTC ~3 turns vs ~10 for weak BM25 — fewer refine loops.",
            "Merchant-owned brain: offline API mid-market can run without a paid LLM.",
            "Literature-aligned CQ/DST; kit-aligned ask policy after measured A/B.",
            "Same loop as real conversational commerce — catalog-grounded, not chatbot theater.",
        ],
        size=18,
    )
    _footer(s)


def slide_end(prs):
    s = prs.slides.add_slide(prs.slide_layouts[6])
    _bg(s)
    bar = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0), Inches(0), Inches(0.18), H)
    bar.fill.solid()
    bar.fill.fore_color.rgb = ACCENT
    bar.line.fill.background()
    _textbox(s, Inches(0.9), Inches(2.2), Inches(11), Inches(0.9), [("Thanks", 48, True, WHITE)])
    _textbox(
        s,
        Inches(0.9),
        Inches(3.2),
        Inches(11),
        Inches(1.5),
        [
            ("ShopPilot  ·  offline-first shopping copilot", 22, False, ACCENT),
            ("github.com/algorathem/techjam2026-shopping-copilot", 18, False, WHITE),
            ("Demo UI: Astrid CLI  ·  Tech ~0.794  ·  Hit@10 0.935", 16, False, MUTED),
        ],
    )
    _footer(s, "TechJam 2026 Track 4")


def main() -> None:
    prs = Presentation()
    prs.slide_width = W
    prs.slide_height = H
    slide_title(prs)
    slide_problem(prs)
    slide_solution(prs)
    slide_architecture(prs)
    slide_results(prs)
    slide_demo(prs)
    slide_impact(prs)
    slide_end(prs)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    prs.save(OUT)
    print(f"WROTE {OUT}")
    print(f"slides={len(prs.slides)}")


if __name__ == "__main__":
    main()

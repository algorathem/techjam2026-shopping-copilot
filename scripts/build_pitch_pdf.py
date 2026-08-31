#!/usr/bin/env python3
"""Build ShopPilot 9-slide pitch PDF (16:9) from the finalized outline.

Design system = Astrid brand (same as docs/ShopPilot_Demo_Slides.pptx):
  BG deep navy #0A121F · Cyan #00D4FF · Rose/magenta #FF2D8F
  Violet #A855F7 · Muted #8B9BB4 · Gold #FBBF24 · Good #34D399 · White

Do NOT use the one-off outline hexes (#FE2C55 / #00E5FF / #12131A) — those
were TikTok-red variants, not the project brand.

Output:
  docs/ShopPilot_Pitch_Deck.pdf
  optional: ~/Downloads/ShopPilot_Pitch_Deck.pdf

Usage:
  python3 scripts/build_pitch_pdf.py
"""
from __future__ import annotations

from pathlib import Path

from reportlab.lib.colors import HexColor
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "ShopPilot_Pitch_Deck.pdf"

# 16:9
W, H = 13.333 * inch, 7.5 * inch

# Astrid brand — locked to build_demo_slides.py / architecture diagram
BG = HexColor("#0A121F")
BG2 = HexColor("#0E182A")
CARD = HexColor("#152033")
CARD2 = HexColor("#1A263C")
CYAN = HexColor("#00D4FF")
PINK = HexColor("#FF2D8F")
VIOLET = HexColor("#A855F7")
SLATE = HexColor("#8B9BB4")
WHITE = HexColor("#FFFFFF")
MUTED = HexColor("#8B9BB4")
LINE = HexColor("#2A3A55")
GOOD = HexColor("#34D399")
GOLD = HexColor("#FBBF24")

TOTAL = 9


def try_fonts():
    pairs = [
        ("Sans", "/System/Library/Fonts/Supplemental/Arial.ttf"),
        ("Sans-Bold", "/System/Library/Fonts/Supplemental/Arial Bold.ttf"),
        ("Sans", "/Library/Fonts/Arial.ttf"),
        ("Sans-Bold", "/Library/Fonts/Arial Bold.ttf"),
    ]
    registered = set()
    for name, path in pairs:
        if name in registered:
            continue
        p = Path(path)
        if p.exists():
            try:
                pdfmetrics.registerFont(TTFont(name, str(p)))
                registered.add(name)
            except Exception:
                pass
    if "Sans" not in registered:
        return "Helvetica", "Helvetica-Bold"
    bold = "Sans-Bold" if "Sans-Bold" in registered else "Sans"
    return "Sans", bold


FONT, FONT_B = try_fonts()


def draw_bg(c: canvas.Canvas):
    c.setFillColor(BG)
    c.rect(0, 0, W, H, fill=1, stroke=0)
    # atmospheric blobs
    c.setFillColor(HexColor("#1A0B24"))
    c.circle(W * 0.92, H * 0.85, 2.2 * inch, fill=1, stroke=0)
    c.setFillColor(HexColor("#0C2430"))
    c.circle(W * 0.05, H * 0.1, 2.0 * inch, fill=1, stroke=0)
    # left rail
    c.setFillColor(CYAN)
    c.rect(0, 0, 0.12 * inch, H, fill=1, stroke=0)
    c.setFillColor(PINK)
    c.rect(0.12 * inch, 0, 0.04 * inch, H, fill=1, stroke=0)


def footer(c: canvas.Canvas, page: int, left: str = "ShopPilot · TikTok TechJam 2026 Track 4"):
    c.setStrokeColor(LINE)
    c.setLineWidth(1)
    c.line(0.5 * inch, 0.38 * inch, W - 0.5 * inch, 0.38 * inch)
    c.setFillColor(SLATE)
    c.setFont(FONT, 9)
    c.drawString(0.55 * inch, 0.18 * inch, left)
    c.drawRightString(W - 0.55 * inch, 0.18 * inch, f"{page} / {TOTAL}")


def section_label(c: canvas.Canvas, text: str, x=0.55 * inch, y=H - 0.45 * inch):
    c.setFillColor(PINK)
    c.setFont(FONT_B, 10)
    c.drawString(x, y, text.upper())


def title(c: canvas.Canvas, text: str, x=0.55 * inch, y=H - 0.95 * inch, size=26):
    c.setFillColor(WHITE)
    c.setFont(FONT_B, size)
    c.drawString(x, y, text)


def subtitle(c: canvas.Canvas, text: str, x=0.55 * inch, y=H - 1.35 * inch, size=12):
    c.setFillColor(MUTED)
    c.setFont(FONT, size)
    c.drawString(x, y, text)


def rounded_rect(c: canvas.Canvas, x, y, w, h, fill=CARD, stroke=None, radius=10, sw=1.5):
    c.setFillColor(fill)
    if stroke:
        c.setStrokeColor(stroke)
        c.setLineWidth(sw)
        c.roundRect(x, y, w, h, radius, fill=1, stroke=1)
    else:
        c.setStrokeColor(fill)
        c.roundRect(x, y, w, h, radius, fill=1, stroke=0)


def badge(c, x, y, w, h, label, value, delta, accent):
    rounded_rect(c, x, y, w, h, CARD, None, 12)
    c.setFillColor(accent)
    c.rect(x, y + h - 5, w, 5, fill=1, stroke=0)
    c.setFillColor(SLATE)
    c.setFont(FONT, 10)
    c.drawString(x + 14, y + h - 28, label)
    c.setFillColor(WHITE)
    c.setFont(FONT_B, 26)
    c.drawString(x + 14, y + h - 62, value)
    c.setFillColor(accent)
    c.setFont(FONT, 10)
    c.drawString(x + 14, y + 16, delta)


def wrap_text(c, text, x, y, max_width, font=FONT, size=11, leading=15, color=MUTED):
    c.setFont(font, size)
    c.setFillColor(color)
    words = text.split()
    lines = []
    cur = ""
    for w in words:
        trial = (cur + " " + w).strip()
        if c.stringWidth(trial, font, size) <= max_width:
            cur = trial
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    yy = y
    for line in lines:
        c.drawString(x, yy, line)
        yy -= leading
    return yy


# ═══════════════════════════════════════════════════════════════════════════
# SLIDES
# ═══════════════════════════════════════════════════════════════════════════


def slide_01(c: canvas.Canvas):
    draw_bg(c)
    c.setFillColor(PINK)
    c.setFont(FONT_B, 11)
    c.drawString(0.7 * inch, H - 1.3 * inch, "TIKTOK TECHJAM 2026  ·  TRACK 4 (SHOPPING COPILOT)")

    # ShopPilot split
    c.setFont(FONT_B, 54)
    c.setFillColor(CYAN)
    c.drawString(0.7 * inch, H - 2.35 * inch, "Shop")
    sw = c.stringWidth("Shop", FONT_B, 54)
    c.setFillColor(PINK)
    c.drawString(0.7 * inch + sw, H - 2.35 * inch, "Pilot")

    c.setFillColor(WHITE)
    c.setFont(FONT, 16)
    c.drawString(0.7 * inch, H - 2.85 * inch, "An Offline-First Conversational Shopping Copilot for Multi-Turn E-Commerce")

    c.setFillColor(SLATE)
    c.setFont(FONT, 11)
    c.drawString(0.7 * inch, H - 3.25 * inch, "Astrid CLI Engine  ·  Zero Token Cost  ·  Offline Default Path")

    # 4 scoreboard badges
    metrics = [
        ("TechnicalScore", "0.907", "Starter 0.107 · 8.5× lift", CYAN),
        ("Hit Rate@10", "97.5%", "Starter 12.5%", PINK),
        ("MRR", "0.858", "Starter 0.068 · 12.6×", VIOLET),
        ("MTTC", "2.88 turns", "Starter 9.81 · −70.6%", GOLD),
    ]
    bw = 2.9 * inch
    for i, (lab, val, delta, col) in enumerate(metrics):
        x = 0.7 * inch + i * (bw + 0.2 * inch)
        badge(c, x, 1.55 * inch, bw, 1.55 * inch, lab, val, delta, col)

    c.setFillColor(CYAN)
    c.setFont(FONT, 11)
    c.drawString(0.7 * inch, 1.05 * inch, "github.com/algorathem/techjam2026-shopping-copilot")
    footer(c, 1, "ShopPilot  ·  Executive scoreboard")


def slide_02(c: canvas.Canvas):
    draw_bg(c)
    section_label(c, "01  ·  Problem")
    title(c, "Why Keyword Search Collapses in Conversational Commerce", size=22)
    subtitle(c, "Single-turn search assumes static intent. Real sessions hit four core failure modes.")

    cards = [
        ("01", "Aesthetic Under-specification",
         'Vague queries ("something nice for summer") flood pools with flat lexical scores.', CYAN),
        ("02", "Semantic Collisions",
         'Polysemy causes category drag ("dress sandals" pulling party dresses).', PINK),
        ("03", "Mid-Session Preference Shifts",
         'Pivots ("actually forget sneakers…") pollute state with stale tokens.', VIOLET),
        ("04", "Turn Fatigue & Horizon",
         "Abandonment compounds each unnecessary ask; sessions fail at the ≤10-turn limit.", GOLD),
    ]
    for i, (num, h, b, col) in enumerate(cards):
        col_i, row_i = i % 2, i // 2
        x = 0.55 * inch + col_i * 6.25 * inch
        y = H - 2.0 * inch - row_i * 2.15 * inch - 1.9 * inch
        rounded_rect(c, x, y, 6.0 * inch, 1.95 * inch, CARD, None, 12)
        c.setFillColor(col)
        c.rect(x, y + 1.95 * inch - 5, 6.0 * inch, 5, fill=1, stroke=0)
        c.setFont(FONT_B, 11)
        c.drawString(x + 18, y + 1.55 * inch, num)
        c.setFillColor(WHITE)
        c.setFont(FONT_B, 14)
        c.drawString(x + 18, y + 1.2 * inch, h)
        wrap_text(c, b, x + 18, y + 0.85 * inch, 5.5 * inch, size=11, leading=15, color=MUTED)

    # objective banner
    rounded_rect(c, 0.55 * inch, 0.55 * inch, 12.2 * inch, 0.7 * inch, CARD2, CYAN, 10, 1.2)
    c.setFillColor(CYAN)
    c.setFont(FONT_B, 10)
    c.drawString(0.75 * inch, 1.0 * inch, "OBJECTIVE FUNCTION")
    c.setFillColor(WHITE)
    c.setFont(FONT, 12)
    c.drawString(
        0.75 * inch,
        0.72 * inch,
        "TechnicalScore  =  0.50·Hit@10  +  0.30·MRR  +  0.20·((11 − MTTC) / 10)",
    )
    footer(c, 2)


def slide_03(c: canvas.Canvas):
    draw_bg(c)
    section_label(c, "02  ·  Solution")
    title(c, "ShopPilot Engine: In-Memory Multi-Turn Pipeline", size=22)
    subtitle(
        c,
        "Every respond() returns a natural message, one structured ask_attribute, and Top-10 ASINs in <15 ms.",
    )

    steps = [
        ("1", "Intent & Entity Triage", "Regex triage: buy/browse, audience, taxonomy anchors.", CYAN),
        ("2", "Provenance-Aware DST", "Slots separate disclosed facts from transient soft prefs.", PINK),
        ("3", "In-Memory Hybrid Recall", "SQLite FTS5 (BM25) fused with NumPy char n-gram dense hash.", VIOLET),
        ("4", "Dynamic Clarification Ladder", "Asymmetric other-first funnel; skip satisfied slots.", GOLD),
        ("5", "Constraint-Coverage Reranker", "Exact-match bonuses + leaf-category + audience align.", GOOD),
    ]
    for i, (n, h, b, col) in enumerate(steps):
        y = H - 2.0 * inch - i * 0.95 * inch
        # number circle
        c.setFillColor(col)
        c.circle(0.9 * inch, y + 0.28 * inch, 0.22 * inch, fill=1, stroke=0)
        c.setFillColor(BG)
        c.setFont(FONT_B, 14)
        c.drawCentredString(0.9 * inch, y + 0.22 * inch, n)
        rounded_rect(c, 1.35 * inch, y, 11.4 * inch, 0.75 * inch, CARD, None, 10)
        c.setFillColor(WHITE)
        c.setFont(FONT_B, 14)
        c.drawString(1.55 * inch, y + 0.42 * inch, h)
        c.setFillColor(MUTED)
        c.setFont(FONT, 11)
        c.drawString(1.55 * inch, y + 0.18 * inch, b)
        if i < len(steps) - 1:
            c.setStrokeColor(LINE)
            c.setLineWidth(2)
            c.line(0.9 * inch, y - 0.05 * inch, 0.9 * inch, y - 0.2 * inch)
    footer(c, 3)


def slide_04(c: canvas.Canvas):
    draw_bg(c)
    section_label(c, "03  ·  Architecture")
    title(c, "State Is the Product: Non-Monotonic Dialog Tracking", size=22)
    subtitle(c, "Override hygiene · taxonomy locks · empirically validated ask policy · zero-token default.")

    # invariant banner
    rounded_rect(c, 0.55 * inch, H - 2.35 * inch, 12.2 * inch, 0.75 * inch, CARD2, CYAN, 10, 1.5)
    c.setFillColor(CYAN)
    c.setFont(FONT_B, 10)
    c.drawString(0.75 * inch, H - 1.8 * inch, "CORE INVARIANT")
    c.setFillColor(WHITE)
    c.setFont(FONT, 13)
    c.drawString(
        0.75 * inch,
        H - 2.15 * inch,
        'Turn t₃ ("black") ranks against [dress + plus-size + black] — never "black" in isolation.',
    )

    mechanisms = [
        ("Selective Soft-Only Invalidation",
         "On override: wipe soft prefs; keep disclosed facts the simulator will not re-send.", CYAN),
        ("Taxonomy Boundary Lock",
         "Disambiguate at ingest: dress sandals → family:footwear (not garment dresses).", PINK),
        ("Empirically Validated Ask Policy",
         "other-first funnel beats naive max-IG (max-IG dropped Tech to ≈0.72).", VIOLET),
        ("Zero-Token Footprint",
         "In-memory stdlib + NumPy. MiniLM / LLM paths are optional flags only.", GOOD),
    ]
    for i, (h, b, col) in enumerate(mechanisms):
        col_i, row_i = i % 2, i // 2
        x = 0.55 * inch + col_i * 6.25 * inch
        y = 0.7 * inch + (1 - row_i) * 2.05 * inch
        rounded_rect(c, x, y, 6.0 * inch, 1.9 * inch, CARD, None, 12)
        c.setFillColor(col)
        c.rect(x, y, 6, 1.9 * inch, fill=1, stroke=0)
        c.setFillColor(WHITE)
        c.setFont(FONT_B, 13)
        c.drawString(x + 22, y + 1.4 * inch, h)
        wrap_text(c, b, x + 22, y + 1.0 * inch, 5.5 * inch, size=12, leading=16, color=MUTED)
    footer(c, 4)


def slide_05(c: canvas.Canvas):
    draw_bg(c)
    section_label(c, "04  ·  Public Benchmark")
    title(c, "Official Benchmark: 8.5× Lift Over Baseline", size=22)
    subtitle(c, "Deterministic evaluator.local_evaluator · Amazon CSJ 50k · N=200 · SHOPPILOT_DENSE=hash")

    # table header
    headers = ["Metric", "Weak BM25", "ShopPilot (hash)", "Delta / Lift"]
    rows = [
        ["TechnicalScore", "0.107", "0.907", "+0.800  (8.5×)"],
        ["Hit Rate@10", "12.5%", "97.5%", "+85.0 pp"],
        ["MRR", "0.068", "0.858", "+0.790  (12.6×)"],
        ["MTTC (turns)", "9.81", "2.88", "−6.93  (−70.6%)"],
        ["LLM Token Cost", "0", "0", "100% offline"],
    ]
    x0, y0 = 0.55 * inch, H - 2.0 * inch
    col_w = [3.2 * inch, 2.6 * inch, 3.2 * inch, 3.2 * inch]
    row_h = 0.48 * inch

    # header row
    rounded_rect(c, x0, y0 - row_h, sum(col_w), row_h, CARD2, None, 6)
    c.setFillColor(CYAN)
    c.setFont(FONT_B, 11)
    xx = x0 + 12
    for i, h in enumerate(headers):
        c.drawString(xx, y0 - row_h + 16, h)
        xx += col_w[i]

    for r, row in enumerate(rows):
        y = y0 - (r + 2) * row_h
        fill = CARD if r % 2 == 0 else CARD2
        c.setFillColor(fill)
        c.rect(x0, y, sum(col_w), row_h, fill=1, stroke=0)
        xx = x0 + 12
        for i, cell in enumerate(row):
            if i == 0:
                c.setFillColor(WHITE)
                c.setFont(FONT_B, 11)
            elif i == 2:
                c.setFillColor(CYAN)
                c.setFont(FONT_B, 12)
            elif i == 3:
                c.setFillColor(PINK)
                c.setFont(FONT_B, 11)
            else:
                c.setFillColor(MUTED)
                c.setFont(FONT, 11)
            c.drawString(xx, y + 16, cell)
            xx += col_w[i]

    # trade-off callout
    rounded_rect(c, 0.55 * inch, 0.55 * inch, 12.2 * inch, 1.55 * inch, CARD2, PINK, 10, 1.5)
    c.setFillColor(PINK)
    c.setFont(FONT_B, 11)
    c.drawString(0.75 * inch, 1.8 * inch, "METRIC TRADE-OFF  ·  THE EARLY-TERMINATION PARADOX")
    wrap_text(
        c,
        "Emitting Top-10 too early on Turn 1 risks a low-rank hit (e.g. Rank 8 ⇒ MRR=0.125), freezing a poor score. "
        "Because MRR carries 1.5× the weight of MTTC in TechnicalScore, ShopPilot uses Precision Gating "
        "(Top-1 limit orders on ambiguous early turns) to gather constraints and force final conversion toward Rank 1.",
        0.75 * inch,
        1.45 * inch,
        11.7 * inch,
        size=11,
        leading=15,
        color=WHITE,
    )
    footer(c, 5)


def slide_06(c: canvas.Canvas):
    draw_bg(c)
    section_label(c, "05  ·  Scenario Breakdown")
    title(c, "Performance Breakdown Across Scenarios", size=22)
    subtitle(c, "High conversion maintained across buying, browse, override, and boundary (N=200).")

    headers = ["Scenario", "N", "Hit@10", "MRR", "MTTC"]
    rows = [
        ["Targeted Buying", "80", "97.5%", "0.833", "2.45"],
        ["Open Browsing", "80", "96.3%", "0.816", "2.79"],
        ["Intent Override", "30", "96.7%", "0.866", "4.20"],
        ["Boundary (Don't Care)", "10", "100.0%", "0.933", "3.00"],
        ["Overall Public Benchmark", "200", "97.5%", "0.858", "2.88"],
    ]
    x0, y0 = 0.55 * inch, H - 2.0 * inch
    col_w = [4.2 * inch, 1.4 * inch, 2.2 * inch, 2.2 * inch, 2.2 * inch]
    row_h = 0.5 * inch

    rounded_rect(c, x0, y0 - row_h, sum(col_w), row_h, CARD2, None, 6)
    c.setFillColor(CYAN)
    c.setFont(FONT_B, 11)
    xx = x0 + 12
    for i, h in enumerate(headers):
        c.drawString(xx, y0 - row_h + 18, h)
        xx += col_w[i]

    for r, row in enumerate(rows):
        y = y0 - (r + 2) * row_h
        fill = CARD if r % 2 == 0 else CARD2
        if r == len(rows) - 1:
            fill = HexColor("#1E2438")
        c.setFillColor(fill)
        c.rect(x0, y, sum(col_w), row_h, fill=1, stroke=0)
        xx = x0 + 12
        for i, cell in enumerate(row):
            if r == len(rows) - 1 or i in (2, 3):
                c.setFillColor(CYAN if i != 0 else WHITE)
                c.setFont(FONT_B, 12 if i else 11)
            else:
                c.setFillColor(WHITE if i == 0 else MUTED)
                c.setFont(FONT_B if i == 0 else FONT, 11)
            c.drawString(xx, y + 17, cell)
            xx += col_w[i]

    rounded_rect(c, 0.55 * inch, 0.55 * inch, 12.2 * inch, 1.15 * inch, CARD2, VIOLET, 10, 1.2)
    c.setFillColor(VIOLET)
    c.setFont(FONT_B, 10)
    c.drawString(0.75 * inch, 1.4 * inch, "KEY TAKEAWAY")
    wrap_text(
        c,
        "Preference override incurs a turn penalty (4.20 MTTC) from pivot re-elicitation, "
        "but holds 96.7% Hit@10 and 0.866 MRR via clean soft-only state invalidation.",
        0.75 * inch,
        1.1 * inch,
        11.7 * inch,
        size=12,
        leading=16,
        color=WHITE,
    )
    footer(c, 6)


def slide_07(c: canvas.Canvas):
    draw_bg(c)
    section_label(c, "06  ·  Live Demo")
    title(c, "Live Execution: Astrid Multi-Turn Terminal", size=22)
    subtitle(c, "python3 cli_chat.py --dense hash   ·   /new  /state  /quit")

    # terminal panel
    rounded_rect(c, 0.55 * inch, 0.9 * inch, 7.4 * inch, 4.7 * inch, HexColor("#0A0C12"), None, 12)
    c.setFillColor(HexColor("#161822"))
    c.rect(0.55 * inch, 0.9 * inch + 4.7 * inch - 0.4 * inch, 7.4 * inch, 0.4 * inch, fill=1, stroke=0)
    for i, col in enumerate([HexColor("#FF5F57"), HexColor("#FEBC2E"), HexColor("#28C840")]):
        c.setFillColor(col)
        c.circle(0.85 * inch + i * 0.28 * inch, 0.9 * inch + 4.7 * inch - 0.2 * inch, 0.07 * inch, fill=1, stroke=0)
    c.setFillColor(SLATE)
    c.setFont(FONT, 10)
    c.drawString(1.8 * inch, 0.9 * inch + 4.7 * inch - 0.25 * inch, "astrid — dense=hash")

    lines = [
        (SLATE, "$ python3 cli_chat.py --dense hash"),
        (PINK, "  Astrid  ·  quiet clarity for every aisle"),
        (CYAN, "  You · shoes for my son"),
        (WHITE, "  Astrid: Got it (footwear; boys). Any color…?"),
        (GOLD, "  ↳ ask · other"),
        (CYAN, "  You · Actually forget sneakers, dress shoes size 9"),
        (WHITE, "  Astrid: Updated (footwear; size 9). Color?"),
        (PINK, "  ↳ soft wipe · disclosed kept · family=footwear"),
        (MUTED, "  /state → size=9  asked={other}"),
    ]
    yy = 0.9 * inch + 4.0 * inch
    for col, line in lines:
        c.setFillColor(col)
        c.setFont(FONT, 11)
        c.drawString(0.8 * inch, yy, line)
        yy -= 0.38 * inch

    # three traces
    traces = [
        ("Vague → Clarify",
         'dress + exploring → ask other → "plus size" locks size (no re-ask).', CYAN),
        ("Taxonomy Lock",
         '"dress sandals" → family=footwear; suppresses garment dresses.', PINK),
        ("Preference Override",
         "running shoes → dress shoes size 9; soft wipe; size persists.", VIOLET),
    ]
    for i, (h, b, col) in enumerate(traces):
        y = 4.3 * inch - i * 1.4 * inch
        rounded_rect(c, 8.2 * inch, y, 4.55 * inch, 1.25 * inch, CARD, None, 10)
        c.setFillColor(col)
        c.rect(8.2 * inch, y, 5, 1.25 * inch, fill=1, stroke=0)
        c.setFillColor(WHITE)
        c.setFont(FONT_B, 12)
        c.drawString(8.45 * inch, y + 0.85 * inch, h)
        wrap_text(c, b, 8.45 * inch, y + 0.55 * inch, 4.1 * inch, size=11, leading=14, color=MUTED)
    footer(c, 7)


def slide_08(c: canvas.Canvas):
    draw_bg(c)
    section_label(c, "07  ·  Commercial Impact")
    title(c, "Bridging Benchmark Metrics to Commercial Value", size=22)
    subtitle(c, "Kit scores read as merchant KPIs — findability, rank quality, cost-to-serve, infra overhead.")

    cards = [
        ("Hit@10  ·  97.5%", "Minimizes zero-result searches and bounce across sparse catalogs.", CYAN),
        ("MRR  ·  0.858", "Positions converters above the mobile fold without endless scroll.", PINK),
        ("MTTC  ·  2.88 turns", "Cuts turn fatigue and abandonment before checkout.", VIOLET),
        ("Zero Token Footprint", "Edge latency, deterministic path, $0 recurring LLM API cost.", GOOD),
    ]
    for i, (h, b, col) in enumerate(cards):
        y = H - 2.15 * inch - i * 1.2 * inch
        rounded_rect(c, 0.55 * inch, y - 0.95 * inch, 12.2 * inch, 1.05 * inch, CARD, None, 12)
        c.setFillColor(col)
        c.rect(0.55 * inch, y - 0.95 * inch, 8, 1.05 * inch, fill=1, stroke=0)
        c.setFillColor(col)
        c.setFont(FONT_B, 16)
        c.drawString(0.9 * inch, y - 0.35 * inch, h)
        c.setFillColor(WHITE)
        c.setFont(FONT, 13)
        c.drawString(5.2 * inch, y - 0.35 * inch, b)
    footer(c, 8)


def slide_09(c: canvas.Canvas):
    draw_bg(c)
    c.setFillColor(PINK)
    c.setFont(FONT_B, 12)
    c.drawString(0.7 * inch, H - 1.5 * inch, "08  ·  CONCLUSION & REPRODUCIBILITY")

    c.setFont(FONT_B, 42)
    c.setFillColor(CYAN)
    c.drawString(0.7 * inch, H - 2.4 * inch, "Shop")
    sw = c.stringWidth("Shop", FONT_B, 42)
    c.setFillColor(PINK)
    c.drawString(0.7 * inch + sw, H - 2.4 * inch, "Pilot")

    c.setFillColor(WHITE)
    c.setFont(FONT, 16)
    c.drawString(0.7 * inch, H - 2.95 * inch, "Deterministic, Fast, & Open Source")

    # scorecard chips
    chips = [
        ("0.907", "TechnicalScore", CYAN),
        ("97.5%", "Hit@10", PINK),
        ("0.858", "MRR", VIOLET),
        ("2.88", "MTTC", GOLD),
        ("0", "Tokens", GOOD),
    ]
    for i, (val, lab, col) in enumerate(chips):
        x = 0.7 * inch + i * 2.4 * inch
        rounded_rect(c, x, 2.9 * inch, 2.2 * inch, 1.15 * inch, CARD, col, 12, 1.5)
        c.setFillColor(WHITE)
        c.setFont(FONT_B, 22)
        c.drawCentredString(x + 1.1 * inch, 3.5 * inch, val)
        c.setFillColor(MUTED)
        c.setFont(FONT, 10)
        c.drawCentredString(x + 1.1 * inch, 3.15 * inch, lab)

    # reproduce box
    rounded_rect(c, 0.7 * inch, 1.5 * inch, 11.9 * inch, 1.1 * inch, CARD2, CYAN, 10, 1.2)
    c.setFillColor(CYAN)
    c.setFont(FONT_B, 10)
    c.drawString(0.95 * inch, 2.3 * inch, "ONE-LINE REPRODUCTION")
    c.setFillColor(WHITE)
    c.setFont(FONT, 13)
    c.drawString(0.95 * inch, 1.9 * inch, "export SHOPPILOT_DENSE=hash;  python3 -m evaluator.local_evaluator")
    c.setFillColor(MUTED)
    c.setFont(FONT, 11)
    c.drawString(0.95 * inch, 1.65 * inch, "github.com/algorathem/techjam2026-shopping-copilot")

    c.setFillColor(WHITE)
    c.setFont(FONT_B, 14)
    c.drawString(0.7 * inch, 1.05 * inch, "Thank you — we welcome your questions.")
    footer(c, 9, "TikTok TechJam 2026 Track 4")


def main() -> None:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    c = canvas.Canvas(str(OUT), pagesize=(W, H))
    c.setTitle("ShopPilot — TikTok TechJam 2026 Pitch Deck")
    c.setAuthor("ShopPilot")
    builders = [
        slide_01, slide_02, slide_03, slide_04, slide_05,
        slide_06, slide_07, slide_08, slide_09,
    ]
    for i, fn in enumerate(builders):
        fn(c)
        c.showPage()
    c.save()
    print(f"WROTE {OUT} ({OUT.stat().st_size} bytes) pages={TOTAL}")

    # convenience copies
    dl = Path.home() / "Downloads" / "ShopPilot_Pitch_Deck.pdf"
    try:
        dl.write_bytes(OUT.read_bytes())
        print(f"WROTE {dl}")
    except Exception as e:
        print(f"Downloads copy skipped: {e}")

    # also replace the badly named pulled PDF with a pointer note? keep both.
    # Write a short README next to it
    note = ROOT / "docs" / "PITCH_DECK_README.md"
    note.write_text(
        f"""# ShopPilot Pitch Deck (PDF)

**Canonical 9-slide PDF:** `docs/ShopPilot_Pitch_Deck.pdf`  
**Rebuild:** `python3 scripts/build_pitch_pdf.py`  
**Outline source:** finalized 9-slide systems-engineering deck (TechJam 2026 Track 4)

## Design system (Astrid brand — same as PPTX)
- BG `#0A121F` · Cyan `#00D4FF` · Rose `#FF2D8F` · Violet `#A855F7` · Muted `#8B9BB4` · Gold `#FBBF24`

## Slides
1. Title & executive scoreboard  
2. Problem — four failure modes + objective function  
3. Solution — five subsystems  
4. Architecture — state invariance & override hygiene  
5. Public benchmark table + early-termination paradox  
6. Scenario breakdown  
7. Astrid CLI live traces  
8. Commercial impact  
9. Conclusion & reproducibility  

Related PPTX (10-slide extended): `docs/ShopPilot_Demo_Slides.pptx`
""",
        encoding="utf-8",
    )
    print(f"WROTE {note}")


if __name__ == "__main__":
    main()

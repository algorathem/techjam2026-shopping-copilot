#!/usr/bin/env python3
"""Literature-grounded architecture concept diagrams (Astrid brand).

Redraws classical CRS/DST/CQ/IR pipelines — does NOT paste paper PDF figures.
Cites arXiv / classic lines in captions only.

Outputs:
  docs/architecture_literature.png   — multi-panel concept board for slides
  docs/architecture_literature.md    — paper → ShopPilot module map

Usage:
  python3 scripts/render_architecture_literature.py
"""
from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
OUT_PNG = ROOT / "docs" / "architecture_literature.png"
OUT_MD = ROOT / "docs" / "architecture_literature.md"

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
MUTED = (139, 155, 180)
MUTED2 = (100, 116, 139)
LINE = (42, 58, 85)
ROSE_DIM = (50, 22, 40)


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


def rr(d, box, fill=CARD, outline=None, width=2, radius=14):
    d.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=width)


def arrow(d, a, b, col=MUTED2, w=3):
    import math

    x1, y1 = a
    x2, y2 = b
    d.line([a, b], fill=col, width=w)
    ang = math.atan2(y2 - y1, x2 - x1)
    for off in (2.5, -2.5):
        d.line(
            [b, (x2 + 12 * math.cos(ang + off), y2 + 12 * math.sin(ang + off))],
            fill=col,
            width=w,
        )


def box(d, x, y, w, h, title, sub, col, title_size=15):
    rr(d, (x, y, x + w, y + h), CARD, col, 2, 12)
    d.rectangle((x, y, x + w, y + 5), fill=col)
    t(d, (x + w / 2, y + h / 2 - (8 if sub else 0)), title, title_size, WHITE, True, "mm")
    if sub:
        t(d, (x + w / 2, y + h / 2 + 14), sub, 12, MUTED, False, "mm")


def panel_label(d, x, y, text, col):
    t(d, (x, y), text.upper(), 12, col, True, "lt")


def render_png() -> Path:
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)
    d.ellipse((1500, -200, 2100, 400), fill=(26, 11, 36))
    d.ellipse((-150, 800, 400, 1200), fill=(12, 36, 48))

    # header
    t(d, (48, 28), "SHOPPILOT  ·  ARCHITECTURE IN THE LITERATURE", 12, PINK, True, "lt")
    t(d, (48, 52), "Classical CRS / DST / CQ concepts  →  our modules (redrawn, not paper screenshots)", 26, WHITE, True, "lt")
    t(
        d,
        (48, 90),
        "Cites structure from Qulac · Bayesian CRS · multi-domain DST · corpus-informed CQs · hybrid IR  ·  ablations on this kit",
        14,
        MUTED,
        False,
        "lt",
    )

    # ── PANEL A: Classical CRS pipeline (left) ───────────────────────────
    panel_label(d, 48, 125, "A  ·  classical task-oriented / CRS pipeline", CYAN)
    rr(d, (40, 145, 940, 430), CARD2, LINE, 1, 16)
    stages = [
        (60, "User turn", "utterance", CYAN),
        (230, "NLU", "intents + slots", GOOD),
        (400, "DST", "belief state", VIOLET),
        (570, "Policy", "ask or recommend", GOLD),
        (740, "NLG / IR", "response + items", PINK),
    ]
    for x, title, sub, col in stages:
        box(d, x, 200, 150, 90, title, sub, col, 14)
    for x in (210, 380, 550, 720):
        arrow(d, (x, 245), (x + 18, 245), MUTED, 3)
    # loop
    d.line([(815, 290), (815, 360), (135, 360), (135, 290)], fill=CYAN, width=3)
    arrow(d, (135, 300), (135, 290), CYAN, 3)
    t(d, (490, 385), "next turn  (dialogue loop)", 13, CYAN, True, "mm")
    t(d, (60, 410), "Refs: task-oriented dialog / CRS stack  ·  ShopPilot follows same spine under kit constraints", 12, MUTED, False, "lt")

    # ── PANEL B: DST concept (right top) ─────────────────────────────────
    panel_label(d, 980, 125, "B  ·  dialog state tracking (DST)", VIOLET)
    rr(d, (970, 145, 1880, 430), CARD2, LINE, 1, 16)
    box(d, 1000, 185, 200, 100, "Utterance t", "text", CYAN, 14)
    box(d, 1280, 185, 280, 100, "State update", "slots · sources · wipe", GOOD, 14)
    box(d, 1640, 185, 200, 100, "State t", "belief / slots", VIOLET, 14)
    arrow(d, (1200, 235), (1280, 235), MUTED, 3)
    arrow(d, (1560, 235), (1640, 235), MUTED, 3)
    # state contents
    rr(d, (1000, 310, 1860, 400), CARD, GOOD, 2, 10)
    t(d, (1430, 335), "ShopPilot SessionState  =  compact rule-based DST", 15, GOOD, True, "mm")
    t(
        d,
        (1430, 365),
        "constraints[soft|disclosed|override]  ·  filled/asked/dont_care  ·  family · audience  ·  query cursor",
        13,
        WHITE,
        False,
        "mm",
    )
    t(d, (1000, 412), "Refs: scalable multi-domain DST (candidate values) arXiv:1712.10224  ·  we fill values, not new ask enums", 12, MUTED, False, "lt")

    # ── PANEL C: CQ / ask policy ─────────────────────────────────────────
    panel_label(d, 48, 450, "C  ·  clarifying questions: theory vs kit reality", GOLD)
    rr(d, (40, 470, 940, 780), CARD2, LINE, 1, 16)

    # two columns: theory max-IG vs ship other-first
    rr(d, (60, 500, 480, 700), ROSE_DIM, PINK, 2, 12)
    t(d, (270, 525), "Theory path (ablated)", 15, PINK, True, "mm")
    t(d, (270, 560), "max E[IG] / min H(posterior)", 13, WHITE, True, "mm")
    t(d, (270, 595), "Bayesian CRS · pool entropy", 12, MUTED, False, "mm")
    t(d, (270, 630), "brand/store splits look high-IG", 12, MUTED, False, "mm")
    t(d, (270, 665), "on THIS kit  →  Tech ~0.72  REJECT", 14, PINK, True, "mm")

    rr(d, (500, 500, 920, 700), CARD, GOOD, 2, 12)
    t(d, (710, 525), "ShopPilot ship path", 15, GOOD, True, "mm")
    t(d, (710, 560), "other-first  +  static ladder", 13, WHITE, True, "mm")
    t(d, (710, 595), "skip filled / dont_care", 12, MUTED, False, "mm")
    t(d, (710, 630), "corpus facets in MESSAGE only", 12, MUTED, False, "mm")
    t(d, (710, 665), "protocol-aligned CQ  ·  Tech ~0.91", 14, GOOD, True, "mm")

    t(d, (60, 730), "Refs: Qulac CQs (SIGIR)  ·  Bayesian CRS IG  ·  corpus-informed CQs arXiv:2409.18575  ·  PE funnel arXiv:2510.12015", 11, MUTED, False, "lt")
    t(d, (60, 755), "Borrow structure; do not reimplement learned CQ generators on closed ask_attribute enum", 11, MUTED2, False, "lt")

    # ── PANEL D: Hybrid IR ───────────────────────────────────────────────
    panel_label(d, 980, 450, "D  ·  hybrid retrieval + rank (IR lineage)", CYAN)
    rr(d, (970, 470, 1880, 780), CARD2, LINE, 1, 16)

    box(d, 1000, 510, 180, 80, "Query", "from state", CYAN, 14)
    box(d, 1240, 500, 200, 100, "FTS5 BM25", "OR + AND lanes", VIOLET, 14)
    box(d, 1500, 500, 200, 100, "Dense", "hash n-gram / MiniLM", VIOLET, 14)
    box(d, 1760, 510, 100, 80, "U", "fuse", GOLD, 14)
    arrow(d, (1180, 550), (1240, 550), MUTED, 3)
    arrow(d, (1180, 550), (1500, 540), MUTED, 2)
    arrow(d, (1440, 550), (1760, 550), MUTED, 3)
    arrow(d, (1700, 550), (1760, 550), MUTED, 3)

    box(d, 1100, 640, 280, 80, "Coverage rank", "constraints · family", GOOD, 14)
    box(d, 1450, 640, 280, 80, "Precision gate", "early Top-1 / MRR", PINK, 14)
    arrow(d, (1810, 590), (1240, 640), MUTED, 2)
    arrow(d, (1380, 680), (1450, 680), MUTED, 3)

    t(d, (1000, 745), "Refs: classic BM25 lexical IR  ·  dense dual-encoder recall  ·  late fusion  ·  MRR-sensitive early stopping (eval design)", 11, MUTED, False, "lt")

    # ── PANEL E: mapping strip ───────────────────────────────────────────
    panel_label(d, 48, 800, "E  ·  paper concept  →  ShopPilot module (one glance)", PINK)
    rr(d, (40, 820, 1880, 1045), CARD, LINE, 1, 14)

    rows = [
        ("Qulac / CRS CQs", "pair Top-K + one ask every turn; early precision via good questions", CYAN),
        ("Bayesian max-IG [theory]", "implemented then REJECTED on public set (fake entropy / brand trap)", PINK),
        ("Multi-domain DST", "SessionState provenance slots; soft-only override wipe", VIOLET),
        ("Corpus-informed CQs", "facet chips in message from live pool — not free-form ask enums", GOLD),
        ("Hybrid IR", "FTS5 + dense hash late fusion; constraint-coverage rerank", GOOD),
        ("Turn efficiency / fatigue", "MTTC term in TechnicalScore; ≤10-turn horizon", MUTED),
    ]
    for i, (left, right, col) in enumerate(rows):
        y = 845 + i * 32
        d.ellipse((60, y + 4, 72, y + 16), fill=col)
        t(d, (90, y), left, 13, col, True, "lt")
        t(d, (420, y), "→", 13, MUTED2, False, "lt")
        t(d, (460, y), right, 13, WHITE, False, "lt")

    OUT_PNG.parent.mkdir(parents=True, exist_ok=True)
    img.save(OUT_PNG, "PNG", optimize=True)
    print(f"WROTE {OUT_PNG} ({OUT_PNG.stat().st_size} bytes)")
    return OUT_PNG


def write_md() -> Path:
    md = """# Architecture in the literature

ShopPilot is **not** a reimplementation of any single paper. It is an offline,
enum-constrained retrieve-and-ask agent that borrows **problem structure** from
CRS / DST / CQ / hybrid IR work and validates choices with public-set ablations.

**Rule:** cite papers in captions and tables; **redraw** concept diagrams —
never paste paper PDF figures (ToS / clarity / brand).

Asset: `docs/architecture_literature.png` · rebuild
`python3 scripts/render_architecture_literature.py`

---

## Classical pipeline (what we inherit)

```
User utterance
  → NLU / slot fill          (ingest)
  → Dialog State Tracking   (SessionState)
  → Dialog policy           (ask vs recommend)
  → Retrieval + rank        (hybrid IR)
  → Response                (message + ask_attribute + Top-10)
  ↺ next turn
```

This is the standard task-oriented / conversational recommendation spine
(NLU → DST → policy → NLG/IR), not a free-form chatbot.

---

## Paper → module map

| Literature concept | Canonical refs (entry points) | ShopPilot module | What we took | What we did **not** do |
|---|---|---|---|---|
| Clarifying questions improve early precision | Qulac (SIGIR; arXiv:1907.06554); CRS “learn to ask” surveys | Always Top-10 **and** one `ask_attribute` | Pair ask + recommend every turn | Free-form CQ generation |
| Funnel / coarse→fine PE | LLM preference elicitation funnels (arXiv:2510.12015) | `other` first, then static facet ladder | Broad dump then finer slots | Trained PE LLM |
| Max information-gain / min entropy ask | Bayesian CRS IG formulations | `_next_ask` ablation | Implemented max-IG over pool | **Rejected** — Tech ~0.72 (brand entropy trap) |
| Corpus-grounded questions | Corpus-informed CQ / RAG-CQ (arXiv:2409.18575) | Facet chips in `message` from live pool | Only ask/support what catalog supports | Generator that invents intents |
| User fatigue / turn budget | Empirical CQ user studies (e.g. arXiv:2008.00279) | MTTC in TechnicalScore; ≤10 turns | Efficiency as first-class objective | Unlimited chit-chat |
| Dialog state tracking | Multi-domain DST (arXiv:1712.10224); classic DST | `SessionState` + provenance | Slot–value memory across turns | Adding new ask enum names |
| Intent + slots joint NLU | Intent–slot models (various) | `_ingest`: buy/browse, family, audience, constraints | Lightweight rule NLU | End-to-end neural NLU default |
| Soft vs hard constraints / override | Task-oriented state update practice | soft / disclosed / override sources; soft-only wipe | Provenance-aware invalidation | Clear-all on every pivot |
| Lexical retrieval | BM25 / FTS | SQLite FTS5 OR+AND | Strong baseline lane | External search cluster |
| Dense retrieval + late fusion | Dual-encoder dense IR | hash n-gram (default) / MiniLM opt-in | Paraphrase recall | Required GPU / always-on VDB |
| Ranking metrics | IR evaluation (MRR, Hit@K) | Official Hit@10 · MRR · MTTC | Precision gating for MRR | Optimize MTTC alone |

---

## Diagram key (panels in the PNG)

| Panel | Concept | ShopPilot read-out |
|---|---|---|
| **A** | Classical CRS pipeline | Our hot path is the same spine |
| **B** | DST belief update | `SessionState` is rule-based DST with sources |
| **C** | CQ theory vs kit | max-IG rejected; other-first shipped |
| **D** | Hybrid IR | FTS5 + dense → coverage rank → precision gate |
| **E** | One-line map | Six paper ideas → six implementation choices |

---

## Honest positioning (for judges / slides)

1. **Structure from literature, parameters from the kit.**  
   CQ + DST + hybrid IR is decades of work; the closed `ask_attribute` enum and
   simulator oracle are TechJam-specific.

2. **Negative result is a contribution.**  
   Textbook max-IG ask selection failed here (~0.72 Tech). That is expected when
   high-entropy catalog facets ≠ protocol-revealed attributes (“fake entropy”).

3. **Corpus grounding without a CQ model.**  
   We approximate corpus-informed CQs via enum + pool facet wording, not a
   learned generator (arXiv:2409.18575 spirit).

4. **DST without new slots.**  
   arXiv:1712.10224 is about large/dynamic *values*, not inventing new ask
   names. Values stay free-text; names stay the organizer enum.

5. **Offline default.**  
   Optional LLM NLU/rerank is a dashed sidecar; score path is deterministic
   hybrid IR + rules.

---

## Suggested spoken line (architecture slide)

> ShopPilot follows the classical conversational recommendation stack —
> NLU, dialog state, ask policy, hybrid retrieve-and-rank —
> grounded in clarifying-question and DST literature.
> We tried maximum information-gain question selection from Bayesian CRS
> and rejected it on this simulator. What shipped is an other-first,
> protocol-aligned ladder with corpus-grounded message facets and a
> soft-only override DST.

---

## Rebuild / embed

```bash
python3 scripts/render_architecture_literature.py
python3 scripts/build_pitch_pdf.py      # slide 4 uses the board
python3 scripts/build_demo_slides.py    # optional pptx literature slide
```
"""
    OUT_MD.write_text(md, encoding="utf-8")
    print(f"WROTE {OUT_MD}")
    return OUT_MD


def main() -> None:
    render_png()
    write_md()


if __name__ == "__main__":
    main()

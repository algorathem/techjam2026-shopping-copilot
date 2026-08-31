#!/usr/bin/env python3
"""Compile ShopPilot system deep-dive notes into a study PDF."""
from __future__ import annotations

from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    Image,
    KeepTogether,
    ListFlowable,
    ListItem,
    PageBreak,
    Paragraph,
    Preformatted,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "ShopPilot_System_Deep_Dive.pdf"
ARCH_PNG = ROOT / "docs" / "architecture_diagram.png"

# palette
TEAL = colors.HexColor("#0d9488")
SLATE = colors.HexColor("#0f172a")
MUTED = colors.HexColor("#475569")
LIGHT = colors.HexColor("#f1f5f9")
BORDER = colors.HexColor("#cbd5e1")
WHITE = colors.white


def styles():
    base = getSampleStyleSheet()
    s = {
        "cover_title": ParagraphStyle(
            "cover_title",
            parent=base["Title"],
            fontSize=28,
            textColor=SLATE,
            spaceAfter=8,
            alignment=TA_CENTER,
            fontName="Helvetica-Bold",
        ),
        "cover_sub": ParagraphStyle(
            "cover_sub",
            parent=base["Normal"],
            fontSize=12,
            textColor=MUTED,
            alignment=TA_CENTER,
            spaceAfter=6,
            leading=16,
        ),
        "h1": ParagraphStyle(
            "h1",
            parent=base["Heading1"],
            fontSize=16,
            textColor=TEAL,
            spaceBefore=16,
            spaceAfter=8,
            fontName="Helvetica-Bold",
        ),
        "h2": ParagraphStyle(
            "h2",
            parent=base["Heading2"],
            fontSize=12,
            textColor=SLATE,
            spaceBefore=12,
            spaceAfter=6,
            fontName="Helvetica-Bold",
        ),
        "h3": ParagraphStyle(
            "h3",
            parent=base["Heading3"],
            fontSize=11,
            textColor=MUTED,
            spaceBefore=8,
            spaceAfter=4,
            fontName="Helvetica-Bold",
        ),
        "body": ParagraphStyle(
            "body",
            parent=base["Normal"],
            fontSize=9.5,
            textColor=SLATE,
            leading=13,
            alignment=TA_JUSTIFY,
            spaceAfter=6,
        ),
        "bullet": ParagraphStyle(
            "bullet",
            parent=base["Normal"],
            fontSize=9.5,
            textColor=SLATE,
            leading=12,
            leftIndent=4,
            spaceAfter=2,
        ),
        "code": ParagraphStyle(
            "code",
            parent=base["Code"],
            fontSize=7.5,
            leading=10,
            textColor=SLATE,
            backColor=LIGHT,
            fontName="Courier",
            spaceBefore=4,
            spaceAfter=8,
        ),
        "caption": ParagraphStyle(
            "caption",
            parent=base["Normal"],
            fontSize=8,
            textColor=MUTED,
            alignment=TA_CENTER,
            spaceBefore=4,
            spaceAfter=10,
        ),
        "footer": ParagraphStyle(
            "footer",
            parent=base["Normal"],
            fontSize=8,
            textColor=MUTED,
            alignment=TA_CENTER,
        ),
        "callout": ParagraphStyle(
            "callout",
            parent=base["Normal"],
            fontSize=9.5,
            textColor=SLATE,
            leading=13,
            backColor=LIGHT,
            borderPadding=6,
            spaceBefore=6,
            spaceAfter=8,
        ),
    }
    return s


def p(style, text):
    return Paragraph(text.replace("\n", "<br/>"), style)


def bullets(style, items):
    flow = []
    for it in items:
        flow.append(ListItem(Paragraph(it, style), leftIndent=12, value="•"))
    return ListFlowable(flow, bulletType="bullet", start="•", leftIndent=15, spaceBefore=2, spaceAfter=6)


def table(data, col_widths=None):
    # wrap cells
    wrapped = []
    cell = ParagraphStyle(
        "cell",
        fontName="Helvetica",
        fontSize=8,
        leading=10,
        textColor=SLATE,
    )
    head = ParagraphStyle(
        "head",
        fontName="Helvetica-Bold",
        fontSize=8,
        leading=10,
        textColor=WHITE,
    )
    for r, row in enumerate(data):
        wrapped.append(
            [Paragraph(str(c), head if r == 0 else cell) for c in row]
        )
    t = Table(wrapped, colWidths=col_widths, repeatRows=1)
    t.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), TEAL),
                ("TEXTCOLOR", (0, 0), (-1, 0), WHITE),
                ("BACKGROUND", (0, 1), (-1, -1), WHITE),
                ("GRID", (0, 0), (-1, -1), 0.4, BORDER),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 5),
                ("RIGHTPADDING", (0, 0), (-1, -1), 5),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [WHITE, LIGHT]),
            ]
        )
    )
    return t


def code_block(text):
    return Preformatted(text.strip("\n"), styles()["code"])


def footer(canvas, doc):
    canvas.saveState()
    canvas.setStrokeColor(BORDER)
    canvas.line(0.75 * inch, 0.6 * inch, letter[0] - 0.75 * inch, 0.6 * inch)
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(MUTED)
    canvas.drawString(0.75 * inch, 0.4 * inch, "ShopPilot — System Deep Dive")
    canvas.drawRightString(
        letter[0] - 0.75 * inch, 0.4 * inch, f"page {doc.page}"
    )
    canvas.restoreState()


def build():
    S = styles()
    story = []

    # -------- COVER --------
    story.append(Spacer(1, 1.6 * inch))
    story.append(p(S["cover_title"], "ShopPilot"))
    story.append(
        p(
            S["cover_sub"],
            "System Deep Dive — Architecture, Execution, Algorithms &amp; Trade-offs",
        )
    )
    story.append(Spacer(1, 0.25 * inch))
    story.append(
        p(
            S["cover_sub"],
            "TechJam 2026 · Track 4 · Conversational Shopping Agent<br/>"
            "Demo UI: Astrid CLI · Offline-first multi-turn shopping copilot",
        )
    )
    story.append(Spacer(1, 0.4 * inch))
    story.append(
        table(
            [
                ["Metric (public 200, hash)", "Value"],
                ["TechnicalScore", "~0.794"],
                ["Hit@10", "0.935"],
                ["MRR", "~0.558"],
                ["MTTC", "~3.03"],
                ["vs weak BM25 starter Tech", "~0.11 → ~0.794"],
                ["Default path tokens / network", "0 / offline"],
            ],
            col_widths=[3.6 * inch, 2.2 * inch],
        )
    )
    story.append(Spacer(1, 0.5 * inch))
    story.append(
        p(
            S["cover_sub"],
            "Compiled from implementation notes for study.<br/>"
            "Repo: github.com/algorathem/techjam2026-shopping-copilot",
        )
    )
    story.append(PageBreak())

    # -------- TOC-ish overview --------
    story.append(p(S["h1"], "1. What this system is"))
    story.append(
        p(
            S["body"],
            "ShopPilot is a <b>headless, offline-first multi-turn shopping agent</b> over a frozen "
            "Amazon Clothing/Shoes/Jewelry catalog (~50k products). Each turn takes natural language, "
            "updates a compact dialogue state, hybrid-retrieves candidates, ranks them, and returns "
            "<b>Top-10 parent_asin</b> plus <b>exactly one</b> structured <b>ask_attribute</b> "
            "(or null). The official evaluator scores Hit@10, MRR, and MTTC into TechnicalScore.",
        )
    )
    story.append(
        p(
            S["body"],
            "It is <b>not</b> a chatbot UI product, not a required-LLM stack, and not a full neural DST. "
            "The demo face is the <b>Astrid</b> colored CLI; the project/metrics name is <b>ShopPilot</b>.",
        )
    )
    story.append(p(S["h2"], "Problem the kit poses"))
    story.append(
        bullets(
            S["bullet"],
            [
                "Vague multi-turn shoppers (browse, refine, override) vs one-shot keyword search",
                "Ambiguity: dress vs dress shoes; for my son vs women’s items",
                "≤10 turns or the session fails / MTTC hurts",
                "Must emit protocol-legal ask_attribute enum only",
                "Success = rank the <b>hidden target ASIN</b>, not “sound helpful”",
            ],
        )
    )
    story.append(p(S["h2"], "Solution in one line"))
    story.append(
        p(
            S["callout"],
            "Messy multi-turn language → <b>SessionState</b> + hybrid FTS/dense retrieve + "
            "linear constraint rank + protocol-static clarify → right ASIN in fewer turns, offline.",
        )
    )

    # -------- ARCHITECTURE --------
    story.append(p(S["h1"], "2. Architecture (multi-turn, not one-shot)"))
    story.append(
        p(
            S["body"],
            "Every user turn runs on <b>accumulated past state plus the new utterance</b>. "
            "Weak BM25 starter mostly uses tokens from the current message only. "
            "ShopPilot is DST-style state-update: retrieve and ask read the full SessionState.",
        )
    )
    if ARCH_PNG.exists():
        img = Image(str(ARCH_PNG), width=7.0 * inch, height=7.0 * inch * (1000 / 1600))
        story.append(img)
        story.append(
            p(
                S["caption"],
                "Figure: shape-coded architecture — stadium=I/O, hexagon=NLU, parallelogram=retrieve, "
                "diamond=ask, document=SessionState, cylinder=indexes, dashed rose=optional LLM.",
            )
        )
    story.append(p(S["h2"], "Shape key"))
    story.append(
        table(
            [
                ["Shape", "Aspect"],
                ["Stadium (pill)", "Turn I/O — user / response / CLI"],
                ["Hexagon", "NLU / ingest (parse, override, family, audience)"],
                ["Parallelogram", "Hybrid retrieve (FTS ∪ dense; query ← state)"],
                ["Rounded rect", "Linear rank / Dense / LLM / evaluator"],
                ["Diamond", "Ask decision (other→ladder; max-IG rejected)"],
                ["Document", "SessionState (mutable multi-turn memory)"],
                ["Cylinder", "Stores — FTS5, profile"],
                ["Dashed rose zone", "Optional LLM (fail-open, off by default)"],
            ],
            col_widths=[2.0 * inch, 4.5 * inch],
        )
    )
    story.append(p(S["h2"], "Per-turn loop"))
    story.append(
        code_block(
            """
respond(session_id, user_message, turn, top_k)
  1. Load SessionState for session_id          # PAST state
  2. messages.append(user_message)
  3. _ingest → write slots/family/audience/override
  4. _maybe_llm_slots (optional; usually no-op)
  5. _retrieve → FTS + dense + _score         # query FROM full state
  6. _next_ask → one ask_attribute | null
  7. _compose_message
  8. return {message, ask_attribute, recommendations, usage}
next turn (same session_id) reuses updated state until reset / turn 10
"""
        )
    )
    story.append(
        p(
            S["body"],
            '<b>Example:</b> t1 “dress” → t2 “plus size” → t3 “black” ranks with '
            "<b>dress + plus + black</b>, not “black” alone.",
        )
    )

    # -------- PRIMITIVES --------
    story.append(p(S["h1"], "3. Core primitives"))
    story.append(
        table(
            [
                ["Primitive", "Where", "Meaning"],
                [
                    "SessionState",
                    "starter/agent.py",
                    "Compact DST: slots, sources, family, audience, history slice, override flags",
                ],
                [
                    "Agent",
                    "starter/agent.py",
                    "Owns catalog index + sessions; public API reset / respond only",
                ],
                [
                    "Product + FTS",
                    "Agent._products + sqlite FTS5",
                    "Catalog atom: parent_asin → text/facets/price; inverted index",
                ],
                [
                    "DenseIndex",
                    "starter/dense.py",
                    "Semantic recall: hash 512-d n-grams or MiniLM (opt-in)",
                ],
                [
                    "Turn response",
                    "respond() return dict",
                    "Protocol atom: message + one ask_attribute + Top-K ASINs",
                ],
            ],
            col_widths=[1.3 * inch, 1.6 * inch, 3.6 * inch],
        )
    )
    story.append(p(S["h2"], "SessionState fields (domain memory)"))
    story.append(
        bullets(
            S["bullet"],
            [
                "<b>constraints</b> + <b>constraint_sources</b> (soft | disclosed | override)",
                "<b>filled</b> / <b>dont_care</b> / <b>asked</b> — slot machine for clarify policy",
                "<b>category</b>, <b>product_family</b>, <b>audience</b> (family/audience are internal, not kit asks)",
                "<b>messages</b>, <b>query_message_start</b>, <b>discarded_terms</b> — history window after override",
                "<b>profile</b> — long-term prior from reset; <b>browsing</b>, token counters",
            ],
        )
    )
    story.append(p(S["h2"], "Lifecycle &amp; mutation"))
    story.append(
        table(
            [
                ["Primitive", "Init", "Who mutates", "Persist / GC"],
                [
                    "SessionState",
                    "Agent.reset(session_id, profile)",
                    "respond → _ingest, ask append, optional LLM",
                    "RAM only; reset overwrites; process exit drops",
                ],
                [
                    "Agent / catalog",
                    "Agent(catalog_path) once",
                    "Load only; catalog file never written",
                    "In-mem FTS + dense die with process",
                ],
                [
                    "DenseIndex",
                    "DenseIndex.build at Agent init",
                    "Read-only at query time",
                    "Optional MiniLM .npz cache under data/",
                ],
                [
                    "Turn response",
                    "End of each respond",
                    "Ephemeral; CLI may display-enrich titles",
                    "GC after caller; metrics may hit results.json",
                ],
            ],
            col_widths=[1.2 * inch, 1.7 * inch, 1.8 * inch, 1.8 * inch],
        )
    )

    # -------- LIFECYCLE TRACE --------
    story.append(PageBreak())
    story.append(p(S["h1"], "4. Exact execution lifecycle of one turn"))
    story.append(
        p(
            S["body"],
            "Primary operation: <b>Agent.respond(session_id, user_message, turn, top_k)</b>. "
            "Entry surfaces: <b>cli_chat.py</b> (Astrid demo) or <b>evaluator/local_evaluator.py</b> "
            "(official score). Same agent API.",
        )
    )
    story.append(p(S["h2"], "File-by-file order"))
    story.append(
        table(
            [
                ["#", "File", "Symbol", "Role"],
                ["0", "cli_chat / local_evaluator", "main", "Args, env, construct Agent"],
                ["1", "starter/agent.py", "Agent.__init__", "Load catalog, FTS, dense"],
                ["2", "starter/agent.py", "Agent.reset", "New SessionState"],
                ["3", "starter/agent.py", "Agent.respond", "Turn entry"],
                ["4", "starter/agent.py", "Agent._ingest", "Rules NLU → write state"],
                ["5", "starter/llm_slots.py", "_maybe_llm_slots path", "Optional JSON NLU (off)"],
                ["6", "starter/agent.py", "Agent._retrieve", "FTS + dense + merge"],
                ["7", "starter/agent.py", "Agent._score", "Linear feature rank"],
                ["8", "starter/llm_rerank.py", "rerank", "Optional top-K reorder (off)"],
                ["9", "starter/agent.py", "Agent._next_ask", "one ask | null"],
                ["10", "starter/agent.py", "Agent._compose_message", "NL message"],
                ["11", "—", "return dict", "Exit to CLI or evaluator"],
            ],
            col_widths=[0.4 * inch, 1.7 * inch, 1.7 * inch, 2.7 * inch],
        )
    )
    story.append(p(S["h2"], "Payload transforms (boundaries)"))
    story.append(
        bullets(
            S["bullet"],
            [
                "<b>In:</b> session_id, user_message, turn, top_k",
                "<b>After ingest:</b> category/family/audience/constraints/filled updated; override may soft-wipe",
                "<b>After retrieve:</b> ranked list[(asin, score)] from FTS∪dense + _score (+ optional dense weight)",
                "<b>After next_ask:</b> ask_attribute ∈ kit enum or null; asked[] grows",
                "<b>Out:</b> {message, ask_attribute, recommendations[{parent_asin, score}], usage}",
            ],
        )
    )
    story.append(p(S["h2"], "Sync vs async"))
    story.append(
        p(
            S["body"],
            "The entire default path is <b>synchronous, in-process, blocking</b>. "
            "No threads, queues, or asyncio. Optional Gemini calls are still "
            "<b>sync HTTP inside respond</b> (timeout → fail-open to rules). "
            "There is no background job system.",
        )
    )

    # -------- ALGORITHMS --------
    story.append(p(S["h1"], "5. Algorithms &amp; techniques"))
    story.append(p(S["h2"], "5.1 Hybrid retrieval (late fusion)"))
    story.append(
        bullets(
            S["bullet"],
            [
                "<b>Sparse:</b> SQLite FTS5 — OR lane (high recall, ≤45 terms, LIMIT 220) + AND lane on top constraints (LIMIT 80); BM25 field weights title-heavy",
                "<b>Dense:</b> hash char 3-grams → 512-d signed buckets (default) or MiniLM embeddings (opt-in, cached)",
                "<b>Fusion:</b> final = lexical_score(...) + w_backend × cosine; w_hash=4.5, w_minilm=10",
                "Dense also pulls candidates FTS missed (top 80) and re-scores FTS set",
            ],
        )
    )
    story.append(p(S["h2"], "5.2 Linear constraint rerank (_score)"))
    story.append(
        bullets(
            S["bullet"],
            [
                "Phrase/title hits, token coverage of constraints",
                "Product family +6.5 hit / −8.0 miss (dress ≠ dress sandals)",
                "Audience +4.0 / −5.5 (for my son ≠ women’s) — demote, don’t hard-delete",
                "Profile tags + rating priors scaled by cold/warm/hot session specificity",
                "Soft budget distance; stars/n_ratings as tie-break",
            ],
        )
    )
    story.append(p(S["h2"], "5.3 Slot NLU (rules-first)"))
    story.append(
        bullets(
            S["bullet"],
            [
                "Regex: looking-for, what-matters-is, override phrases, no-preference",
                "expand_constraint_phrases → multi-slot fill in one freeform line",
                "classify_constraint → official slots; vibes→style; size cues (big enough)",
                "Latest-wins short soft color/material; plus↔petite size poles",
                "Kit disclosed feature sentences kept <b>whole</b> (atomizing them hurt Tech)",
            ],
        )
    )
    story.append(p(S["h2"], "5.4 Intent override (soft-only wipe)"))
    story.append(
        code_block(
            """
apply_override():
  drop constraints where source == "soft"
  keep disclosed / override facts
  clear asked, dont_care
  query_message_start = last message index
  discarded_terms ← tokens of dropped soft prefs  # block FTS leak
"""
        )
    )
    story.append(p(S["h2"], "5.5 Clarifying-question policy"))
    story.append(
        table(
            [
                ["Policy", "Status", "Notes"],
                ["other first (if open)", "SHIPPED", "Simulator can reveal ≤2 any-type constraints"],
                ["Static ASK_ORDER + skip filled/dont_care/asked", "SHIPPED", "Stable, protocol-fit"],
                ["Stop asks near turn ≥ 9", "SHIPPED", "Leave headroom before hard fail"],
                ["Pool max info-gain / entropy ask", "REJECTED", "Implemented but Tech ~0.72"],
                ["Coverage-gated pool swap", "OFF", "Code retained; not score path"],
            ],
            col_widths=[2.6 * inch, 1.1 * inch, 2.8 * inch],
        )
    )
    story.append(
        p(
            S["body"],
            "Facet entropy code remains for <b>message grounding</b> (corpus-grounded CQ spirit), "
            "not for choosing ask_attribute. Literature (Qulac, Bayesian IG, corpus CQ, DST) "
            "informs design; kit A/B decides what ships.",
        )
    )
    story.append(p(S["h2"], "5.6 Optional LLM sidecars"))
    story.append(
        table(
            [
                ["Mode", "Flag", "Role", "Default"],
                ["Slots NLU always", "SHOPPILOT_LLM_SLOTS=always", "JSON parse every turn", "off"],
                ["Slots NLU lowconf", "SHOPPILOT_LLM_SLOTS=lowconf", "Only if rule confidence low", "off"],
                ["Rerank", "SHOPPILOT_LLM_RERANK=1", "Reorder top-20 titles", "off"],
            ],
            col_widths=[1.6 * inch, 2.2 * inch, 2.0 * inch, 0.7 * inch],
        )
    )
    story.append(
        p(
            S["body"],
            "Needs SHOPPILOT_LLM=1 + API key. Timeouts fall back to rules. "
            "Measured Gemini rerank: tiny Tech bump (~+0.003), ~10× slower. "
            "Slot NLU often timed out here → same answers as rules. "
            "<b>Do not make LLM required for submit.</b>",
        )
    )

    # -------- OPTIMIZATIONS --------
    story.append(p(S["h1"], "6. Optimization tricks"))
    story.append(
        bullets(
            S["bullet"],
            [
                "Everything hot-path in RAM: sqlite :memory: FTS, product dict, dense matrix",
                "Catalog loaded once per process; turns don’t re-read JSONL",
                "FTS candidate caps (220/80) then Python score — not full 50k scan",
                "Hash dense 512×50k float32 ≈ 100MB; NumPy matmul cosine",
                "MiniLM embeddings cached compressed under data/",
                "Query term cap ~45; phrase early-continue in _score",
                "Stdlib-first path (dense=none without NumPy); optional deps only",
                "LLM timeouts caught — fail-open so hung API doesn’t kill the turn",
            ],
        )
    )
    story.append(
        p(
            S["body"],
            "Typical offline turn is usually well under 100ms locally. Optional LLM adds seconds.",
        )
    )

    # -------- TRADEOFFS --------
    story.append(p(S["h1"], "7. Explicit trade-offs"))
    story.append(
        table(
            [
                ["Choice", "Won", "Lost / cost"],
                [
                    "Static ask + other-first",
                    "Tech ~0.79; stable; protocol-fit",
                    "No adaptive “smart” questions",
                ],
                [
                    "Max-IG asks",
                    "Theory-pretty",
                    "Tech ~0.72 — rejected",
                ],
                [
                    "Hash hybrid dense",
                    "+Hit/MRR, offline",
                    "~100MB RAM; NumPy soft-dep",
                ],
                [
                    "Rules NLU + tiny lexicons",
                    "Controllable, kit-safe",
                    "Miss open slang without LLM",
                ],
                [
                    "Soft demote (family/audience)",
                    "Fewer false negatives",
                    "Some wrong items still lower-ranked",
                ],
                [
                    "Hard eliminate missing tokens",
                    "Aggressive filter",
                    "Killed true ASINs — rejected",
                ],
                [
                    "Offline default",
                    "Reproducible, feasible, 0 tokens",
                    "Weaker open-ended NLU than always-on LLM",
                ],
                [
                    "Append-only turns, no locks",
                    "Simple",
                    "Not idempotent; not multi-writer safe",
                ],
            ],
            col_widths=[2.0 * inch, 2.2 * inch, 2.3 * inch],
        )
    )
    story.append(
        p(
            S["callout"],
            "<b>Meta-objective:</b> public TechnicalScore under the frozen simulator beats "
            "abstract conversational-AI elegance. Measure → keep or reject.",
        )
    )

    # -------- INVARIANTS --------
    story.append(PageBreak())
    story.append(p(S["h1"], "8. System invariants"))
    story.append(p(S["h2"], "Protocol (organizer)"))
    story.append(
        bullets(
            S["bullet"],
            [
                "respond always returns message + ask_attribute + recommendations",
                "ask_attribute is one enum string or null — never a list; never invent gender",
                "Recommendations identified by parent_asin",
                "Useful work in ≤10 turns",
                "reset must precede respond",
            ],
        )
    )
    story.append(p(S["h2"], "Dialogue state"))
    story.append(
        bullets(
            S["bullet"],
            [
                "Ask field ⊆ official enum; family/audience stay internal",
                "Don’t re-ask filled ∪ dont_care ∪ asked (until override clears asked)",
                "Override wipes soft only; disclosed survives; discarded terms blocked in FTS",
                "Retrieve is state-first, not current-message-only",
                "Exclusive soft slots: latest-wins color/material; size poles",
            ],
        )
    )
    story.append(p(S["h2"], "Catalog / ranking / runtime"))
    story.append(
        bullets(
            S["bullet"],
            [
                "Catalog read-only; closed world of loaded ASINs",
                "Offline default; LLM fail-open",
                "Prefer demote over hard delete on sparse titles",
                "Single-threaded assumption; turn is fully sync",
                "respond is NOT idempotent if called twice with same text",
            ],
        )
    )

    # -------- SLOTS / DOMAIN --------
    story.append(p(S["h1"], "9. Slots, family, audience (who owns what)"))
    story.append(
        table(
            [
                ["Concept", "Owner", "Notes"],
                [
                    "ask_attribute enum",
                    "Organizer kit",
                    "category, material, color, size, style, brand, budget, feature, use_case, other, null",
                ],
                [
                    "ASK_ORDER / fill policy",
                    "ShopPilot",
                    "other-first then static ladder; skip filled",
                ],
                [
                    "product_family",
                    "ShopPilot (internal)",
                    "dress/footwear/… — fixes CSJ path ambiguity",
                ],
                [
                    "audience",
                    "ShopPilot (internal)",
                    "boys/men/… from gift phrases like for my son",
                ],
                [
                    "Vibe words (cool/cute/…)",
                    "ShopPilot",
                    "Map to style slot; soft FTS text",
                ],
            ],
            col_widths=[1.8 * inch, 1.5 * inch, 3.2 * inch],
        )
    )
    story.append(
        p(
            S["body"],
            "Judges score product findability (Hit/MRR/MTTC), not whether you invented internal "
            "taxonomies. Family/audience matter only if they raise metrics or demo quality.",
        )
    )

    # -------- OFFLINE FIRST --------
    story.append(p(S["h1"], "10. Why offline-first"))
    story.append(
        bullets(
            S["bullet"],
            [
                "Reliability: no timeout/rate-limit kills a scored session",
                "Feasibility: kit does not require paid LLM or vector DB",
                "Latency & cost: sub-second turns, zero tokens on default",
                "Privacy / merchant-owned brain: catalog + chat stay local",
                "Determinism: same inputs → same Tech for A/B",
                "Graceful upgrade: rules spine + optional MiniLM + optional Gemini",
            ],
        )
    )

    # -------- KEY FILES --------
    story.append(p(S["h1"], "11. Key files cheat sheet"))
    story.append(
        table(
            [
                ["Path", "Responsibility"],
                ["starter/agent.py", "Orchestrator: SessionState, ingest, retrieve, score, ask"],
                ["starter/dense.py", "Dense hash / MiniLM lane"],
                ["starter/rewrite.py", "Brief query string for optional rerank"],
                ["starter/llm_slots.py", "Optional dual-meaning slot NLU"],
                ["starter/llm_rerank.py", "Optional top-K LLM rerank"],
                ["cli_chat.py", "Astrid demo CLI"],
                ["evaluator/local_evaluator.py", "Official Hit/MRR/MTTC loop"],
                ["data/catalog.jsonl", "Frozen product corpus"],
                ["docs/architecture_diagram.png", "Shape-coded architecture figure"],
            ],
            col_widths=[2.4 * inch, 4.1 * inch],
        )
    )
    story.append(p(S["h2"], "Reproduce metrics"))
    story.append(
        code_block(
            """
cd techjam2026-shopping-copilot
export SHOPPILOT_DENSE=hash
unset SHOPPILOT_LLM SHOPPILOT_LLM_SLOTS SHOPPILOT_LLM_RERANK
python3 -m unittest tests.test_agent_slots tests.test_dense -q
python3 -m evaluator.local_evaluator
python3 cli_chat.py --dense hash
"""
        )
    )

    # -------- GLOSSARY --------
    story.append(p(S["h1"], "12. Glossary"))
    story.append(
        table(
            [
                ["Term", "Meaning here"],
                ["DST", "Dialogue state tracking — compact slots across turns"],
                ["FTS5", "SQLite full-text search (sparse BM25-like retrieve)"],
                ["Hybrid IR", "Sparse + dense recall, late score fusion"],
                ["Hit@10", "Target parent_asin in top 10 recommendations"],
                ["MRR", "Mean reciprocal rank of the target"],
                ["MTTC", "Mean turns to first correct hit (lower better)"],
                ["TechnicalScore", "0.5·Hit + 0.3·MRR + 0.2·Efficiency(MTTC)"],
                ["ask_attribute", "Single kit enum field requesting a slot (or null)"],
                ["other", "Catch-all ask; simulator may dump multiple constraints"],
                ["soft / disclosed", "Constraint provenance for override hygiene"],
                ["Fail-open LLM", "On API failure, keep rule-based state and continue"],
            ],
            col_widths=[1.5 * inch, 5.0 * inch],
        )
    )

    # -------- CLOSING --------
    story.append(p(S["h1"], "13. Mental model (memorize this)"))
    story.append(
        p(
            S["callout"],
            "One primary operation = synchronous <b>Agent.respond</b>: load multi-turn "
            "<b>SessionState</b>, rule-ingest (optional LLM enrich) the new utterance, "
            "hybrid-retrieve and score from the <b>full state</b>, pick <b>one</b> protocol "
            "ask_attribute, compose a message, return Top-K ASINs — no background workers, "
            "offline by default, optional LLM is a gated sidecar.",
        )
    )
    story.append(Spacer(1, 0.3 * inch))
    story.append(
        p(
            S["body"],
            "For judges: offline hybrid shopping agent that lifts kit Tech ~0.11 → ~0.794 "
            "with multi-turn state, override hygiene, and protocol-safe clarification — "
            "not a fine-tuned foundation model and not a required cloud API.",
        )
    )

    doc = SimpleDocTemplate(
        str(OUT),
        pagesize=letter,
        leftMargin=0.75 * inch,
        rightMargin=0.75 * inch,
        topMargin=0.7 * inch,
        bottomMargin=0.8 * inch,
        title="ShopPilot System Deep Dive",
        author="ShopPilot / TechJam 2026",
    )
    doc.build(story, onFirstPage=footer, onLaterPages=footer)
    print(f"WROTE {OUT}")
    print(f"pages≈ check; size={OUT.stat().st_size}")


if __name__ == "__main__":
    build()

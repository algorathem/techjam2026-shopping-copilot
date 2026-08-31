#!/usr/bin/env python3
"""Build ShopPilot demo video with TTS voiceover aligned to the Astrid deck.

Pipeline:
  1. Write per-slide narration scripts
  2. macOS `say` → AIFF → WAV (offline TTS; no API key)
  3. Render 10 Astrid-themed 1920×1080 frames (embeds architecture PNG on slide 5)
  4. ffmpeg: image + audio per slide → concat → docs/ShopPilot_Demo_Video.mp4

Usage:
  python3 scripts/build_demo_av.py
  SHOPPILOT_TTS_VOICE=Samantha python3 scripts/build_demo_av.py
  SHOPPILOT_TTS_RATE=175 python3 scripts/build_demo_av.py

Optional cloud TTS is NOT wired by default (no keys in repo).
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import wave
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
FRAMES = ROOT / "docs" / "demo_video_frames"
AUDIO = ROOT / "docs" / "demo_video_audio"
OUT_MP4 = ROOT / "docs" / "ShopPilot_Demo_Video.mp4"
OUT_WAV = ROOT / "docs" / "ShopPilot_Demo_Voiceover.wav"
ARCH_PNG = ROOT / "docs" / "architecture_diagram.png"
SCRIPT_MD = ROOT / "docs" / "DEMO_VIDEO_SCRIPT.md"

W, H = 1920, 1080

# Astrid palette
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

# Live metrics (match deck / results.json ballpark)
TECH, HIT, MRR, MTTC = "0.907", "0.975", "0.858", "2.88"
BASE_TECH, BASE_HIT, BASE_MTTC = "0.107", "0.125", "9.81"

# (slide_id, title, narration)
SEGMENTS: list[tuple[str, str, str]] = [
    (
        "01_title",
        "Title",
        "ShopPilot — an offline-first, multi-turn shopping copilot for TechJam twenty twenty-six, Track four. "
        "Demo U I is Astrid C L I. On the public two hundred session kit: Technical Score zero point nine zero seven, "
        "Hit at ten zero point nine seven five, mean turns about two point nine — with zero tokens on the default path.",
    ),
    (
        "02_problem",
        "Problem",
        "Keyword search breaks on real shopping intent. Shoppers are vague. "
        "Dress might mean a garment — or dress sandals. They change their mind mid-session. "
        "And the kit gives you at most ten turns to find a hidden Amazon parent A S I N.",
    ),
    (
        "03_solution",
        "Solution",
        "ShopPilot is a headless agent. Every turn returns three things: a message, one ask attribute, and a top ten of A S I Ns. "
        "Five steps: ingest, state, hybrid retrieve, clarify, and rank. No required L L M.",
    ),
    (
        "04_architecture",
        "Architecture",
        "Ingest is not just an intent router — it writes the full dialogue state: slots with sources, product family, audience, and soft overrides. "
        "Retrieve is hybrid: F T S five plus dense hash, in memory. "
        "Rank uses constraint coverage and light priors. Ask is other-first, then a static ladder that skips filled slots. "
        "Catalog stays immutable. Optional L L M is gated and off the score path.",
    ),
    (
        "05_architecture_detail",
        "Architecture detail",
        "Multi-turn means past Session State plus the current utterance — same session I D. "
        "When the shopper says black on turn three, we rank with dress, plus size, and black together — not black alone.",
    ),
    (
        "06_results",
        "Results",
        "Against the official weak B M twenty five starter: Technical Score from about zero point one one to zero point nine zero seven. "
        "Hit at ten from zero point one three to zero point nine eight. "
        "Mean turns from about nine point eight down to two point nine. Default path uses zero tokens.",
    ),
    (
        "07_scenarios",
        "By scenario",
        "Hit holds across buying, browsing, intent override, and boundary. "
        "Override costs more turns — as mind-change should — but still lands near Hit zero point nine seven.",
    ),
    (
        "08_demo",
        "Astrid CLI",
        "In Astrid C L I: shoes for my son locks footwear and boys, asks other, and shows top titles. "
        "Actually forget sneakers — dress shoes, size nine — fires soft-only override: soft prefs wipe, disclosed facts stay, family stays footwear. "
        "Dress sandals route to footwear — not garment dresses. Plus size fills size once — we do not re-ask it.",
    ),
    (
        "09_impact",
        "Impact",
        "Kit metrics map to merchant outcomes: Hit is findability, M R R is rank quality, mean turns is cost and cognitive load. "
        "Same decision core as conversational commerce — catalog-grounded, measurable, runnable offline.",
    ),
    (
        "10_end",
        "Thanks",
        "ShopPilot. Offline-first multi-turn shopping copilot. "
        "GitHub: github.com/algorathem/techjam2026-shopping-copilot. Thanks.",
    ),
]


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


def t(d, xy, s, size=28, fill=WHITE, bold=False, anchor="lt"):
    d.text(xy, s, font=font(size, bold), fill=fill, anchor=anchor)


def wrap(d, xy, s, size, fill, max_w, gap=10, bold=False):
    f = font(size, bold)
    words = s.split()
    lines, cur = [], ""
    for w in words:
        trial = (cur + " " + w).strip()
        if f.getlength(trial) <= max_w:
            cur = trial
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    x, y = xy
    for line in lines:
        d.text((x, y), line, font=f, fill=fill)
        y += size + gap
    return y


def rr(d, box, fill=CARD, outline=None, width=3, radius=18):
    d.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=width)


def rail(d):
    d.rectangle((0, 0, 16, H), fill=CYAN)
    d.rectangle((16, 0, 22, H), fill=PINK)


def footer(d, page: int, total: int = 10):
    d.rectangle((0, H - 48, W, H - 44), fill=LINE)
    t(d, (48, H - 28), "ShopPilot · TechJam 2026 Track 4", 18, MUTED2, False, "lm")
    t(d, (W - 48, H - 28), f"{page}/{total}", 18, MUTED2, False, "rm")


def new_canvas():
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)
    # soft blobs
    d.ellipse((1500, -180, 2100, 420), fill=(26, 11, 36))
    d.ellipse((-180, 780, 420, 1200), fill=(12, 36, 48))
    rail(d)
    return img, d


def slide_title() -> Image.Image:
    img, d = new_canvas()
    t(d, (80, 220), "TECHJAM 2026  ·  TRACK 4", 22, PINK, True)
    t(d, (80, 290), "Shop", 88, CYAN, True)
    # Pilot next to Shop
    bbox = font(88, True).getbbox("Shop")
    tw = bbox[2] - bbox[0]
    t(d, (80 + tw + 8, 290), "Pilot", 88, PINK, True)
    t(d, (80, 420), "Offline-first multi-turn shopping copilot", 36, WHITE)
    chips = [
        ("Hybrid FTS + dense", CYAN),
        ("Stateful DST", PINK),
        ("Clarify ≤10 turns", CYAN),
        (f"Tech {TECH}", PINK),
    ]
    for i, (lab, col) in enumerate(chips):
        x = 80 + i * 440
        rr(d, (x, 520, x + 410, 590), CARD, col, 2, 28)
        t(d, (x + 205, 555), lab, 22, WHITE, True, "mm")
    t(d, (80, 640), "Demo UI: Astrid CLI  ·  github.com/algorathem/techjam2026-shopping-copilot", 22, MUTED)
    t(d, (80, 690), f"Public 200  ·  Hit@10 {HIT}  ·  MTTC {MTTC}  ·  tokens 0", 22, MUTED2)
    footer(d, 1)
    return img


def slide_problem() -> Image.Image:
    img, d = new_canvas()
    t(d, (80, 50), "01  ·  PROBLEM", 18, PINK, True)
    t(d, (80, 95), "Keyword search breaks on real shopping intent", 40, WHITE, True)
    wrap(d, (80, 160), "Vague goals, dual-meaning SKUs, mid-session mind-change, hard ≤10-turn budget.", 24, MUTED, 1700)
    cards = [
        ("01", "Vague queries", '"something nice for summer"', CYAN),
        ("02", "Ambiguity", "dress vs dress shoes · for my son", PINK),
        ("03", "Mind-change", "intent override mid-session", VIOLET),
        ("04", "Turn budget", "miss after turn 10 → fail", GOLD),
    ]
    for i, (num, h, b, col) in enumerate(cards):
        x = 80 + i * 450
        rr(d, (x, 280, x + 420, 720), CARD, None, 0, 18)
        d.rectangle((x, 280, x + 420, 292), fill=col)
        t(d, (x + 30, 330), num, 20, col, True)
        t(d, (x + 30, 390), h, 28, WHITE, True)
        wrap(d, (x + 30, 460), b, 22, MUTED, 360)
    footer(d, 2)
    return img


def slide_solution() -> Image.Image:
    img, d = new_canvas()
    t(d, (80, 50), "02  ·  SOLUTION", 18, PINK, True)
    t(d, (80, 95), "Headless offline agent — one turn, three outputs", 38, WHITE, True)
    wrap(d, (80, 160), "message + one ask_attribute + Top-10 ASINs. No required LLM.", 24, MUTED, 1700)
    steps = [
        ("1", "Ingest", "slots · family · audience · override", CYAN),
        ("2", "State", "soft | disclosed | override sources", PINK),
        ("3", "Retrieve", "FTS5 OR/AND + dense hash", VIOLET),
        ("4", "Clarify", "other-first · skip filled · ≤10", GOLD),
        ("5", "Rank", "coverage · family · light priors", GOOD),
    ]
    for i, (n, h, b, col) in enumerate(steps):
        y = 240 + i * 120
        d.ellipse((90, y, 150, y + 60), fill=col)
        t(d, (120, y + 30), n, 24, BG, True, "mm")
        rr(d, (180, y - 10, 1840, y + 70), CARD, None, 0, 16)
        t(d, (210, y + 8), h, 28, WHITE, True)
        t(d, (520, y + 12), b, 24, MUTED)
    footer(d, 3)
    return img


def slide_architecture() -> Image.Image:
    img, d = new_canvas()
    t(d, (80, 50), "03  ·  ARCHITECTURE", 18, PINK, True)
    t(d, (80, 95), "Multi-turn loop — state is the product", 38, WHITE, True)
    wrap(d, (80, 155), "Past SessionState + current text → Top-10 + one ask. Catalog immutable. LLM optional / off.", 22, MUTED, 1700)
    steps = [
        ("1", "Ingest", "slots · family", CYAN),
        ("2", "Retrieve", "FTS + dense", VIOLET),
        ("3", "Rank", "coverage", GOOD),
        ("4", "Ask", "other-first", GOLD),
        ("5", "Respond", "msg+ask+Top10", PINK),
    ]
    for i, (n, h, b, col) in enumerate(steps):
        x = 80 + i * 360
        rr(d, (x, 240, x + 330, 430), CARD, col, 3, 18)
        d.ellipse((x + 20, 270, x + 70, 320), fill=col)
        t(d, (x + 45, 295), n, 22, BG, True, "mm")
        t(d, (x + 90, 280), h, 26, WHITE, True)
        t(d, (x + 30, 350), b, 20, MUTED)
        if i < 4:
            d.polygon([(x + 335, 325), (x + 350, 335), (x + 335, 345)], fill=MUTED2)
    panels = [
        ("SessionState · mutable", ["soft|disclosed|override", "family · audience", "soft-only wipe", "same session_id"], GOOD),
        ("Catalog · immutable", ["FTS5 BM25", "dense hash 512-d", "MiniLM opt-in", "50k CSJ freeze"], VIOLET),
        ("Optional LLM · gated", ["slots NLU", "rerank top-20", "fail-open", "not on score path"], PINK),
    ]
    for i, (title, lines, col) in enumerate(panels):
        x = 80 + i * 600
        rr(d, (x, 500, x + 560, 920), CARD, None, 0, 18)
        d.rectangle((x, 500, x + 14, 920), fill=col)
        t(d, (x + 40, 540), title, 24, col, True)
        for j, line in enumerate(lines):
            t(d, (x + 40, 610 + j * 55), "·  " + line, 22, WHITE)
    footer(d, 4)
    return img


def slide_architecture_detail() -> Image.Image:
    img, d = new_canvas()
    t(d, (80, 40), "04  ·  ARCHITECTURE DETAIL", 18, PINK, True)
    t(d, (80, 78), "End-to-end system diagram", 32, WHITE, True)
    if ARCH_PNG.exists():
        arch = Image.open(ARCH_PNG).convert("RGB")
        # fit into content box
        box = (40, 120, W - 40, H - 70)
        bw, bh = box[2] - box[0], box[3] - box[1]
        arch = arch.resize((bw, bh), Image.Resampling.LANCZOS)
        img.paste(arch, (box[0], box[1]))
    else:
        t(d, (80, 400), "Missing architecture_diagram.png — run render_architecture_png.py", 28, PINK)
    footer(d, 5)
    return img


def slide_results() -> Image.Image:
    img, d = new_canvas()
    t(d, (80, 50), "05  ·  RESULTS", 18, PINK, True)
    t(d, (80, 95), "Public 200 — weak BM25 vs ShopPilot", 38, WHITE, True)
    metrics = [
        ("TechnicalScore", TECH, f"from {BASE_TECH}", CYAN),
        ("Hit@10", HIT, f"from {BASE_HIT}", PINK),
        ("MRR", MRR, "from 0.068", VIOLET),
        ("MTTC", MTTC, f"from {BASE_MTTC}", GOLD),
    ]
    for i, (lab, val, delta, col) in enumerate(metrics):
        x = 80 + i * 450
        rr(d, (x, 200, x + 420, 420), CARD, None, 0, 18)
        d.rectangle((x, 200, x + 420, 214), fill=col)
        t(d, (x + 30, 250), lab, 22, MUTED)
        t(d, (x + 30, 300), val, 52, WHITE, True)
        t(d, (x + 30, 370), delta, 20, col)
    # simple bar comparison
    rr(d, (80, 480, 1840, 920), CARD, None, 0, 18)
    t(d, (120, 520), "Metric comparison (higher better)", 24, MUTED, True)
    pairs = [("Tech", 0.107, 0.907), ("Hit@10", 0.125, 0.975), ("MRR", 0.068, 0.858), ("Eff.", 0.119, 0.813)]
    base_x, base_y, max_h, bar_w = 180, 860, 280, 70
    gap = 380
    for i, (name, a, b) in enumerate(pairs):
        x = base_x + i * gap
        ha, hb = int(max_h * a), int(max_h * b)
        d.rectangle((x, base_y - ha, x + bar_w, base_y), fill=MUTED2)
        d.rectangle((x + bar_w + 16, base_y - hb, x + 2 * bar_w + 16, base_y), fill=CYAN)
        t(d, (x + bar_w, base_y + 30), name, 22, WHITE, True, "mm")
        t(d, (x + bar_w // 2, base_y - ha - 28), f"{a:.2f}", 18, MUTED, False, "mm")
        t(d, (x + bar_w + 16 + bar_w // 2, base_y - hb - 28), f"{b:.2f}", 18, CYAN, True, "mm")
    t(d, (1400, 520), "gray = BM25   cyan = ShopPilot", 20, MUTED)
    footer(d, 6)
    return img


def slide_scenarios() -> Image.Image:
    img, d = new_canvas()
    t(d, (80, 50), "06  ·  BY SCENARIO", 18, PINK, True)
    t(d, (80, 95), "Hit@10 holds across all scenario types", 38, WHITE, True)
    rows = [
        ("Buying", 0.975, 2.45, CYAN),
        ("Browsing", 0.975, 2.79, PINK),
        ("Override", 0.967, 4.20, VIOLET),
        ("Boundary", 1.000, 3.00, GOLD),
    ]
    for i, (name, hit, mttc, col) in enumerate(rows):
        y = 220 + i * 170
        rr(d, (80, y, 1840, y + 150), CARD, None, 0, 16)
        d.rectangle((80, y, 96, y + 150), fill=col)
        t(d, (140, y + 55), name, 32, WHITE, True)
        t(d, (520, y + 35), "Hit@10", 20, MUTED)
        t(d, (520, y + 75), f"{hit:.3f}", 40, col, True)
        t(d, (900, y + 35), "MTTC", 20, MUTED)
        t(d, (900, y + 75), f"{mttc:.2f}", 40, WHITE, True)
        # mini bar vs 10
        bw = int(600 * (mttc / 10))
        d.rounded_rectangle((1200, y + 70, 1800, y + 95), radius=8, fill=(30, 42, 64))
        d.rounded_rectangle((1200, y + 70, 1200 + bw, y + 95), radius=8, fill=col)
    footer(d, 7)
    return img


def slide_demo() -> Image.Image:
    img, d = new_canvas()
    t(d, (80, 50), "07  ·  DEMO", 18, PINK, True)
    t(d, (80, 95), "Astrid CLI — live multi-turn", 38, WHITE, True)
    # terminal
    rr(d, (80, 180, 1180, 920), (8, 14, 24), None, 0, 16)
    d.rectangle((80, 180, 1180, 240), fill=(18, 26, 40))
    for i, col in enumerate([(255, 95, 87), (254, 188, 46), (40, 200, 64)]):
        d.ellipse((110 + i * 36, 200, 130 + i * 36, 220), fill=col)
    t(d, (280, 210), "astrid — dense=hash", 20, MUTED, False, "lm")
    lines = [
        (MUTED2, "$ python3 cli_chat.py --dense hash"),
        (PINK, "  Astrid  ·  quiet clarity for every aisle"),
        (CYAN, "  You · shoes for my son"),
        (WHITE, "  Astrid: Got it (footwear; boys). Any color…?"),
        (GOLD, "  ↳ ask · other"),
        (CYAN, "  You · Actually forget sneakers, dress shoes size 9"),
        (WHITE, "  Astrid: Updated (footwear; size 9). Color?"),
        (PINK, "  ↳ soft wipe · disclosed kept"),
        (MUTED, "  /state → family=footwear  size=9"),
    ]
    y = 280
    for col, line in lines:
        t(d, (120, y), line, 22, col)
        y += 55
    # side cards
    demos = [
        ("Vague → clarify", "dress + exploring → other → plus size locks size", CYAN),
        ("Family lock", "dress sandals → footwear, not garments", PINK),
        ("Intent override", "running shoes → dress shoes; size 9 persists", VIOLET),
    ]
    for i, (h, b, col) in enumerate(demos):
        y = 180 + i * 250
        rr(d, (1240, y, 1840, y + 220), CARD, None, 0, 16)
        d.rectangle((1240, y, 1256, y + 220), fill=col)
        t(d, (1280, y + 40), h, 26, col, True)
        wrap(d, (1280, y + 100), b, 22, MUTED, 520)
    footer(d, 8)
    return img


def slide_impact() -> Image.Image:
    img, d = new_canvas()
    t(d, (80, 50), "08  ·  IMPACT", 18, PINK, True)
    t(d, (80, 95), "Kit metrics → merchant outcomes", 38, WHITE, True)
    rows = [
        ("Hit@10", HIT, "Findability — target ASIN in top 10", CYAN),
        ("MRR", MRR, "Rank quality — earlier positions win", PINK),
        ("MTTC", MTTC, "Cost / cognitive load — fewer refine loops", VIOLET),
        ("Tokens", "0", "Offline default — no paid LLM on score path", GOLD),
    ]
    for i, (k, v, note, col) in enumerate(rows):
        y = 200 + i * 170
        rr(d, (80, y, 1840, y + 150), CARD, None, 0, 16)
        d.rectangle((80, y, 100, y + 150), fill=col)
        t(d, (140, y + 55), k, 28, MUTED, True)
        t(d, (480, y + 45), v, 48, col, True)
        t(d, (820, y + 55), note, 26, WHITE)
    footer(d, 9)
    return img


def slide_end() -> Image.Image:
    img, d = new_canvas()
    t(d, (80, 260), "THANKS  ·  QUESTIONS", 22, PINK, True)
    t(d, (80, 330), "Shop", 72, CYAN, True)
    bbox = font(72, True).getbbox("Shop")
    t(d, (80 + (bbox[2] - bbox[0]) + 8, 330), "Pilot", 72, PINK, True)
    t(d, (80, 440), "Offline-first multi-turn shopping copilot", 32, WHITE)
    t(d, (80, 510), "github.com/algorathem/techjam2026-shopping-copilot", 28, CYAN)
    t(d, (80, 580), f"Astrid CLI  ·  Tech {TECH}  ·  Hit@10 {HIT}  ·  MTTC {MTTC}", 24, MUTED)
    chips = [("Live demo ready", CYAN), ("Reproduce: local_evaluator", PINK), ("Track 4 · CSJ 50k", VIOLET)]
    for i, (lab, col) in enumerate(chips):
        x = 80 + i * 560
        rr(d, (x, 700, x + 520, 780), CARD, col, 2, 28)
        t(d, (x + 260, 740), lab, 24, WHITE, True, "mm")
    footer(d, 10)
    return img


RENDERERS = [
    slide_title,
    slide_problem,
    slide_solution,
    slide_architecture,
    slide_architecture_detail,
    slide_results,
    slide_scenarios,
    slide_demo,
    slide_impact,
    slide_end,
]


def which(cmd: str) -> str | None:
    return shutil.which(cmd)


def wav_duration(path: Path) -> float:
    with wave.open(str(path), "rb") as w:
        return w.getnframes() / float(w.getframerate())


def synthesize_segment(text: str, out_wav: Path, voice: str, rate: str) -> float:
    """macOS say → AIFF → WAV. Returns duration seconds."""
    out_wav.parent.mkdir(parents=True, exist_ok=True)
    aiff = out_wav.with_suffix(".aiff")
    # write text file to avoid shell escaping issues
    txt = out_wav.with_suffix(".txt")
    txt.write_text(text, encoding="utf-8")
    cmd = ["say", "-v", voice, "-r", str(rate), "-f", str(txt), "-o", str(aiff)]
    subprocess.run(cmd, check=True)
    # convert to 16-bit PCM wav
    subprocess.run(
        ["afconvert", "-f", "WAVE", "-d", "LEI16@44100", str(aiff), str(out_wav)],
        check=True,
    )
    aiff.unlink(missing_ok=True)
    return wav_duration(out_wav)


def concat_wavs(paths: list[Path], out: Path) -> float:
    """Simple PCM concat (same format assumed)."""
    frames = []
    params = None
    for p in paths:
        with wave.open(str(p), "rb") as w:
            if params is None:
                params = w.getparams()
            frames.append(w.readframes(w.getnframes()))
    assert params is not None
    out.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(out), "wb") as w:
        w.setparams(params)
        for f in frames:
            w.writeframes(f)
    return wav_duration(out)


def render_frames() -> list[Path]:
    FRAMES.mkdir(parents=True, exist_ok=True)
    paths = []
    for i, (seg, renderer) in enumerate(zip(SEGMENTS, RENDERERS), start=1):
        sid = seg[0]
        path = FRAMES / f"{sid}.png"
        img = renderer()
        img.save(path, "PNG", optimize=True)
        paths.append(path)
        print(f"  frame {i:02d} {path.name}")
    return paths


def build_video(frame_paths: list[Path], wav_paths: list[Path], durations: list[float]) -> Path:
    if not which("ffmpeg"):
        raise RuntimeError("ffmpeg not found")
    # per-slide clips
    clips_dir = FRAMES / "clips"
    clips_dir.mkdir(parents=True, exist_ok=True)
    clip_list = []
    for i, (fp, wp, dur) in enumerate(zip(frame_paths, wav_paths, durations), start=1):
        # pad duration slightly so last phoneme isn't cut
        d = max(dur + 0.25, 1.5)
        clip = clips_dir / f"clip_{i:02d}.mp4"
        cmd = [
            "ffmpeg", "-y",
            "-loop", "1", "-i", str(fp),
            "-i", str(wp),
            "-c:v", "libx264", "-tune", "stillimage", "-pix_fmt", "yuv420p",
            "-c:a", "aac", "-b:a", "192k",
            "-t", f"{d:.3f}",
            "-shortest",
            "-vf", f"scale={W}:{H}:force_original_aspect_ratio=decrease,pad={W}:{H}:(ow-iw)/2:(oh-ih)/2",
            str(clip),
        ]
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        clip_list.append(clip)
        print(f"  clip {i:02d} {d:.1f}s")

    concat_file = clips_dir / "concat.txt"
    concat_file.write_text("".join(f"file '{c.resolve()}'\n" for c in clip_list), encoding="utf-8")
    cmd = [
        "ffmpeg", "-y",
        "-f", "concat", "-safe", "0", "-i", str(concat_file),
        "-c", "copy",
        str(OUT_MP4),
    ]
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return OUT_MP4


def pick_voice() -> str:
    env = os.environ.get("SHOPPILOT_TTS_VOICE")
    if env:
        return env
    # prefer natural English voices if installed
    try:
        out = subprocess.check_output(["say", "-v", "?"], text=True, stderr=subprocess.STDOUT)
    except Exception:
        return "Samantha"
    preferred = ["Samantha", "Karen", "Moira", "Daniel", "Kathy", "Alex", "Fred"]
    available = {line.split()[0] for line in out.splitlines() if line.strip()}
    for v in preferred:
        if v in available:
            return v
    return "Samantha"


def main() -> None:
    if not which("say"):
        raise SystemExit("macOS `say` required for offline TTS")
    if not which("afconvert"):
        raise SystemExit("`afconvert` required")
    if not which("ffmpeg"):
        raise SystemExit("ffmpeg required")

    voice = pick_voice()
    rate = os.environ.get("SHOPPILOT_TTS_RATE", "175")
    print(f"TTS voice={voice} rate={rate}")

    # ensure architecture asset exists for detail slide
    if not ARCH_PNG.exists():
        render_arch = ROOT / "scripts" / "render_architecture_png.py"
        if render_arch.exists():
            subprocess.run(["python3", str(render_arch)], check=True)

    print("Rendering frames…")
    frames = render_frames()

    print("Synthesizing voiceover…")
    AUDIO.mkdir(parents=True, exist_ok=True)
    wavs: list[Path] = []
    durs: list[float] = []
    for i, (sid, title, text) in enumerate(SEGMENTS, start=1):
        wav = AUDIO / f"{sid}.wav"
        dur = synthesize_segment(text, wav, voice, rate)
        wavs.append(wav)
        durs.append(dur)
        print(f"  audio {i:02d} {title:22s} {dur:5.1f}s")

    total = concat_wavs(wavs, OUT_WAV)
    print(f"Full voiceover: {OUT_WAV} ({total:.1f}s)")

    print("Stitching mp4…")
    mp4 = build_video(frames, wavs, durs)
    size = mp4.stat().st_size
    print(f"WROTE {mp4} ({size} bytes)")
    # manifest
    manifest = {
        "voice": voice,
        "rate": rate,
        "total_audio_s": round(total, 2),
        "segments": [
            {"id": s[0], "title": s[1], "duration_s": round(d, 2)}
            for s, d in zip(SEGMENTS, durs)
        ],
        "mp4": str(mp4),
        "wav": str(OUT_WAV),
        "script": str(SCRIPT_MD),
    }
    man_path = ROOT / "docs" / "demo_video_manifest.json"
    man_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"WROTE {man_path}")
    print(f"TOTAL ~{sum(max(d + 0.25, 1.5) for d in durs):.0f}s with pads")


if __name__ == "__main__":
    main()

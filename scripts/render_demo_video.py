#!/usr/bin/env python3
"""Render ShopPilot demo slides to PNG + stitch MP4 (no LibreOffice needed)."""
from __future__ import annotations

import subprocess
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "docs" / "demo_video_frames"
OUT_MP4 = ROOT / "docs" / "ShopPilot_Demo_Video.mp4"
W, H = 1920, 1080

BG = (11, 15, 20)
CARD = (22, 30, 42)
ACCENT = (46, 211, 198)
ACCENT2 = (167, 139, 250)
WHITE = (241, 245, 249)
MUTED = (148, 163, 184)
GOOD = (52, 211, 153)
WARN = (248, 180, 76)


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = [
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf" if bold else "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
        "/Library/Fonts/Arial.ttf",
        "/System/Library/Fonts/SFNSMono.ttf",
    ]
    for path in candidates:
        try:
            return ImageFont.truetype(path, size=size)
        except OSError:
            continue
    return ImageFont.load_default()


def new_slide() -> tuple[Image.Image, ImageDraw.ImageDraw]:
    img = Image.new("RGB", (W, H), BG)
    draw = ImageDraw.Draw(img)
    # left accent bar
    draw.rectangle([0, 0, 14, H], fill=ACCENT)
    return img, draw


def text(draw, xy, s, size=36, fill=WHITE, bold=False):
    draw.text(xy, s, font=font(size, bold=bold), fill=fill)


def wrapped(draw, xy, s, size, fill, max_width, line_gap=8, bold=False):
    f = font(size, bold=bold)
    words = s.split()
    lines: list[str] = []
    cur = ""
    for w in words:
        trial = (cur + " " + w).strip()
        if f.getlength(trial) <= max_width:
            cur = trial
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    x, y = xy
    for line in lines:
        draw.text((x, y), line, font=f, fill=fill)
        y += size + line_gap
    return y


def rounded_rect(draw, box, fill, radius=24):
    draw.rounded_rectangle(box, radius=radius, fill=fill)


def footer(draw, s="ShopPilot · TechJam 2026 Track 4"):
    text(draw, (48, H - 48), s, size=22, fill=MUTED)


def slide_title() -> Image.Image:
    img, d = new_slide()
    text(d, (80, 280), "ShopPilot", size=92, bold=True)
    text(d, (80, 400), "Offline-first multi-turn shopping copilot", size=40, fill=ACCENT)
    text(d, (80, 490), "TechJam 2026  ·  Track 4 — Conversational Search & Recommendations", size=26, fill=MUTED)
    text(d, (80, 540), "Demo UI: Astrid CLI  ·  github.com/algorathem/techjam2026-shopping-copilot", size=24, fill=MUTED)
    footer(d, "Public kit · Tech ~0.794  ·  Hit@10 0.935  ·  MTTC ~3.0")
    return img


def slide_problem() -> Image.Image:
    img, d = new_slide()
    text(d, (60, 50), "Problem", size=56, bold=True, fill=ACCENT)
    wrapped(
        d,
        (60, 130),
        "Keyword search fails when shoppers are vague, change their mind, or need multi-turn constraints.",
        30,
        WHITE,
        1750,
    )
    cards = [
        ("Vague queries", '"something nice for summer"'),
        ("Ambiguity", "dress vs dress shoes · for my son"),
        ("Mind-change", "intent override mid-session"),
        ("Turn budget", "≤10 turns or the session fails"),
    ]
    for i, (h, b) in enumerate(cards):
        x = 60 + i * 460
        rounded_rect(d, (x, 320, x + 430, 720), CARD)
        text(d, (x + 30, 360), h, size=28, bold=True, fill=ACCENT2)
        wrapped(d, (x + 30, 430), b, 24, WHITE, 370)
    text(
        d,
        (60, 780),
        "Scored on Hit@10 · MRR · MTTC → TechnicalScore   |   Frozen CSJ 50k · hidden parent_asin",
        size=24,
        fill=MUTED,
    )
    footer(d)
    return img


def slide_solution() -> Image.Image:
    img, d = new_slide()
    text(d, (60, 50), "Solution", size=56, bold=True, fill=ACCENT)
    wrapped(
        d,
        (60, 130),
        "Headless offline-first agent: each turn returns message + one ask_attribute + Top-10 ASINs.",
        28,
        WHITE,
        1750,
    )
    steps = [
        ("1", "Intent", "Buy/browse · family · audience"),
        ("2", "State", "Slots · override hygiene · multi-fill"),
        ("3", "Retrieve", "FTS5 + dense hybrid (in-memory)"),
        ("4", "Clarify", "other-first · skip filled · ≤10 turns"),
        ("5", "Rank", "Constraints · family · light priors"),
    ]
    for i, (n, h, b) in enumerate(steps):
        y = 240 + i * 120
        d.ellipse([70, y, 130, y + 60], fill=ACCENT)
        # center number roughly
        text(d, (88, y + 12), n, size=28, bold=True, fill=BG)
        text(d, (170, y + 8), h, size=32, bold=True)
        text(d, (420, y + 12), b, size=28, fill=MUTED)
    footer(d)
    return img


def slide_architecture() -> Image.Image:
    img, d = new_slide()
    text(d, (60, 40), "Architecture", size=56, bold=True, fill=ACCENT)
    boxes = [
        (60, 160, "User turn", "free text"),
        (400, 160, "DST state", "slots · family · audience"),
        (740, 160, "Hybrid retrieve", "FTS + dense"),
        (1080, 160, "Rank", "constraints · priors"),
        (740, 420, "Clarify policy", "other → open slots"),
        (1080, 420, "Response", "msg + ask + Top-10"),
    ]
    for x, y, h, b in boxes:
        rounded_rect(d, (x, y, x + 300, y + 180), CARD)
        text(d, (x + 24, y + 40), h, size=26, bold=True, fill=ACCENT)
        text(d, (x + 24, y + 100), b, size=22, fill=MUTED)
    # arrows as simple lines
    d.line([(360, 250), (400, 250)], fill=ACCENT, width=4)
    d.line([(700, 250), (740, 250)], fill=ACCENT, width=4)
    d.line([(1040, 250), (1080, 250)], fill=ACCENT, width=4)
    d.line([(890, 340), (890, 420)], fill=ACCENT, width=4)
    d.line([(1230, 340), (1230, 420)], fill=ACCENT, width=4)

    text(d, (60, 700), "Design choices (measured)", size=28, bold=True, fill=ACCENT2)
    wrapped(
        d,
        (60, 760),
        "other-first + static ask ladder (max-IG → Tech ~0.72 rejected) · soft-only override wipe · "
        "corpus-grounded facets · offline default · optional LLM gated",
        24,
        WHITE,
        1750,
    )
    footer(d)
    return img


def slide_results() -> Image.Image:
    img, d = new_slide()
    text(d, (60, 40), "Results — public 200", size=52, bold=True, fill=ACCENT)
    metrics = [
        ("TechnicalScore", "0.11 → 0.794", "7×+ vs weak BM25"),
        ("Hit@10", "0.125 → 0.935", "target in top 10"),
        ("MTTC", "9.8 → 3.0", "fewer turns to hit"),
        ("Tokens", "0", "offline default path"),
    ]
    for i, (h, v, note) in enumerate(metrics):
        x = 60 + i * 460
        rounded_rect(d, (x, 160, x + 430, 480), CARD)
        text(d, (x + 30, 200), h, size=24, fill=MUTED)
        text(d, (x + 30, 280), v, size=36, bold=True, fill=GOOD)
        text(d, (x + 30, 380), note, size=22, fill=WHITE)
    text(d, (60, 560), "What moved the needle", size=28, bold=True, fill=ACCENT2)
    wrapped(
        d,
        (60, 620),
        "Override hygiene · hybrid dense hash · family/audience routing · multi-slot freeform · "
        "cold-start profile/rating priors — kept only under Tech guardrail.",
        26,
        WHITE,
        1750,
    )
    text(d, (60, 760), "Optional Gemini NLU/rerank: flags only — not required for score.", size=24, fill=MUTED)
    footer(d)
    return img


def slide_demo() -> Image.Image:
    img, d = new_slide()
    text(d, (60, 40), "Live demo — Astrid CLI", size=52, bold=True, fill=ACCENT)
    rounded_rect(d, (60, 130, 1860, 920), CARD, radius=28)
    lines = [
        (MUTED, "$ python3 cli_chat.py --dense hash"),
        (ACCENT2, "     _        _        _     _"),
        (ACCENT2, "    / \\   ___| |_ _ __(_) __| |"),
        (ACCENT2, "   / _ \\ / __| __| '__| |/ _` |"),
        (ACCENT2, "  / ___ \\__ \\ |_| |  | | (_| |"),
        (ACCENT2, " /_/   \\_\\___/\\__|_|  |_|\\__,_|"),
        (WHITE, "  Astrid  ·  quiet clarity for every aisle"),
        (MUTED, "  offline hybrid · dense=hash"),
        (ACCENT, "  You · shoes for my son"),
        (WHITE, "  Astrid: Got it (footwear; boys). Any other must-have?"),
        (WARN, "  ↳ asking · other"),
        (MUTED, "  1. Kids Boys Soft Slippers …"),
        (MUTED, "  2. Toddler Rain Boots …"),
    ]
    y = 170
    for color, line in lines:
        text(d, (100, y), line, size=28 if not line.startswith("     ") else 26, fill=color, bold=False)
        y += 52
    footer(d, "Prefer a real terminal recording for YouTube · this is the storyboard cut")
    return img


def slide_impact() -> Image.Image:
    img, d = new_slide()
    text(d, (60, 50), "Impact & takeaways", size=52, bold=True, fill=ACCENT)
    bullets = [
        "Findability KPI: Hit@10 0.935 on public kit (exact parent_asin).",
        "Cost-to-serve: MTTC ~3 turns vs ~10 for weak BM25 — fewer refine loops.",
        "Merchant-owned brain: offline API without a required paid LLM.",
        "CQ/DST ideas from literature; kit-aligned ask policy after measured A/B.",
        "Same loop as real conversational commerce — catalog-grounded, not chatbot theater.",
    ]
    y = 180
    for b in bullets:
        text(d, (80, y), "▸", size=32, fill=ACCENT)
        wrapped(d, (130, y), b, 30, WHITE, 1650)
        y += 120
    footer(d)
    return img


def slide_end() -> Image.Image:
    img, d = new_slide()
    text(d, (80, 300), "Thanks", size=84, bold=True)
    text(d, (80, 420), "ShopPilot  ·  offline-first shopping copilot", size=36, fill=ACCENT)
    text(d, (80, 500), "github.com/algorathem/techjam2026-shopping-copilot", size=30, fill=WHITE)
    text(d, (80, 570), "Demo UI: Astrid CLI  ·  Tech ~0.794  ·  Hit@10 0.935", size=26, fill=MUTED)
    footer(d, "TechJam 2026 Track 4")
    return img


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    slides = [
        ("01_title", slide_title),
        ("02_problem", slide_problem),
        ("03_solution", slide_solution),
        ("04_architecture", slide_architecture),
        ("05_results", slide_results),
        ("06_demo", slide_demo),
        ("07_impact", slide_impact),
        ("08_end", slide_end),
    ]
    paths = []
    for name, fn in slides:
        img = fn()
        path = OUT_DIR / f"{name}.png"
        img.save(path, "PNG")
        paths.append(path)
        print("frame", path)

    # Durations seconds per slide (total ~2:20)
    durations = [5, 8, 8, 9, 9, 10, 8, 6]
    # Build concat demuxer with stills
    list_file = OUT_DIR / "concat.txt"
    lines = []
    for path, dur in zip(paths, durations):
        lines.append(f"file '{path}'")
        lines.append(f"duration {dur}")
    # last file repeated for concat demuxer
    lines.append(f"file '{paths[-1]}'")
    list_file.write_text("\n".join(lines) + "\n")

    cmd = [
        "ffmpeg",
        "-y",
        "-f",
        "concat",
        "-safe",
        "0",
        "-i",
        str(list_file),
        "-vf",
        "fps=30,format=yuv420p",
        "-c:v",
        "libx264",
        "-pix_fmt",
        "yuv420p",
        "-movflags",
        "+faststart",
        str(OUT_MP4),
    ]
    print("RUN", " ".join(cmd))
    subprocess.check_call(cmd)
    print("WROTE", OUT_MP4)
    print("duration_s", sum(durations))


if __name__ == "__main__":
    main()

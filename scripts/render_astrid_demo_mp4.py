#!/usr/bin/env python3
"""Render a terminal-style MP4 of the scripted Astrid demo (no live GUI).

Produces docs/demo_out/Astrid_CLI_Demo.mp4 for YouTube upload when
screen-recording Terminal is unavailable from the agent environment.
"""
from __future__ import annotations

import os
import subprocess
import sys
import tempfile
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "docs" / "demo_out"
W, H = 1280, 720
FPS = 8
CHAR_W = 9
LINE_H = 18
MARGIN = 28
MAX_VISIBLE = 32
BG = (12, 14, 18)
FG = (200, 220, 230)
ACCENT = (180, 120, 255)
CYAN = (100, 220, 230)
GOLD = (240, 200, 100)
DIM = (110, 120, 130)
GREEN = (120, 200, 140)


def _font(size: int = 15) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    for path in (
        "/System/Library/Fonts/Supplemental/Menlo.ttc",
        "/System/Library/Fonts/Monaco.ttf",
        "/Library/Fonts/SF-Mono-Regular.otf",
        "/System/Library/Fonts/SFNSMono.ttf",
    ):
        try:
            return ImageFont.truetype(path, size)
        except OSError:
            continue
    return ImageFont.load_default()


def _color_for(line: str) -> tuple[int, int, int]:
    s = line.strip()
    if s.startswith("You"):
        return ACCENT
    if s.startswith("Astrid:") or "Astrid" in s[:20]:
        return CYAN
    if "asking" in s or s.startswith("↳"):
        return GOLD
    if s.startswith("turn ") or s.startswith("session") or s.startswith("suggestions"):
        return DIM
    if s.startswith("1.") or s.startswith("2.") or s.startswith("3."):
        return GREEN
    if "────" in s or s.startswith("_") or "/_" in s:
        return ACCENT
    return FG


def capture_demo_lines() -> list[str]:
    env = os.environ.copy()
    env["SHOPPILOT_DENSE"] = "hash"
    env["PYTHONUNBUFFERED"] = "1"
    proc = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "demo_astrid_scripted.py"),
            "--delay",
            "0",
            "--type-delay",
            "0",
            "--top-k",
            "5",
            "--no-color",
        ],
        cwd=str(ROOT),
        env=env,
        capture_output=True,
        text=True,
        timeout=180,
    )
    text = proc.stdout + ("\n" + proc.stderr if proc.returncode else "")
    lines = []
    for line in text.splitlines():
        # wrap long lines
        while len(line) > 120:
            lines.append(line[:120])
            line = "  " + line[120:]
        lines.append(line)
    return lines


def render_frame(visible: list[str], font: ImageFont.ImageFont, frame_i: int) -> Image.Image:
    img = Image.new("RGB", (W, H), BG)
    draw = ImageDraw.Draw(img)
    # title bar
    draw.rectangle([0, 0, W, 36], fill=(24, 28, 36))
    draw.text((MARGIN, 10), "Astrid  ·  ShopPilot CLI demo  ·  offline hash", fill=DIM, font=font)
    y = 48
    for line in visible[-MAX_VISIBLE:]:
        draw.text((MARGIN, y), line[:130], fill=_color_for(line), font=font)
        y += LINE_H
        if y > H - 40:
            break
    # footer
    draw.text((MARGIN, H - 28), f"frame {frame_i}  ·  TechJam Track 4", fill=DIM, font=font)
    return img


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    print("running scripted demo…", flush=True)
    lines = capture_demo_lines()
    (OUT_DIR / "astrid_demo.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"lines={len(lines)}", flush=True)

    font = _font(15)
    frames_dir = Path(tempfile.mkdtemp(prefix="astrid_frames_"))
    # Progressive reveal: add ~1 line every 2–3 frames; pause on user/agent beats
    visible: list[str] = []
    frame_i = 0
    # intro hold
    for _ in range(FPS * 2):
        render_frame(["", "  loading Astrid…", ""], font, frame_i).save(
            frames_dir / f"f{frame_i:05d}.png"
        )
        frame_i += 1

    for line in lines:
        visible.append(line)
        hold = FPS  # ~1s per line
        if line.strip().startswith("You"):
            hold = int(FPS * 1.4)
        if "Astrid:" in line:
            hold = int(FPS * 1.6)
        if line.strip().startswith("1."):
            hold = int(FPS * 1.2)
        for _ in range(max(2, hold)):
            render_frame(visible, font, frame_i).save(frames_dir / f"f{frame_i:05d}.png")
            frame_i += 1

    # end hold
    for _ in range(FPS * 3):
        render_frame(visible, font, frame_i).save(frames_dir / f"f{frame_i:05d}.png")
        frame_i += 1

    out_mp4 = OUT_DIR / "Astrid_CLI_Demo.mp4"
    print(f"encoding {frame_i} frames → {out_mp4}", flush=True)
    cmd = [
        "ffmpeg",
        "-y",
        "-framerate",
        str(FPS),
        "-i",
        str(frames_dir / "f%05d.png"),
        "-c:v",
        "libx264",
        "-pix_fmt",
        "yuv420p",
        "-crf",
        "20",
        str(out_mp4),
    ]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        print(r.stderr[-800:], file=sys.stderr)
        return r.returncode
    # cleanup frames
    for p in frames_dir.glob("*.png"):
        p.unlink()
    frames_dir.rmdir()
    print(f"OK {out_mp4} ({out_mp4.stat().st_size // 1024} KB)", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

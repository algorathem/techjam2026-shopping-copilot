# Astrid CLI — screen-record demo

## Goal

~90–150 seconds of Terminal: Astrid multi-turn chat (recommend + ask), then a mind-change.

## Before you hit record

1. Full-screen or large Terminal window (dark theme looks best with Astrid colors).
2. Font size ~16–18 so titles read on video.
3. From repo root:

```bash
cd /Users/kyecin/Downloads/techjam2026-shopping-copilot
export SHOPPILOT_DENSE=hash
# optional: clear scrollback (Cmd+K in Terminal)
```

4. Have catalog present: `data/catalog.jsonl` (you already do).

## Option A — Scripted (recommended)

No live typing mistakes. Good for a clean take.

```bash
python3 scripts/demo_astrid_scripted.py --delay 1.0 --top-k 5
```

**Record:**

1. Open **QuickTime Player** → **File → New Screen Recording**  
   (or macOS **Screenshot** toolbar: `Cmd+Shift+5` → **Record Selected Portion**)
2. Select the Terminal window only (not the whole desktop).
3. Start recording, then run the command above (or start the command, then record — either works).
4. Stop when you see the closing line.
5. Save as e.g. `Astrid_ShopPilot_Demo.mov`, then upload to YouTube (unlisted/public).

**ffmpeg crop/encode (optional):**

```bash
ffmpeg -i Astrid_ShopPilot_Demo.mov -c:v libx264 -crf 20 -pix_fmt yuv420p docs/Astrid_Demo.mp4
```

## Option B — Live interactive

```bash
python3 cli_chat.py --dense hash --top-k 5
```

Type slowly (or paste) these lines:

```text
I'm looking for Women Dresses. A key requirement is: black.
For that, what matters is: cotton; midi length.
I don't have an additional preference for style.
Actually, ignore my earlier preference. What I need is: comfortable walking shoes under 80.
/state
/quit
```

Narrate off-mic or in a voiceover:

- Turn 1–2: state + `other` / constraints  
- Suggestions list = ranked ASINs  
- Override: soft wipe, new intent, still offline  

## What to say (30-sec voiceover skeleton)

1. “ShopPilot agent, Astrid CLI — offline multi-turn shopping.”  
2. “Session state, hybrid FTS + hash dense, evidence ranking.”  
3. “One official ask per turn — other first — then recommend.”  
4. “Intent override without poisoning retrieval.”  
5. “Public Tech ~0.909, Hit 0.975, zero API tokens on the default path.”

## Tips

- Do **not** show API keys or `.env`.  
- Prefer **window capture**, not full desktop (hides Slack/mail).  
- One clean take > fancy edits.  
- If colors look wrong: `python3 cli_chat.py --no-color` or fix Terminal theme.  
- First run may pause on “loading catalog…” (~50k) — start recording **after** the banner, or include a 2s “loading” beat.

## Checklist

- [ ] Banner “Astrid” visible  
- [ ] At least 2–3 turns with ask chip + suggestions  
- [ ] Override line shown  
- [ ] No secrets on screen  
- [ ] Under ~3 minutes  

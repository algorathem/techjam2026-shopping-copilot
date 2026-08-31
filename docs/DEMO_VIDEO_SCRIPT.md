# Demo video script — ShopPilot + Astrid deck

**Length:** ~2:30–3:00  
**Format:** Deck slides (Astrid cyan/pink) + TTS voiceover (+ optional 30–60s live Astrid CLI cut)  
**Deck:** `docs/ShopPilot_Demo_Slides.pptx` · rebuild `python3 scripts/build_demo_slides.py`  
**Video:** `docs/ShopPilot_Demo_Video.mp4` · rebuild `python3 scripts/build_demo_av.py`  
**Upload:** YouTube → Public → paste into Devpost  

No product UI required. Backend agent + slides are enough.

---

## Recording / rebuild setup

```bash
cd ~/Downloads/techjam2026-shopping-copilot
export SHOPPILOT_DENSE=hash
# metrics already in results.json — slides read live ballpark Tech 0.907 / Hit 0.975

python3 scripts/build_demo_slides.py
python3 scripts/render_architecture_png.py   # if architecture PNG stale
python3 scripts/build_demo_av.py             # TTS + frames + mp4
```

- Terminal font large if you splice real CLI  
- Hide secrets / no API keys on screen  
- Do **not** scrape Amazon product images  

**TTS note:** default path uses macOS `say` (offline). Optional cloud TTS only if you set a key yourself — never commit keys.

---

## Slide ↔ timing map (voiceover)

| t | Slide | On-screen | Speak |
|---|---|---|---|
| 0:00–0:12 | 01 Title | ShopPilot · Tech 0.907 | Hook + title |
| 0:12–0:32 | 02 Problem | 4 failure cards | Problem |
| 0:32–0:50 | 03 Solution | 5-step pipeline | Solution one-liner |
| 0:50–1:15 | 04 Architecture overview | Ingest→…→Respond + 3 panels | Architecture |
| 1:15–1:35 | 05 Architecture detail | Full diagram PNG | State loop callout |
| 1:35–1:55 | 06 Results | KPI + chart | Metrics |
| 1:55–2:10 | 07 By scenario | Hit/MRR + MTTC | Scenario hold |
| 2:10–2:40 | 08 Demo | Astrid CLI storyboard | Live-demo narration (or splice real CLI) |
| 2:40–2:55 | 09 Impact | KPI → merchant | Impact |
| 2:55–3:05 | 10 Thanks | GitHub | Close |

---

## Full voiceover script (read as-is)

### 1 · Title (0:00–0:12)
ShopPilot — an offline-first, multi-turn shopping copilot for TechJam twenty twenty-six, Track four.  
Demo UI is Astrid CLI. On the public two-hundred session kit: Technical Score zero point nine zero seven, Hit at ten zero point nine seven five, mean turns about two point nine — with zero tokens on the default path.

### 2 · Problem (0:12–0:32)
Keyword search breaks on real shopping intent. Shoppers are vague. “Dress” might mean a garment — or dress sandals. They change their mind mid-session. And the kit gives you at most ten turns to find a hidden Amazon parent A-S-I-N.

### 3 · Solution (0:32–0:50)
ShopPilot is a headless agent. Every turn returns three things: a message, one ask_attribute, and a Top-ten of A-S-I-Ns.  
Five steps: ingest, state, hybrid retrieve, clarify, and rank. No required L-L-M.

### 4 · Architecture overview (0:50–1:15)
Ingest is not just an intent router — it writes the full dialogue state: slots with sources, product family, audience, and soft overrides.  
Retrieve is hybrid: F-T-S-five plus dense hash, in memory. Rank uses constraint coverage and light priors. Ask is other-first, then a static ladder that skips filled slots.  
Catalog stays immutable. Optional L-L-M is gated and off the score path.

### 5 · Architecture detail (1:15–1:35)
Multi-turn means past SessionState plus the current utterance — same session I-D.  
When the shopper says “black” on turn three, we rank with dress, plus size, and black together — not black alone.

### 6 · Results (1:35–1:55)
Against the official weak B-M-twenty-five starter: Technical Score from about zero point one one to zero point nine zero seven. Hit at ten from zero point one three to zero point nine eight. Mean turns from about nine point eight down to two point nine. Default path uses zero tokens.

### 7 · By scenario (1:55–2:10)
Hit holds across buying, browsing, intent override, and boundary. Override costs more turns — as mind-change should — but still lands near Hit zero point nine seven.

### 8 · Demo / Astrid CLI (2:10–2:40)
In Astrid CLI: “shoes for my son” locks footwear and boys, asks other, and shows Top titles.  
“Actually forget sneakers — dress shoes, size nine” fires soft-only override: soft prefs wipe, disclosed facts stay, family stays footwear.  
Dress sandals route to footwear — not garment dresses. Plus size fills size once — we do not re-ask it.

### 9 · Impact (2:40–2:55)
Kit metrics map to merchant outcomes: Hit is findability, M-R-R is rank quality, mean turns is cost and cognitive load.  
Same decision core as conversational commerce — catalog-grounded, measurable, runnable offline.

### 10 · Close (2:55–3:05)
ShopPilot. Offline-first multi-turn shopping copilot.  
GitHub: github.com/algorathem/techjam2026-shopping-copilot. Thanks.

---

## Optional live CLI splice (30–60s, preferred for YouTube depth)

Record after slide 07 or replace slide 08 narration with screen capture:

```bash
export SHOPPILOT_DENSE=hash
python3 cli_chat.py --dense hash
```

**A — vague browse**
```text
I'm looking for a dress, but I'm still exploring.
plus size
party
black
/state
```

**B — family**
```text
/new
I'm looking for dress sandals
```

**C — override**
```text
/new
I'm looking for running shoes
Actually forget running shoes, I need dress shoes instead. Still size 9.
```

---

## Spoken metrics (keep consistent)

| Metric | Weak BM25 | ShopPilot (hash) |
|---|---:|---:|
| TechnicalScore | ~0.107 | **~0.907** |
| Hit@10 | 0.125 | **0.975** |
| MRR | ~0.068 | **~0.858** |
| MTTC | ~9.81 | **~2.88** |
| Tokens | 0 | **0** |

TechnicalScore = `0.50×Hit + 0.30×MRR + 0.20×Efficiency`.

---

## Audio / edit tips

- macOS `say` voice default in `build_demo_av.py` is Samantha (override with `SHOPPILOT_TTS_VOICE`)  
- Speak rate ~175 wpm equivalent; script is already paced for ~3 min  
- If you re-record live voice, keep the same section order as the slide map  
- Jump-cut long eval runs; never show API keys  
- No Amazon logos or scraped product photos  

## YouTube package

- **Title:** `ShopPilot — TechJam 2026 Track 4 Shopping Copilot`  
- **Description:** Offline-first multi-turn agent · Tech ~0.907 · Hit@10 0.975 · GitHub link · “backend agent demo”  
- **Visibility:** Public  
- After upload: paste URL into Devpost  

## Rebuild one-liner

```bash
python3 scripts/build_demo_slides.py && python3 scripts/build_demo_av.py
open docs/ShopPilot_Demo_Video.mp4
```

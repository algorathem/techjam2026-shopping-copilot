# ShopPilot + Astrid — Demo voiceover script

**Total target:** ~2:30–3:00 (slides ~1:45 + Astrid CLI ~0:45–1:00)  
**Tone:** calm, technical, no hype words.  
**On-screen:** `upload/ShopPilot_Project_Deck_Astrid_FINAL.pptx` then `docs/demo_out/Astrid_CLI_Demo.mp4`

---

## Timing map

| # | Slide / segment | Sec | Cue |
|---:|---|---:|---|
| 1 | Title | 12 | “ShopPilot…” |
| 2 | Problem | 15 | “Keyword search breaks…” |
| 3 | Solution | 18 | “Headless offline agent…” |
| 4 | Architecture | 20 | “State-first multi-turn…” |
| 5 | Results | 18 | “On the public 200…” |
| 6 | By scenario | 12 | “Hit holds across…” |
| 7 | **Gallery transition** | 12 | “Same stack — now live…” |
| 8 | Demo slide (bridge) | 8 | “Astrid CLI…” |
| — | **Astrid CLI video** | 45–60 | (optional light VO or music bed) |
| 9 | Impact | 12 | “What the metrics mean…” |
| 10 | Thanks | 10 | “Repo link…” |

---

## Full script (read aloud)

### 1 — Title (~12s)
ShopPilot — TechJam twenty twenty-six, Track four, Shopping Copilot.  
An offline-first, multi-turn agent that finds a hidden catalog purchase in at most ten turns.  
Demo face: Astrid CLI. No required LLM on the scoring path.

### 2 — Problem (~15s)
Keyword search breaks on real shopping intent: vague goals, dual-meaning products — dress versus dress shoes — mid-session mind-change, and a hard ten-turn budget.  
The scored job is simple and strict: put the true parent A-S-I-N in the top ten before the session ends. Metrics: Hit at ten, M-R-R, and mean turns to convert.

### 3 — Solution (~18s)
We ship a headless offline agent on a classical conversational recommendation spine.  
Each respond call returns a message, one official ask attribute, and a top-ten list.  
Pipeline: ingest and N-L-U, session state with soft, disclosed, and override provenance, hybrid F-T-S-five plus dense hash retrieval, other-first clarification, then coverage-based ranking.

### 4 — Architecture (~20s)
State-first multi-turn system. The hot path is synchronous Agent.respond: ingest, retrieve, rank, ask, respond.  
SessionState holds slots, family and gift-audience routing, and override hygiene — soft-only wipe so disclosed facts survive a mind-change without poisoning search.  
Default path is fully offline — Technical Score about zero point nine zero nine, Hit zero point nine seven five, zero API tokens.

### 5 — Results (~18s)
On the official public two hundred sessions, weak B-M-twenty-five sits near zero point one Technical Score.  
ShopPilot reaches about zero point nine oh nine: Hit at ten zero point nine seven five, M-R-R about zero point eight seven, mean turns around three.  
What moved the needle: override hygiene, hybrid dense hash, family and audience routing, other-first asks, and multi-slot freeform parsing — each kept only after full-set A/B.

### 6 — By scenario (~12s)
Hit holds across buying, browsing, override, and boundary.  
Override costs more turns — mind-change is structural — but still lands Hit about zero point nine six seven.

### 7 — Gallery transition (~12s)
Gallery: state, retrieve and rank, then Astrid live.  
Same offline stack you just saw — now running in the terminal.

### 8 — Demo bridge (~8s)
Astrid CLI — multi-turn shopping face.  
Command: python three cli underscore chat dot py, dense hash.

### Astrid CLI segment (~45–60s)
*(Optional soft VO, or silence + light music)*  
Watch the loop: user turn, Astrid message, one ask chip, ranked suggestions.  
Constraints accumulate; other unlocks simulator-style dumps.  
Then an intent override — soft preferences clear, new goal, still offline.

**Optional VO lines over CLI:**
- “Turn one: category and a key requirement — agent asks other.”  
- “Turn two: multi-slot dump — cotton, midi — rank updates.”  
- “Override: walking shoes — state resets soft prefs, retrieval continues.”

### 9 — Impact (~12s)
Kit metrics map to merchant outcomes: findability, rank quality, fewer refine loops, and zero token cost on the default path.  
Honest frame: offline simulation is not a live G-M-V experiment — same job-to-be-done as conversational commerce.

### 10 — Thanks (~10s)
ShopPilot. Offline-first multi-turn shopping copilot.  
GitHub: algorathem slash techjam two zero two six hyphen shopping hyphen copilot.  
Questions welcome.

---

## Recording tips

1. Export slides to PDF or play FINAL pptx in full screen; advance on the timing map.  
2. Record VO with QuickTime or Voice Memos; keep peaks under −6 dB.  
3. Concat: slides video + `docs/demo_out/Astrid_CLI_Demo.mp4` (see build script).  
4. Burn VO under the full timeline; duck music −12 dB under speech.

## File outputs

| File | Role |
|---|---|
| `upload/ShopPilot_Project_Deck_Astrid_FINAL.pptx` | Deck + gallery transition |
| `upload/VOICEOVER_SCRIPT.md` | This script |
| `docs/demo_out/Astrid_CLI_Demo.mp4` | CLI demo segment |
| `upload/ShopPilot_Full_Demo.mp4` | Slides + Astrid (when built) |

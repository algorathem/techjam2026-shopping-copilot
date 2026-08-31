# Demo video script — ShopPilot (backend / NLP track)

**Length:** 2:00–3:00  
**Format:** Screen recording of terminal + 2–3 slides (optional)  
**Upload:** YouTube → Public → paste URL into Devpost  

No product UI required. Walkthrough of API / CLI / eval is accepted.

---

## Recording setup
- Terminal font large; hide secrets; no personal files in frame  
- Repo root: `techjam2026-shopping-copilot`  
- Catalog already at `data/catalog.jsonl`  
- `export SHOPPILOT_DENSE=hash`  
- Do **not** show API keys  

Optional title slide (5s):  
**ShopPilot — TechJam 2026 Track 4**  
Offline hybrid shopping agent · Tech ~0.79 · Hit@10 0.93  

---

## Shot list

### 0:00–0:20 — Problem (talk over terminal or one slide)
> Static keyword search fails real shoppers: buying vs browsing, mind-changes, vague goals.  
> This track scores an agent that finds a hidden purchase ASIN in ≤10 turns: Hit@10, MRR, MTTC.

### 0:20–0:45 — Architecture one-liner
Show `docs` or draw verbally:
```text
message → state (slots/family/override)
        → hybrid FTS ± dense
        → Top-10 + ask_attribute
```
> Offline-first. No required LLM. In-memory only.

### 0:45–1:30 — Live CLI demo (`cli_chat.py`)

```bash
export SHOPPILOT_DENSE=hash
python3 cli_chat.py --dense hash
```

**Scenario A — vague → clarify (browsing)**  
```text
You: I'm looking for a dress, but I'm still exploring.
# show ask=other, dress family, Top titles are dresses not sandals
You: plus size
# ask moves on; size filled — does NOT re-ask size
You: party
You: black
# /state  → show filled size,style,color
```

**Scenario B — family disambiguation (15s)**  
```text
/new
You: I'm looking for dress sandals
# footwear / sandals tops — not garment dresses
```

**Scenario C — override (20s)**  
```text
/new
You: I'm looking for running shoes
You: Actually forget running shoes, I need dress shoes instead. Still size 9.
# override fires; family stays footwear; constraints update
```

### 1:30–2:10 — Official metrics

```bash
python3 -m unittest tests.test_agent_slots tests.test_dense -q
python3 -m evaluator.local_evaluator
```

Show printed JSON or:
```bash
python3 -c "import json;d=json.load(open('results.json'));print(d['recommended_technical_score'], d['hit_rate_at_10'], d['mrr'], d['mttc'])"
```

Speak:
> Public 200: TechnicalScore about **0.79**, Hit@10 **0.93**, mean turns about **3.1**, versus starter BM25 about **0.11** Hit **0.13**.  
> Override hygiene alone moved override Hit from 0.80 to about 0.97.

### 2:10–2:30 — Impact close
> Same decision core merchants need for findability: intent, state, hybrid recall, clarify, rank—as an API.  
> Optional MiniLM or Gemini rerank exists; default stays offline for judges.

### 2:30–2:45 — End card
- GitHub: https://github.com/algorathem/techjam2026-shopping-copilot  
- “ShopPilot · Track 4 · Offline hybrid shopping agent”

---

## Audio tips
- Speak slower than you think; cut dead air in edit  
- Don’t read the whole README  
- If eval takes ~1 min, jump-cut to results with a “~60s later” caption  

## YouTube
- Title: `ShopPilot — TechJam 2026 Shopping Copilot (Track 4)`  
- Description: 2-line summary + GitHub link + “backend agent demo, no UI”  
- Visibility: **Public**  
- No Amazon trademark logos; plain terminal is fine  

## After upload
1. Copy public YouTube URL  
2. Paste into Devpost “Demo video” / description  
3. Confirm link opens without login  

# Devpost — ShopPilot (paste into Devpost)

**Project title:** ShopPilot — Multi-Turn Shopping Copilot for Catalog Findability  
**Track:** 4. Shopping Copilot (AI Conversational Search and Recommendations)  
**GitHub:** https://github.com/algorathem/techjam2026-shopping-copilot  
**Demo video:** [PASTE YOUTUBE URL AFTER UPLOAD]

---

## Elevator (2–3 sentences)

ShopPilot is a **headless multi-turn shopping agent** that turns messy shopper text into ranked catalog ASINs in ≤10 turns. On the official public 200-session kit it lifts TechnicalScore from the weak BM25 starter **~0.11 → ~0.79** (Hit@10 **0.93**, MTTC **~3.1**) with an **offline-first** hybrid pipeline—no required paid LLM or vector DB cluster.

---

## How the solution addresses the problem statement

Traditional e-commerce search is static keyword matching. This track needs an agent that handles **buying vs browsing**, **multi-turn slots**, **intent override**, and **efficient conversion**, scored by Hit@10 / MRR / MTTC on a frozen Amazon Clothing/Shoes/Jewelry catalog.

ShopPilot maps the four pillars as follows:

### I. Intent routing & hybrid pipeline
- **Buying vs browsing** from first-turn cues (e.g. hard “key requirement” vs “still exploring”).
- **Product-family intent** so “dress” ≠ “dress sandals” / “dress shoes”.
- **In-memory multi-lane retrieval:** SQLite **FTS5** (OR session terms + AND hard constraints) plus optional **dense** lane (hashed char n-grams by default; MiniLM opt-in).
- Lexical + constraint-coverage + family scoring; optional LLM **rerank of top‑20 only** (off by default).

### II. Dialog strategy — multi-turn evolution
- **Session state machine:** category, family, constraints with sources (`soft` / `disclosed` / `override`), `filled` / `dont_care` / `asked`.
- **Intent override:** soft-only wipe (keep simulator-disclosed hard facts), block discarded tokens, cut retrieval history, reset asks so `other` can fire again.
- **Clarification under vagueness:** always Top‑10 **and** `ask_attribute` same turn; first ask = **`other`** (protocol catch-all); then static order **skipping filled slots**. Pool max-IG ask selection was A/B’d and **rejected** (Tech ~0.72 vs ~0.75+).
- **Corpus-grounded wording:** message facet examples drawn from the live candidate pool (aligns with “don’t ask what the catalog can’t support”).

### III. Self-evolution / dynamic context
- Short-term: accumulate slots; rich freeform lines expand into multi-slot atoms (color/material/size/budget).
- Latest-wins on short soft color/material; plus↔petite conflict resolution.
- Long-term: weak prior from `user_profile.preference_tags` in ranking.
- Kit disclosed feature sentences stay **whole** (score-safe); freeform/override may atomize.

### IV. Evaluation matrix
- Local official evaluator: Hit@10, MRR, MTTC → TechnicalScore  
  `0.50×Hit + 0.30×MRR + 0.20×Efficiency`.
- Public 200 (hash default): **Tech ~0.789**, Hit **0.930**, MRR ~0.55, MTTC ~3.06, **0 tokens**.
- MiniLM opt-in peak: Tech ~**0.794**.
- Override slice after hygiene: Hit ~0.97, MTTC ~4.1 (was ~0.80 / ~5.8).

**Constraints respected:** headless API only; catalog read-only; in-memory only; no foundation-model full fine-tune; max 10 turns; typos/ASR out of scope by kit assumption.

---

## Real-world impact (beyond the hackathon)

Static site search still fails a large share of shoppers (e.g. Baymard: majority of sites weak on Search UX). Conversational commerce is a multi‑billion category as dialogue collapses intent→purchase. Amazon productized catalog-grounded assistants (Rufus). ShopPilot is the **merchant-owned decision core**—intent, state, hybrid recall, clarify, rank—as a measurable API mid-market can run offline.

Kit metrics read as business KPIs: **findability (Hit@10)**, **ranking quality (MRR)**, **cost-to-serve / cognitive load (MTTC)**.

*(Full cited write-up: `docs/REAL_WORLD_IMPACT.md` in repo.)*

---

## Development tools used
- **VS Code / Cursor / terminal** (macOS + SSH)
- **Git + GitHub**
- **Python 3.9–3.13** standard library + unittest
- **Hermes Agent** (local iteration / research notes)
- Optional: browser only for Devpost/YouTube (no product UI required)

## APIs used
- **None required** for scoring or default demo.
- **Optional:**
  - Google **Gemini** (`GEMINI_API_KEY` + `SHOPPILOT_LLM=1`) — semantic rerank of top candidates only  
  - **xAI** (`XAI_API_KEY` + `SHOPPILOT_LLM=1`) — same optional rerank path  
- No Maps / payment / external product APIs.

## Libraries and frameworks used
- **Required (default path):** Python stdlib only (`sqlite3` FTS5, `re`, `json`, `unittest`, …)
- **Optional dense hash:** `numpy`
- **Optional MiniLM dense:** `sentence-transformers`, `torch` (local embeddings; first run may download weights)
- **Not used for core score:** PyTorch training, full HF fine-tunes, FAISS/Milvus clusters, pandas/sklearn pipelines

## Datasets and assets used
- **TechJam participant kit** derived from **Amazon Reviews 2023** — Clothing_Shoes_and_Jewelry  
  - Frozen catalog **50,000** products (`catalog.jsonl`)  
  - **200** labeled public development sessions  
  - Official weak BM25 starter + local evaluator + API contract  
- Original upstream docs: https://amazon-reviews-2023.github.io/  
- Kit: https://github.com/TechJam2026/techjam-conversational-search  
- No private 800-set used for reported numbers  
- No injected/mock ASINs; catalog treated read-only  

---

## What’s in the GitHub repo
- `starter/agent.py` — orchestrator, state, retrieve, ask, score  
- `starter/dense.py` — hash / MiniLM dense backends  
- `starter/llm_rerank.py` — optional Gemini/xAI rerank  
- `starter/rewrite.py` — brief rewrite helper  
- `cli_chat.py` — interactive terminal demo  
- `evaluator/` — official local evaluator (unchanged)  
- `tests/` — slots, dense, rewrite, evaluator  
- `docs/` — competition notes, error analysis, impact  

**Reproduce:**
```bash
# catalog from official release → data/catalog.jsonl (50k rows)
export SHOPPILOT_DENSE=hash   # or none
python -m unittest tests.test_agent_slots tests.test_rewrite tests.test_dense tests.test_evaluator -q
python -m evaluator.local_evaluator
python cli_chat.py --dense hash
```

---

## Limitations & future work
- ~7% public misses: near-duplicate titles / sparse attributes  
- Ask **order** is static after `other` (adaptive IG lost on this simulator)  
- Slot cues are high-precision lexicons, not full NLU  
- Private 800 unknown; avoid over-claiming  
- With more time: sibling demotion, domain lexicon packs, optional local slot classifier—not entropy ask rewrite without A/B  

## Team
Solo — all implementation, evaluation, and write-up by the submitting participant.

---

## Built with (Devpost tags)
Python · SQLite FTS5 · NumPy · sentence-transformers (optional) · Gemini API (optional) · unittest · Amazon Reviews 2023 (kit)

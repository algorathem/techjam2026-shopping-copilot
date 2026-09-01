# Devpost — ShopPilot (paste into Devpost)

**Project title:** ShopPilot — Multi-Turn Shopping Copilot for Catalog Findability  
**Track:** 4. Shopping Copilot (AI Conversational Search and Recommendations)  
**GitHub:** https://github.com/algorathem/techjam2026-shopping-copilot  
**Demo video:** [PASTE YOUTUBE URL AFTER UPLOAD]

---

## Elevator (2–3 sentences)

ShopPilot is a **headless multi-turn shopping agent** that turns messy shopper text into ranked catalog ASINs in ≤10 turns. On the official public 200-session kit it reaches **TechnicalScore ~0.909** (hash default) and **~0.910** with local MiniLM (Hit@10 **0.975–0.980**), fully **offline-first**—**no external API required** for scoring or the default Astrid demo, **0 tokens** on the ship path.

---

## How the solution addresses the problem statement

Traditional e-commerce search is static keyword matching. This track needs an agent that handles **buying vs browsing**, **multi-turn slots**, **intent override**, and **efficient conversion**, scored by Hit@10 / MRR / MTTC on a frozen Amazon Clothing/Shoes/Jewelry catalog.

**ShopPilot is offline-first.** The scored path and default Astrid demo run entirely on-device: in-memory FTS5 + rules (+ optional local dense). **No external API key is required.** Optional cloud LLMs exist only as fail-open experiments and stay **off** for judging.

ShopPilot maps the four pillars as follows:

### I. Intent routing & hybrid pipeline
- **Buying vs browsing** from first-turn cues (hard “key requirement” vs “still exploring”).
- **Product-family intent** so “dress” ≠ “dress sandals” / “dress shoes”; gift **audience** only on explicit relationship phrases.
- **In-memory multi-lane retrieval:** SQLite **FTS5** (OR session terms + AND constraint lane) plus optional **dense** lane:
  - default **hashed char n-grams** (NumPy, local), or
  - opt-in **MiniLM** (`all-MiniLM-L6-v2`) as a **local sentence encoder** — weights downloaded once, then embedded offline; **not** a hosted chat API.
- Rank: constraint **coverage × exact** evidence, category-tail, family/audience, full-match jackpot, weak profile priors; **margin-gated** Top‑1 vs Top‑10 emission (first hit freezes MRR).

### II. Dialog strategy — multi-turn evolution
- **SessionState:** category, family, constraints with sources (`soft` / `disclosed` / `override`), `filled` / `dont_care` / `asked`.
- **Intent override:** soft-only wipe (keep simulator-disclosed hard facts), block discarded tokens, cut pre-override retrieval history, reset asks so `other` can re-fire.
- **Clarification:** one official `ask_attribute` per turn; first ask = **`other`** (catch-all, ≤2 hidden facts); optional second `other` while thin; then static ladder **skipping filled / dont_care**. Pool max-IG ask order was A/B’d and **rejected**.
- Message facet hints can ground wording in the live candidate pool; the simulator scores **ASINs + ask_attribute**, not prose.

### III. Self-evolution / dynamic context
- Short-term: accumulate slots; rich freeform / “what matters is:” lines expand into multi-slot atoms.
- Latest-wins on short soft color/material; size-pole conflict resolution.
- Long-term: weak prior from `user_profile.preference_tags` / rating style (tie-break only; short-term constraints dominate).
- Optional LLM slot parse / top‑k rerank: **env-gated, default off, fail-open to rules** — never on the critical path for TechnicalScore.

### IV. Evaluation matrix
- Official local evaluator: Hit@10, MRR, MTTC →  
  `TechnicalScore = 0.50·Hit + 0.30·MRR + 0.20·Efficiency`.
- **Public 200, hash default (ship):** Tech **~0.909**, Hit **0.975**, MRR **~0.872**, MTTC **~3.01**, **0 tokens**.
- **Public 200, MiniLM opt-in (local):** Tech **~0.910**, Hit **0.980**, MRR **~0.867**, MTTC **~2.98**, **0 API tokens** (local embed only).
- Override after hygiene: Hit **~0.967**, MTTC **~4.2** (protocol floor on pivot turn).

**Constraints respected:** headless API only; catalog read-only; in-memory index; no foundation-model fine-tune required; ≤10 turns; typos/ASR out of scope per kit; **scoring path needs no network and no paid API**.

---

## Real-world impact

Static site search still fails a large share of shoppers (e.g. Baymard on Search UX). Conversational commerce grows as dialogue collapses intent → purchase; large retailers productize catalog-grounded assistants. ShopPilot is the **merchant-owned decision core**—intent, state, hybrid recall, clarify, rank—as a **measurable API** mid-market teams can run **on their own infra without metering every turn to a public LLM API**.

Kit metrics as business KPIs: **findability (Hit@10)**, **rank quality (MRR)**, **cost-to-serve / cognitive load (MTTC)**, plus **zero token burn on the default path**.

---

## Development tools used
- VS Code / Cursor / terminal (macOS)
- Git + GitHub
- Python 3.10+ stdlib + unittest
- Hermes Agent for local iteration
- Optional: browser for Devpost / YouTube only (no product web UI required)

## APIs used
- **None required** for TechnicalScore, public 200 eval, or default Astrid demo.
- **Optional (off by default, not used in reported default metrics):**
  - Google Gemini or xAI — experimental slot NLU / top‑candidate rerank only (`SHOPPILOT_LLM*`); fail-open to rules if missing key/network.
- **Not used:** Maps, payments, live Amazon APIs, hosted embedding endpoints.
- **MiniLM** is a **local model file** (Hugging Face weights cached on disk), not a runtime external API dependency for scoring once cached.

## Libraries and frameworks used
- **Required (default score path):** Python stdlib (`sqlite3` FTS5, `re`, `json`, `unittest`, …)
- **Optional dense hash:** `numpy`
- **Optional local MiniLM dense:** `sentence-transformers` (+ `torch` as its backend) — **on-device embeddings only**
- **Not required for core score:** cloud LLM SDKs, FAISS/Milvus clusters, full HF fine-tunes, pandas/sklearn pipelines

## Datasets and assets used
- **TechJam participant kit** (Amazon Reviews 2023 — Clothing_Shoes_and_Jewelry):  
  - Frozen catalog **50,000** products  
  - **200** public development sessions  
  - Official weak BM25 starter + local evaluator + API contract  
- Upstream catalog docs: https://amazon-reviews-2023.github.io/  
- Kit: https://github.com/TechJam2026/techjam-conversational-search  
- No private 800-set used for reported numbers  
- No injected/mock ASINs; catalog read-only  
- Optional local weight cache: `all-MiniLM-L6-v2` (first download only; eval runs offline thereafter)

---

## One-line offline claim (for judges)

> **ShopPilot’s default and reported scoring path is fully offline—no external API. Dense MiniLM, when enabled, runs as a local encoder; any cloud LLM is optional, default-off, and unused for the hash ship metrics (Tech ~0.909, 0 tokens).**

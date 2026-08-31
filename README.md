# ShopPilot

Multi-turn shopping agent for TechJam Track 4 (Shopping Copilot). Finds a hidden catalog purchase in ≤10 turns via structured clarification and hybrid retrieval.

Built on the [official conversational-search kit](https://github.com/TechJam2026/techjam-conversational-search). Default path is **offline** (stdlib + optional NumPy hash dense). No required LLM, GPU, or vector DB.

## Public metrics (200 sessions)

`python -m evaluator.local_evaluator` with `SHOPPILOT_DENSE=hash`:

| Metric | Starter BM25 | ShopPilot |
|---|---:|---:|
| Hit@10 | 0.125 | **0.975** |
| MRR | 0.068 | **0.872** |
| MTTC | 9.81 | **3.01** |
| Efficiency | 0.119 | **0.800** |
| TechnicalScore | 0.107 | **0.909** |

```text
TechnicalScore = 0.50·Hit@10 + 0.30·MRR + 0.20·clip((11 − MTTC) / 10, 0, 1)
```

| Scenario | N | Hit@10 | MRR | MTTC |
|---|---:|---:|---:|---:|
| Buying | 80 | 0.975 | 0.884 | 2.56 |
| Browsing | 80 | 0.975 | 0.855 | 2.99 |
| Intent override | 30 | 0.967 | 0.867 | 4.20 |
| Boundary | 10 | 1.000 | 0.933 | 3.10 |

Token usage on the default path: **0**.

## Architecture

```text
user turn
  → SessionState ingest     (slots, family, audience, override hygiene)
  → hybrid retrieve         (FTS5 ∪ dense hash / optional MiniLM)
  → rank                    (evidence coverage×exact + category-tail + priors)
  → emit Top-K              (confidence margin policy)
  → ask_attribute           (other-first ladder; one official field)
  → { message, ask_attribute, recommendations, usage }
```

**State.** Constraints carry provenance `soft | disclosed | override`. Mind-change (“actually, ignore…”) drops soft prefs, keeps disclosed facts, blocks discarded tokens in FTS, and re-opens `other`.

**Retrieve.** In-memory SQLite FTS5 (OR session terms + AND constraint lane) plus optional dense char-ngram hash (`starter/dense.py`). Catalog is frozen; no external search.

**Rank.** Per-constraint token coverage and exact phrase match, category-tail bonus, product-family / gift-audience adapters, full-match jackpot, weak profile/rating priors. Linear feature fusion — not a trained cross-encoder.

**Ask.** At most one kit `ask_attribute` per turn. Policy: `other` first (simulator catch-all, ≤2 hidden facts), optional second `other` while thin, then static order color → material → style → …. Max-entropy ask order was measured and rejected.

**Emit.** First appearance of the true ASIN freezes Hit/MRR/MTTC. Default emission is **margin-gated**: Top-1 while `score(top1) − score(top2)` is small; Top-10 when the gap is large or turn ≥ force-widen. Optional fixed early Top-1 window if margin mode is off.

**Interface.** `starter/agent.py` → `Agent.reset` / `Agent.respond`. Demo CLI: `cli_chat.py` (Astrid).

## Quick start

Python 3.10+. Default path needs no pip packages.

```bash
# Catalog (50k rows) from the official kit release
gh release download participant-kit \
  --repo TechJam2026/techjam-conversational-search \
  --pattern catalog.jsonl.gz --dir data
python -c "import gzip,shutil,pathlib; p=pathlib.Path('data'); shutil.copyfileobj(gzip.open(p/'catalog.jsonl.gz','rb'), (p/'catalog.jsonl').open('wb'))"

export SHOPPILOT_DENSE=hash   # none | hash | auto | minilm
python -m unittest discover -s tests -q
python -m evaluator.local_evaluator
python cli_chat.py --dense hash
```

Optional NumPy for the hash dense lane:

```bash
pip install "numpy>=1.24,<2.1"
```

Optional MiniLM dense (`sentence-transformers`) and optional LLM slots/rerank are env-gated and **off by default**. See `starter/llm_slots.py` / `starter/llm_rerank.py`.

## Policy knobs (scored defaults)

```bash
export SHOPPILOT_DENSE=hash
export SHOPPILOT_PRECISION_GAP=10      # margin for Top-10; 0 → fixed turn window
export SHOPPILOT_PRECISION_TURNS=0     # used only when gap=0
export SHOPPILOT_FORCE_TOP10_TURN=4
export SHOPPILOT_OTHER_TWICE=1
export SHOPPILOT_CATEGORY_TAIL=1
export SHOPPILOT_EVIDENCE_RANK=1
export SHOPPILOT_FULL_MATCH=8          # 0 disables
```

## Layout

```text
starter/agent.py      Agent + SessionState + rank/ask/emit
starter/dense.py      hash / MiniLM dense backends
starter/rewrite.py    query brief helpers
starter/llm_*.py      optional fail-open LLM hooks (default off)
evaluator/            official local evaluator (do not modify for scoring)
cli_chat.py           Astrid interactive demo
tests/                unit tests
docs/                 Devpost paste, API contract, kit rules
data/                 public_set.jsonl; catalog.jsonl (local)
```

## Data

Catalog and sessions derive from Amazon Reviews 2023 (McAuley Lab, UCSD). See `DATA_ATTRIBUTION.md`. Catalog is read-only.

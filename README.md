# ShopPilot

## Project overview

ShopPilot is a **headless multi-turn shopping agent** for TikTok TechJam 2026 Track 4 (Shopping Copilot). It maps messy shopper text to a ranked list of frozen-catalog `parent_asin` values in **at most 10 turns**.

The official simulator only reveals hidden product constraints when `ask_attribute` is set. ShopPilot therefore always returns recommendations **and** one structured clarification on the same turn. State is a compact dialog tracker (slots, product family, gift audience, intent override). Retrieval is **in-memory hybrid**: SQLite FTS5 plus an optional hashed char-ngram dense lane. Ranking is lexical evidence (constraint coverage and exact phrases), not a trained LLM by default.

It is built on the [official conversational-search kit](https://github.com/TechJam2026/techjam-conversational-search). The scored default path is **offline**: Python stdlib + optional NumPy. No GPU, no paid API, no external vector DB.

**Public 200-session result** (`SHOPPILOT_DENSE=hash`), reproduced on CPU and Mac:

| Metric | Starter BM25 | ShopPilot |
|---|---:|---:|
| Hit@10 | 0.125 | **0.975** |
| MRR | 0.068 | **0.872** |
| MTTC | 9.81 | **3.01** |
| Efficiency | 0.119 | **0.800** |
| TechnicalScore | 0.107 | **0.909** |
| Tokens | 0 | **0** |

```text
TechnicalScore = 0.50·Hit@10 + 0.30·MRR + 0.20·clip((11 − MTTC) / 10, 0, 1)
```

| Scenario | N | Hit@10 | MRR | MTTC |
|---|---:|---:|---:|---:|
| Buying | 80 | 0.975 | 0.884 | 2.56 |
| Browsing | 80 | 0.975 | 0.855 | 2.99 |
| Intent override | 30 | 0.967 | 0.867 | 4.20 |
| Boundary | 10 | 1.000 | 0.933 | 3.10 |

Kit contract: `starter/agent.py` exports `Agent.reset` / `Agent.respond`. Demo CLI: `python cli_chat.py`.

## Setup and installation instructions

**Requirements:** Python **3.10+** (tested on 3.10–3.13). Default path needs **no pip packages**.

```bash
git clone https://github.com/algorathem/techjam2026-shopping-copilot.git
cd techjam2026-shopping-copilot
```

Download the frozen 50,000-product catalog from the official participant-kit release (not committed; ~60 MB unzipped):

```bash
gh release download participant-kit \
  --repo TechJam2026/techjam-conversational-search \
  --pattern catalog.jsonl.gz --dir data

python -c "import gzip,shutil,pathlib; p=pathlib.Path('data'); shutil.copyfileobj(gzip.open(p/'catalog.jsonl.gz','rb'), (p/'catalog.jsonl').open('wb'))"
```

Expect `data/catalog.jsonl` to contain **50,000** lines. Optional checksum: `data/SHA256SUMS`.

Optional NumPy for the hash dense lane used in the reported table:

```bash
pip install -r requirements.txt
# or: pip install "numpy>=1.24,<2.1"
```

Optional (off by default, not required to reproduce 0.909):

| Env | Effect |
|---|---|
| `SHOPPILOT_DENSE=hash` | Hashed n-gram dense lane (reported default) |
| `SHOPPILOT_DENSE=none` | FTS5 only |
| `SHOPPILOT_DENSE=minilm` | MiniLM embeddings (`sentence-transformers`) |
| `SHOPPILOT_LLM=1` + `XAI_API_KEY` or `GEMINI_API_KEY` | Optional LLM slot parse / top-20 rerank |

Never commit API keys. Official judging may disable network; the default path does not need it.

### Code layout

```text
starter/agent.py      Agent + SessionState (ingest, retrieve, rank, ask, emit)
starter/dense.py      Optional dense backends (hash / MiniLM)
starter/rewrite.py    Slot → short brief for optional LLM rerank
starter/llm_rerank.py Optional fail-open LLM rerank of top-20
starter/llm_slots.py  Optional fail-open LLM slot parse
evaluator/            Official local scorer — do not edit when reporting scores
cli_chat.py           Interactive demo (Astrid)
tests/                Unit tests for slots, rewrite, dense, evaluator
docs/                 Kit contract, Devpost notes
data/                 public_set.jsonl; catalog.jsonl (local only)
```

## Steps to reproduce your results

From the repository root, with `data/catalog.jsonl` present:

```bash
# 1. Unit tests
python -m unittest discover -s tests -q

# 2. Official 200-session evaluator (reported table)
export SHOPPILOT_DENSE=hash          # macOS / Linux / Git Bash
python -m evaluator.local_evaluator
```

The evaluator prints Hit@10, MRR, MTTC, Efficiency, and TechnicalScore, and writes `results.json` (gitignored). Do **not** edit `evaluator/` or `data/public_set.jsonl` when reporting.

Interactive smoke test (not scored):

```bash
python cli_chat.py --dense hash
```

Windows one-shot:

```powershell
cd C:\Users\USER\techjam-shopping-copilot
$env:SHOPPILOT_DENSE = "hash"
python -m unittest discover -s tests -q
python -m evaluator.local_evaluator
```

The 0.975 / 0.909 numbers above were produced with `SHOPPILOT_DENSE=hash` and no LLM env vars, on both an Intel CPU and Apple Silicon.

## A brief reflection on your solution's limitations and what you would improve given more time

**Limitations**

- Ranking is still mostly **lexical**. Paraphrases of a long Amazon feature sentence can retrieve the right category but miss the exact `parent_asin` (about 2.5% of public sessions).
- **Intent override** cannot convert before turn 3–4 by protocol, so MTTC on that slice is structurally higher even when Hit is strong.
- Default dense is **hashed char n-grams**, not a true embedding model. MiniLM exists as opt-in but is not the scored default (deps + first-run download).
- Optional LLM rerank/slots need a live key and may be **disabled at official scoring**. We therefore cannot depend on them for the primary number.
- Public-set metrics can **overfit**. The hidden 800 sessions use different users and targets.

**If we had more time**

- A calibrated local cross-encoder on the top 50 titles to lift MRR without an API.
- Leak-safe time-aware user/item stats only if extra signals were allowed (they are not in this catalog).
- Tighter override hygiene so discarded preference tokens never leak into FTS.
- Cache dense vectors more aggressively so CPU eval is minutes, not hours, on small laptops.

## Team member contributions

Solo / team work on this repository: implementation of `Agent`, hybrid retrieval, evaluation, demo CLI, and this README. Catalog and public sessions are from the organizer kit (Amazon Reviews 2023 / McAuley Lab). See `DATA_ATTRIBUTION.md`.

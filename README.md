# ShopPilot

Multi-turn shopping agent for TechJam Track 4 (Shopping Copilot). Finds a hidden catalog purchase in ≤10 turns via structured clarification and hybrid retrieval.

Built on the [official conversational-search kit](https://github.com/TechJam2026/techjam-conversational-search). Default path is **offline** (stdlib + optional NumPy hash dense). No required LLM, GPU, or vector DB.

## Public metrics (200 sessions)

`python -m evaluator.local_evaluator` — official weak BM25 starter vs ShopPilot dense backends:

| Metric | Starter BM25 | ShopPilot **hash** (default) | ShopPilot **minilm** (opt-in) |
|---|---:|---:|---:|
| Hit@10 | 0.125 | 0.975 | **0.985** |
| MRR | 0.068 | **0.872** | 0.861 |
| MTTC | 9.81 | 3.01 | **2.97** |
| Efficiency | 0.119 | 0.800 | 0.804 |
| TechnicalScore | 0.107 | 0.909 | **0.912** |

```text
TechnicalScore = 0.50·Hit@10 + 0.30·MRR + 0.20·clip((11 − MTTC) / 10, 0, 1)
```

**hash** (default): zero extra ML deps beyond optional NumPy; Tech **0.909**.  
**minilm** (`SHOPPILOT_DENSE=minilm`, local `all-MiniLM-L6-v2`, fusion weight **15**): Tech **0.912** (+0.003 vs hash), Hit **0.985** (3 misses); MRR slightly lower. Still **0 API tokens**. Override with `SHOPPILOT_DENSE_WEIGHT`.

Hash scenario breakdown (default ship):

| Scenario | N | Hit@10 | MRR | MTTC |
|---|---:|---:|---:|---:|
| Buying | 80 | 0.975 | 0.884 | 2.56 |
| Browsing | 80 | 0.975 | 0.855 | 2.99 |
| Intent override | 30 | 0.967 | 0.867 | 4.20 |
| Boundary | 10 | 1.000 | 0.933 | 3.10 |

MiniLM scenarios: buying Hit **0.988**; browsing MRR **0.862** / MTTC **2.94**; override/boundary unchanged at Hit 0.967 / 1.0. Full tables: `docs/benchmark_dense.md`.

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

**Retrieve.** In-memory SQLite FTS5 (OR session terms + AND constraint lane) plus optional dense char-ngram hash (`starter/dense.py`). MiniLM (`all-MiniLM-L6-v2`) is opt-in via `SHOPPILOT_DENSE=minilm`. Catalog is frozen; no external search.

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

Optional MiniLM dense (`pip install sentence-transformers`, then `SHOPPILOT_DENSE=minilm`) and optional LLM slots/rerank are env-gated and **off by default**. First MiniLM run downloads `all-MiniLM-L6-v2` and caches `data/dense_minilm_all-MiniLM-L6-v2.npz` (gitignored). See `starter/llm_slots.py` / `starter/llm_rerank.py`.

```bash
# MiniLM 200-eval (opt-in; scored default stays hash)
pip install "numpy>=1.24,<2.1" sentence-transformers
export SHOPPILOT_DENSE=minilm
python scripts/build_minilm_cache.py          # skip if the npz already exists
python -m evaluator.local_evaluator --output results_minilm.json
python scripts/eval_subset.py --limit 24      # fast A/B vs hash
```

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

## Future work 

ShopPilot’s ship path is already near the public-200 ceiling (hash Tech ~0.909, MiniLM ~0.912, ≤5 misses). With unlimited time we would not replace the offline hybrid core; we would attack the residual miss tail and the MRR freeze with measured upgrades:

1. Stronger local dense recall. Keep FTS5 as the backbone; swap or stack denser on-device encoders (or multi-field embeddings over title + features + leaf category) and retune late-fusion weights. MiniLM already shows the shape of the gain: Hit 0.975→0.985 at 0 API tokens, with a small MRR trade — a reminder that recall lifts must be gated by emission policy.

2. Field-aware lexical IR. Move from a single text blob to weighted fields (title, bullets, brand, category tail) and add phrase / proximity soft features into the evidence ranker. We would avoid hard boolean filters: on this catalog, hard elimination of missing tokens previously reduced TechnicalScore.

3. Catalog-grounded query expansion. Build a small, high-precision synonym/morphology pack mined from the frozen CSJ corpus and public sessions only — not web-scraped thesauri — to improve recall when shopper language diverges from title tokens.

4. Top-K learned re-ranking. Train a lightweight cross-encoder or pairwise model only on the hybrid shortlist (e.g. top 50), with cross-validated folds on the public 200, optimizing MRR under the same first-hit stopping rule.

5. Joint ask + emission policy. Co-optimize the second-other schedule and margin-gated Top-1/Top-10 emission against TechnicalScore, with hard guardrails so no change ships below the hash floor (~0.909).

We would not revisit pure maximum information-gain ask selection, always-on cloud LLM retrieval, or inventing new ask_attribute values: those either failed A/B on this simulator or violate the kit protocol. Fuzzy/wildcard matching remains valuable for real-world ASR/typos but is out of scope for the official kit assumptions.

Every candidate change would require: unit tests, full public-200 eval, scenario breakdown (buy/browse/override/boundary), and a miss-category autopsy before adoption.


## Data

Catalog and sessions derive from Amazon Reviews 2023 (McAuley Lab, UCSD). See `DATA_ATTRIBUTION.md`. Catalog is read-only.

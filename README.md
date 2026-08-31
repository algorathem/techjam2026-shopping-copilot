# ShopPilot — TechJam 2026 Conversational Shopping Agent

Track **4. Shopping Copilot**: a headless shopping agent that finds a hidden Amazon purchase in at most 10 turns.

This repository starts from the official
[TechJam conversational-search kit](https://github.com/TechJam2026/techjam-conversational-search)
and replaces the weak BM25 starter with a **stateful hybrid retriever**. It uses
the Python standard library only (no LLM, no GPU, no vector database).

## Results on the public 200-session set

Official weak BM25 starter vs this agent (`python -m evaluator.local_evaluator`):

| Metric | Starter BM25 | ShopPilot (hash) | + MiniLM opt-in |
|---|---:|---:|---:|
| Hit Rate@10 | 0.125 | **0.935** | 0.925 |
| MRR | 0.068 | **0.558** | 0.574 |
| MTTC | 9.81 | **3.03** | 3.04 |
| Efficiency | 0.119 | **0.798** | 0.796 |
| TechnicalScore | 0.107 | **0.794** | **0.794** |

Default / judge-friendly path is **hash** (or `none` without NumPy). MiniLM is explicit: `SHOPPILOT_DENSE=minilm` (needs `sentence-transformers`, first run embeds 50k once). Hash path includes weak long-term profile priors + catalog rating tie-breaks that scale down as session constraints accumulate (cold-start / tie-break only).

TechnicalScore = `0.50×Hit@10 + 0.30×MRR + 0.20×clip((11−MTTC)/10, 0, 1)`.

By scenario (hash default):

| Scenario | N | Hit@10 | MRR | MTTC |
|---|---:|---:|---:|---:|
| Buying | 80 | 0.950 | 0.559 | 2.33 |
| Browsing | 80 | 0.913 | 0.498 | 3.39 |
| Intent override | 30 | 0.967 | 0.715 | 4.07 |
| Boundary | 10 | 0.800 | 0.460 | 3.60 |

Token usage: **0** on lexical/dense paths.

## How it addresses the four pillars

1. **Intent routing & hybrid pipeline.** Buying vs browsing is inferred from the
   first message. Retrieval is multi-lane in-memory: FTS5 (OR over session terms,
   AND over constraint tokens) plus an optional dense hashed char-ngram lane
   (`starter/dense.py`, NumPy when available) for paraphrase recall/rerank,
   then constraint-coverage scoring. MiniLM is opt-in via `SHOPPILOT_DENSE=minilm`.
2. **Multi-turn state machine.** Slots accumulate with source tags
   (`soft` / `disclosed` / `override`). `Actually, ignore my earlier preference`
   erases only soft prefs (keeps already-disclosed hard facts the simulator will
   not re-send), blocks discarded tokens from FTS, truncates pre-override
   message history for retrieval, and resets `asked` so `other` can re-fire.
   `I don't have a preference for X` marks `X` as don't-care (boundary).
3. **Dynamic context / clarification.** The official simulator only reveals
   hidden product constraints when `ask_attribute` is set. The agent always
   returns a Top-10 **and** asks. The first question is `other` (simulator
   catch-all that dumps remaining constraints). Later questions follow the
   kit-tuned static order color → material → style → … (public-set A/B:
   pure max-IG over the candidate pool *drops* TechnicalScore ~0.03 because
   high-entropy brand/store splits rarely match the simulator classifier).
   Facet tags are still extracted per product so `message` can ground options
   in the live pool (e.g. "black, navy, grey?").
4. **Efficiency.** Asking and recommending on the same turn cuts MTTC. No model
   API is required, so official scoring can run with network disabled.

## Setup

Python **3.10+** (tested on 3.13). No pip packages for the default path.

Optional **dense hybrid lane** (auto when NumPy is installed; judges without
NumPy get the stdlib FTS path):

```bash
pip install "numpy>=1.24,<2.1"          # hashed char-ngram backend
# optional:
# pip install sentence-transformers
# export SHOPPILOT_DENSE=minilm

export SHOPPILOT_DENSE=hash            # or none|auto|minilm
python -m evaluator.local_evaluator
```

Optional **LLM semantic rerank** (off unless you set both vars). Judges may disable network, so this only shuffles the already-retrieved top 20:

```powershell
$env:XAI_API_KEY = "xai-..."           # https://console.x.ai
$env:SHOPPILOT_LLM = "1"
python -m evaluator.local_evaluator
```

```bash
git clone <this-repo> techjam-shopping-copilot
cd techjam-shopping-copilot

# Frozen 50k catalog from the official participant-kit release
gh release download participant-kit --repo TechJam2026/techjam-conversational-search --pattern catalog.jsonl.gz --dir data
python -c "import gzip,shutil,pathlib; p=pathlib.Path('data'); shutil.copyfileobj(gzip.open(p/'catalog.jsonl.gz','rb'), (p/'catalog.jsonl').open('wb'))"
```

Verify `data/SHA256SUMS` if you also download that file. Expected: 50,000 catalog rows.

## Reproduce

From the repository root:

```bash
# unit tests
python -m unittest tests.test_agent_slots tests.test_rewrite tests.test_dense tests.test_evaluator -q

# official public metrics (writes results.json)
export SHOPPILOT_DENSE=hash    # or none | minilm
python -m evaluator.local_evaluator

# interactive backend demo (no UI required for the track)
python cli_chat.py --dense hash
```

The evaluator writes `results.json` (gitignored) with per-session hits and the
aggregate metrics above. Do not edit `evaluator/` or `data/public_set.jsonl`
when reporting scores.

Agent entry point (required interface): `starter/agent.py` → class `Agent`
(`reset` / `respond`).

Optional LLM rerank (network; off by default):

```bash
export SHOPPILOT_LLM=1
export GEMINI_API_KEY=***          # or XAI_API_KEY
export SHOPPILOT_GEMINI_MODEL=gemini-flash-latest
python -m evaluator.local_evaluator
```

## Limitations and what we would do with more time

- Retrieval is hybrid lexical + optional dense. Near-paraphrases of a feature
  sentence can still miss the exact `parent_asin` (~7% of public sessions).
  `SHOPPILOT_DENSE=minilm` (local MiniLM over 50k titles) is the next step when
  sentence-transformers is available; hash n-grams already recover some gaps.
- Intent-override sessions cannot convert before turn 3–4 by protocol; MTTC on
  that slice is structurally higher. Soft-only wipe + ask reset lifted override
  Hit@10 from 0.80 → 0.97 and MTTC from 5.8 → 4.1 on the public set.
- Ask *order* after `other` is static by design (pool max-IG ask policy dropped
  TechnicalScore on this simulator). Adaptivity is slot memory + retrieval.
- LLM rerank is opt-in (`SHOPPILOT_LLM=1` + Gemini or xAI key). Without a key the
  lexical/dense path still scores.
- We did not use the private 800-session set. Public-set numbers can overfit.

## Team

Solo. All implementation, evaluation, and write-up by the submitting participant.

## Data

Catalog and sessions are derived from Amazon Reviews 2023 (McAuley Lab, UCSD).
See `DATA_ATTRIBUTION.md`. The catalog is read-only; no ASINs are injected.

## Submission notes

- Devpost paste-ready description: `docs/DEVPOST.md`
- Demo video shot list (backend walkthrough): `docs/DEMO_VIDEO_SCRIPT.md`
- Impact narrative (cited): `docs/REAL_WORLD_IMPACT.md`

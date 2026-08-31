# ShopPilot — TechJam 2026 Conversational Shopping Agent

Track **4. Shopping Copilot**: a headless shopping agent that finds a hidden Amazon purchase in at most 10 turns.

This repository starts from the official
[TechJam conversational-search kit](https://github.com/TechJam2026/techjam-conversational-search)
and replaces the weak BM25 starter with a **stateful hybrid retriever**. It uses
the Python standard library only (no LLM, no GPU, no vector database).

## Results on the public 200-session set

Official weak BM25 starter vs this agent (`python -m evaluator.local_evaluator`):

| Metric | Starter BM25 | ShopPilot (hash) |
|---|---:|---:|
| Hit Rate@10 | 0.125 | **0.970** |
| MRR | 0.068 | **0.836** |
| MTTC | 9.81 | **2.93** |
| Efficiency | 0.119 | **0.807** |
| TechnicalScore | 0.107 | **0.897** |

Default path is offline **hash** dense + rules (or `none` without NumPy). MiniLM remains opt-in (`SHOPPILOT_DENSE=minilm`). Score lift vs earlier ~0.794 stack comes from peer-validated levers: **precision Top-1 for turns 1–2**, **category-tail exact bonus**, and a **second `other` ask** when evidence is still thin (each A/B’d; disable via env if needed).

TechnicalScore = `0.50×Hit@10 + 0.30×MRR + 0.20×clip((11−MTTC)/10, 0, 1)`.

By scenario (hash default):

| Scenario | N | Hit@10 | MRR | MTTC |
|---|---:|---:|---:|---:|
| Buying | 80 | 0.975 | 0.833 | 2.54 |
| Browsing | 80 | 0.963 | 0.816 | 2.85 |
| Intent override | 30 | 0.967 | 0.866 | 4.17 |
| Boundary | 10 | 1.000 | 0.933 | 3.00 |

Token usage: **0** on lexical/dense paths.

Env knobs (defaults are the scored path):

```bash
export SHOPPILOT_PRECISION_TURNS=2   # 0 disables Top-1 early turns
export SHOPPILOT_OTHER_TWICE=1       # 0 disables second other
export SHOPPILOT_CATEGORY_TAIL=1     # 0 disables tail bonus
```

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
   pure max-IG over the candidate pool *drops* TechnicalScore (historical ~0.72) because
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
python -m unittest tests.test_agent_slots tests.test_rewrite tests.test_dense tests.test_llm_slots tests.test_evaluator -q

# official public metrics (writes results.json)
export SHOPPILOT_DENSE=hash    # or none | minilm
python -m evaluator.local_evaluator

# interactive demo — Astrid CLI (single brand UI)
python cli_chat.py --dense hash
```

The evaluator writes `results.json` (gitignored) with per-session hits and the
aggregate metrics above. Do not edit `evaluator/` or `data/public_set.jsonl`
when reporting scores.

Agent entry point (required interface): `starter/agent.py` → class `Agent`
(`reset` / `respond`).

Optional light LLM (network; **off by default** — default path stays offline ~Tech 0.897):

```bash
export SHOPPILOT_LLM=1
export GEMINI_API_KEY=***          # or XAI_API_KEY
export SHOPPILOT_GEMINI_MODEL=gemini-flash-latest

# Dual-meaning / multi-slot normalizer (recommended experiment)
export SHOPPILOT_LLM_SLOTS=lowconf   # or always | off
# export SHOPPILOT_LLM_SLOTS_THRESHOLD=0.55
# export SHOPPILOT_LLM_SLOTS_MIN_P=0.55

# Separate: candidate rerank (slow; small MRR bump in past A/B)
# export SHOPPILOT_LLM_RERANK=1

python cli_chat.py --dense hash
# or: python -m evaluator.local_evaluator
```

| Flag | Default | Role |
|---|---|---|
| `SHOPPILOT_LLM_SLOTS=off` | **off** | No NLU calls |
| `=always` | | One JSON slot parse **every** user turn |
| `=lowconf` | | Call only when rule confidence is low (dual meanings / vague freeform) |
| `SHOPPILOT_LLM_RERANK=1` | off | Rerank top candidates (independent of slots) |

LLM output is validated against the official `ask_attribute` enum (+ internal family/audience). Failures fall back to rules. **Do not** submit a required-API path for judging.

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
- Optional LLM dual-meaning slot NLU (`SHOPPILOT_LLM_SLOTS=lowconf|always`) and
  rerank (`SHOPPILOT_LLM_RERANK=1`) need a key and network. Default remains
  pure lexical/dense. Validate public Tech ≥ ~0.897 before relying on LLM modes.
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

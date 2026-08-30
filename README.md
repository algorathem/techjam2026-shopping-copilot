# ShopPilot — TechJam 2026 Conversational Shopping Agent

Track **4. Shopping Copilot**: a headless shopping agent that finds a hidden Amazon purchase in at most 10 turns.

This repository starts from the official
[TechJam conversational-search kit](https://github.com/TechJam2026/techjam-conversational-search)
and replaces the weak BM25 starter with a **stateful hybrid retriever**. It uses
the Python standard library only (no LLM, no GPU, no vector database).

## Results on the public 200-session set

Official weak BM25 starter vs this agent (`python -m evaluator.local_evaluator`):

| Metric | Starter BM25 | ShopPilot | Δ |
|---|---:|---:|---:|
| Hit Rate@10 | 0.125 | 0.900 | +0.775 |
| MRR | 0.068 | 0.503 | +0.435 |
| MTTC | 9.81 | 3.38 | −6.43 |
| Efficiency | 0.119 | 0.762 | +0.643 |
| TechnicalScore | 0.107 | 0.753 | +0.646 |

TechnicalScore = `0.50×Hit@10 + 0.30×MRR + 0.20×clip((11−MTTC)/10, 0, 1)`.

By scenario (this agent):

| Scenario | N | Hit@10 | MRR | MTTC |
|---|---:|---:|---:|---:|
| Buying | 80 | 0.938 | 0.539 | 2.30 |
| Browsing | 80 | 0.913 | 0.484 | 3.46 |
| Intent override | 30 | 0.800 | 0.493 | 5.80 |
| Boundary | 10 | 0.800 | 0.398 | 4.10 |

Token usage: **0**. Offline fallback is the only path.

## How it addresses the four pillars

1. **Intent routing & hybrid pipeline.** Buying vs browsing is inferred from the
   first message. Retrieval is two-lane in-memory FTS5 (OR over session terms,
   AND over constraint tokens) followed by a constraint-coverage rerank.
2. **Multi-turn state machine.** Slots accumulate. `Actually, ignore my earlier
   preference` erases prior constraints (intent override). `I don't have a
   preference for X` marks `X` as don't-care (boundary).
3. **Dynamic context / clarification.** The official simulator only reveals
   hidden product constraints when `ask_attribute` is set. The agent always
   returns a Top-10 **and** asks. The first question is `other` (simulator
   catch-all that dumps remaining constraints). Later questions follow
   color → material → style → …
4. **Efficiency.** Asking and recommending on the same turn cuts MTTC. No model
   API is required, so official scoring can run with network disabled.

## Setup

Python **3.10+** (tested on 3.13). No pip packages for the default path.

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
python -m unittest tests.test_agent_slots tests.test_evaluator -q
python -m evaluator.local_evaluator
```

The evaluator writes `results.json` (gitignored) with per-session hits and the
aggregate metrics above. Do not edit `evaluator/` or `data/public_set.jsonl`
when reporting scores.

Agent entry point (required interface): `starter/agent.py` → class `Agent`.

## Limitations and what we would do with more time

- Retrieval is lexical. Near-paraphrases of a feature sentence can miss the
  exact `parent_asin` even when the category is right (about 10% of public
  sessions). A local MiniLM index over the 50k titles would help without an API.
- Intent-override sessions cannot convert before turn 3–4 by protocol; MTTC on
  that slice is structurally higher.
- LLM rerank is opt-in (`SHOPPILOT_LLM=1` + `XAI_API_KEY`). Without a key the
  lexical path still scores. Mean hit rank is ~3.6; rerank is aimed at MRR.
- We did not use the private 800-session set. Public-set numbers can overfit.

## Team

Solo. All implementation, evaluation, and write-up by the submitting participant.

## Data

Catalog and sessions are derived from Amazon Reviews 2023 (McAuley Lab, UCSD).
See `DATA_ATTRIBUTION.md`. The catalog is read-only; no ASINs are injected.

# Dense backend benchmark (public 200)

Official `python -m evaluator.local_evaluator`. Offline, 0 API tokens.
MiniLM = local `sentence-transformers/all-MiniLM-L6-v2`.

## Headlines

| Metric | hash (default) | minilm w=10 | **minilm w=15 (opt-in default)** |
|---|---:|---:|---:|
| TechnicalScore | 0.909068 | 0.910487 | **0.911568** |
| Hit@10 | 0.975 | 0.980 | **0.985** |
| MRR | **0.872228** | 0.866956 | 0.861226 |
| MTTC | 3.005 | 2.980 | **2.965** |
| Misses | 5 | 4 | **3** |

## MiniLM fusion-weight A/B

| Weight | Tech | Hit | Notes |
|---:|---:|---:|---|
| 6–8 | ~0.905–0.906 | 0.975 | too weak |
| 10 | 0.910 | 0.980 | prior default |
| 12 | ~0.911 | 0.980 | flat |
| **15** | **0.912** | **0.985** | **ship** |
| 18–20 | ~0.908 | 0.980 | over-weight |

## Rejected follow-ups

| Idea | Result |
|---|---|
| Title-heavy product text | Tech down (~0.910, Hit 0.98) |
| RRF dense∪lexical | Tech crash (~0.83–0.88) |

## Misses (w=15)

`public_0020`, `public_0076`, `public_0144`  
(fixed vs hash: `0174` bathrobe, `0175` boot-cut jean)

## Reproduce

```bash
export SHOPPILOT_DENSE=minilm
# code default weight is 15; or:
export SHOPPILOT_DENSE_WEIGHT=15
python -m evaluator.local_evaluator --output results_minilm.json
```

Default scored path remains **hash** (minimal deps).

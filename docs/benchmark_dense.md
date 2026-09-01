# Dense backend benchmark (public 200)

Official `python -m evaluator.local_evaluator`. Offline, 0 API tokens.

## Headlines

| Metric | hash (default) | **minilm w=15** | **bge w=18** |
|---|---:|---:|---:|
| TechnicalScore | 0.909068 | 0.911568 | **0.912270** |
| Hit@10 | 0.975 | **0.985** | 0.980 |
| MRR | **0.872228** | 0.861226 | **0.871234** |
| MTTC | 3.005 | 2.965 | **2.955** |
| Misses | 5 | **3** | 4 |
| Tokens | 0 | 0 | 0 |

**Models (local ST only)**  
- minilm = `sentence-transformers/all-MiniLM-L6-v2`  
- bge = `BAAI/bge-small-en-v1.5`

## MiniLM fusion-weight A/B

| Weight | Tech | Hit | Notes |
|---:|---:|---:|---|
| 6–8 | ~0.905–0.906 | 0.975 | too weak |
| 10 | 0.910 | 0.980 | prior default |
| **15** | **0.912** | **0.985** | **ship minilm** |
| 18–20 | ~0.908 | 0.980 | over-weight |

## BGE-small fusion-weight A/B

| Weight | Tech | Hit | MRR | Miss |
|---:|---:|---:|---:|---:|
| 8 | 0.908 | 0.975 | 0.869 | 5 |
| 10–16 | ~0.909 | 0.975 | ~0.871 | 5 |
| **17** | 0.9122 | 0.980 | 0.871 | 4 |
| **18** | **0.9123** | 0.980 | **0.871** | 4 |
| 20 | 0.9121 | 0.980 | 0.871 | 4 |
| 22–25 | ~0.911 | 0.980 | ~0.868 | 4 |

Verified twice at w=18. **Ship bge default weight = 18.**

## Tradeoff: MiniLM vs BGE

| | MiniLM w=15 | BGE w=18 |
|---|---|---|
| Best Tech | 0.9116 | **0.9123** |
| Best Hit | **0.985** (3 misses) | 0.980 (4 misses) |
| Best MRR among ST | lower | **higher (~0.871)** |
| Speed / size | smaller/faster | slightly heavier encode |

Pick **minilm** if Hit is priority; **bge** if Tech/MRR edge. Default score path remains **hash**.

## Rejected follow-ups

| Idea | Result |
|---|---|
| Title-heavy product text | Tech down |
| RRF dense∪lexical | Tech crash |

## Misses

| Backend | IDs |
|---|---|
| hash | 0020, 0076, 0144, 0174, 0175 |
| minilm w=15 | 0020, 0076, 0144 |
| bge w=18 | 0020, 0076, 0144, 0174 |

## Reproduce

```bash
# MiniLM
export SHOPPILOT_DENSE=minilm
python scripts/build_st_cache.py --backend minilm   # if cache missing
python -m evaluator.local_evaluator --output results_minilm.json

# BGE
export SHOPPILOT_DENSE=bge
python scripts/build_st_cache.py --backend bge
python -m evaluator.local_evaluator --output results_bge.json
# optional: export SHOPPILOT_DENSE_WEIGHT=18
```

Default scored path remains **hash** (minimal deps).

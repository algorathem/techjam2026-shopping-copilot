# Dense backend benchmark (public 200)

Official `python -m evaluator.local_evaluator` on the frozen public set.
Both paths offline (no API tokens). MiniLM = local `sentence-transformers/all-MiniLM-L6-v2` + cached `data/dense_minilm_all-MiniLM-L6-v2.npz`.

## Headlines

| Metric | hash (default) | minilm | Δ |
|---|---:|---:|---:|
| TechnicalScore | 0.909068 | **0.910487** | **+0.001419** |
| Hit@10 | 0.975 | **0.980** | +0.005 |
| MRR | **0.872228** | 0.866956 | −0.005272 |
| MTTC | 3.005 | **2.980** | −0.025 |
| Efficiency | 0.7995 | 0.802 | +0.0025 |
| Misses | 5 | **4** | −1 |
| Tokens | 0 | 0 | — |

## Misses

| Backend | Miss sample_ids |
|---|---|
| hash | public_0020, public_0076, public_0144, public_0174, public_0175 |
| minilm | public_0020, public_0076, public_0144, public_0175 |

**Fixed by minilm:** `public_0174` (mens bathrobe).  
**No regressions** vs hash miss set.

## Scenarios

| Scenario | hash Hit / MRR / MTTC | minilm Hit / MRR / MTTC |
|---|---|---|
| Buying | 0.975 / 0.884 / 2.56 | **0.988** / 0.863 / 2.55 |
| Browsing | 0.975 / 0.855 / 2.99 | 0.975 / **0.862** / **2.94** |
| Intent override | 0.967 / 0.867 / 4.20 | 0.967 / 0.869 / 4.20 |
| Boundary | 1.000 / 0.933 / 3.10 | 1.000 / 0.933 / 3.10 |

## Reproduce

```bash
# default
export SHOPPILOT_DENSE=hash
python -m evaluator.local_evaluator --output results_hash.json

# MiniLM opt-in
pip install "numpy>=1.24,<2.1" sentence-transformers
export SHOPPILOT_DENSE=minilm
python scripts/build_minilm_cache.py   # if npz missing
python -m evaluator.local_evaluator --output results_minilm.json
```

**Ship recommendation:** keep **hash** as default (minimal deps). Document **minilm** as measured +0.001 Tech / +Hit opt-in when `sentence-transformers` is allowed.

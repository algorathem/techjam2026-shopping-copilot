# Error analysis (public 200)

14 / 200 sessions miss Top-10 within 10 turns
(TechnicalScore 0.788 with dense hash; 0.781 offline FTS-only; 0.753 pre-override-hygiene).

## False negatives (typical)

- **Lexical / near-duplicate gap (partially mitigated).** The hidden constraint is a long feature sentence. FTS5 retrieves the right category but a sibling title can outrank the exact `parent_asin`. Hashed char-ngram dense recall+rerank lifts some of these (Hit 0.925 → 0.930, MRR 0.537 → 0.550). Remaining misses need true semantic embeddings (MiniLM opt-in).
- **Intent override (mitigated).** Protocol forbids a hit before turn 3 or 4. Soft-only wipe keeps disclosed hard facts the simulator will not re-send; discarded soft tokens are blocked from FTS; `asked` resets so `other` re-fires.
- **Boundary first turn.** The first `ask_attribute` is always answered with "no preference", so turn 1 is under-informed.

## False positives (typical)

- High-review popular items in the same category/color outrank the true target when constraints are still generic ("I'm still exploring").
- Store-name overlap: a brand token matches many SKUs from the same seller.

## Trade-off

We optimize MTTC by asking `other` immediately (dumps hidden constraints) while still emitting a Top-10 every turn. That raises Hit@10 a lot versus silent BM25, at the cost of sometimes ranking a popular sibling above the exact ASIN.

### Ask policy A/B

| Ask policy | Hit@10 | MRR | MTTC | Tech |
|---|---:|---:|---:|---:|
| Static order after `other` (shipped) | 0.900 | 0.503 | 3.38 | 0.753 |
| Coverage-gated pool swap | 0.900 | 0.502 | 3.42 | 0.752 |
| Pure max pool info-gain | 0.865 | 0.478 | 3.78 | 0.720 |

### Override hygiene delta

| Slice | Before | After |
|---|---:|---:|
| Overall Tech | 0.753 | **0.781** |
| Override Hit@10 | 0.800 | **0.967** |
| Override MRR | 0.493 | **0.714** |
| Override MTTC | 5.80 | **4.07** |

### Dense hybrid weight sweep (`SHOPPILOT_DENSE=hash`)

| Weight | Hit@10 | MRR | MTTC | Tech |
|---|---:|---:|---:|---:|
| 0 (FTS only) | 0.925 | 0.537 | 3.12 | 0.781 |
| 1.5 | 0.925 | 0.540 | 3.11 | 0.783 |
| 2.5 | 0.930 | 0.542 | 3.10 | 0.786 |
| 3.2 | 0.930 | 0.542 | 3.09 | 0.786 |
| **4.5 (shipped)** | **0.930** | **0.550** | **3.10** | **0.788** |
| 6.0 | 0.930 | 0.547 | 3.10 | 0.787 |

`SHOPPILOT_DENSE=none` matches the weight-0 row (stdlib judges / no NumPy).

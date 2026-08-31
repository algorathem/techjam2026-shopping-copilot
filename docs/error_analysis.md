# Error analysis (public 200)

14 / 200 miss on hash default (Tech **0.789**); MiniLM opt-in Tech **0.794** (15 miss, higher MRR).

## Clarifying-question strategy — keep current (measured)

Simulator only reveals hidden constraints when `ask_attribute` is set. Policy:

1. **Always ask + always Top-10** (until turn 9) — silent turns waste MTTC.
2. **First ask = `other`** — catch-all dumps up to 2 undisclosed constraints (max protocol info gain).
3. **Then static order** color → material → style → brand → …
4. **Boundary fix:** if user says no-pref for `other`, do **not** kill the catch-all; re-ask `other` next turn (boundary MTTC 4.1 → 3.6).
5. **After override:** reset `asked` so `other` can fire again.

### Ask-policy A/B (do not reopen without new evidence)

| Policy | Tech | Call |
|---|---:|---|
| other-first + static order | **0.753+** stack | **shipped** |
| coverage-gated pool swap | 0.752 | skip |
| pure max pool info-gain | 0.720 | **reject** (brand entropy trap) |
| early belief-stop (`ask=null`) | ~0.720 | **reject** (simulator stalls) |
| LLM-chosen asks | unmeasured | high risk; kit classifier ≠ free-form facets |

**Verdict:** clarifying questions are highly relevant, but “smarter” selection lost to the simulator’s closed attribute enum. Improve **messages** and **retrieval**, not the ask enum order.

## Dense backends

| Backend | Tech | Hit | MRR | MTTC | Notes |
|---|---:|---:|---:|---:|---|
| none | 0.781 | 0.925 | 0.537 | 3.12 | stdlib |
| hash w=4.5 (default) | **0.789** | **0.930** | 0.553 | 3.08 | + boundary fix |
| minilm w=10 (opt-in) | **0.794** | 0.925 | **0.574** | 3.04 | best MRR; heavier |

## False negatives (residual)

- Near-duplicate titles (lexical siblings outrank true ASIN) — MiniLM helps MRR more than Hit.
- Boundary still only 0.80 Hit (n=10).
- One override miss left.

## Override hygiene (kept)

| Slice | Before | After |
|---|---:|---:|
| Override Hit@10 | 0.800 | **0.967** |
| Override MTTC | 5.80 | **4.07** |

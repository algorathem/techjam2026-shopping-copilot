# Worth-trying experiment results

Floor before this round: Tech **0.908104**, Hit 0.975, MRR 0.860, misses 5.

## Implemented

1. **Miss-oriented family fixes**
   - `boot cut` / jeans before footwear patterns
   - `lounge` family (robe / bathrobe / sleepwear)
   - hoodie/tee cues on top
2. **Canonical dense query** (off by default — hurt MRR slightly)
3. **Recency weight on evidence** (off by default — flat/slight down at 1.0)

## A/B (public 200, hash)

| Config | Tech | Hit | MRR | Misses |
|---|---:|---:|---:|---:|
| Ship floor | 0.908104 | 0.975 | 0.860 | 5 |
| Family fixes only | **0.908104** | 0.975 | 0.860 | 5 |
| + canonical dense | 0.9074 | 0.975 | 0.858 | 5 |
| + recency 0.35 | 0.9080 | 0.975 | 0.860 | 5 |
| + canonical + recency 0.5 | 0.9073 | 0.975 | 0.858 | 5 |

## Takeaway

- Family disambiguation is **correct engineering** (boot-cut ≠ boots) but **did not clear the 5 public misses** on this run (targets may still fail for other reasons: novelty tees, sparse titles, override).
- Canonical query / recency **not** default.
- Cross-encoder Top-30 **not** run (heavy deps); optional later.
- **Keep Tech 0.9081 ship path**; freeze further global rank soup.

## Miss IDs still open

`public_0020`, `public_0076`, `public_0144`, `public_0174`, `public_0175`
(novelty grandma tee, army hoodie, winter parka override, bathrobe, boot-cut jean)

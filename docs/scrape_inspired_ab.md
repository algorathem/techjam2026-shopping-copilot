# Scrape-inspired ideas A/B (public 200)

Floor (margin gap=10 ship): **Tech 0.909068**, Hit 0.975, MRR 0.872, MTTC 3.005.

Ideas taken from public peer patterns (Unknownflow emission/evidence, multi-band K):

| Exp | Idea | Tech | Δ | Hit | MRR | MTTC |
|---|---|---:|---:|---:|---:|---:|
| **base** | ship gap=10 | **0.909068** | 0 | 0.975 | 0.872 | 3.005 |
| mid5 | K=5 when mid margin≥5 | 0.909144 | +0.00008 | 0.975 | 0.871 | 2.980 |
| mid3 | K=3 mid band | 0.909044 | −0.00002 | 0.975 | 0.871 | 2.985 |
| mid3_delay | + delayed other precision | 0.909044 | −0.00002 | 0.975 | 0.871 | 2.985 |
| feat | multi-token feature exact +6 | 0.908968 | −0.00010 | 0.975 | 0.872 | 3.010 |
| feat8 | feature exact +8 | 0.908218 | −0.00085 | 0.975 | 0.870 | 3.010 |
| mid3g4 / g6 | other mid thresholds | ≤0.9085 | down | 0.975 | ↓ | ~2.97 |
| all3 | mid+delay+feat | 0.908294 | −0.00077 | 0.975 | 0.868 | 2.985 |

## Verdict

- **No clear win** above noise. mid5 is +0.00008 with **lower MRR** — do not ship.
- Peer levers already absorbed (evidence rank, other-first, precision/margin emission).
- Remaining leader gap is deeper catalog/field coupling + Hit≈1.0, not another emission band.

## Flags (optional, default off)

```bash
SHOPPILOT_MID_GAP=5 SHOPPILOT_MID_K=3   # three-band emission
SHOPPILOT_DELAYED_OTHER=1               # Top-1 longer after declined other
SHOPPILOT_FEAT_EXACT=1                  # multi-token exact bonus
```

Ship defaults unchanged: `PRECISION_GAP=10`, no mid band, no feat exact, delayed off.

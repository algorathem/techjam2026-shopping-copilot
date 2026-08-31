# Override + novelty miss investigation

## Root cause (replay of 5 public misses)

Not primarily "shoes". Failures:

| ID | Type | Issue |
|---|---|---|
| public_0144 | **intent_override** | After pivot to `polyester`, state still flooded with Zipper closure / Imported / 100% blends; target winter parka never enters Top-10 until late attempts |
| public_0020 | novelty tee | Category "Novelty Women" + cotton/grey; FTS dominated by generic cotton tees; title-specific "Grandma" never retrieved |
| public_0076 | novelty hoodie | "Women Hoodies" + cotton/grey; military/girlfriend title tokens unused |
| public_0174 | bathrobe | Lounge family OK; polyester-only list is huge; spa robe not distinctive enough |
| public_0175 | boot-cut jean | Family bottom OK; cotton jeans pool huge; Ariat-specific not retrieved |

## What we tried

1. **Drop catalog filler constraints** (Imported, Zipper closure, long % blend tables)
2. **Override also strips fillers**
3. **Novelty/hoodie/robe/jean path boosts**
4. **Aggressive FTS token blocklist** for filler tokens

## Result

- Isolated replays: override parka + robe **could** hit (rank ~6)
- **Full public 200**: Tech **0.908 → 0.84–0.88** (Hit drop) — classic "strip Imported hurts recall" failure mode
- **Reverted** to ship baseline Tech **0.908104**

## Why hard to fix without regression

- Kit discloses boilerplate as real soft/hard strings; many true products only match via shared "Imported"/closure noise in the OR query
- Novelty targets need **title-phrase** retrieval (Grandma, Army Girlfriend) the simulator never says
- Override "new_value" is often a lone material (`polyester`) — too weak alone to unique the parka among thousands of polyester coats

## Safer future ideas (not shipped)

- Title-only OR lane for tokens from **category path** (Novelty, Hoodies) without dropping Imported globally
- After override, boost products matching **override message material + existing category path** only
- Optional second FTS query: `category AND material` without filler — merge candidates (don't replace)

## Status

Ship path unchanged: Tech 0.908, Hit 0.975, MRR 0.860. Override/novelty remain known hard tails.

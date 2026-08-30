# Error analysis (public 200)

20 / 200 sessions miss Top-10 within 10 turns.

## False negatives (typical)

- **Lexical gap.** The hidden constraint is a long feature sentence. FTS5 retrieves the right category (e.g. walking shoes) but a near-duplicate title ranks above the exact `parent_asin`.
- **Intent override.** Protocol forbids a hit before turn 3 or 4. After the wipe, residual tokens from the discarded preference can still leak into the OR query.
- **Boundary first turn.** The first `ask_attribute` is always answered with "no preference", so turn 1 is under-informed.

## False positives (typical)

- High-review popular items in the same category/color outrank the true target when constraints are still generic ("I'm still exploring").
- Store-name overlap: a brand token matches many SKUs from the same seller.

## Trade-off

We optimize MTTC by asking `other` immediately (dumps hidden constraints) while still emitting a Top-10 every turn. That raises Hit@10 a lot versus silent BM25, at the cost of sometimes ranking a popular sibling above the exact ASIN (MRR 0.50, mean hit rank ~3.6).

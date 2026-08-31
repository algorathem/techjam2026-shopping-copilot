# Architecture in the literature

ShopPilot is **not** a reimplementation of any single paper. It is an offline,
enum-constrained retrieve-and-ask agent that borrows **problem structure** from
CRS / DST / CQ / hybrid IR work and validates choices with public-set ablations.

**Rule:** cite papers in captions and tables; **redraw** concept diagrams —
never paste paper PDF figures (ToS / clarity / brand).

Asset: `docs/architecture_literature.png` · rebuild
`python3 scripts/render_architecture_literature.py`

---

## Classical pipeline (what we inherit)

```
User utterance
  → NLU / slot fill          (ingest)
  → Dialog State Tracking   (SessionState)
  → Dialog policy           (ask vs recommend)
  → Retrieval + rank        (hybrid IR)
  → Response                (message + ask_attribute + Top-10)
  ↺ next turn
```

This is the standard task-oriented / conversational recommendation spine
(NLU → DST → policy → NLG/IR), not a free-form chatbot.

---

## Paper → module map

| Literature concept | Canonical refs (entry points) | ShopPilot module | What we took | What we did **not** do |
|---|---|---|---|---|
| Clarifying questions improve early precision | Qulac (SIGIR; arXiv:1907.06554); CRS “learn to ask” surveys | Always Top-10 **and** one `ask_attribute` | Pair ask + recommend every turn | Free-form CQ generation |
| Funnel / coarse→fine PE | LLM preference elicitation funnels (arXiv:2510.12015) | `other` first, then static facet ladder | Broad dump then finer slots | Trained PE LLM |
| Max information-gain / min entropy ask | Bayesian CRS IG formulations | `_next_ask` ablation | Implemented max-IG over pool | **Rejected** — Tech ~0.72 (brand entropy trap) |
| Corpus-grounded questions | Corpus-informed CQ / RAG-CQ (arXiv:2409.18575) | Facet chips in `message` from live pool | Only ask/support what catalog supports | Generator that invents intents |
| User fatigue / turn budget | Empirical CQ user studies (e.g. arXiv:2008.00279) | MTTC in TechnicalScore; ≤10 turns | Efficiency as first-class objective | Unlimited chit-chat |
| Dialog state tracking | Multi-domain DST (arXiv:1712.10224); classic DST | `SessionState` + provenance | Slot–value memory across turns | Adding new ask enum names |
| Intent + slots joint NLU | Intent–slot models (various) | `_ingest`: buy/browse, family, audience, constraints | Lightweight rule NLU | End-to-end neural NLU default |
| Soft vs hard constraints / override | Task-oriented state update practice | soft / disclosed / override sources; soft-only wipe | Provenance-aware invalidation | Clear-all on every pivot |
| Lexical retrieval | BM25 / FTS | SQLite FTS5 OR+AND | Strong baseline lane | External search cluster |
| Dense retrieval + late fusion | Dual-encoder dense IR | hash n-gram (default) / MiniLM opt-in | Paraphrase recall | Required GPU / always-on VDB |
| Ranking metrics | IR evaluation (MRR, Hit@K) | Official Hit@10 · MRR · MTTC | Precision gating for MRR | Optimize MTTC alone |

---

## Diagram key (panels in the PNG)

| Panel | Concept | ShopPilot read-out |
|---|---|---|
| **A** | Classical CRS pipeline | Our hot path is the same spine |
| **B** | DST belief update | `SessionState` is rule-based DST with sources |
| **C** | CQ theory vs kit | max-IG rejected; other-first shipped |
| **D** | Hybrid IR | FTS5 + dense → coverage rank → precision gate |
| **E** | One-line map | Six paper ideas → six implementation choices |

---

## Honest positioning (for judges / slides)

1. **Structure from literature, parameters from the kit.**  
   CQ + DST + hybrid IR is decades of work; the closed `ask_attribute` enum and
   simulator oracle are TechJam-specific.

2. **Negative result is a contribution.**  
   Textbook max-IG ask selection failed here (~0.72 Tech). That is expected when
   high-entropy catalog facets ≠ protocol-revealed attributes (“fake entropy”).

3. **Corpus grounding without a CQ model.**  
   We approximate corpus-informed CQs via enum + pool facet wording, not a
   learned generator (arXiv:2409.18575 spirit).

4. **DST without new slots.**  
   arXiv:1712.10224 is about large/dynamic *values*, not inventing new ask
   names. Values stay free-text; names stay the organizer enum.

5. **Offline default.**  
   Optional LLM NLU/rerank is a dashed sidecar; score path is deterministic
   hybrid IR + rules.

---

## Suggested spoken line (architecture slide)

> ShopPilot follows the classical conversational recommendation stack —
> NLU, dialog state, ask policy, hybrid retrieve-and-rank —
> grounded in clarifying-question and DST literature.
> We tried maximum information-gain question selection from Bayesian CRS
> and rejected it on this simulator. What shipped is an other-first,
> protocol-aligned ladder with corpus-grounded message facets and a
> soft-only override DST.

---

## Rebuild / embed

```bash
python3 scripts/render_architecture_literature.py
python3 scripts/build_pitch_pdf.py      # slide 4 uses the board
python3 scripts/build_demo_slides.py    # optional pptx literature slide
```

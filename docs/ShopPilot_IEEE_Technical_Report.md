## ShopPilot: An Offline-First Conversational Shopping Agent for Constraint-Grounded Multi-Turn Retrieval

TikTok TechJam 2026 — Track 4 (Shopping Copilot) Participant Submission

TikTok TechJam 2026 · Track 4 Shopping Copilot · IEEE-style technical report (hackathon documentation)

Abstract—Conversational e-commerce agents must map ambiguous, multi-turn natural language into a ranked shortlist from a large catalog while minimizing dialogue length. We present ShopPilot, an offline-first shopping agent built on the official TechJam 2026 conversational-search kit (50,000 Clothing_Shoes_and_Jewelry products; 200 public evaluation sessions). ShopPilot combines (i) dual-track buying/browsing intent cues, (ii) a compact dialog state with soft/disclosed/override slot provenance, (iii) in-memory hybrid retrieval (SQLite FTS5 BM25 plus optional hashed character n-gram dense lane), and (iv) constraint-coverage reranking with early-turn precision control and category-tail exact bonuses. On the public set, the default hash path achieves Hit Rate@10 = 0.970, MRR = 0.836, MTTC = 2.93, and TechnicalScore = 0.897 versus the weak BM25 starter (0.125 / 0.068 / 9.81 / 0.107), using zero model tokens. We report per-scenario metrics, ablation-informed design choices, limitations, and reproducibility details.

Index Terms—conversational recommendation, multi-turn retrieval, dialog state tracking, hybrid search, e-commerce agents, offline evaluation.

## I. Introduction

Traditional product search optimizes a single query against a static index. Modern shoppers instead refine goals across turns: they open with vague category language, disclose hard constraints when asked, change their mind mid-session, or declare that some attributes do not matter. The TechJam 2026 Track 4 challenge formalizes this setting. Each session hides a target parent_asin in a frozen Amazon Reviews 2023 catalog subset. An agent may take at most ten turns; each turn must return a natural-language message, at most one structured ask_attribute from a fixed enum, and a Top-10 recommendation list. Scoring emphasizes coverage (Hit Rate@10), ranking quality (MRR), and efficiency (mean turns to conversion, MTTC).

The organizer-provided weak BM25 starter is intentionally underpowered (TechnicalScore approximately 0.107 on 200 public sessions). Rebuilding a full LLM stack is unnecessary for a strong entry and can harm feasibility (API keys, latency, non-determinism). ShopPilot therefore targets a different design point: a deterministic, network-optional agent whose default path uses only the Python standard library (plus optional NumPy for a hashed dense lane).

Contributions. (1) A production-shaped multi-turn agent interface fully compatible with the official evaluator. (2) A dialog-state design that separates soft preferences from disclosed facts and implements soft-only wipe on intent override. (3) A hybrid retrieve–rerank stack with precision-first early turns, category-tail bonuses, and an other-first clarification policy matched to the simulator. (4) A fully offline public-set result of TechnicalScore 0.897 with 0 tokens, with scenario breakdowns and documented negative ablations (e.g., pure max information-gain ask order).

## II. Related Work and Problem Framing

Conversational recommendation and task-oriented dialog systems classically separate natural language understanding (slot filling), dialog management (what to ask next), and retrieval/ranking. Industrial shopping assistants further add intent routing between high-precision buying and exploratory browsing. Dense retrieval and cross-encoders improve paraphrase recall but add dependencies. ShopPilot follows the classical pipeline under strict hackathon constraints: in-memory execution, read-only catalog, no ASIN injection, and a protocol-legal ask_attribute vocabulary.

The challenge’s four pillars map directly onto system modules: (I) intent routing and hybrid multi-route retrieval; (II) multi-turn state evolution including override and boundary don’t-care; (III) context programming via accumulated slots and retrieval query construction; (IV) evaluation on Hit@10, MRR, and MTTC aggregated as TechnicalScore = 0.50·Hit@10 + 0.30·MRR + 0.20·clip((11−MTTC)/10, 0, 1).

## III. System Architecture

ShopPilot implements the kit’s Agent API (reset / respond). On each user utterance the agent executes: ingest and slot update → optional query rewrite → hybrid candidate generation → constraint-aware scoring and ranking → ask policy → response assembly. Figure conceptually: User utterance → NLU/ingest (constraints, family, audience, override) → SessionState → FTS5 + dense recall → rerank (coverage, category tail, combo exact, audience/family) → Top-K (precision gate) + one ask_attribute → evaluator.

### A. Dialog State and Intent / Override Hygiene

SessionState stores ordered constraints with provenance tags soft, disclosed, or override; parallel sets for asked attributes and don’t-care attributes; product family and audience (internal, not official asks); message history with a cursor that drops pre-override turns from retrieval; and flags such as override_applied.

Intent cues. Buying vs browsing is inferred from opening language (targeted requirements vs open exploration). This biases filtering strictness and message tone without requiring a trained classifier.

Override. Patterns such as “ignore my earlier preference,” “change of plans,” or “switch to …” trigger apply_override: soft constraints are erased; disclosed hard facts are retained (the simulator will not re-send them); discarded soft tokens are blocked from FTS; history before the override is excluded from query construction; asked is reset so other can fire again. This design lifted override Hit@10 from approximately 0.80 to 0.97 in intermediate public-set iterations.

Boundary don’t-care. Utterances of the form “I don’t have a preference for X” mark attribute X as don’t-care so the agent neither filters nor re-asks it.

Audience and family. Gift/relationship phrases (e.g., for my son, for him) set an internal audience label used only in ranking. Product-family patterns disambiguate senses such as dress garment vs dress shoes. Over-broad audience matching on category strings (e.g., treating “Women Dresses” as gift-for-her) was measured to cost approximately 0.01 TechnicalScore and was removed.

### B. Hybrid Retrieval

Lexical lane. Products are indexed in an in-process SQLite FTS5 table. Queries combine OR over session terms with AND-oriented constraint tokens. After override, pre-override message text and discarded soft tokens are omitted to avoid resurrecting abandoned goals.

Dense lane (optional). starter/dense.py builds a hashed character n-gram embedding over titles/attributes (NumPy). At query time, DenseIndex supplies a recall set (K≈80) and a cosine-style score fused into reranking (default weight 4.5 for hash; higher weight for optional MiniLM). Without NumPy the agent degrades to pure FTS. MiniLM (sentence-transformers) remains explicit opt-in via SHOPPILOT_DENSE=minilm and is not required for the reported 0.897 score.

### C. Reranking and Precision Control

Candidates are scored with a linear combination of normalized BM25, dense similarity, constraint coverage (disclosed/override phrases preferred over soft), super-linear combo exact-match bonuses when multiple session phrases hit product text, audience/family hit–miss adjustments, and category-tail bonuses when session category terms align with product leaf categories (exact bonus 10.0; partial 2.5).

Early-turn precision. Because the evaluator ends a session at first Top-10 hit, a lucky but poorly ranked early hit freezes a weak reciprocal rank. ShopPilot therefore emits Top-1 only for the first precision turns (default 3, configurable) and can extend precision until a minimum constraint count is reached (capped by turn). This peer-validated lever primarily improves MRR without sacrificing eventual Hit@10.

### D. Clarification Policy

The official simulator reveals hidden product constraints only when ask_attribute is set. ShopPilot always pairs recommendations with a question. The first ask is other (simulator catch-all that dumps remaining constraints). Subsequent asks follow a static order color → material → style → … with limited pool-split reordering among a safe subset. Public-set A/B tests rejected pure maximum information-gain over the candidate pool (TechnicalScore dropped to approximately 0.72 historically) because high-entropy brand/store splits rarely match the simulator’s hidden classifier. Facet tags extracted from the live pool still ground message wording (e.g., offering concrete color options).

A second other ask when evidence remains thin (SHOPPILOT_OTHER_TWICE, default on) is another measured lever for residual uncertainty after the first disclosure dump.

### E. Optional LLM Path (Non-Default)

When SHOPPILOT_LLM=1 and a provider key is present, the agent may call a light slot normalizer (always or low-confidence only) and/or rerank the already-retrieved top candidates. Outputs are schema-validated against the official ask enum; failures fall back to rules. The judged default remains offline. Reported token usage on the hash evaluation path is zero.

## IV. Experimental Setup

Catalog. Frozen 50,000-product JSONL from the TechJam participant kit (Amazon Reviews 2023 Clothing_Shoes_and_Jewelry derivative). Read-only; SHA256 verification supported.

Evaluation. Official python -m evaluator.local_evaluator on data/public_set.jsonl (N=200). Scenarios: buying (80), browsing (80), intent_override (30), boundary (10). We do not modify evaluator/ or public labels when reporting scores. Private 800-session set was not used.

Implementation. Python 3.10+ (tested 3.13). Core agent approximately 1.6k LOC in starter/agent.py plus dense, rewrite, and optional LLM helpers. Unit tests cover slots, rewrite, dense, and evaluator smoke paths.

Baseline. Organizer weak BM25 starter: Hit@10=0.125, MRR=0.068034, MTTC=9.81, Efficiency=0.119, TechnicalScore=0.10671 (docs/baseline_results.json).

## V. Results

Table I reports the primary public-set comparison for the default offline hash configuration (results.json). ShopPilot improves TechnicalScore from 0.107 to 0.897 (approximately 8.4×). Hit Rate@10 rises from 12.5% to 97.0%; MRR from 0.068 to 0.836; MTTC falls from 9.81 to 2.93 turns.

TABLE I. Public 200-session results (official evaluator).

| System | Hit@10 | MRR | MTTC | Efficiency | TechnicalScore | Tokens |
| --- | --- | --- | --- | --- | --- | --- |
| Weak BM25 starter | 0.125 | 0.068 | 9.81 | 0.119 | 0.107 | 0 |
| ShopPilot (hash, default) | 0.970 | 0.836 | 2.93 | 0.807 | 0.897 | 0 |

Table II breaks down ShopPilot by scenario. Buying converts fastest (MTTC 2.54). Intent override remains slower by protocol (MTTC 4.17) yet retains Hit@10 0.967 and strong MRR 0.866 after soft-only wipe and ask reset. Boundary reaches Hit@10 1.000 and MRR 0.933 on N=10.

TABLE II. ShopPilot per-scenario metrics (hash default, N=200).

| Scenario | N | Hit@10 | MRR | MTTC |
| --- | --- | --- | --- | --- |
| Buying | 80 | 0.975 | 0.833 | 2.54 |
| Browsing | 80 | 0.963 | 0.816 | 2.85 |
| Intent override | 30 | 0.967 | 0.866 | 4.17 |
| Boundary | 10 | 1.000 | 0.933 | 3.00 |
| Overall | 200 | 0.970 | 0.836 | 2.93 |

Intermediate stack. An earlier public hash run (results_hash.json) scored TechnicalScore 0.789 (Hit 0.93, MRR 0.553, MTTC 3.08). The lift to 0.897 is attributed primarily to precision Top-1 early turns, category-tail exact bonuses, and a second other ask under thin evidence—each gated by environment flags for ablation.

Negative results (selected). Pure max-IG ask ordering over the live pool reduced TechnicalScore (historical approximately 0.72). Aggressive stemming and some RRF fusions hurt held-out style checks in related experiments. Optional MiniLM dense improved paraphrase cases in isolation but was not required for the default 0.897 hash path.

## VI. Discussion

Why offline hybrid works here. The simulator’s information channel is dominated by structured ask_attribute disclosures and lexical overlap with catalog fields (title, categories, features). Once constraints are captured with provenance, BM25 + coverage scoring recovers the target ASIN for most sessions. Dense hash n-grams help residual paraphrase gaps without a GPU.

MRR as the critical lever. TechnicalScore weights MRR at 0.30. Ending sessions on a Top-10 hit that is not rank-1 caps reciprocal rank. Precision turns deliberately delay broad Top-10 emission until the state is rich enough to place the target higher—trading a small risk of later hit for large MRR gains (0.55 → 0.84 class improvement between intermediate and final stacks).

Public-set overfitting risk. All reported numbers use the same 200 sessions available to every team. High public scores can exploit simulator phrasing. We mitigate via unit tests, scenario breakdowns, documented rejected policies, and an offline default that judges can run with network disabled. The private 800 remains the only pristine ranking; we did not access it.

Positioning vs leaderboard claims. Public GitHub READMEs report TechnicalScores from approximately 0.75 to 0.97. ShopPilot at 0.897 is competitive on the official metric while prioritizing reproducibility, zero tokens, and explicit failure analysis. Final hackathon ranking also includes innovation, impact, feasibility, and presentation beyond TechnicalScore alone.

## VII. Limitations and Future Work

(1) Approximately 3% of public sessions still miss Top-10; near-paraphrase feature sentences and sparse titles remain failure modes. (2) Ask order after other is intentionally static relative to this simulator; transferring to a different user model may need adaptive policies. (3) Override MTTC is structurally bounded by disclosure timing. (4) Optional LLM NLU/rerank needs keys and is not the submission default. (5) No private-800 numbers. Future work: calibrated dense/lexical gating, learned rerankers trained only on development folds, robust synonym normalization, and stress tests under paraphrased user wording.

## VIII. Reproducibility

Repository: https://github.com/algorathem/techjam2026-shopping-copilot (local mirror used for this report: Downloads/techjam2026-shopping-copilot). Entry point: starter/agent.py class Agent. Reproduce:

export SHOPPILOT_DENSE=hash; python -m evaluator.local_evaluator

Expected aggregate fields in results.json: hit_rate_at_10≈0.97, mrr≈0.836, mttc≈2.93, recommended_technical_score≈0.897, reported_token_usage total_tokens=0. Interactive demo: python cli_chat.py --dense hash. Tests: python -m unittest tests.test_agent_slots tests.test_rewrite tests.test_dense tests.test_evaluator -q.

## IX. Ethics and Data

Catalog and sessions derive from Amazon Reviews 2023 (McAuley Lab, UCSD); see DATA_ATTRIBUTION.md. No personal user data beyond synthetic evaluation sessions is processed. No secrets are committed. The agent does not mutate the catalog or inject ASINs.

## X. Conclusion

ShopPilot demonstrates that a carefully engineered offline multi-turn retrieve-and-ask agent can approach strong TechnicalScores on the TechJam 2026 shopping copilot benchmark without LLMs or GPUs. The decisive ingredients are provenance-aware dialog state (especially override hygiene), hybrid in-memory retrieval, constraint-coverage ranking, early-turn precision control, and a simulator-aligned clarification policy. On 200 public sessions the default hash system reaches TechnicalScore 0.897 (Hit@10 0.970, MRR 0.836, MTTC 2.93) versus 0.107 for the official weak baseline, at zero token cost.

## Appendix A — Environment Flags (Default = Reported Path)

| Variable | Default | Role |
| --- | --- | --- |
| SHOPPILOT_DENSE | hash/auto | none | hash | minilm dense backend |
| SHOPPILOT_PRECISION_TURNS | 3 | Early turns emit Top-1 only |
| SHOPPILOT_OTHER_TWICE | 1 | Second other ask if thin evidence |
| SHOPPILOT_CATEGORY_TAIL | 1 | Category-tail exact/partial bonus |
| SHOPPILOT_LLM | off | Optional network LLM features |
| SHOPPILOT_LLM_SLOTS | off | off | lowconf | always slot NLU |
| SHOPPILOT_LLM_RERANK | off | Optional top-candidate rerank |

## Appendix B — Implementation Footprint

Approximate sizes: starter/agent.py 1632 lines; dense.py 235; llm_slots.py 361; llm_rerank.py 197; rewrite.py 64. Supporting docs include DEVPOST.md, DEMO_VIDEO_SCRIPT.md, architecture diagram, miss-category reports, and unit tests under tests/.

Acknowledgment—Built on the TechJam2026/techjam-conversational-search participant kit and evaluator. Metrics in Section V are taken from the author’s results.json produced by the unmodified official local evaluator.

Document type: IEEE-style technical report for hackathon documentation (not a peer-reviewed IEEE publication). Generated for TikTok TechJam 2026 Track 4 submission materials.

# Real-world impact beyond the hackathon prompt

**Devpost / judging angle:** Impact & Relevance (20%) — value for real retailers and shoppers, not only Hit@10 on a frozen kit.

ShopPilot is not “another chatbot demo.” It is a **production-shaped decision layer** between messy human intent and a large SKU catalog: dual-track buying vs browsing, multi-turn slot state (including intent override), hybrid recall, and clarification that is machine-scored via `ask_attribute`. That same stack is what large retailers are already shipping, and what mid-market catalogs still fail at.

---

## 1. The commercial problem is already priced in the market

Conversational commerce is no longer experimental budget. Mordor Intelligence projects the category at **USD 11.26B (2025) → 12.64B (2026) → 22.56B (2031)** at **12.28% CAGR**, driven by real-time, context-aware dialogue that **collapses intent → purchase** and cuts cart abandonment versus static forms.[1]

That growth is not “chat for chat’s sake.” The winning surface is **in-flow assistance on the path to buy**: messaging, voice, and on-site assistants that keep the shopper inside one thread instead of bouncing between search box, filters, FAQ, and cart.[1]

**Impact claim for judges:** ShopPilot implements the *decision core* of that category (intent split, state, hybrid retrieve, clarify, rank) as a headless API — the part every merchant must own even if the UI is WhatsApp, app chat, or Rufus-like overlay.

---

## 2. Catalog search is still broken for most of retail

Baymard’s 2026 ecommerce Search UX benchmark (170+ sites/apps) finds **56% of sites fail to adequately support users’ search needs**; only **44%** of desktop/mobile sites and apps reach “decent” or “good” Search UX.[2]

Poor search is not a cosmetic UX ding. Baymard links it directly to **time wasted refining queries and abandonments when shoppers cannot find products that exist in the catalog**.[2]

Keyword boxes fail the exact failure modes this track encodes:

| Real shopper behavior | Kit scenario | ShopPilot mechanism |
|---|---|---|
| “I need black leather walking shoes under $80” | Buying | Hard-constraint track + AND lane |
| “Something for a hiking trip, not sure” | Browsing | High-recall OR + clarify `other` |
| “Actually ignore that — I need acrylic not cotton” | Intent override | Soft-only wipe, keep disclosed facts, re-ask |
| “No color preference” | Boundary | `dont_care` + continue |

**Impact claim:** Every mid-size apparel/footwear merchant with 10k–500k SKUs still ships the Baymard failure mode. A headless agent that raises Hit@10 and cuts turns-to-find is **recoverable revenue on traffic they already paid for**, not net-new acquisition spend.

---

## 3. Incumbents already productized “shopping copilot”

Amazon’s **Rufus** is positioned as a generative shopping assistant **trained on Amazon’s product catalog**, rolled from beta to **all U.S. customers** in the Shopping app and desktop.[3][4]

Amazon’s stated job-to-be-done matches this track’s pillars: save time, answer product and need questions, and support **more informed purchase decisions** — including open questions like what to consider when buying a category, and comparisons across use cases.[3][4]

**Impact claim:** The category is validated at Amazon scale. ShopPilot shows how a **merchant-owned, in-memory, API-scored** agent can deliver the same loop (ask → constrain → retrieve → rank) without depending on a single platform’s assistant — relevant to any retailer that cannot wait for Amazon/Google to mediate discovery.

---

## 4. Clarification is a conversion lever, not small talk

Classic IR result (Qulac, SIGIR): on an oracle setup, **one good clarifying question** can improve P@1 by **over 170%**.[5]

User study on product-repository clarifying systems: people will answer a **substantial but finite** number of questions (**~11–21 on average**), and **66–84%** found the question-based system helpful for completing the task.[6]

ShopPilot operationalizes that under industrial constraints:

- Max 10 turns (hard MTTC pressure)
- Always recommend **and** ask (no silent turns)
- First ask = `other` (max protocol info gain)
- Then static high-yield facets (color → material → …) after public-set A/B rejected pure entropy max-IG
- Override hygiene so “changed my mind” does not destroy already-earned constraints

**Impact claim:** Clarification is the cheapest way to recover relevance when the query is under-specified — which is the default for apparel (fit, material, use case, budget). ShopPilot makes that loop **measurable** (Hit@10, MRR, MTTC), so a retailer can A/B it like any other conversion experiment.

---

## 5. Concrete value hypotheses a retailer can take to finance

Map kit metrics → business language (for pitch / Devpost; not claimed as causal production lifts):

| Kit metric | Business translation | Why it matters |
|---|---|---|
| **Hit@10 ↑** (0.125 → 0.93 on public set) | Higher “found the right SKU” rate on assisted sessions | Directly attacks Baymard-style findability failure[2] |
| **MRR ↑** | Better rank of the eventual purchase | Fewer scroll/refines; stronger add-to-cart from top slot |
| **MTTC ↓** (9.8 → 3.1 turns) | Lower cognitive load / chat cost | Aligns with finite question budget users tolerate[6] |
| **Override-robust state** | Handles preference revision without restart | Real carts change mid-journey; hard wipe was leaving money on the table |
| **0 tokens default path** | Predictable COGS; works offline | Mordor notes software-led market; cost control decides SME adoption[1] |
| **In-memory / no vector DB cluster** | Fits mid-market infra and edge/regional deploy | Matches “out of scope: heavy external VDB” but still hybrid-capable |

**Worked illustration (transparent, not a promise):**  
If assisted sessions are even a small slice of site search traffic, and better findability converts a fraction of Baymard-style abandonments, the agent pays for itself in recovered GMV long before “AI brand” benefits. The point for judges is **instrumentation**: Hit / MRR / MTTC are already the KPI board a retail search team would run.

---

## 6. Who benefits beyond the competition

1. **Apparel & footwear pure-plays** (the Amazon Clothing_Shoes_Jewelry slice): high attribute ambiguity, frequent “still exploring,” size/material/use-case slots.
2. **Marketplaces with long-tail SKUs**: keyword collision and near-duplicate titles — dense hybrid lane is aimed here.
3. **CS / sales chat teams**: same agent behind agent-assist (“next best question” + shortlist) to cut handle time.
4. **Privacy-sensitive retailers**: aggregate `user_profile` tags only; no raw PII; offline path needs no third-party LLM.
5. **Emerging markets messaging commerce**: Mordor ties growth to chat + payments collapsing abandonment (e.g. in-chat pay reducing abandonment vs redirect flows).[1] ShopPilot is the catalog brain those threads need.

---

## 7. One-paragraph Devpost blurb (paste-ready)

> Static ecommerce search still fails most shoppers: Baymard finds 56% of sites inadequate on Search UX, driving refine-loops and abandonment even when the product exists.[2] Meanwhile conversational commerce is scaling into a multi-billion-dollar category as dialogue collapses intent-to-purchase,[1] and Amazon has productized catalog-grounded assistants (Rufus) for informed buying at consumer scale.[3][4] ShopPilot attacks that gap as a **merchant-owned shopping brain**: buying/browsing routing, multi-turn slots with intent-override hygiene, hybrid FTS + dense recall, and clarification tuned to real question budgets.[5][6] On the public kit it raises Hit@10 from 0.125 → 0.93 and cuts mean turns-to-find from 9.8 → 3.1 with a zero-token offline path — metrics a retailer can read as findability, ranking quality, and cost-to-serve, not just a leaderboard score.

---

## 8. Pitch soundbites (30 seconds)

- “We’re not scoring chat wit — we’re scoring **find the purchase SKU in fewer turns**, which is the same KPI as site search conversion.”
- “Baymard says most catalogs still fail search UX;[2] Amazon already shipped the assistant category;[3][4] we shipped the **portable core** mid-market can run in-memory.”
- “Override hygiene alone moved intent-change sessions from 0.80 → 0.97 Hit — that’s the ‘I changed my mind’ path every cart has.”
- “Clarification isn’t engagement bait: one good question can more than double top-rank relevance in IR studies;[5] users will answer a bounded number of good questions.[6]”

---

## 9. Honest limits (builds trust with judges)

- Public-set metrics are **offline simulation** on frozen Amazon metadata, not a live A/B on paid traffic.
- Market-size figures vary by firm methodology; we cite Mordor’s published range as one industry estimate, not a single source of truth.[1]
- Amazon does not publish a single public “Rufus lifted conversion X%” number in the pages we retrieved; impact is framed as **category validation + job-to-be-done**, not a borrowed ROI claim.[3][4]
- Residual misses are mostly near-duplicate titles — next production lever is stronger semantic embeddings / sibling demotion.

---

## Sources

[1] https://www.mordorintelligence.com/industry-reports/conversational-commerce-market — Mordor Intelligence Conversational Commerce Market
    > "The conversational commerce market size is projected to be USD 11.26 billion in 2025, USD 12.64 billion in 2026, and reach USD 22.56 billion by 2031, growing at a CAGR of 12.28% from 2026 to 2031."
    > "Real-time, context-aware dialogues inside familiar messaging and voice platforms are replacing static web forms, collapsing the steps from intent to purchase and reducing cart abandonment."
    > "WhatsApp Pay completes those payments without redirecting users, reducing cart abandonment by 30% when compared with"
    > "By type, chatbots held 47.89% of the conversational commerce market share in 2025"
[2] https://baymard.com/blog/ecommerce-search-query-types — Baymard Ecommerce Search UX 2026 Query Types
    > "56% of sites fail to adequately support users’ search needs"
    > "Only 44% of desktop and mobile sites and apps have a “decent” or “good” Search UX performance"
    > "Poor-performing ecommerce Search leads to frustrating search experiences, time wasted refining queries, and abandonments as users are unable to find products they’re looking for."
    > "170+ benchmarked sites and apps"
[3] https://www.aboutamazon.com/news/retail/amazon-rufus — Amazon announces Rufus AI shopping assistant
    > "Rufus is an expert shopping assistant trained on Amazon’s product catalog"
[4] https://www.aboutamazon.com/news/retail/how-to-use-amazon-rufus — Amazon Rufus available to all US customers
    > "Rufus is designed to help customers save time and make more informed purchase decisions by answering questions on a variety of shopping needs and products"
[5] https://arxiv.org/abs/1907.06554 — Qulac clarifying questions SIGIR 2019
    > "asking only one good question leads to over 170% retrieval performance improvement in terms of P@1"
[6] https://arxiv.org/abs/2008.00279 — Empirical study of clarifying question systems
    > "users are willing to answer a good number of clarifying questions (11-21 on average), but not many more than that"
    > "most of the users (66-84%) find the question-based system helpful towards completing their tasks"

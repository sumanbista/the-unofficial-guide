# The Unofficial Guide — Project 1

> **How to use this template:**
> Complete each section *after* you've built and tested the corresponding part of your system.
> Do not write placeholder text — if a section isn't done yet, leave it blank and come back.
> Every section below is required for submission. One-liners will not receive full credit.

---

## Domain

**Chosen Domain**: Student reviews and unofficial advice about CS/EECS courses and professors at UC Berkeley.

This system covers real student-generated knowledge about UC Berkeley’s Computer Science (CS) program — including professor teaching styles, course difficulty, workload, workload management tips, major declaration/switching experiences, and survival advice for classes like CS61A, CS61B, CS70, CS170, etc.

**Why this knowledge is valuable**: Official course catalogs and university websites only provide dry descriptions (topics covered, prerequisites). They don’t tell students which professors are engaging vs. confusing, how brutal the workload actually is, whether a class is curved harshly, or how to succeed with no prior programming experience. This “unofficial” knowledge helps students make better scheduling decisions, reduce stress, and improve their academic experience.

**Why it’s hard to find**: High-quality student insights are scattered across old Reddit threads (r/berkeley), RateMyProfessors pages, Medium posts, and Discord servers. They’re hard to search, often outdated, and mixed with noise. A RAG system makes this collective student wisdom searchable and reliable.
---

## Document Sources

| # | Source/Type | Description | URL or file path |
|---|--------|------|-----------------|
| 1 | Rate My Professors|Best Rated RMP Professors| [Best Rated RMP Professors](https://www.ratemyprofessors.com/search/professors/1072?q=*&did=11)|
| 2 | Rate My Professors| Low-rated CS professors and common complaints |[Low-rated CS professors](https://www.ratemyprofessors.com/search/professors/1072?q=*&did=11) |
| 3 | Reddit|CS70 Professor Rao: |[Reddit Thread](https://www.reddit.com/r/berkeley/comments/1fvht2b/cs70_professor_rao_is_the_worst_lecturer_ever/)|
| 4 |Reddit|CS Classes Ranked by Difficulty |[Reddit Thread](https://www.reddit.com/r/berkeley/comments/179uk2u/berkeley_cs_classes_ranked_by_difficulty/) |
| 5 |Medium |CS vs EECS |[Medium] (https://carolynwangjy.medium.com/berkeley-cs-and-clarification-over-the-new-high-demand-major-policy-addd7ea76f89)|
| 6 |Reddit| No Programming Experience |[Reddit Thread](https://www.reddit.com/r/berkeley/comments/118maog/what_percent_of_students_enter_berkeley_cseecs/) |
| 7 |Reddit|Concerns about being CS at Berkeley |[Reddit Thread](https://www.reddit.com/r/berkeley/comments/uuhkod/concerns_about_being_cs_at_berkeley/)|
| 8 | Medium | Switching Into CS | [Medium](https://carolynwangjy.medium.com/berkeley-cs-and-clarification-over-the-new-high-demand-major-policy-addd7ea76f89) |
| 9 | Reddit | Switching Into CS | [Reddit Thread](https://www.reddit.com/r/ApplyingToCollege/comments/13car4d/admitted_to_berkeley_off_the_waitlist_can_i/) |
| 10| Reddit | Switching Into CS | [Reddit Thread](https://www.reddit.com/r/berkeley/comments/181jhuq/how_hard_is_it_change_to_cs_major_after_getting/)|
| 11 |Reddit|CS Classes Ranked by Difficulty | [Reddit Thread](https://www.reddit.com/r/berkeley/comments/179uk2u/berkeley_cs_classes_ranked_by_difficulty/)|
| 12 |Reddit|How Hard and Time Consuming is CS at Berkeley | [Reddit Thread](https://www.reddit.com/r/berkeley/comments/hho2nr/comment/fwbmvvn/)|

---

## Chunking Strategy

<!-- Describe your chunking approach with enough specificity that someone else could reproduce it.
     Include:
     - Chunk size (characters or tokens) and why that size fits your documents
     - Overlap size and why (or why not) you used overlap
     - Any preprocessing you did before chunking (e.g., stripping HTML, removing headers)
     - What your final chunk count was across all documents -->

**Chunk size:** ~250–400 tokens (~1,000–1,600 characters) per chunk, using structure-aware boundaries rather than a fixed-length cut. The atomic unit is one review or one Reddit reply; short units are grouped (2–4 consecutive ones) up to the target size, and any single reply longer than ~400 tokens is sub-split at sentence boundaries.

**Overlap:** ~50 tokens (~1–2 sentences), applied *only* when a long reply has to be sub-split. The majority of chunks have **no overlap** because they end on natural blank-line boundaries between reviews/replies.

**Why these choices fit my documents:** The corpus is two document types, both with mixed-length content. (1) RateMyProfessor files are *collections*: several professors per file, each with a header (name, overall rating, % would-take-again, difficulty) followed by many short 1–3 sentence student reviews. (2) Reddit files each contain **one main thread question plus all of that thread's replies**, where replies range from a single line to ~250-word essays. A fixed 512-token chunk would splice two different opinions together and could separate a review from its professor header (or a reply from its question), producing chunks no one can attribute. Splitting on the documents' natural delimiters keeps each opinion intact, and prepending context (professor name/rating/course, or the thread question) makes every chunk self-contained and attributable. Small conditional overlap protects only the long essay-replies from mid-argument cuts. This avoids the failure modes at both extremes: too-small chunks return noisy, context-free fragments; too-large chunks (a full professor block or whole thread) average many opinions into one diluted embedding that scores "vaguely related" to everything.

**Preprocessing before chunking:** Read each `.txt` file; detect type by delimiter (RMP files contain `Professor in the Computer Science department...`; Reddit files contain `Thread response:`). For RMP, segment by professor header, then by blank-line-separated reviews, retaining each professor's header as the prepended context. For Reddit, separate the main question (everything before `Thread response:`) from the replies (blank-line separated), and prepend the question to each reply chunk. Collapse extra whitespace; no HTML stripping is needed since the sources are already plain text.

**Final chunk count:** 117 chunks total.

---

## Embedding Model

<!-- Name the embedding model you used and explain your choice.
     Then answer: if you were deploying this system for real users and cost wasn't a constraint,
     what tradeoffs would you weigh in choosing a different model?
     Consider: context length limits, multilingual support, accuracy on domain-specific text,
     latency, and local vs. API-hosted. -->

**Model used:** `all-MiniLM-L6-v2` via the `sentence-transformers` library — a free, open-source embedding model that runs locally with no API key, no per-query cost, and full data privacy. It outputs 384-dimensional vectors, is fast on CPU, and performs well on short English semantic-similarity tasks, which matches our corpus of student reviews and Reddit replies. I chose it for the right cost/speed/quality balance for a small local RAG system. Note its **256 word-piece input limit**: it silently truncates longer inputs, so chunks are kept at/under ~256 tokens to ensure no text is lost before embedding. Retrieval uses **top-k = 5**, enough to gather several independent opinions for a consensus answer without diluting context with weakly-related chunks.

**Production tradeoff reflection:** If I were deploying for real users and cost weren't a constraint, I'd weigh:
- **Accuracy on domain-specific text:** A larger model — `all-mpnet-base-v2` (768-dim, local) or an API model like OpenAI `text-embedding-3-large` / Voyage `voyage-3` — better captures nuance in slangy, sarcastic student language where MiniLM can miss intent. This is the biggest potential win.
- **Context-length limits:** MiniLM's 256-token cap forces small chunks. A model with an 8K context (OpenAI/Voyage/`nomic-embed-text`) could embed a full professor block or long Reddit reply as one unit, removing truncation risk and simplifying chunking.
- **Multilingual support:** Low priority here (English-only corpus), but `paraphrase-multilingual-mpnet` or Cohere `embed-multilingual-v3` would matter if non-English sources were added.
- **Latency & local vs. API-hosted:** MiniLM is local — no network round-trip, no rate limits, no third-party data sharing, and zero marginal cost — with very low latency. An API-hosted model adds latency, per-call cost, and a privacy/availability dependency in exchange for higher accuracy and larger context.

So, my first upgrade would be `all-mpnet-base-v2` locally (better accuracy while staying free and private), moving to an API-hosted model only if evaluation showed recall on nuanced queries was insufficient.

---

## Grounded Generation

<!-- Explain how your system enforces grounding — how does it prevent the LLM from answering
     beyond the retrieved documents?
     Describe both your system prompt (what instruction you gave the model) and any structural
     choices (e.g., how you formatted the context, whether you filtered low-relevance chunks).
     Do not just say "I told it to use the documents" — show the actual instruction or explain
     the mechanism. -->

**System prompt grounding instruction:**

The model never sees the raw question alone. We retrieve the top-k = 5 chunks, format each as a numbered, attributed context block, and send them with a system prompt that *enforces* (not merely suggests) answering from context only:

> You are an assistant that answers questions about UC Berkeley CS/EECS courses and professors using **only** the student reviews and Reddit/Medium excerpts in the Context below.
>
> Rules:
> 1. Use only the information in the Context. Do not use outside or prior knowledge.
> 2. If the Context does not contain enough information to answer, reply exactly: **"I don't have enough information on that."** Do not guess or fill gaps from general knowledge.
> 3. The Context is subjective student opinion and reviews often disagree. When sources conflict (e.g. "great lecturer" vs. "reads off slides"), represent the range of views rather than averaging them into one verdict or silently picking a side.
> 4. Do not invent professor names, ratings, course numbers, or URLs that are not in the Context.
> 5. Be concise and specific; ground claims in the provided reviews.

**Structural choices that reinforce grounding:**

- **Attributed context blocks.** Each retrieved chunk is injected with its metadata header intact — `Professor <name> — <rating>/5, <% would-take-again>` for RMP chunks, or `Thread: <question/title>` for Reddit/Medium chunks. The model sees *whose* opinion each excerpt is, so it can attribute correctly instead of merging opinions (directly addresses Anticipated Challenge #1, lost attribution).
- **Refusal over a hard distance cutoff.** We deliberately do **not** drop chunks above a fixed cosine-distance threshold. Retrieval testing showed a *correct* answer (John DeNero's 4.3/5 rating) sits at distance ≈ 0.57, above the 0.5 "good match" line — a hard cutoff would falsely refuse an answerable question. Out-of-corpus questions (a professor we have no documents for) are instead handled by Rule 2: the retrieved chunks won't contain the answer, so the model returns "I don't have enough information on that" rather than hallucinating. The distance scores are surfaced for inspection but not used to gate answers.
- **Conflict-preserving instruction.** Because the corpus is contradictory opinion (Challenge #3), Rule 3 tells the model to report disagreement explicitly rather than produce a bland averaged claim.

**How source attribution is surfaced in the response:**

Sources are appended **programmatically**, not generated by the LLM — this prevents fabricated citations. After generation, we collect the `source`/`url` metadata from the chunks that were actually retrieved and de-duplicate them into a "Retrieved from" list shown beneath the answer (e.g. the RateMyProfessors, Reddit, or Medium links carried in each chunk's `url` field). Because attribution comes from the vector store's metadata rather than the model's text, a displayed citation always points to a real document that was actually fed into the prompt.

---

## Evaluation Report

<!-- Run your 5 test questions from planning.md through your system and record the results.
     Be honest — a partially accurate or inaccurate result that you explain well is more
     valuable than a suspiciously perfect result. -->

All 5 questions were run end-to-end through `ask()` (`query.py`) against the live ChromaDB index. "Top distance" is the cosine distance of the best-matching retrieved chunk (lower = closer).

| # | Question | Expected answer | System response (summarized) | Retrieval quality | Response accuracy |
|---|----------|-----------------|------------------------------|-------------------|-------------------|
| 1 | What is John DeNero's overall quality rating? | 4.3/5 overall | "John DeNero's overall quality rating is 4.3/5." | Partially relevant — correct chunk ranked #1 but top distance 0.573 (>0.5); ranks 4–5 pulled in Dan Garcia | Accurate |
| 2 | What classes does Professor Jennifer Listgarten teach? | CS189 | "Professor Jennifer Listgarten teaches CS189." | Relevant — all 5 chunks Listgarten/CS189, top distance 0.372 | Accurate |
| 3 | Do students need prior programming experience to succeed in UC Berkeley's CS program? | No, with explanation | "It's possible to succeed without prior experience… students with none still declared CS and landed FAANG internships, but often worked extra hard in CS61A; ~15% with no experience got a B+ or higher." | Relevant — all 5 chunks from `no_programming_experience.txt`, top distance 0.307 | Accurate |
| 4 | What is the "Would Take Again" percentage for Professor Kannan Ramchandran? | 85% | "The 'Would Take Again' percentage for Professor Kannan Ramchandran is 85%." | Relevant — all 5 chunks Ramchandran, top distance 0.424 | Accurate |
| 5 | What do students say about Professor Satish Rao's teaching? | Students criticized Rao for reading slides with minimal explanation | "Opinions are highly divided: some say he 'reads off slides' with no explanation and is hard to follow; others value his emphasis on intuition and call him caring." | Relevant — all 5 chunks Rao/CS70, top distance 0.348 | Accurate |

**Retrieval quality:** Relevant / Partially relevant / Off-target  
**Response accuracy:** Accurate / Partially accurate / Inaccurate

All five answers were accurate. Q5 is worth noting as a *success* of the grounding design: rather than averaging the contradictory reviews into a single verdict, the system preserved the disagreement (per Rule 3 of the system prompt), which is the honest representation of an opinion corpus. The one retrieval weakness — Q1's distances all above 0.5 — is analyzed below.

---

## Failure Case Analysis

<!-- Identify at least one question where retrieval or generation did not work as expected.
     Write a specific explanation of *why* it failed, tied to a part of the pipeline.

     "The answer was wrong" is not an explanation.

     "The relevant information was split across a chunk boundary, so retrieval returned
     only half the context — the model didn't have enough to answer correctly" is an explanation.

     "The embedding model treated the professor's nickname as out-of-vocabulary and returned
     results from an unrelated review" is an explanation. -->

**Question that failed:** Q1 — "What is John DeNero's overall quality rating?" (a *retrieval* failure, not a generation one — the final answer happened to be correct, but the retrieval that produced it was weak and fragile.)

**What the system returned:** The correct answer ("4.3/5"), but only because the right chunk landed at rank #1 by a thin margin. Every one of the top-5 retrieved chunks had a cosine distance **above 0.5** (0.573, 0.607, 0.614, 0.649, 0.668) — past the "good match" threshold my Retrieval Approach set — and ranks #4–#5 were **Dan Garcia** chunks, a different professor entirely. If the ranking had shifted even slightly, the model could have been handed a majority of off-professor context.

**Root cause (tied to a specific pipeline stage):** The **embedding + chunking** stages, interacting badly with the *kind* of question. Q1 asks for a single structured metadata fact ("overall quality rating"), but the rating lives in a short prepended header (`… — 4.3/5 overall quality …`) while the rest of each chunk is opinion prose about Data 8 projects, office hours, and exams. all-MiniLM-L6-v2 embeds the *whole* chunk, so the rating phrase is diluted by the surrounding review text, and a terse factual query embeds weakly against opinion-heavy chunks. The professor's name in the header isn't enough to pull the distance down, so DeNero and Garcia chunks (both CS61A/Data-8 intro-course reviews) end up near-tied in vector space. This is exactly Anticipated Challenge #4 (thin/factual queries retrieving loosely-related chunks).

**What you would change to fix it:** Two options, in order of preference. (1) **Store the structured fields as queryable metadata and short-circuit factual lookups** — the chunker already extracts `overall_quality`, `would_take_again`, and `professor` into metadata; a rating/percentage question could be answered directly from a metadata filter (`where professor == "John DeNero"`) instead of relying on semantic distance. (2) **Add a dedicated "professor summary" chunk** per professor containing just the header stats (name + rating + would-take-again + difficulty) with no review prose, so factual queries have a clean, low-dilution target to match against. I'd try (1) first since the metadata already exists.

---

## Spec Reflection

<!-- Reflect on how planning.md shaped your implementation.
     Answer both questions with at least 2–3 sentences each. -->

**One way the spec helped you during implementation:** The Chunking Strategy section's decision to *prepend attribution context (professor header / thread question) to every chunk* was the single most useful directive, and it paid off directly in evaluation. Because I'd committed to that on paper before writing code, the chunker put `Professor John DeNero — 4.3/5 overall quality …` and `Professor Kannan Ramchandran — 85% would take again …` at the top of every review chunk. That meant Q1 and Q4 (both factual-lookup questions) were *answerable at all* — the fact lived in the header — and Q5's contradictory Rao reviews stayed attributable to Rao instead of blurring into other professors. Having the strategy written down also gave me concrete numbers (256-token cap, ~250-token target) to implement against instead of guessing chunk sizes mid-build.

**One way your implementation diverged from the spec, and why:** My Retrieval Approach planned a *score threshold to drop weak matches* (anything roughly above 0.5–0.6). I dropped that during implementation. Testing revealed that the **correct** answer for Q1 (DeNero's 4.3/5) sits at distance 0.573 — above the threshold I'd planned — so a hard cutoff would have made the system refuse a question it could actually answer. I therefore enforce grounding through the **system prompt's refusal rule** ("if the context doesn't contain the answer, say 'I don't have enough information on that'") rather than a distance gate. This handles out-of-corpus questions correctly (verified: "Is Professor Alan Turing a good lecturer?" → refusal) without falsely rejecting answerable-but-loosely-embedded factual queries. A second, smaller divergence: I planned to embed by calling `SentenceTransformer(...)` manually, but used ChromaDB's built-in `SentenceTransformerEmbeddingFunction` instead, because it guarantees queries and documents are embedded by the exact same model.

---

## AI Usage

<!-- Describe at least 2 specific instances where you used an AI tool during this project.
     For each: what did you give the AI as input, what did it produce, and what did you
     change, override, or direct differently?

     "I used Claude to help me code" is not sufficient.
     "I gave Claude my Chunking Strategy section from planning.md and asked it to implement
     chunk_text(). It returned a function using a fixed character split. I overrode the
     chunk size from 500 to 200 because my documents are short reviews, not long guides." -->

**Instance 1 — Ingestion & chunking (Milestone 3)**

- *What I gave the AI:* My Documents, Chunking Strategy, and Architecture sections from planning.md, pointed it at the `documents/` folder, and constrained it to stdlib-only and to stages 1–2 only.
- *What it produced:* `ingest.py` with `load_documents()` / `clean_text()` / `chunk_documents()` — a structure-aware splitter that detects RMP-collection vs Reddit-thread files, prepends the professor header or thread question to each chunk, and groups units toward ~250 tokens. While inspecting the data it also caught that the reply-section delimiter is phrased five different ways across the files (`Thread response:`, `Thread Responses:`, `Reddit Response:`, `Other Reddit Responses on the thread:`, etc.) and matched all of them.
- *What I changed or overrode:* Two directions I drove. (1) I overrode the chunk `source` from the local `.txt` filename to the **original document URL** from my planning Documents table, so answers cite a clickable RMP/Reddit/Medium link — it added a `SOURCE_URLS` map and a `url` metadata field. (2) When I pointed out that `switch_into_cs.txt` actually concatenates three different sources (one Medium article + two Reddit threads), I directed it to **split that file per-section** so each chunk carries the correct URL, instead of mislabeling all of them with one file-level link.

**Instance 2 — Embedding approach (Milestone 4)**

- *What I gave the AI:* My Retrieval Approach section, plus `embed_and_store()` code from an earlier project of mine that used ChromaDB's `SentenceTransformerEmbeddingFunction`, and asked how that differed from what it was proposing.
- *What it produced:* An initial `embed.py` that embedded chunks by calling `SentenceTransformer(...).encode()` manually and cached the model with `functools.lru_cache`. It also explained the lru_cache and the manual-vs-embedding-function tradeoff when I asked.
- *What I changed or overrode:* I directed it to **switch to ChromaDB's built-in `SentenceTransformerEmbeddingFunction`** (matching my familiar pattern, and guaranteeing the query and documents are embedded by the same model) rather than embedding manually — while keeping a clean delete-and-rebuild step and passing my full metadata through. I confirmed this divergence didn't break anything in planning.md before accepting it. Later, in Milestone 5, I also directed it to **suppress the source list on refusals** and to make the example questions **one-click** (fill the box and answer without pressing Ask).

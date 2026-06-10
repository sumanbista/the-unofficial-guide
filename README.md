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

| # | Question | Expected answer | System response (summarized) | Retrieval quality | Response accuracy |
|---|----------|-----------------|------------------------------|-------------------|-------------------|
| 1 | | | | | |
| 2 | | | | | |
| 3 | | | | | |
| 4 | | | | | |
| 5 | | | | | |

**Retrieval quality:** Relevant / Partially relevant / Off-target  
**Response accuracy:** Accurate / Partially accurate / Inaccurate

---

## Failure Case Analysis

<!-- Identify at least one question where retrieval or generation did not work as expected.
     Write a specific explanation of *why* it failed, tied to a part of the pipeline.

     "The answer was wrong" is not an explanation.

     "The relevant information was split across a chunk boundary, so retrieval returned
     only half the context — the model didn't have enough to answer correctly" is an explanation.

     "The embedding model treated the professor's nickname as out-of-vocabulary and returned
     results from an unrelated review" is an explanation. -->

**Question that failed:**

**What the system returned:**

**Root cause (tied to a specific pipeline stage):**

**What you would change to fix it:**

---

## Spec Reflection

<!-- Reflect on how planning.md shaped your implementation.
     Answer both questions with at least 2–3 sentences each. -->

**One way the spec helped you during implementation:**

**One way your implementation diverged from the spec, and why:**

---

## AI Usage

<!-- Describe at least 2 specific instances where you used an AI tool during this project.
     For each: what did you give the AI as input, what did it produce, and what did you
     change, override, or direct differently?

     "I used Claude to help me code" is not sufficient.
     "I gave Claude my Chunking Strategy section from planning.md and asked it to implement
     chunk_text(). It returned a function using a fixed character split. I overrode the
     chunk size from 500 to 200 because my documents are short reviews, not long guides." -->

**Instance 1**

- *What I gave the AI:*
- *What it produced:*
- *What I changed or overrode:*

**Instance 2**

- *What I gave the AI:*
- *What it produced:*
- *What I changed or overrode:*

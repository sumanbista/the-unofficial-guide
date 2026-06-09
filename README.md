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

<!-- List every source you collected documents from.
     Be specific: include URLs, subreddit names, forum thread titles, or file names.
     Aim for variety — sources that together cover different subtopics or perspectives. -->

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

**Chunk size:**

**Overlap:**

**Why these choices fit your documents:**

**Final chunk count:**

---

## Embedding Model

<!-- Name the embedding model you used and explain your choice.
     Then answer: if you were deploying this system for real users and cost wasn't a constraint,
     what tradeoffs would you weigh in choosing a different model?
     Consider: context length limits, multilingual support, accuracy on domain-specific text,
     latency, and local vs. API-hosted. -->

**Model used:**

**Production tradeoff reflection:**

---

## Grounded Generation

<!-- Explain how your system enforces grounding — how does it prevent the LLM from answering
     beyond the retrieved documents?
     Describe both your system prompt (what instruction you gave the model) and any structural
     choices (e.g., how you formatted the context, whether you filtered low-relevance chunks).
     Do not just say "I told it to use the documents" — show the actual instruction or explain
     the mechanism. -->

**System prompt grounding instruction:**

**How source attribution is surfaced in the response:**

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

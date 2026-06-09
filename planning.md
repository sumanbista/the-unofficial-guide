# Project 1 Planning: The Unofficial Guide

> Write this document before you write any pipeline code.
> Your spec and architecture diagram are what you'll use to direct AI tools (Claude, Copilot, etc.) to generate your implementation — the more specific they are, the more useful the generated code will be.
> Update the Retrieval Approach and Chunking Strategy sections if you change your approach during implementation.
> Update this file before starting any stretch features.

---

## Domain

**Chosen Domain**: Student reviews and unofficial advice about CS/EECS courses and professors at UC Berkeley.

This system covers real student-generated knowledge about UC Berkeley’s Computer Science (CS) program — including professor teaching styles, course difficulty, workload, workload management tips, major declaration/switching experiences, and survival advice for classes like CS61A, CS61B, CS70, CS170, etc.

**Why this knowledge is valuable**: Official course catalogs and university websites only provide dry descriptions (topics covered, prerequisites). They don’t tell students which professors are engaging vs. confusing, how brutal the workload actually is, whether a class is curved harshly, or how to succeed with no prior programming experience. This “unofficial” knowledge helps students make better scheduling decisions, reduce stress, and improve their academic experience.

**Why it’s hard to find**: High-quality student insights are scattered across old Reddit threads (r/berkeley), RateMyProfessors pages, Medium posts, and Discord servers. They’re hard to search, often outdated, and mixed with noise. A RAG system makes this collective student wisdom searchable and reliable.
---

## Documents

| # | Source | Description | URL or location |
|---|--------|-------------|-----------------|
| 1 | Rate My Professors|Best Rated RMP Professors|documets/best_rating_rmpt.txt|
| 2 | Rate My Professors| Low-rated CS professors and common complaints |documets/worst_rating_rmp.txt |
| 3 | Reddit|CS70 Professor Rao|documets/cs_70_professor_rao.txt|
| 4 |Reddit|CS Classes Ranked by Difficulty |documets/cs_classes_ranked_difficulty.txt|
| 5 |Medium |CS vs EECS |documets/cs_vs_eecs.txt |
| 6 |Reddit| No Programming Experience |documets/no_programming_experience.txt|
| 7 |Reddit|Concerns about being CS at Berkeley |documets/concerns_cs_at_berkley|
| 8 | Medium | Switching Into CS | documets/switch_into_cs.txt |
| 9 | Reddit | Switching Into CS | documets/switch_into_cs.txt|
| 10| Reddit | Switching Into CS |documets/switch_into_cs.txt|
| 11 |Reddit|CS Classes Ranked by Difficulty |documets/cs_classes_ranked_difficulty.txt|
| 12 |Reddit|How Hard and Time Consuming is CS at Berkeley |how_hard_cs.txt|

---

## Chunking Strategy

<!-- How will you split documents into chunks?
     State your chunk size (in tokens or characters), overlap size, and explain why those
     numbers fit the structure of your documents.
     A review-heavy corpus warrants different chunking than a long FAQ. -->

**Chunk size:**

**Overlap:**

**Reasoning:**

---

## Retrieval Approach

<!-- Which embedding model are you using (e.g., all-MiniLM-L6-v2 via sentence-transformers)?
     How many chunks will you retrieve per query (top-k)?
     If you were deploying this for real users and cost wasn't a constraint, what tradeoffs
     would you weigh in choosing a different embedding model — context length, multilingual
     support, accuracy on domain-specific text, latency? -->

**Embedding model:**

**Top-k:**

**Production tradeoff reflection:**

---

## Evaluation Plan

<!-- List your 5 test questions with their expected correct answers.
     Questions should be specific enough that you can judge whether the system's response
     is right or wrong. "What are good dining halls?" is too vague.
     "What do students say about wait times at [dining hall name] during lunch?" is testable. -->

| # | Question | Expected answer |
|---|----------|-----------------|
| 1 | | |
| 2 | | |
| 3 | | |
| 4 | | |
| 5 | | |

---

## Anticipated Challenges

<!-- What could go wrong? Name at least two specific risks with reasoning.
     Consider: noisy or inconsistent documents, missing source attribution, off-topic
     retrieval, chunks that split key information across boundaries. -->

1.

2.

---

## Architecture

<!-- Draw a diagram of your pipeline showing the five stages:
     Document Ingestion → Chunking → Embedding + Vector Store → Retrieval → Generation
     Label each stage with the tool or library you're using.
     You can use ASCII art, a Mermaid diagram, or embed a sketch as an image.
     You'll use this diagram as context when prompting AI tools to implement each stage. -->

---

## AI Tool Plan

<!-- For each part of the pipeline below, describe:
     - Which AI tool you plan to use (Claude, Copilot, ChatGPT, etc.)
     - What you'll give it as input (which sections of this planning.md, which requirements)
     - What you expect it to produce
     - How you'll verify the output matches your spec

     "I'll use AI to help me code" is not a plan.
     "I'll give Claude my Chunking Strategy section and ask it to implement chunk_text()
     with my specified chunk size and overlap" is a plan. -->

**Milestone 3 — Ingestion and chunking:**

**Milestone 4 — Embedding and retrieval:**

**Milestone 5 — Generation and interface:**

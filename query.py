"""Grounded generation (Milestone 5, stage 5).

`ask(question)` ties the pipeline together: retrieve the top-k chunks, build a
grounded prompt that instructs the LLM to answer from the retrieved context
only, call Groq's llama-3.3-70b-versatile, and return the answer plus a
programmatically-built source list.

The system prompt below is kept verbatim in sync with the "Grounded
Generation" section of README.md — if you change one, change the other.
Sources are appended from chunk metadata (never invented by the model), so a
displayed citation always points to a document that was actually retrieved.
"""

from __future__ import annotations

import os

from dotenv import load_dotenv
from groq import Groq

from embed import DEFAULT_TOP_K, retrieve

load_dotenv()

MODEL = "llama-3.3-70b-versatile"

# Exact refusal string the system prompt (Rule 2) tells the model to return
# when the context can't answer the question. When the answer is a refusal we
# suppress the source list — citing documents under "I don't have enough
# information" would be misleading, since none of them actually answered.
REFUSAL = "I don't have enough information on that."

# Verbatim with README.md "System prompt grounding instruction".
SYSTEM_PROMPT = """You are an assistant that answers questions about UC Berkeley CS/EECS courses and professors using only the student reviews and Reddit/Medium excerpts in the Context below.

Rules:
1. Use only the information in the Context. Do not use outside or prior knowledge.
2. If the Context does not contain enough information to answer, reply exactly: "I don't have enough information on that." Do not guess or fill gaps from general knowledge.
3. The Context is subjective student opinion and reviews often disagree. When sources conflict (e.g. "great lecturer" vs. "reads off slides"), represent the range of views rather than averaging them into one verdict or silently picking a side.
4. Do not invent professor names, ratings, course numbers, or URLs that are not in the Context.
5. Be concise and specific; ground claims in the provided reviews."""


def _client() -> Groq:
    key = os.environ.get("GROQ_API_KEY")
    if not key:
        raise RuntimeError(
            "GROQ_API_KEY is not set. Add your free Groq key to .env "
            "(see .env.example) before calling ask()."
        )
    return Groq(api_key=key)


def _format_context(chunks: list[dict]) -> str:
    """Render retrieved chunks as numbered, attributed context blocks. Each
    chunk's text already carries its attribution header (professor + rating, or
    thread title); we add the source URL so the model sees provenance."""
    blocks = []
    for i, c in enumerate(chunks, 1):
        url = c["metadata"].get("url", "")
        blocks.append(f"[{i}] (source: {url})\n{c['text']}")
    return "\n\n".join(blocks)


def _collect_sources(chunks: list[dict]) -> list[str]:
    """Build a de-duplicated source list from chunk metadata (not the model).

    One entry per distinct URL, labelled with who/what it covers (professor
    name for RMP, thread title for Reddit/Medium)."""
    by_url: dict[str, list[str]] = {}
    for c in chunks:
        m = c["metadata"]
        url = m.get("url", "") or m.get("source", "")
        label = m.get("professor") or m.get("title") or m.get("source", "")
        labels = by_url.setdefault(url, [])
        if label and label not in labels:
            labels.append(label)
    sources = []
    for url, labels in by_url.items():
        sources.append(f"{', '.join(labels)} — {url}" if labels else url)
    return sources


def ask(question: str, k: int = DEFAULT_TOP_K) -> dict:
    """Answer `question` grounded in the retrieved corpus.

    Returns {"answer": str, "sources": list[str], "chunks": list[dict]} where
    `chunks` are the retrieved results (text + metadata + distance) for
    inspection/debugging.
    """
    chunks = retrieve(question, k=k)
    context = _format_context(chunks)

    response = _client().chat.completions.create(
        model=MODEL,
        temperature=0.2,  # low: we want grounded, not creative, answers
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": f"Context:\n{context}\n\nQuestion: {question}",
            },
        ],
    )
    answer = response.choices[0].message.content.strip()
    # suppress citations when the model declined to answer
    is_refusal = answer.rstrip(".").strip().lower() == REFUSAL.rstrip(".").lower()
    sources = [] if is_refusal else _collect_sources(chunks)
    return {
        "answer": answer,
        "sources": sources,
        "chunks": chunks,
    }


# --------------------------------------------------------------------------- #
# end-to-end smoke test
# --------------------------------------------------------------------------- #
def main() -> None:
    queries = [
        "What is John DeNero's overall quality rating?",
        "What do students say about Professor Satish Rao's teaching?",
        # out-of-corpus: we have no documents on this professor -> should refuse
        "Is Professor Alan Turing a good lecturer at Berkeley?",
    ]
    for q in queries:
        print("=" * 78)
        print(f"Q: {q}")
        print("=" * 78)
        result = ask(q)
        print(f"\nANSWER:\n{result['answer']}\n")
        print("RETRIEVED FROM:")
        for s in result["sources"]:
            print(f"  • {s}")
        print()


if __name__ == "__main__":
    main()

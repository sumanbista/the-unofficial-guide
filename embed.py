"""Embedding + vector store + retrieval (Milestone 4, stages 3-4).

Takes the chunks produced by ingest.py and stores them in a persistent
ChromaDB collection. ChromaDB embeds the chunk text for us using
sentence-transformers with all-MiniLM-L6-v2 (384-dim, local, no API key) — the
model is attached to the collection, so queries and documents are guaranteed to
be embedded the same way.

`retrieve(query, k=5)` runs a cosine-similarity search and returns the top-k
chunks with their source metadata and distance scores.

See planning.md "Retrieval Approach": top-k = 5, cosine distance, MiniLM's
256 word-piece cap (already respected by the chunker).

Run directly to (re)build the index and test the evaluation-plan queries:
    python embed.py
"""

from __future__ import annotations

from pathlib import Path

import chromadb
from chromadb.utils import embedding_functions

from ingest import chunk_documents, load_documents

EMBEDDING_MODEL = "all-MiniLM-L6-v2"
PERSIST_DIR = str(Path(__file__).parent / "chroma_db")
COLLECTION_NAME = "unofficial_guide"
DEFAULT_TOP_K = 5

# Embedding function, client, and collection are initialized once at import.
# sentence-transformers loads the model on first use (cached locally after the
# first download). The embedding_function is attached to the collection, so
# ChromaDB embeds both stored documents and incoming queries with this model.
_ef = embedding_functions.SentenceTransformerEmbeddingFunction(
    model_name=EMBEDDING_MODEL
)
_client = chromadb.PersistentClient(path=PERSIST_DIR)
_collection = _client.get_or_create_collection(
    name=COLLECTION_NAME,
    embedding_function=_ef,
    metadata={"hnsw:space": "cosine"},  # cosine distance, per the spec
)

# A few of the Evaluation Plan queries (planning.md) used to smoke-test retrieval.
EVAL_QUERIES = [
    "What is John DeNero's overall quality rating?",
    "What classes does Professor Jennifer Listgarten teach?",
    'What is the "Would Take Again" percentage for Professor Kannan Ramchandran?',
    "What do students say about Professor Satish Rao's teaching?",
    "Do students need prior programming experience to succeed in CS at Berkeley?",
]


def get_collection() -> chromadb.Collection:
    """Return the ChromaDB collection (used by app.py / retrieval)."""
    return _collection


def embed_and_store(chunks: list[dict]) -> chromadb.Collection:
    """Embed a list of chunks and store them in the vector database.

    We hand ChromaDB three parallel lists; the attached embedding_function
    converts each `documents` string into a 384-dim vector automatically:
      - documents : the chunk text (context header + body), embedded for search
      - metadatas : one dict per chunk (source, chunk_index, professor/title,
                    ratings) — stored alongside the vector for attribution
      - ids       : the unique chunk_id strings

    No manual model.encode() call here — ChromaDB does the vector math.
    """
    _collection.add(
        documents=[c["text"] for c in chunks],
        metadatas=[c["metadata"] for c in chunks],
        ids=[c["metadata"]["chunk_id"] for c in chunks],
    )
    print(f"Stored {_collection.count()} total chunks in the vector database.")
    return _collection


def build_index() -> chromadb.Collection:
    """Load + chunk documents and (re)populate the collection from scratch.

    Drops any existing collection first so re-running after a chunker change
    never leaves stale or duplicate vectors behind.
    """
    global _collection
    chunks = chunk_documents(load_documents())
    if not chunks:
        raise RuntimeError("No chunks produced — check documents/ and ingest.py")

    # reset: delete and recreate so the index always matches the current chunks
    try:
        _client.delete_collection(COLLECTION_NAME)
    except Exception:
        pass
    _collection = _client.get_or_create_collection(
        name=COLLECTION_NAME,
        embedding_function=_ef,
        metadata={"hnsw:space": "cosine"},
    )
    return embed_and_store(chunks)


def retrieve(query: str, k: int = DEFAULT_TOP_K) -> list[dict]:
    """Embed `query` and return the top-k most similar chunks.

    Each result: {"text", "metadata", "distance"} where distance is cosine
    distance (0 = identical direction; lower is more relevant), ordered
    nearest-first.
    """
    res = _collection.query(
        query_texts=[query],
        n_results=k,
        include=["documents", "metadatas", "distances"],
    )
    results = []
    for text, meta, dist in zip(
        res["documents"][0], res["metadatas"][0], res["distances"][0]
    ):
        results.append({"text": text, "metadata": meta, "distance": dist})
    return results


# --------------------------------------------------------------------------- #
# retrieval smoke test
# --------------------------------------------------------------------------- #
def _preview(text: str, max_chars: int = 350) -> str:
    text = " ".join(text.split())
    return text if len(text) <= max_chars else text[:max_chars] + " …"


def main() -> None:
    print(f"Building index with {EMBEDDING_MODEL} → ChromaDB ({PERSIST_DIR}) …")
    build_index()
    print()

    for q in EVAL_QUERIES:
        print("=" * 78)
        print(f"QUERY: {q}")
        print("=" * 78)
        for rank, r in enumerate(retrieve(q), 1):
            m = r["metadata"]
            attribution = m.get("professor") or m.get("title") or "?"
            flag = "  <-- weak (>0.5)" if r["distance"] > 0.5 else ""
            print(
                f"\n[{rank}] distance={r['distance']:.3f}{flag}  "
                f"source={m['source']} #{m['chunk_index']}  ({attribution})"
            )
            print(f"    url: {m.get('url', '')}")
            print(f"    {_preview(r['text'])}")
        print()


if __name__ == "__main__":
    main()

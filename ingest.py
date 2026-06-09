"""Document ingestion + chunking pipeline (Milestone 3, stages 1-2).

Two jobs, per planning.md:
  1. load documents from documents/ into memory
  2. split them into attributable chunks our embedding model can handle

The corpus has three structural shapes:
  - RMP files      : one professor header (name + ratings) followed by many
                     blank-line-separated student reviews, each starting with a
                     course code. Detected by the "Professor in the Computer
                     Science department" marker line.
  - Reddit threads : a title/question at the top, a reply-section marker
                     (phrased several different ways across files), then
                     blank-line-separated replies. Some files chain >1 thread.
  - Medium articles: plain prose paragraphs, no headers or replies.

Chunking strategy (see planning.md "Chunking Strategy"):
  - atomic unit = one review / one reply / one paragraph
  - group short consecutive units up to ~250 tokens
  - sub-split any single unit over the embedding cap at sentence boundaries,
    with ~50-token overlap (this is the ONLY place overlap is used)
  - prepend attribution context (professor header / thread title) to EVERY
    chunk so each chunk is self-contained and attributable

stdlib only, by design for this milestone.
"""

from __future__ import annotations

import html
import os
import re
from pathlib import Path

DOCUMENTS_DIR = Path(__file__).parent / "documents"

# Token budgeting. all-MiniLM-L6-v2 silently truncates past ~256 word-pieces,
# so we treat 256 as a hard ceiling (context + body together) and aim a bit
# under it. We have no tokenizer here (stdlib only), so estimate from words.
MAX_TOKENS = 256          # MiniLM input cap; nothing may exceed this
TARGET_TOKENS = 230       # what we aim each grouped chunk to land near
OVERLAP_TOKENS = 50       # carried between sub-splits of one long unit only
TOKENS_PER_WORD = 1.3     # rough word->wordpiece inflation for English text

# The RMP professor-header marker.
RMP_MARKER = "Professor in the Computer Science department"

# Reply-section markers seen across the Reddit/Medium files (case-insensitive).
# Anything matching is treated as a section break, not content.
SECTION_MARKER_RE = re.compile(
    r"^\s*(thread responses?|other reddit responses[^\n]*|reddit response|"
    r"reddit question|sourced from medium)\s*:?\s*$",
    re.IGNORECASE,
)

# Short category/flair lines that carry no question content on their own.
FLAIR_RE = re.compile(r"^\s*(CS/EECS|Waitlists?/Deferrals?)\s*$", re.IGNORECASE)

# A leading "Thread Title:" prefix we strip when deriving a title.
TITLE_PREFIX_RE = re.compile(r"^\s*thread title\s*:\s*", re.IGNORECASE)

# RMP header field patterns.
RE_OVERALL = re.compile(r"([\d.]+)\s*/\s*5\s+Overall Quality", re.IGNORECASE)
RE_WTA = re.compile(r"(\d+)%\s+Would take again", re.IGNORECASE)
RE_DIFFICULTY = re.compile(r"([\d.]+)\s+Level of Difficulty", re.IGNORECASE)

# A review's first line is a course code, e.g. CS61B / cs61a / CS10 / EECS106A / Data 8.
RE_COURSE = re.compile(r"^(CS|EECS|EE|DATA|DS)\s?\w*\d+\w*\s*$", re.IGNORECASE)

# Sentence boundary for sub-splitting long units.
RE_SENTENCE = re.compile(r"(?<=[.!?])\s+")


# --------------------------------------------------------------------------- #
# Stage 1: load
# --------------------------------------------------------------------------- #
def load_documents(directory: str | os.PathLike = DOCUMENTS_DIR) -> list[dict]:
    """Read every .txt file under `directory` into memory.

    Returns a list of {"source": filename, "text": raw_text}, sorted by name
    for stable, reproducible chunk ordering.
    """
    directory = Path(directory)
    docs = []
    for path in sorted(directory.glob("*.txt")):
        docs.append({"source": path.name, "text": path.read_text(encoding="utf-8")})
    return docs


# --------------------------------------------------------------------------- #
# Stage 1.5: clean
# --------------------------------------------------------------------------- #
def clean_text(text: str) -> str:
    """Normalize whitespace and unescape any stray HTML entities.

    The sources are already plain text, so this is light: decode entities
    (&amp;, &nbsp;, ...), normalize line endings, strip trailing spaces, and
    collapse runs of 3+ blank lines down to a single blank-line separator
    (our unit delimiter). Review/reply text and all attribution context are
    preserved untouched.
    """
    text = html.unescape(text)
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = text.replace(" ", " ")  # non-breaking space -> normal space
    # strip trailing whitespace per line
    lines = [ln.rstrip() for ln in text.split("\n")]
    text = "\n".join(lines)
    # collapse 3+ newlines into exactly two (one blank line)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


# --------------------------------------------------------------------------- #
# helpers
# --------------------------------------------------------------------------- #
def estimate_tokens(text: str) -> int:
    """Cheap word-piece estimate (no tokenizer dependency)."""
    return round(len(text.split()) * TOKENS_PER_WORD)


def _split_units(block: str) -> list[str]:
    """Split a block into atomic units on blank lines, dropping marker/flair-only
    lines and empty units."""
    raw_units = re.split(r"\n\s*\n", block)
    units = []
    for u in raw_units:
        # drop section-marker / flair lines that may sit alone in a unit
        kept = [
            ln
            for ln in u.split("\n")
            if ln.strip()
            and not SECTION_MARKER_RE.match(ln)
            and not FLAIR_RE.match(ln)
        ]
        joined = "\n".join(kept).strip()
        if joined:
            units.append(joined)
    return units


def _sentence_subsplit(unit: str, max_body_tokens: int) -> list[str]:
    """Split one over-long unit at sentence boundaries into pieces under
    `max_body_tokens`, carrying ~OVERLAP_TOKENS of trailing sentences into the
    next piece so a mid-argument cut is never lost."""
    sentences = RE_SENTENCE.split(unit)
    pieces: list[str] = []
    current: list[str] = []
    cur_tokens = 0
    for sent in sentences:
        st = estimate_tokens(sent)
        if current and cur_tokens + st > max_body_tokens:
            pieces.append(" ".join(current))
            # build overlap tail from the end of the current piece
            overlap, ot = [], 0
            for s in reversed(current):
                overlap.insert(0, s)
                ot += estimate_tokens(s)
                if ot >= OVERLAP_TOKENS:
                    break
            current = overlap
            cur_tokens = sum(estimate_tokens(s) for s in current)
        current.append(sent)
        cur_tokens += st
    if current:
        pieces.append(" ".join(current))
    return pieces


def _group_units(units: list[str], context: str) -> list[tuple[str, list[str]]]:
    """Greedily group consecutive units so each chunk's (context + body) stays
    under MAX_TOKENS, aiming near TARGET_TOKENS. Over-long single units are
    sentence-sub-split. Returns (body_text, member_units) pairs."""
    ctx_tokens = estimate_tokens(context)
    max_body = MAX_TOKENS - ctx_tokens
    target_body = max(TARGET_TOKENS - ctx_tokens, max_body // 2)

    chunks: list[tuple[str, list[str]]] = []
    current: list[str] = []
    cur_tokens = 0

    def flush():
        nonlocal current, cur_tokens
        if current:
            chunks.append(("\n\n".join(current), list(current)))
            current = []
            cur_tokens = 0

    for unit in units:
        ut = estimate_tokens(unit)
        if ut > max_body:
            flush()
            for piece in _sentence_subsplit(unit, max_body):
                chunks.append((piece, [piece]))
            continue
        if current and cur_tokens + ut > target_body:
            flush()
        current.append(unit)
        cur_tokens += ut
    flush()
    return chunks


def _courses_in(units: list[str]) -> list[str]:
    """Collect course codes that appear as the first line of member units."""
    courses = []
    for u in units:
        first = u.split("\n", 1)[0].strip()
        if RE_COURSE.match(first):
            code = first.upper().replace(" ", "")
            if code not in courses:
                courses.append(code)
    return courses


# --------------------------------------------------------------------------- #
# Stage 2: chunk
# --------------------------------------------------------------------------- #
def _chunk_rmp(text: str, source: str) -> list[dict]:
    """Split an RMP file into per-professor review chunks with the professor
    header prepended to every chunk."""
    lines = text.split("\n")
    # professor block starts at the line BEFORE each RMP_MARKER line
    starts = [i - 1 for i, ln in enumerate(lines) if RMP_MARKER in ln and i > 0]
    chunks: list[dict] = []

    for b, start in enumerate(starts):
        end = starts[b + 1] if b + 1 < len(starts) else len(lines)
        block = "\n".join(lines[start:end]).strip()
        block_lines = block.split("\n")

        professor = block_lines[0].strip()

        # The header (name + marker + stat lines, with blank lines interleaved)
        # runs until the first review, which always begins with a course code.
        first_review = next(
            (i for i, ln in enumerate(block_lines) if RE_COURSE.match(ln.strip())),
            len(block_lines),
        )
        header_blob = "\n".join(block_lines[:first_review])
        m_overall = RE_OVERALL.search(header_blob)
        m_wta = RE_WTA.search(header_blob)
        m_diff = RE_DIFFICULTY.search(header_blob)
        overall = m_overall.group(1) if m_overall else None
        wta = m_wta.group(1) if m_wta else None
        diff = m_diff.group(1) if m_diff else None

        # human-readable attribution context prepended to each chunk
        ctx_parts = [f"Professor {professor} (UC Berkeley CS)"]
        stats = []
        if overall:
            stats.append(f"{overall}/5 overall quality")
        if wta:
            stats.append(f"{wta}% would take again")
        if diff:
            stats.append(f"difficulty {diff}/5")
        if stats:
            ctx_parts.append(", ".join(stats) + ".")
        context = " — ".join(ctx_parts)

        # reviews = everything from the first course-code line onward
        review_region = "\n".join(block_lines[first_review:]).strip()
        units = _split_units(review_region)
        if not units:
            continue

        for body, members in _group_units(units, context):
            courses = _courses_in(members)
            chunk_text = f"{context}\n\n{body}"
            chunks.append(
                {
                    "text": chunk_text,
                    "metadata": {
                        "source": source,
                        "type": "rmp",
                        "professor": professor,
                        "courses": ", ".join(courses),
                        "overall_quality": overall or "",
                        "would_take_again": (wta + "%") if wta else "",
                        "difficulty": diff or "",
                        "n_tokens": estimate_tokens(chunk_text),
                    },
                }
            )
    return chunks


def _derive_title(text: str) -> str:
    """First meaningful line as a thread/article title, with known prefixes
    stripped and marker/flair lines skipped."""
    for ln in text.split("\n"):
        s = ln.strip()
        if not s or SECTION_MARKER_RE.match(s) or FLAIR_RE.match(s):
            continue
        s = TITLE_PREFIX_RE.sub("", s).strip()
        if s:
            return s
    return "Untitled"


def _chunk_thread(text: str, source: str) -> list[dict]:
    """Split a Reddit-thread or Medium-article file. Title is prepended to
    every chunk for attribution; the question/reply distinction is not
    structurally required since the title carries attribution."""
    title = _derive_title(text)
    context = f"Thread: {title}"
    units = _split_units(text)

    # Drop a unit that is just the title line repeated (avoid duplicating it).
    units = [u for u in units if u.strip() != title]

    chunks: list[dict] = []
    for body, _members in _group_units(units, context):
        chunk_text = f"{context}\n\n{body}"
        chunks.append(
            {
                "text": chunk_text,
                "metadata": {
                    "source": source,
                    "type": "thread",
                    "title": title,
                    "n_tokens": estimate_tokens(chunk_text),
                },
            }
        )
    return chunks


def chunk_documents(docs: list[dict]) -> list[dict]:
    """Turn loaded+cleaned documents into a flat list of chunk dicts.

    Each chunk: {"text": str, "metadata": {... source, type, n_tokens, chunk_index, chunk_id ...}}
    """
    all_chunks: list[dict] = []
    for doc in docs:
        cleaned = clean_text(doc["text"])
        source = doc["source"]
        if RMP_MARKER in cleaned:
            doc_chunks = _chunk_rmp(cleaned, source)
        else:
            doc_chunks = _chunk_thread(cleaned, source)

        for i, ch in enumerate(doc_chunks):
            ch["metadata"]["chunk_index"] = i
            ch["metadata"]["chunk_id"] = f"{source}::{i}"
        all_chunks.extend(doc_chunks)
    return all_chunks


# --------------------------------------------------------------------------- #
# inspection entrypoint
# --------------------------------------------------------------------------- #
def _preview(chunk: dict, max_chars: int = 600) -> str:
    text = chunk["text"]
    if len(text) > max_chars:
        text = text[:max_chars] + " …"
    return text


def main() -> None:
    docs = load_documents()
    chunks = chunk_documents(docs)

    print(f"Loaded {len(docs)} documents from {DOCUMENTS_DIR}")
    print(f"Produced {len(chunks)} chunks total\n")

    # per-document breakdown
    print("Chunks per document:")
    by_source: dict[str, int] = {}
    for c in chunks:
        by_source[c["metadata"]["source"]] = by_source.get(c["metadata"]["source"], 0) + 1
    for src, n in sorted(by_source.items()):
        print(f"  {src:<35} {n:>3}")

    # token distribution sanity
    tokens = [c["metadata"]["n_tokens"] for c in chunks]
    over_cap = [t for t in tokens if t > MAX_TOKENS]
    print(
        f"\nToken estimate — min {min(tokens)}, max {max(tokens)}, "
        f"avg {sum(tokens) // len(tokens)}; {len(over_cap)} chunk(s) over the "
        f"{MAX_TOKENS}-token cap"
    )

    # representative chunks: one RMP, one short thread reply, one sub-split
    print("\n" + "=" * 70)
    print("REPRESENTATIVE CHUNKS")
    print("=" * 70)

    def show(label, chunk):
        print(f"\n--- {label} ---")
        print(f"metadata: {chunk['metadata']}")
        print(_preview(chunk))

    rmp = next((c for c in chunks if c["metadata"]["type"] == "rmp"), None)
    short = min(
        (c for c in chunks if c["metadata"]["type"] == "thread"),
        key=lambda c: c["metadata"]["n_tokens"],
        default=None,
    )
    longest = max(chunks, key=lambda c: c["metadata"]["n_tokens"])
    if rmp:
        show("RMP review chunk", rmp)
    if short:
        show("Short Reddit reply chunk", short)
    show("Longest chunk (closest to cap)", longest)


if __name__ == "__main__":
    main()

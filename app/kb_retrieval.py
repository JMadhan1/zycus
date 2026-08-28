"""Lightweight local RAG over the markdown knowledge base.

Uses TF-IDF + cosine similarity instead of a hosted embedding API: the KB is
small (9 docs), retrieval must be deterministic for the eval harness, and it
keeps ticket/account text from ever leaving the machine for the retrieval step
(see README design note on data sensitivity).
"""
import re
from dataclasses import dataclass
from functools import lru_cache

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from app.config import KB_DIR


@dataclass
class Chunk:
    doc_path: str
    section: str
    text: str


def _chunk_markdown(path) -> list[Chunk]:
    raw = path.read_text(encoding="utf-8")
    rel_path = str(path.relative_to(KB_DIR.parent))
    parts = re.split(r"\n-{3,}\n", raw)
    chunks = []
    current_heading = path.stem
    for part in parts:
        part = part.strip()
        if not part:
            continue
        heading_match = re.search(r"^#{1,3}\s+(.+)$", part, re.MULTILINE)
        heading = heading_match.group(1).strip() if heading_match else current_heading
        current_heading = heading
        chunks.append(Chunk(doc_path=rel_path, section=heading, text=part))
    return chunks


@lru_cache(maxsize=1)
def load_chunks() -> tuple[Chunk, ...]:
    chunks: list[Chunk] = []
    for path in sorted(KB_DIR.rglob("*.md")):
        chunks.extend(_chunk_markdown(path))
    return tuple(chunks)


@lru_cache(maxsize=1)
def _index():
    chunks = load_chunks()
    vectorizer = TfidfVectorizer(stop_words="english", ngram_range=(1, 2))
    matrix = vectorizer.fit_transform([c.text for c in chunks])
    return vectorizer, matrix, chunks


def retrieve(query: str, top_k: int = 3, min_score: float = 0.05) -> list[dict]:
    vectorizer, matrix, chunks = _index()
    query_vec = vectorizer.transform([query])
    scores = cosine_similarity(query_vec, matrix).flatten()
    ranked = sorted(range(len(chunks)), key=lambda i: scores[i], reverse=True)
    results = []
    for i in ranked[:top_k]:
        if scores[i] < min_score:
            continue
        c = chunks[i]
        excerpt = c.text if len(c.text) <= 600 else c.text[:600].rsplit(" ", 1)[0] + "…"
        results.append(
            {
                "doc_path": c.doc_path,
                "section": c.section,
                "relevance_score": round(float(scores[i]), 4),
                "excerpt": excerpt,
            }
        )
    return results

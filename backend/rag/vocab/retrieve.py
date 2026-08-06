"""Culture vocabulary RAG retrieval for companion per-turn context."""

from __future__ import annotations

from typing import Any

from backend.app.config import settings
from backend.rag.embeddings import embed_texts
from backend.rag.query import query_collection
from backend.rag.store import get_vocab_collection


def _term_in_resident_text(term: str, resident_text: str) -> bool:
    """True when the indexed culture term appears in the resident message."""
    needle = term.strip().lower()
    if not needle:
        return False
    return needle in resident_text.lower()


def format_vocabulary_context(chunks: list[dict[str, Any]]) -> str:
    parts: list[str] = []
    for i, chunk in enumerate(chunks, start=1):
        meta = chunk.get("metadata") or {}
        term = meta.get("term", "")
        if not term:
            continue
        meaning = chunk.get("text", "")
        parts.append(f"### Vocabulary {i} — {term}\n{term} → {meaning}")
    return "\n\n".join(parts)


def retrieve_vocabulary_chroma_hits(
    resident_text: str,
    *,
    locale: str,
    top_k: int | None = None,
) -> list[dict[str, Any]]:
    """Top-k culture vocabulary chunks from Chroma by cosine similarity (before literal filter)."""
    k = top_k or settings.rag_vocab_top_k
    query = resident_text.strip()
    if not query:
        return []

    collection = get_vocab_collection()
    count = collection.count()
    if count == 0:
        return []

    query_embedding = embed_texts([query])[0]
    return query_collection(
        query,
        doc_type="culture_vocabulary",
        locale=locale,
        top_k=k,
        query_embedding=query_embedding,
        apply_similarity_threshold=False,
        n_results=min(k, count),
    )


def retrieve_vocabulary_for_companion(
    resident_text: str,
    *,
    locale: str,
    top_k: int | None = None,
) -> list[dict[str, Any]]:
    """Retrieve culture vocabulary for the companion from top-k Chroma hits.

    Fetches top_k chunks from the vector DB by cosine similarity, then keeps only
    terms that literally appear in the resident text.
    """
    query = resident_text.strip()
    if not query:
        return []

    merged: dict[str, dict[str, Any]] = {}
    for row in retrieve_vocabulary_chroma_hits(
        query, locale=locale, top_k=top_k
    ):
        meta = row.get("metadata") or {}
        term = (meta.get("term") or "").strip()
        if not term or not _term_in_resident_text(term, query):
            continue
        similarity = row.get("cosine_similarity")
        existing = merged.get(term)
        if existing is None or (similarity or -1) > (existing.get("cosine_similarity") or -1):
            merged[term] = row

    return sorted(merged.values(), key=lambda r: r.get("cosine_similarity") or -1, reverse=True)

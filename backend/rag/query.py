"""Low-level Chroma cosine search shared by policy and vocab retrieval."""

from __future__ import annotations

from typing import Any

from backend.app.config import settings
from backend.rag.embeddings import embed_texts
from backend.rag.store import get_collection_for_type


def similarity_from_chroma_distance(distance: float | None) -> float | None:
    """Chroma cosine space returns distance; convert to similarity."""
    if distance is None:
        return None
    return 1.0 - distance


def _build_where(
    *,
    locale: str | None,
    pathways: list[str] | None,
    facility_id: str | None = None,
    doc_id: str | None = None,
) -> dict[str, Any] | None:
    clauses: list[dict[str, Any]] = []
    if locale and locale != "all":
        clauses.append({"locale": locale})
    if facility_id:
        clauses.append({"facility_id": facility_id})
    if doc_id:
        clauses.append({"doc_id": doc_id})
    if pathways:
        clauses.append({"pathway": {"$in": pathways}})
    if not clauses:
        return None
    if len(clauses) == 1:
        return clauses[0]
    return {"$and": clauses}


def query_collection(
    query: str,
    *,
    doc_type: str = "facility_policy",
    locale: str | None = None,
    pathways: list[str] | None = None,
    facility_id: str | None = None,
    doc_id: str | None = None,
    top_k: int | None = None,
    query_embedding: list[float] | None = None,
    apply_similarity_threshold: bool = True,
    n_results: int | None = None,
) -> list[dict[str, Any]]:
    k = top_k or settings.rag_top_k
    collection = get_collection_for_type(doc_type)
    if collection.count() == 0:
        return []

    where = _build_where(
        locale=locale, pathways=pathways, facility_id=facility_id, doc_id=doc_id
    )

    embedding = query_embedding if query_embedding is not None else embed_texts([query])[0]
    result = collection.query(
        query_embeddings=[embedding],
        n_results=n_results or min(k * 3, max(collection.count(), 1)),
        where=where,
        include=["documents", "metadatas", "distances"],
    )

    rows: list[dict[str, Any]] = []
    docs = result.get("documents", [[]])[0]
    metas = result.get("metadatas", [[]])[0]
    dists = result.get("distances", [[]])[0]
    for doc, meta, dist in zip(docs, metas, dists, strict=False):
        meta = meta or {}
        similarity = similarity_from_chroma_distance(dist)
        if (
            apply_similarity_threshold
            and similarity is not None
            and similarity < settings.rag_min_similarity
        ):
            continue
        rows.append({"text": doc, "metadata": meta, "cosine_similarity": similarity})
        if len(rows) >= k:
            break
    return rows

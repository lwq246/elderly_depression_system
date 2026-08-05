from dataclasses import dataclass
from typing import Any

from backend.app.config import settings
from backend.rag.embeddings import embed_texts
from backend.rag.store import get_collection

_QUERY_PREFIX = (
    "Residential aged care facility screening follow-up escalation documentation SOP. "
    "Session summary for policy retrieval:"
)


@dataclass
class RagRetrievalResult:
    chunks: list[dict[str, Any]]
    summary: str | None = None
    summary_failed: bool = False


def _chunk_key(meta: dict[str, Any]) -> str:
    locale = meta.get("locale", "all")
    section = meta.get("section") or "unknown"
    return f"{locale}:{section}"


def build_facility_policy_query(summary: str) -> str:
    return f"{_QUERY_PREFIX}\n{summary.strip()}"


def retrieve(
    query: str,
    *,
    doc_type: str = "facility_policy",
    locale: str | None = None,
    top_k: int | None = None,
    query_embedding: list[float] | None = None,
) -> list[dict[str, Any]]:
    k = top_k or settings.rag_top_k
    collection = get_collection()
    if collection.count() == 0:
        return []

    where: dict[str, Any] | None = {"type": doc_type}
    if locale and locale != "all":
        where = {"$and": [{"type": doc_type}, {"locale": locale}]}

    embedding = query_embedding if query_embedding is not None else embed_texts([query])[0]
    result = collection.query(
        query_embeddings=[embedding],
        n_results=min(k * 3, max(collection.count(), 1)),
        where=where,
        include=["documents", "metadatas", "distances"],
    )

    rows: list[dict[str, Any]] = []
    docs = result.get("documents", [[]])[0]
    metas = result.get("metadatas", [[]])[0]
    dists = result.get("distances", [[]])[0]
    for doc, meta, dist in zip(docs, metas, dists, strict=False):
        meta = meta or {}
        if dist is not None and dist > settings.rag_max_distance:
            continue
        rows.append({"text": doc, "metadata": meta, "distance": dist})
        if len(rows) >= k:
            break
    return rows


async def retrieve_for_analyst(
    transcript: list[dict[str, Any]],
    *,
    locale: str = "en-SG",
) -> RagRetrievalResult:
    """Retrieve facility operational SOP chunks for the session locale."""
    collection = get_collection()
    if collection.count() == 0:
        return RagRetrievalResult(chunks=[])

    if not settings.rag_use_llm_summary:
        return RagRetrievalResult(chunks=[])

    try:
        from backend.rag.summary import summarize_transcript_for_rag

        summary = await summarize_transcript_for_rag(transcript, locale=locale)
    except Exception:
        return RagRetrievalResult(chunks=[], summary_failed=True)

    if not summary.strip():
        return RagRetrievalResult(chunks=[], summary_failed=True)

    merged: dict[str, dict[str, Any]] = {}
    query = build_facility_policy_query(summary)
    embedding = embed_texts([query])[0]
    for row in retrieve(
        query,
        doc_type="facility_policy",
        locale=locale,
        top_k=settings.rag_top_k,
        query_embedding=embedding,
    ):
        key = _chunk_key(row["metadata"])
        existing = merged.get(key)
        if existing is None or (row["distance"] or 1) < (existing.get("distance") or 1):
            merged[key] = row

    ranked = sorted(merged.values(), key=lambda r: r.get("distance") or 0)
    return RagRetrievalResult(chunks=ranked[: settings.rag_top_k], summary=summary)


def format_rag_context(chunks: list[dict[str, Any]]) -> str:
    parts: list[str] = []
    for i, chunk in enumerate(chunks, start=1):
        meta = chunk.get("metadata") or {}
        source = meta.get("source", "unknown")
        section = meta.get("section", "")
        chunk_locale = meta.get("locale", "")
        parts.append(
            f"### Facility policy {i} ({source} — {section}, {chunk_locale})\n{chunk['text']}"
        )
    return "\n\n".join(parts)

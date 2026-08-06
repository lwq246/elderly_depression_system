"""Facility policy RAG retrieval for analyst exit."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from backend.app.config import settings
from backend.rag.embeddings import embed_texts
from backend.rag.policy.summary import summarize_transcript_for_rag
from backend.rag.query import query_collection
from backend.rag.store import get_policy_collection

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


async def retrieve_for_analyst(
    transcript: list[dict[str, Any]],
    *,
    locale: str = "en-SG",
) -> RagRetrievalResult:
    """Retrieve facility operational SOP chunks for the session locale."""
    collection = get_policy_collection()
    if collection.count() == 0:
        return RagRetrievalResult(chunks=[])

    if not settings.rag_use_llm_summary:
        return RagRetrievalResult(chunks=[])

    try:
        summary = await summarize_transcript_for_rag(transcript, locale=locale)
    except Exception:
        return RagRetrievalResult(chunks=[], summary_failed=True)

    if not summary.strip():
        return RagRetrievalResult(chunks=[], summary_failed=True)

    merged: dict[str, dict[str, Any]] = {}
    query = build_facility_policy_query(summary)
    embedding = embed_texts([query])[0]
    for row in query_collection(
        query,
        doc_type="facility_policy",
        locale=locale,
        top_k=settings.rag_top_k,
        query_embedding=embedding,
    ):
        key = _chunk_key(row["metadata"])
        existing = merged.get(key)
        row_sim = row.get("cosine_similarity") or -1
        existing_sim = (existing or {}).get("cosine_similarity") or -1
        if existing is None or row_sim > existing_sim:
            merged[key] = row

    ranked = sorted(merged.values(), key=lambda r: r.get("cosine_similarity") or -1, reverse=True)
    return RagRetrievalResult(chunks=ranked[: settings.rag_top_k], summary=summary)


def format_rag_context(chunks: list[dict[str, Any]]) -> str:
    parts: list[str] = []
    for i, chunk in enumerate(chunks, start=1):
        meta = chunk.get("metadata") or {}
        section = meta.get("section", "")
        chunk_locale = meta.get("locale", "")
        parts.append(
            f"### Facility policy {i} ({section}, {chunk_locale})\n{chunk['text']}"
        )
    return "\n\n".join(parts)

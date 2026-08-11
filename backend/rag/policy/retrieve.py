"""Facility policy RAG retrieval for analyst exit."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from backend.app.config import settings
from backend.rag.embeddings import embed_texts
from backend.rag.policy.questions import generate_policy_questions
from backend.rag.policy.rerank import rerank_rows
from backend.rag.policy.routing import (
    PATHWAY_ACTIVE,
    PATHWAY_PASSIVE,
    parse_policy_summary,
    pathways_for_summary,
    pathways_from_transcript_heuristic,
)
from backend.rag.policy.summary import summarize_transcript_for_rag
from backend.rag.query import query_collection
from backend.rag.store import get_policy_collection

_SAFETY_PATHWAYS = {PATHWAY_PASSIVE, PATHWAY_ACTIVE}

_QUERY_PREFIX = (
    "Residential aged care facility screening follow-up escalation documentation SOP. "
    "Policy lookup question:"
)

_TAGS_QUERY_PREFIX = (
    "Residential aged care facility screening follow-up escalation documentation SOP. "
    "Session summary for policy retrieval:"
)


@dataclass
class RagRetrievalResult:
    chunks: list[dict[str, Any]]
    summary: str | None = None
    summary_failed: bool = False
    query: str | None = None
    questions: list[str] = field(default_factory=list)


def _chunk_key(meta: dict[str, Any]) -> str:
    # Dedup at the parent-section level: many child windows collapse to one section.
    parent_id = meta.get("parent_id")
    if parent_id:
        return str(parent_id)
    locale = meta.get("locale", "all")
    section = meta.get("section") or "unknown"
    return f"{locale}:{section}"


def _candidate_pool() -> int:
    if settings.rag_rerank_enabled:
        return max(settings.rag_candidate_pool, settings.rag_top_k)
    return settings.rag_top_k


def _finalize(
    merged: dict[str, dict[str, Any]],
    *,
    rerank_query: str,
    must_include_keys: frozenset[str] = frozenset(),
) -> list[dict[str, Any]]:
    """Cosine-sort, cross-encoder rerank, then take top_k.

    ``must_include_keys`` (safety sections) are guaranteed in the output even if the
    reranker would rank them below top_k — they are never dropped.
    """
    cosine_sorted = sorted(
        merged.values(), key=lambda r: r.get("cosine_similarity") or -1, reverse=True
    )
    ranked = rerank_rows(rerank_query, cosine_sorted)

    must = [r for r in ranked if _chunk_key(r["metadata"]) in must_include_keys]
    rest = [r for r in ranked if _chunk_key(r["metadata"]) not in must_include_keys]

    top = (must + rest)[: settings.rag_top_k]
    for row in must:  # never drop a guaranteed safety section
        if row not in top:
            top.append(row)
    return top


def build_facility_policy_query(text: str, *, mode: str | None = None) -> str:
    strategy = mode or settings.rag_retrieval_mode
    prefix = _QUERY_PREFIX if strategy == "questions" else _TAGS_QUERY_PREFIX
    return f"{prefix}\n{text.strip()}"


def _merge_rows(merged: dict[str, dict[str, Any]], rows: list[dict[str, Any]]) -> None:
    for row in rows:
        key = _chunk_key(row["metadata"])
        existing = merged.get(key)
        row_sim = row.get("cosine_similarity") or -1
        existing_sim = (existing or {}).get("cosine_similarity") or -1
        if existing is None or row_sim > existing_sim:
            merged[key] = row


async def _retrieve_by_questions(
    transcript: list[dict[str, Any]],
    *,
    locale: str,
    collection: Any,
) -> RagRetrievalResult:
    try:
        questions = await generate_policy_questions(transcript, locale=locale)
    except Exception:
        return RagRetrievalResult(chunks=[], summary_failed=True)

    if not questions:
        return RagRetrievalResult(chunks=[], summary_failed=True)

    queries = [build_facility_policy_query(q, mode="questions") for q in questions]
    embeddings = embed_texts(queries)
    merged: dict[str, dict[str, Any]] = {}
    per_query_k = max(_candidate_pool(), 3)

    for query, embedding in zip(queries, embeddings, strict=True):
        _merge_rows(
            merged,
            query_collection(
                query,
                doc_type="facility_policy",
                locale=locale,
                top_k=per_query_k,
                query_embedding=embedding,
                n_results=min(collection.count(), per_query_k * 3),
            ),
        )

    summary = "\n".join(f"{i}. {q}" for i, q in enumerate(questions, start=1))
    top = _finalize(merged, rerank_query=" ".join(questions))
    return RagRetrievalResult(
        chunks=top,
        summary=summary,
        query="\n---\n".join(queries),
        questions=questions,
    )


async def _retrieve_by_tags(
    transcript: list[dict[str, Any]],
    *,
    locale: str,
    collection: Any,
) -> RagRetrievalResult:
    try:
        summary = await summarize_transcript_for_rag(transcript, locale=locale)
    except Exception:
        return RagRetrievalResult(chunks=[], summary_failed=True)

    if not summary.strip():
        return RagRetrievalResult(chunks=[], summary_failed=True)

    merged: dict[str, dict[str, Any]] = {}
    query = build_facility_policy_query(summary, mode="tags")
    embedding = embed_texts([query])[0]
    tags = parse_policy_summary(summary)
    pathways = pathways_for_summary(tags) or pathways_from_transcript_heuristic(transcript)
    pool = _candidate_pool()

    def _collect(pathway_filter: list[str] | None) -> None:
        _merge_rows(
            merged,
            query_collection(
                query,
                doc_type="facility_policy",
                locale=locale,
                pathways=pathway_filter,
                top_k=pool,
                query_embedding=embedding,
                n_results=min(collection.count(), pool * 3),
            ),
        )

    # Broad retrieval first (no hard pathway exclusion), then *guarantee-include* the
    # safety sections when a passive/active cue is detected — a misclassified tag can
    # never drop the crisis protocol. The reranker orders the final set.
    _collect(None)
    safety = [p for p in (pathways or []) if p in _SAFETY_PATHWAYS]
    must_keys: frozenset[str] = frozenset()
    if safety:
        # Any safety cue pulls BOTH passive and active sections: a passive/active
        # mislabel (residents under-disclose intent) must never hide the more urgent
        # protocol. The content distinction lives in the sections; retrieval shows both.
        _collect(list(_SAFETY_PATHWAYS))
        must_keys = frozenset(
            _chunk_key(r["metadata"])
            for r in merged.values()
            if r["metadata"].get("pathway") in _SAFETY_PATHWAYS
        )

    top = _finalize(merged, rerank_query=summary, must_include_keys=must_keys)
    return RagRetrievalResult(
        chunks=top,
        summary=summary,
        query=query,
    )


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

    if settings.rag_retrieval_mode == "questions":
        return await _retrieve_by_questions(transcript, locale=locale, collection=collection)
    return await _retrieve_by_tags(transcript, locale=locale, collection=collection)


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

"""Facility policy RAG retrieval for analyst exit."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from backend.app.config import settings
from backend.app.safety import transcript_signals_safety_risk
from backend.rag.embeddings import embed_texts
from backend.rag.policy.routing import (
    PATHWAY_ACTIVE,
    PATHWAY_PASSIVE,
    parse_policy_summary,
    pathways_for_summary,
)
from backend.rag.policy.summary import summarize_transcript_for_rag
from backend.rag.query import query_collection
from backend.rag.store import get_policy_collection

_SAFETY_PATHWAYS = {PATHWAY_PASSIVE, PATHWAY_ACTIVE}

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


def _chunk_key(meta: dict[str, Any]) -> str:
    # Dedup at the parent-section level: many child windows collapse to one section.
    parent_id = meta.get("parent_id")
    if parent_id:
        return str(parent_id)
    locale = meta.get("locale", "all")
    section = meta.get("section") or "unknown"
    return f"{locale}:{section}"


def _finalize(
    merged: dict[str, dict[str, Any]],
    *,
    must_include_keys: frozenset[str] = frozenset(),
) -> list[dict[str, Any]]:
    """Cosine-sort, then take top_k.

    ``must_include_keys`` (safety sections) are guaranteed in the output even if they
    would rank below top_k — they are never dropped.
    """
    ranked = sorted(
        merged.values(), key=lambda r: r.get("cosine_similarity") or -1, reverse=True
    )

    must = [r for r in ranked if _chunk_key(r["metadata"]) in must_include_keys]
    rest = [r for r in ranked if _chunk_key(r["metadata"]) not in must_include_keys]

    top = (must + rest)[: settings.rag_top_k]
    for row in must:  # never drop a guaranteed safety section
        if row not in top:
            top.append(row)
    return top


def build_facility_policy_query(text: str) -> str:
    return f"{_TAGS_QUERY_PREFIX}\n{text.strip()}"


def _merge_rows(merged: dict[str, dict[str, Any]], rows: list[dict[str, Any]]) -> None:
    for row in rows:
        key = _chunk_key(row["metadata"])
        existing = merged.get(key)
        row_sim = row.get("cosine_similarity") or -1
        existing_sim = (existing or {}).get("cosine_similarity") or -1
        if existing is None or row_sim > existing_sim:
            merged[key] = row


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
    query = build_facility_policy_query(summary)
    embedding = embed_texts([query])[0]
    tags = parse_policy_summary(summary)
    pathways = pathways_for_summary(tags)
    pool = settings.rag_top_k

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
    # never drop the crisis protocol. Cosine similarity orders the final set.
    #
    # Two independent triggers, either of which forces the safety sections:
    #   1. the LLM summariser tagged a passive/active pathway, and
    #   2. a deterministic scan of the raw transcript for explicit self-harm language.
    # (2) is the hardening backstop: if a small local model under-tags the summary, the
    # literal detector still pulls the escalation protocol. Bias is toward triggering.
    _collect(None)
    llm_safety = [p for p in (pathways or []) if p in _SAFETY_PATHWAYS]
    transcript_safety = transcript_signals_safety_risk(transcript)
    must_keys: frozenset[str] = frozenset()
    if llm_safety or transcript_safety:
        # Any safety cue pulls BOTH passive and active sections: a passive/active
        # mislabel (residents under-disclose intent) must never hide the more urgent
        # protocol. The content distinction lives in the sections; retrieval shows both.
        _collect(list(_SAFETY_PATHWAYS))
        must_keys = frozenset(
            _chunk_key(r["metadata"])
            for r in merged.values()
            if r["metadata"].get("pathway") in _SAFETY_PATHWAYS
        )

    top = _finalize(merged, must_include_keys=must_keys)
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

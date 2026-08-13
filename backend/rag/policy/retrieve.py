"""Facility policy RAG retrieval for analyst exit."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from backend.app.config import settings
from backend.app.safety import transcript_signals_safety_risk
from backend.rag.embeddings import embed_texts
from backend.rag.policy.routing import (
    NON_SAFETY_PATHWAYS,
    PATHWAY_ACTIVE,
    PATHWAY_PASSIVE,
    STATUS_ACTIVE,
    parse_policy_summary,
    pathways_for_summary,
)
from backend.rag.policy.rerank import rerank_chunks
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
    def _rank_score(row: dict[str, Any]) -> float:
        # Prefer the cross-encoder score when reranking ran; else first-stage cosine.
        rr = row.get("rerank_score")
        if rr is not None:
            return rr
        return row.get("cosine_similarity") or -1

    ranked = sorted(merged.values(), key=_rank_score, reverse=True)

    must = [r for r in ranked if _chunk_key(r["metadata"]) in must_include_keys]
    rest = [r for r in ranked if _chunk_key(r["metadata"]) not in must_include_keys]

    top = (must + rest)[: settings.rag_policy_top_k]
    for row in must:  # never drop a guaranteed safety section
        if row not in top:
            top.append(row)
    return top


def build_facility_policy_query(text: str) -> str:
    return f"{_TAGS_QUERY_PREFIX}\n{text.strip()}"


def _fetch_safety_sections(
    collection: Any, locale: str, *, facility_id: str, status: str
) -> list[dict[str, Any]]:
    """Fetch the passive/active safety sections by METADATA, bypassing the vector index.

    This is the hard safety guarantee (Fix 1 + Fix 2): the crisis protocol is pulled from
    Chroma with a ``where`` filter on ``pathway`` — no embedding, no cosine score, no
    similarity threshold, and no dependency on the LLM summary. If a safety cue fires, these
    sections are *always* fetched. Rows carry ``cosine_similarity: None`` so they sort last
    on relevance but are force-kept via ``must_include_keys`` in :func:`_finalize`.
    """
    where = {
        "$and": [
            {"locale": locale},
            {"facility_id": facility_id},
            {"status": status},
            {"pathway": {"$in": list(_SAFETY_PATHWAYS)}},
        ]
    }
    try:
        res = collection.get(where=where, include=["documents", "metadatas"])
    except Exception:
        return []
    documents = res.get("documents") or []
    metadatas = res.get("metadatas") or []
    rows: list[dict[str, Any]] = []
    for doc, meta in zip(documents, metadatas):
        rows.append(
            {
                "text": doc,
                "metadata": meta or {},
                "cosine_similarity": None,
            }
        )
    return rows


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
    facility_id: str = "default",
    status: str = STATUS_ACTIVE,
) -> RagRetrievalResult:
    # The LLM summary drives the *general* semantic query. It is best-effort: if it fails or
    # comes back empty we degrade to safety-only retrieval rather than aborting (Fix 2).
    summary: str | None = None
    summary_failed = False
    try:
        summary = await summarize_transcript_for_rag(transcript, locale=locale)
    except Exception:
        summary_failed = True
    if not summary or not summary.strip():
        summary_failed = True
        summary = None

    merged: dict[str, dict[str, Any]] = {}
    query: str | None = None
    tags: dict[str, str] = {}

    if summary:
        tags = parse_policy_summary(summary)
        # Embed ONLY the natural-language retrieval_focus line — it is written to read like the
        # SOP section we want to match. The machine tag lines (booleans/enums) are decision
        # flags, not search text, and only add noise to the query vector. Fall back to the full
        # summary if the focus line is ever missing.
        focus = tags.get("retrieval_focus", "").strip()
        query = build_facility_policy_query(focus or summary)
        embedding = embed_texts([query])[0]
        pool = settings.rag_policy_top_k
        # "Filter then rank": when enabled, the broad lane cosine-ranks only the non-safety
        # buckets. Safety sections are excluded here on purpose — they are governed solely by
        # the deterministic guarantee-include below, never by cosine leakage into a routine
        # session. Disabled by default (pathways=None searches everything).
        broad_pathways = (
            sorted(NON_SAFETY_PATHWAYS)
            if settings.rag_policy_pathway_filter
            else None
        )
        # Two-stage retrieve when reranking is on: fetch a wider (capped) candidate pool,
        # rerank to relevance, then keep the top `pool`. Off by default → single-stage cosine
        # with the historical pool*3 fetch breadth (behaviour-neutral).
        if settings.rag_policy_rerank:
            fetch_k = settings.rag_policy_candidate_pool
        else:
            fetch_k = pool
        candidates = query_collection(
            query,
            doc_type="facility_policy",
            locale=locale,
            pathways=broad_pathways,
            facility_id=facility_id,
            status=status,
            top_k=fetch_k,
            query_embedding=embedding,
            n_results=min(collection.count(), max(fetch_k, pool * 3)),
        )
        if settings.rag_policy_rerank:
            candidates = rerank_chunks(query, candidates)[:pool]
        _merge_rows(merged, candidates)

    # Safety guarantee-include. Two independent triggers, either of which forces BOTH the
    # passive and active safety sections into the result:
    #   1. the LLM summariser tagged a passive/active pathway, and
    #   2. a deterministic scan of the raw transcript for explicit self-harm language.
    # The sections are fetched BY METADATA (see _fetch_safety_sections) — no embedding, no
    # cosine threshold, no dependency on the summary succeeding. This closes two gaps:
    #   * Fix 1: the crisis protocol can no longer be filtered out by a low similarity score.
    #   * Fix 2: a summariser failure still yields the escalation protocol via trigger (2).
    # Any safety cue pulls BOTH sections because residents under-disclose intent; a
    # passive/active mislabel must never hide the more urgent protocol.
    llm_safety = [p for p in (pathways_for_summary(tags) or []) if p in _SAFETY_PATHWAYS]
    transcript_safety = transcript_signals_safety_risk(transcript)
    must_keys: frozenset[str] = frozenset()
    if llm_safety or transcript_safety:
        _merge_rows(
            merged,
            _fetch_safety_sections(
                collection, locale, facility_id=facility_id, status=status
            ),
        )
        must_keys = frozenset(
            _chunk_key(r["metadata"])
            for r in merged.values()
            if r["metadata"].get("pathway") in _SAFETY_PATHWAYS
        )

    top = _finalize(merged, must_include_keys=must_keys)
    return RagRetrievalResult(
        chunks=top,
        summary=summary,
        summary_failed=summary_failed,
        query=query,
    )


async def retrieve_for_analyst(
    transcript: list[dict[str, Any]],
    *,
    locale: str = "en-SG",
    facility_id: str | None = None,
) -> RagRetrievalResult:
    """Retrieve facility operational SOP chunks for the session locale and facility.

    ``facility_id`` scopes retrieval to one tenant's policy (multi-facility partitioning);
    it defaults to ``settings.rag_default_facility_id``, which matches what single-facility
    ingest stamps — so this is behaviour-neutral until multiple facilities are indexed.
    Retrieval is additionally pinned to the active document version via ``status``.
    """
    collection = get_policy_collection()
    if collection.count() == 0:
        return RagRetrievalResult(chunks=[])

    if not settings.rag_use_llm_summary:
        return RagRetrievalResult(chunks=[])

    return await _retrieve_by_tags(
        transcript,
        locale=locale,
        collection=collection,
        facility_id=facility_id or settings.rag_default_facility_id,
        status=STATUS_ACTIVE,
    )


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

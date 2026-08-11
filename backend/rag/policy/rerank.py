"""Second-stage cross-encoder reranking for policy retrieval.

Chroma cosine gives a candidate pool; a cross-encoder (default BAAI/bge-reranker-base)
re-scores each (query, chunk) pair for far better ordering than single-stage similarity.
Fully optional and gated by ``rag_rerank_enabled`` — if the model or package is
unavailable, retrieval falls back to cosine order without raising.
"""

from __future__ import annotations

from typing import Any

from backend.app.config import settings

_cross_encoder: Any | None = None
_rerank_unavailable = False


def _get_cross_encoder() -> Any | None:
    global _cross_encoder, _rerank_unavailable
    if _rerank_unavailable:
        return None
    if _cross_encoder is None:
        try:
            from sentence_transformers import CrossEncoder

            _cross_encoder = CrossEncoder(settings.rag_rerank_model)
        except Exception:
            # Package or model missing / offline — degrade gracefully to cosine order.
            _rerank_unavailable = True
            return None
    return _cross_encoder


def rerank_rows(
    query: str,
    rows: list[dict[str, Any]],
    *,
    top_k: int | None = None,
) -> list[dict[str, Any]]:
    """Return rows reranked by cross-encoder score (falls back to input order)."""
    if not rows:
        return rows
    if not settings.rag_rerank_enabled:
        return rows[: top_k] if top_k else rows

    model = _get_cross_encoder()
    if model is None:
        return rows[: top_k] if top_k else rows

    pairs = [(query, row.get("text") or "") for row in rows]
    try:
        scores = model.predict(pairs)
    except Exception:
        return rows[: top_k] if top_k else rows

    for row, score in zip(rows, scores, strict=False):
        row["rerank_score"] = float(score)
    ranked = sorted(rows, key=lambda r: r.get("rerank_score", float("-inf")), reverse=True)
    return ranked[: top_k] if top_k else ranked

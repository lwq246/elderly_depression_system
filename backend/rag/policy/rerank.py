"""Optional cross-encoder reranking stage for facility policy retrieval.

Dormant by default: :func:`rerank_chunks` returns the rows unchanged unless a reranker
model is configured via ``settings.rag_policy_reranker_model``. It is wired in as a hook so
turning on a real cross-encoder later is a config change, not a code change.

When a model is set, each candidate is scored against the query with a cross-encoder
(query + full section text), which is far more precise than the bi-encoder cosine used for
first-stage recall — the standard "retrieve wide, rerank narrow" pattern for scale.
"""

from __future__ import annotations

from typing import Any

from backend.app.config import settings

# Cache one loaded model per name so repeated exits don't reload weights.
_RERANKERS: dict[str, Any] = {}


def _load_reranker(model_name: str) -> Any:
    model = _RERANKERS.get(model_name)
    if model is None:
        from sentence_transformers import CrossEncoder

        model = CrossEncoder(model_name)
        _RERANKERS[model_name] = model
    return model


def rerank_chunks(query: str, rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Reorder ``rows`` by cross-encoder relevance to ``query``.

    No-op (returns ``rows`` unchanged) when no reranker model is configured or there is
    nothing to reorder. Each reranked row gets a ``rerank_score`` used downstream for
    ordering in place of the first-stage cosine score.
    """
    model_name = settings.rag_policy_reranker_model
    if not model_name or len(rows) <= 1:
        return rows

    model = _load_reranker(model_name)
    pairs = [(query, row.get("text") or "") for row in rows]
    scores = model.predict(pairs)
    for row, score in zip(rows, scores, strict=False):
        row["rerank_score"] = float(score)
    return sorted(rows, key=lambda r: r.get("rerank_score", 0.0), reverse=True)
